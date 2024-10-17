import pytest
from pathlib import Path

from jhive_previz import dataproc as dataproc
from jhive_previz import main as main


@pytest.fixture
def load_config():
    # TODO: put this in a conftest file
    return main.load_config()


@pytest.fixture
def setup_dataframes(load_config):
    # Create dictionary to store all file names and data frames once loaded
    data_frames = {}
    # load in main catalogue file
    data_frames["cat_filename"] = dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"],
        file_path=dataproc.get_cat_filepath("cat_filename", load_config[0]),
    )
    return data_frames


@pytest.fixture
def create_cat(load_config):
    file_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    return dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"], file_path=file_path
    )


@pytest.fixture()
def test_output_path(monkeypatch):

    # def mock_destbase(*args, **kwargs):
    #    return Path("./")

    monkeypatch.setattr(dataproc, "output_path", Path("./tests/test_output/"))


def test_load_dataframe(create_cat):
    """Test that load_dataframe works as expected"""

    create_cat = dataproc.load_dataframe("cat_filename", create_cat)

    # test that the catalog has been updated
    assert create_cat.loaded == True
    # test that there is actually a dataframe with one of the relevant columns
    assert "id" in create_cat.df.columns


def test_populate_columns(setup_dataframes, load_config):
    """Make sure populate columns works as expected"""

    setup_dataframes = dataproc.populate_column_information(
        setup_dataframes, load_config[0], load_config[1]
    )

    assert "ra" in setup_dataframes["cat_filename"].columns_to_use
    assert len(setup_dataframes["cat_filename"].columns_to_use) == 6


def test_filter_columns(load_config):
    """Make sure that filter_columns is working as expected"""

    # pick a column with a minimum value
    col_name = "f435w_corr_1"
    out_col_name = "abmag_f435w"

    # test data frame
    cat_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    df = dataproc.read_table(cat_path)

    # test that there were values less than min value
    assert df[col_name].min() < load_config[1][out_col_name]["min_value"]

    dataproc.filter_column_values(df, col_name, load_config[1][out_col_name])

    assert df[col_name].min() >= load_config[1][out_col_name]["min_value"]


def test_convert_columns(load_config, setup_dataframes):
    """Make sure that convert columns is working as expected"""

    # populate columns
    setup_dataframes = dataproc.populate_column_information(
        setup_dataframes, load_config[0], load_config[1]
    )

    # load dataframe
    setup_dataframes["cat_filename"] = dataproc.load_dataframe(
        "cat_filename", setup_dataframes["cat_filename"]
    )

    # test there are a lot of columns
    assert len(setup_dataframes["cat_filename"].df.columns) > 6

    # get subset of columns
    # update the dataframe to only include the columns that we want to use
    setup_dataframes["cat_filename"].df = setup_dataframes["cat_filename"].df[
        setup_dataframes["cat_filename"].columns_to_use
    ]

    assert len(setup_dataframes["cat_filename"].df.columns) == len(
        setup_dataframes["cat_filename"].columns_to_use
    )
    assert "f435w_corr_1" in setup_dataframes["cat_filename"].df.columns

    # convert any columns needed
    setup_dataframes["cat_filename"] = dataproc.convert_columns_in_df(
        setup_dataframes["cat_filename"], load_config[1]
    )

    assert "f435w_corr_1" not in setup_dataframes["cat_filename"].df.columns
    assert "abmag_f435w" in setup_dataframes["cat_filename"].df.columns


def test_process_data(load_config, test_output_path):
    """Make sure that process_data is working as expected+"""

    cat_df = dataproc.process_data(load_config[0], load_config[1])

    assert len(load_config[0]["columns_to_use"]) == len(cat_df.columns)
