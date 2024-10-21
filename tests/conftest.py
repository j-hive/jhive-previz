import pytest

from jhive_previz import main


@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):

    monkeypatch.setattr(main, "config_path", "./tests/test_config.yaml")
    monkeypatch.setattr(main, "field_path", "./tests/test_fields.yaml")


@pytest.fixture(autouse=True)
def load_config(mock_config_paths):
    # TODO: put this in a conftest file
    return main.load_config()
