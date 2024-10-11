import pytest

from jhive_previz import dataproc as dataproc
from jhive_previz import main as main


@pytest.fixture
def load_config():
    return main.load_config()


@pytest.fixture
def create_cat(load_config):
    file_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    return dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"], file_path=file_path
    )


def test_load_dataframe(create_cat):
    """Test that load_dataframe works as expected"""

    create_cat = dataproc.load_dataframe("cat_filename", create_cat)

    # test that the catalog has been updated
    assert create_cat.loaded == True
    # test that there is actually a dataframe with one of the relevant columns
    assert "id" in create_cat.df.columns
