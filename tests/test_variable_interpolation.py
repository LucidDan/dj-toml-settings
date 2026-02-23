import pytest

from dj_toml_settings.exceptions import InvalidActionError
from dj_toml_settings.toml_parser import Parser


def test_variable_interpolation_in_string(tmp_path):
    toml_content = """
[tool.django]
BASE_URL = "https://example.com"
LOGIN_URL = "${BASE_URL}/login"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["LOGIN_URL"] == "https://example.com/login"


def test_variable_interpolation_in_path_operator(tmp_path):
    toml_content = """
[tool.django]
BASE_DIR = { "$path" = "." }
DB_NAME = { "$path" = "${BASE_DIR}/db.sqlite3" }
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    expected_path = (tmp_path / "db.sqlite3").resolve()
    assert settings["DB_NAME"] == expected_path


def test_variable_interpolation_deep_nesting(tmp_path):
    toml_content = """
[tool.django]
VERSION = "v1"
API = { url = "https://api.example.com/${VERSION}", timeout = 30 }
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["API"]["url"] == "https://api.example.com/v1"


def test_variable_interpolation_multiple_vars(tmp_path):
    toml_content = """
[tool.django]
PROTOCOL = "https"
DOMAIN = "example.com"
URL = "${PROTOCOL}://${DOMAIN}/index"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["URL"] == "https://example.com/index"


def test_variable_interpolation_type_preservation(tmp_path):
    toml_content = """
[tool.django]
DEBUG_VAL = true
DEBUG = "${DEBUG_VAL}"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["DEBUG"] is True


def test_variable_interpolation_int_casting(tmp_path):
    toml_content = """
[tool.django]
VAL = 123
RESULT = "${VAL}4"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["RESULT"] == 1234
    assert isinstance(settings["RESULT"], int)


def test_variable_interpolation_float_casting(tmp_path):
    toml_content = """
[tool.django]
VAL = 12.3
RESULT = "${VAL}4"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()
    assert settings["RESULT"] == 12.34
    assert isinstance(settings["RESULT"], float)


def test_variable_interpolation_list_error(tmp_path):
    # If a list is used in a partial match, it should raise an error
    toml_content = """
[tool.django]
MY_LIST = [1, 2, 3]
RESULT = "Prefix ${MY_LIST}"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    with pytest.raises(InvalidActionError, match="Cannot interpolate <class 'list'> into a string"):
        Parser(toml_file).parse_file()


def test_variable_interpolation_dict_error(tmp_path):
    # If a dict is used in a partial match, it should raise an error
    toml_content = """
[tool.django]
MY_DICT = { a = 1 }
RESULT = "Prefix ${MY_DICT}"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    with pytest.raises(InvalidActionError, match="Cannot interpolate <class 'dict'> into a string"):
        Parser(toml_file).parse_file()


def test_variable_interpolation_callable_error(tmp_path):
    def my_func():
        return "hello"

    toml_content = """
[tool.django]
RESULT = "Prefix ${MY_FUNC}"
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    with pytest.raises(InvalidActionError, match="Cannot interpolate <class 'function'> into a string"):
        Parser(toml_file, data={"MY_FUNC": my_func}).parse_file()


def test_variable_interpolation_database_path(tmp_path):
    toml_content = """
[tool.django]
BASE_DIR = { "$path" = "." }

[tool.django.DATABASES.default]
ENGINE = "django.db.backends.sqlite3"
NAME = { "$path" = "${BASE_DIR}/db.sqlite3" }
"""
    toml_file = tmp_path / "test.toml"
    toml_file.write_text(toml_content)

    settings = Parser(toml_file).parse_file()

    # BASE_DIR should be resolved to tmp_path
    assert settings["BASE_DIR"] == tmp_path.resolve()

    # NAME should be resolved to tmp_path / db.sqlite3
    expected_db_path = (tmp_path / "db.sqlite3").resolve()
    assert settings["DATABASES"]["default"]["NAME"] == expected_db_path
