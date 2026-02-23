import logging
import os
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import parse_qs, urlparse

from dateutil import parser as dateparser
from dj_typed_settings import parse_cache_url, parse_database_url
from typeguard import typechecked

from dj_toml_settings.exceptions import InvalidActionError

logger = logging.getLogger(__name__)


def get_value_by_path(data: dict, path: str) -> Any:
    """Helper to get a value from a nested dictionary using a dot-separated path."""
    current: Any = data
    parts = path.split(".")

    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


class DictParser:
    data: dict
    value: dict
    key: str

    def __init__(self, data: dict, value: dict):
        self.data = data
        self.value = value

        if not hasattr(self, "key"):
            raise NotImplementedError("Missing key attribute")

        self.key = self.add_prefix_to_key(self.key)

    def match(self) -> bool:
        return self.key in self.value

    @typechecked
    def add_prefix_to_key(self, key: str) -> str:
        """Gets the key for the special operator."""

        return f"${key}"

    def parse(self, *args, **kwargs):
        raise NotImplementedError("parse() not implemented")


class EnvParser(DictParser):
    key: str = "env"

    def parse(self) -> Any:
        default_special_key = self.add_prefix_to_key("default")
        default_value = self.value.get(default_special_key)

        env_value = self.value[self.key]
        value = os.getenv(env_value, default_value)

        return value


class PathParser(DictParser):
    key: str = "path"

    def __init__(self, data: dict, value: dict, path: Path):
        super().__init__(data, value)
        self.path = path

    def parse(self) -> Any:
        self.file_name = self.value[self.key]
        value = self.resolve_file_name()

        return value

    @typechecked
    def resolve_file_name(self) -> Path:
        """Parse a path string relative to a base path.

        Args:
            file_name: Relative or absolute file name.
            path: Base path to resolve file_name against.
        """

        current_path = Path(self.path).parent if self.path.is_file() else self.path

        return Path((current_path / self.file_name).resolve())


class ValueParser(DictParser):
    key = "value"

    def parse(self) -> Any:
        return self.value[self.key]


class InsertParser(DictParser):
    key = "insert"

    def __init__(self, data: dict, value: dict, data_key: str):
        super().__init__(data, value)
        self.data_key = data_key

    def parse(self) -> Any:
        insert_data = get_value_by_path(self.data, self.data_key)

        # If it doesn't exist, default to an empty list
        if insert_data is None:
            insert_data = []

        # Check the existing value is an array
        if not isinstance(insert_data, list):
            raise InvalidActionError(f"`insert` cannot be used for value of type: {type(insert_data)}")

        # Insert the data
        index_key = self.add_prefix_to_key("index")
        index = self.value.get(index_key, len(insert_data))

        insert_data.insert(index, self.value[self.key])

        return insert_data


class NoneParser(DictParser):
    key = "none"

    def match(self) -> bool:
        return super().match() and self.value.get(self.key) is not None

    def parse(self) -> Any:
        return None


class DatabaseParser(DictParser):
    key = "db"

    def match(self) -> bool:
        return super().match() or self.add_prefix_to_key("database") in self.value

    def parse(self) -> Any:
        key = self.key if self.key in self.value else self.add_prefix_to_key("database")
        return parse_database_url(str(self.value[key]))


class CacheParser(DictParser):
    key = "cache"

    def match(self) -> bool:
        return super().match()

    def parse(self) -> Any:
        return parse_cache_url(str(self.value[self.key]))


class EmailParser(DictParser):
    key = "email"

    def match(self) -> bool:
        return super().match()

    def parse(self) -> Any:
        return parse_email_url(str(self.value[self.key]))


def parse_email_url(url: str) -> dict:
    """Simple email URL parser since dj-typed-settings doesn't provide one directly."""
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)

    settings = {
        "EMAIL_BACKEND": f"django.core.mail.backends.{parsed_url.scheme}.EmailBackend",
        "EMAIL_HOST": parsed_url.hostname,
        "EMAIL_PORT": parsed_url.port,
        "EMAIL_HOST_USER": parsed_url.username,
        "EMAIL_HOST_PASSWORD": parsed_url.password,
    }

    if "tls" in params:
        settings["EMAIL_USE_TLS"] = params["tls"][0].lower() == "true"
    if "ssl" in params:
        settings["EMAIL_USE_SSL"] = params["ssl"][0].lower() == "true"

    # Handle some common backend name remappings if necessary
    if parsed_url.scheme == "smtp":
        settings["EMAIL_BACKEND"] = "django.core.mail.backends.smtp.EmailBackend"
    elif parsed_url.scheme == "console":
        settings["EMAIL_BACKEND"] = "django.core.mail.backends.console.EmailBackend"
    elif parsed_url.scheme == "file":
        settings["EMAIL_BACKEND"] = "django.core.mail.backends.filebased.EmailBackend"
    elif parsed_url.scheme == "memory":
        settings["EMAIL_BACKEND"] = "django.core.mail.backends.locmem.EmailBackend"
    elif parsed_url.scheme == "dummy":
        settings["EMAIL_BACKEND"] = "django.core.mail.backends.dummy.EmailBackend"

    return settings


