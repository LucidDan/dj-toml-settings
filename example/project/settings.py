"""
Django settings in TOML.

To see the settings, look at `django.toml`
"""

from dj_toml_settings import configure_toml_settings

configure_toml_settings(data=globals())
