import importlib
import logging
import os
from pathlib import Path
from typing import Any

from typeguard import typechecked

from dj_toml_settings.toml_parser import Parser

logger = logging.getLogger(__name__)

TOML_SETTINGS_FILES = [
    "pyproject.toml",
    "django.toml",
]


@typechecked
def configure_toml_settings(
    data: dict | None = None, base_dir: Path = Path("."), toml_settings_files: list[str] | None = None
) -> None:
    """Configure Django settings from TOML files.

    Args:
        base_dir: Base directory to look for TOML files
        data: Dictionary to update with settings from TOML files

    Returns:
        The updated dictionary with settings from TOML files
    """

    toml_settings = get_toml_settings(data=data, base_dir=base_dir, toml_settings_files=toml_settings_files)

    if data is not None:
        data.update(toml_settings)
    else:
        if django_settings_module := os.getenv("DJANGO_SETTINGS_MODULE"):
            module = importlib.import_module(django_settings_module)

            for k, v in toml_settings.items():
                setattr(module, k, v)

        raise RuntimeError("No DJANGO_SETTINGS_MODULE environment variable configured")


def get_toml_settings(
    data: dict | None = None, base_dir: Path = Path("."), toml_settings_files: list[str] | None = None
) -> dict[str, Any]:
    toml_settings_files = toml_settings_files or TOML_SETTINGS_FILES
    data = data or {}

    for settings_file_name in toml_settings_files:
        settings_path = base_dir / settings_file_name

        if settings_path.exists():
            file_data = Parser(settings_path, data=data.copy()).parse_file()
            data.update(file_data)

    return data