class GenericTypeParser(DictParser):
    def __init__(self, data: dict, value: dict):
        # We don't set a default key here as it will be determined during match
        self.data = data
        self.value = value
        self.matched_type: str | None = None

    def match(self) -> bool:
        for t in TypeParser.SUPPORTED_TYPES:
            if self.add_prefix_to_key(t) in self.value:
                self.matched_type = t
                return True
        return False

    def parse(self) -> Any:
        if not self.matched_type:
            raise ValueError("No type matched")

        key = self.add_prefix_to_key(self.matched_type)
        return TypeParser(self.data, self.value).cast(self.matched_type, self.value[key])


class TypeParser(DictParser):
    key = "type"

    SUPPORTED_TYPES: ClassVar[list[str]] = [
        "bool",
        "int",
        "str",
        "float",
        "decimal",
        "datetime",
        "date",
        "time",
        "timedelta",
        "url",
        "db",
        "database",
        "cache",
        "email",
        "path",
    ]

    def parse(self, resolved_value: Any) -> Any:
        value_type = self.value[self.key]

        if not isinstance(value_type, str):
            raise ValueError(f"Type must be a string, got {type(value_type).__name__}")

        return self.cast(value_type, resolved_value)

    def cast(self, value_type: str, resolved_value: Any) -> Any:
        try:
            match value_type:
                case "bool":
                    match resolved_value:
                        case str():
                            return resolved_value.lower() == "true"
                        case int():
                            return bool(resolved_value)
                        case bool():
                            return resolved_value
                        case _:
                            raise ValueError(
                                f"Type must be a string, int, or bool, got {type(resolved_value).__name__}"
                            )
                case "int":
                    return int(resolved_value)
                case "str":
                    return str(resolved_value)
                case "float":
                    return float(resolved_value)
                case "decimal":
                    return Decimal(str(resolved_value))
                case "datetime":
                    return dateparser.parse(resolved_value)
                case "date":
                    return dateparser.parse(resolved_value).date()
                case "time":
                    return dateparser.parse(resolved_value).time()
                case "timedelta":
                    return parse_timedelta(resolved_value)
                case "url":
                    return urlparse(str(resolved_value))
                case "db" | "database":
                    return parse_database_url(str(resolved_value))
                case "cache":
                    return parse_cache_url(str(resolved_value))
                case "email":
                    return parse_email_url(str(resolved_value))
                case "path":
                    return Path(resolved_value).resolve()
                case _:
                    raise ValueError(f"Unsupported type: {value_type}")
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Failed to convert {resolved_value!r} to {value_type}: {e}")

            raise ValueError(f"Failed to convert {resolved_value!r} to {value_type}: {e}") from e


def parse_timedelta(value):
    if isinstance(value, int | float):
        return timedelta(seconds=value)
    elif not isinstance(value, str):
        raise ValueError(f"Unsupported type for timedelta: {type(value).__name__}")

    # Pattern to match both space-separated and combined formats like '7w2d'
    pattern = r"(?:\s*(\d+\.?\d*)([u|ms|s|m|h|d|w]+))"
    matches = re.findall(pattern, value, re.IGNORECASE)

    if not matches and value.strip():
        raise ValueError(f"Invalid timedelta format: {value}")

    unit_map = {
        "u": "microseconds",
        "ms": "milliseconds",
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "w": "weeks",
    }
    kwargs = {}

    for num_str, unit in matches:
        try:
            num = float(num_str)
        except ValueError as e:
            raise ValueError(f"Invalid number in timedelta: {num_str}") from e

        if unit not in unit_map:
            raise ValueError(f"Invalid time unit: {unit}")

        key = unit_map[unit]
        kwargs[key] = kwargs.get(key, 0) + num

    return timedelta(**kwargs)
