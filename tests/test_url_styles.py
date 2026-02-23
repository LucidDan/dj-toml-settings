from datetime import date, datetime, time, timedelta
from decimal import Decimal
from urllib.parse import ParseResult

from dj_toml_settings.toml_parser import Parser


def test_db_shorthand(tmp_path):
    toml_content = """
[tool.django]
DATABASES = { default = { "$db" = "sqlite:///:memory:" } }
"""
    toml_file = tmp_path / "shorthand.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["DATABASES"]["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_db_explicit(tmp_path):
    toml_content = """
[tool.django]
DATABASES = { default = { "$value" = "sqlite:///:memory:", "$type" = "db" } }
"""
    toml_file = tmp_path / "explicit.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["DATABASES"]["default"]["ENGINE"] == "django.db.backends.sqlite3"


def test_cache_shorthand(tmp_path):
    toml_content = """
[tool.django]
CACHES = { default = { "$cache" = "redis://127.0.0.1:6379/1" } }
"""
    toml_file = tmp_path / "shorthand_cache.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["CACHES"]["default"]["BACKEND"] == "django.core.cache.backends.redis.RedisCache"


def test_cache_explicit(tmp_path):
    toml_content = """
[tool.django]
CACHES = { default = { "$value" = "redis://127.0.0.1:6379/1", "$type" = "cache" } }
"""
    toml_file = tmp_path / "explicit_cache.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["CACHES"]["default"]["BACKEND"] == "django.core.cache.backends.redis.RedisCache"


def test_email_shorthand(tmp_path):
    toml_content = """
[tool.django]
EMAIL = { "$email" = "smtp://user:pass@smtp.example.com:587" }
"""
    toml_file = tmp_path / "shorthand_email.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["EMAIL"]["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"


def test_email_explicit(tmp_path):
    toml_content = """
[tool.django]
EMAIL = { "$value" = "smtp://user:pass@smtp.example.com:587", "$type" = "email" }
"""
    toml_file = tmp_path / "explicit_email.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["EMAIL"]["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"


def test_shorthand_with_aliases(tmp_path):
    toml_content = """
[tool.django]
DB1 = { "$database" = "sqlite:///:memory:" }
"""
    toml_file = tmp_path / "aliases_direct.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["DB1"]["ENGINE"] == "django.db.backends.sqlite3"


def test_explicit_with_aliases(tmp_path):
    toml_content = """
[tool.django]
DB1 = { "$value" = "sqlite:///:memory:", "$type" = "database" }
"""
    toml_file = tmp_path / "explicit_aliases.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["DB1"]["ENGINE"] == "django.db.backends.sqlite3"


def test_universal_shorthands(tmp_path):
    toml_content = """
[tool.django]
INT_VAL = { "$int" = "42" }
BOOL_VAL = { "$bool" = "true" }
FLOAT_VAL = { "$float" = "3.14" }
STR_VAL = { "$str" = 123 }
DECIMAL_VAL = { "$decimal" = "10.50" }
DATETIME_VAL = { "$datetime" = "2023-01-01 12:00:00" }
DATE_VAL = { "$date" = "2023-01-01" }
TIME_VAL = { "$time" = "12:00:00" }
TIMEDELTA_VAL = { "$timedelta" = "1h" }
URL_VAL = { "$url" = "https://example.com" }
"""
    toml_file = tmp_path / "universal.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()

    assert settings["INT_VAL"] == 42
    assert settings["BOOL_VAL"] is True
    assert settings["FLOAT_VAL"] == 3.14
    assert settings["STR_VAL"] == "123"
    assert settings["DECIMAL_VAL"] == Decimal("10.50")
    assert isinstance(settings["DATETIME_VAL"], datetime)
    assert isinstance(settings["DATE_VAL"], date)
    assert isinstance(settings["TIME_VAL"], time)
    assert settings["TIMEDELTA_VAL"] == timedelta(hours=1)
    assert isinstance(settings["URL_VAL"], ParseResult)


def test_nested_universal_shorthands(tmp_path):
    toml_content = """
[tool.django]
PORT = { "$int" = { "$env" = "PORT", "$default" = "8000" } }
"""
    toml_file = tmp_path / "nested_universal.toml"
    toml_file.write_text(toml_content)
    settings = Parser(toml_file).parse_file()
    assert settings["PORT"] == 8000
