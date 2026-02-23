from dj_toml_settings.toml_parser import Parser


def test_integer_access_creates_list(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django.TEMPLATES.0]
BACKEND = "django.template.backends.django.DjangoTemplates"
""")

    actual = Parser(path).parse_file()

    # This currently fails (returns a dict)
    assert isinstance(actual["TEMPLATES"], list)
    assert len(actual["TEMPLATES"]) == 1
    assert actual["TEMPLATES"][0]["BACKEND"] == "django.template.backends.django.DjangoTemplates"


def test_integer_access_updates_existing_list(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
TEMPLATES = [
    { "BACKEND" = "old" }
]

[tool.django.apps.myapp]
TEMPLATES.0 = { "BACKEND" = "new" }
""")

    actual = Parser(path).parse_file()

    # This currently fails (replaces list with dict {"0": ...})
    assert isinstance(actual["TEMPLATES"], list)
    assert actual["TEMPLATES"][0]["BACKEND"] == "new"


def test_integer_access_multiple_indices(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django.TEMPLATES.0]
BACKEND = "zero"
[tool.django.TEMPLATES.1]
BACKEND = "one"
""")

    actual = Parser(path).parse_file()

    assert isinstance(actual["TEMPLATES"], list)
    assert len(actual["TEMPLATES"]) == 2
    assert actual["TEMPLATES"][0]["BACKEND"] == "zero"
    assert actual["TEMPLATES"][1]["BACKEND"] == "one"
