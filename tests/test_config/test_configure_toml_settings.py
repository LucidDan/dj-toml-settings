from dj_toml_settings.config import configure_toml_settings


def test(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "dj_toml_settings.config.get_toml_settings",
        lambda **_: {},
    )

    expected = {}

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_toml_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "dj_toml_settings.config.get_toml_settings",
        lambda **_: {"ALLOWED_HOSTS": ["127.0.0.1"]},
    )

    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_existing_settings(tmp_path):
    expected = {"DEBUG": True, "ALLOWED_HOSTS": ["127.0.0.1"]}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {"ALLOWED_HOSTS": ["127.0.0.1"]}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_empty_existing_settings_empty(tmp_path):
    expected = {"DEBUG": True}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_override_existing_settings(tmp_path):
    expected = {"DEBUG": True}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {"DEBUG": False}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_override_toml_settings(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.3"]}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
ALLOWED_HOSTS = ["127.0.0.2"]
""")

    (tmp_path / "django.toml").write_text("""
[tool.django]
ALLOWED_HOSTS = ["127.0.0.3"]
""")

    actual = {"ALLOWED_HOSTS": ["127.0.0.1"]}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


import pprint
from pathlib import Path


def test_default_settings():
    test_dir = Path(__file__).parent

    expected = {
        "ALLOWED_HOSTS": [],
        "AUTH_PASSWORD_VALIDATORS": [
            {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
            {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
            {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
            {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
        ],
        "BASE_DIR": test_dir,
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": test_dir / "db.sqlite3",
            }
        },
        "DEBUG": False,
        "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
        "DJANGO_TEMPLATE": {
            "APP_DIRS": True,
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        },
        "INSTALLED_APPS": [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ],
        "LANGUAGE_CODE": "en-us",
        "MIDDLEWARE": [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ],
        "ROOT_URLCONF": "project.urls",
        "SECRET_KEY": None,
        "STATIC_URL": "static/",
        "TEMPLATES": [
            {
                "APP_DIRS": True,
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ]
                },
            }
        ],
        "TIME_ZONE": "UTC",
        "USE_I18N": True,
        "USE_TZ": True,
        "WSGI_APPLICATION": "project.wsgi.application",
    }

    actual = {}
    configure_toml_settings(base_dir=test_dir, data=actual)
    pprint.pprint(actual)

    assert expected == actual
