import logging
import re
from pathlib import Path
from typing import Any

from typeguard import typechecked

from dj_toml_settings.exceptions import InvalidActionError

logger = logging.getLogger(__name__)


class VariableParser:
    data: dict
    value: str

    def __init__(self, data: dict, value: str):
        self.data = data
        self.value = value

    def parse(self) -> Any:
        value: Any = self.value
        has_path = False

        while True:
            val_to_search = value if isinstance(value, str) else str(value)
            match = re.search(r"\$\{(\w+)\}", val_to_search)
            if not match:
                break

            data_key = match.group(1)
            variable = self.data.get(data_key)

            if variable is not None:
                # If the variable is the entire string, return it in its original type
                if match.group(0) == val_to_search:
                    return variable

                if isinstance(variable, list | dict) or callable(variable):
                    raise InvalidActionError(f"Cannot interpolate {type(variable)} into a string: '{val_to_search}'")

                if isinstance(variable, Path):
                    has_path = True

                # Otherwise, smush it into the string
                value = combine_bookends(str(value), match, variable)
            else:
                logger.warning(f"Missing variable substitution {match.group(0)}")
                # Break to avoid infinite loop if replacement is skipped
                break

        if has_path:
            return Path(value)

        # Try to cast to int or float if it looks like one
        if isinstance(value, str):
            try:
                return int(value)
            except Exception:  # noqa: S110
                pass

            try:
                return float(value)
            except Exception:  # noqa: S110
                pass

        return value


@typechecked
def combine_bookends(original: str, match: re.Match, middle: Any) -> str:
    """Get the beginning of the original string before the match, and the
    end of the string after the match and smush the replaced value in between
    them to generate a new string.
    """

    start_idx = match.start()
    start = original[:start_idx]

    end_idx = match.end()
    ending = original[end_idx:]

    return start + str(middle) + ending
