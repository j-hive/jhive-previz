import pytest

from jhive_previz import main


@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):
    """Monkeypatch the config filepaths to use the test config files."""
    monkeypatch.setattr(main, "config_path", "./tests/test_config.yaml")
    monkeypatch.setattr(main, "field_path", "./tests/test_fields.yaml")


@pytest.fixture(autouse=True)
def load_config(mock_config_paths):
    """Load in the config files."""
    return main.load_config()
