from dj_toml_settings.config import get_toml_settings
from dj_toml_settings.toml_parser import Parser


def test_insert_into_existing(tmp_path):
    # First file defines the base
    toml_content_1 = """
[tool.django]
ALLOWED_HOSTS = ["127.0.0.1"]
"""
    # Second file inserts into it
    toml_content_2 = """
[tool.django]
ALLOWED_HOSTS = { "$insert" = "example.localhost" }
"""
    base_dir = tmp_path
    (base_dir / "pyproject.toml").write_text(toml_content_1)
    (base_dir / "django.toml").write_text(toml_content_2)

    settings = get_toml_settings(base_dir=base_dir)

    assert settings["ALLOWED_HOSTS"] == ["127.0.0.1", "example.localhost"]


def test_db_type(tmp_path):
    toml_content = """
[tool.django]
DATABASES = { default = { "$db" = "sqlite:///:memory:" } }
"""
    toml_file = tmp_path / "django.toml"
    toml_file.write_text(toml_content)

    parser = Parser(toml_file)
    settings = parser.parse_file()

    assert settings["DATABASES"]["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert settings["DATABASES"]["default"]["NAME"] == ":memory:"


def test_cache_type(tmp_path):
    toml_content = """
[tool.django]
CACHES = { default = { "$cache" = "redis://127.0.0.1:6379/1" } }
"""
    toml_file = tmp_path / "django.toml"
    toml_file.write_text(toml_content)

    parser = Parser(toml_file)
    settings = parser.parse_file()

    assert settings["CACHES"]["default"]["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert settings["CACHES"]["default"]["LOCATION"] == "redis://127.0.0.1:6379/1"
