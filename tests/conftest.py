import pytest

from jhive_previz import main
from jhive_previz import dataproc


# @pytest.fixture(autouse=True)
# def mock_config_paths(monkeypatch):
#     """Monkeypatch the config filepaths to use the test config files."""
#     monkeypatch.setattr(main, "config_path", "./tests/test_config.yaml")
#     monkeypatch.setattr(main, "field_path", "./tests/test_fields.yaml")


@pytest.fixture(autouse=True)
def load_config():
    """Load in the config files."""
    return main.load_config(
        "./tests/test_config.yaml",
        ["./tests/test_fields.yaml", "./tests/test2_fields.yaml"],
    )


@pytest.fixture(autouse=True)
def test_output_path(monkeypatch, load_config, tmp_path):

    monkeypatch.setitem(load_config[0], "output_path", tmp_path)


@pytest.fixture
def get_processed_data(load_config, test_output_path):
    return dataproc.process_data(load_config[0], load_config[1])
