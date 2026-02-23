import logging
from pathlib import Path
from typing import Any

from dj_toml_settings.toml_parser import Parser

logger = logging.getLogger(__name__)

TOML_SETTINGS_FILES = [
    "pyproject.toml",
    "django.toml",
]


def configure_toml_settings(
    data: dict, base_dir: Path = Path("."), toml_settings_files: list[str] | None = None
) -> None:
    data.update(get_toml_settings(data=data, base_dir=base_dir, toml_settings_files=toml_settings_files))


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
