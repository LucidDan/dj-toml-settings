"""
Django settings in TOML.

To see the settings, look at `django.toml`
"""

from dj_toml_settings import configure_toml_settings, load_env

# Load environment variables from .env file
# For variables that should be kept a secret and follow the https://12factor.net
load_env()

# Configure settings based on TOML file
configure_toml_settings(data=globals())
