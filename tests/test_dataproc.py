import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from jhive_previz import dataproc as dataproc
from jhive_previz import main as main
from jhive_previz import conversions as conv


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
def test_output_path(monkeypatch, load_config):

    # def mock_destbase(*args, **kwargs):
    #    return Path("./")

    monkeypatch.setitem(load_config[0], "output_path", "./tests/test_output/")


@pytest.fixture()
def mock_config():

    # load in a test config file?
    # or just return the variables I need?
    configdict = {
        "paths": {"cat_path": "./data/"},
        "field_name": "test-field",
        "file_names": {"cat_filename": "testfile.csv"},
        "output_file_suffix": "_test_output",
        "output_path": "./tests/output/",
        "columns_to_use": ["id", "mass", "abmag_f333w", "abmag_f444w"],
    }

    return configdict


@pytest.fixture()
def mock_fields():
    fieldsdict = {
        "id": {
            "display": "DJA Source ID",
            "data_type": "int",
            "output_units": None,
            "input_units": None,
            "file_name": "cat_filename",
            "input_column_name": "id",
            "output_num_decimals": None,
        },
        "mass": {
            "display": "Stellar Mass",
            "output_units": "log Solar Masses",
            "input_units": "Solar Masses",
            "input_column_name": "stellar_mass",
            "is_magnitude": False,
            "data_type": "float",
            "output_num_decimals": 3,
            "file_name": "cat_filename",
            "filt_max_val": None,
            "filt_min_val": 0.0,
        },
        "abmag_f333w": {
            "display": "Magnitude (F333W)",
            "output_units": "magnitude",
            "input_units": "microJansky",
            "input_column_name": "f333w_corr_1",
            "is_magnitude": True,
            "data_type": "float",
            "output_num_decimals": 3,
            "file_name": "cat_filename",
            "filt_max_val": None,
            "filt_min_val": 0.0,
            "wl_micron": 0.330,
            "zero_point": 28.9,
        },
        "abmag_f444w": {
            "display": "Magnitude (F444W)",
            "output_units": "magnitude",
            "input_units": "Jansky",
            "input_column_name": "f444w_corr_1",
            "is_magnitude": True,
            "data_type": "float",
            "output_num_decimals": 3,
            "file_name": "cat_filename",
            "filt_max_val": None,
            "filt_min_val": 0.0,
            "wl_micron": 0.440,
            "zero_point": 28.9,
        },
    }
    return fieldsdict


@pytest.fixture()
def mock_data():

    id_col = np.arange(1, 52, 1)
    x1 = np.linspace(0, 50, 50)
    # add in a value to be filtered out
    x1 = np.insert(x1, 3, -99.0)

    x2 = np.linspace(-1, 15, 51)

    # make pandas table
    data = {"id": id_col, "stellar_mass": x1, "f333w_corr_1": x2, "f444w_corr_1": x1}

    return pd.DataFrame(data)


def test_load_dataframe(create_cat):
    """Test that load_dataframe works as expected"""

    create_cat = dataproc.load_dataframe("cat_filename", create_cat)

    # test that the catalog has been updated
    assert create_cat.loaded == True
    # test that there is actually a dataframe with one of the relevant columns
    assert "id" in create_cat.df.columns
    assert len(create_cat.df.columns) == 5


def test_populate_columns(setup_dataframes, load_config):
    """Make sure populate columns works as expected"""

    setup_dataframes = dataproc.populate_column_information(
        setup_dataframes, load_config[0], load_config[1]
    )

    assert "stellar_mass" in setup_dataframes["cat_filename"].columns_to_use
    assert len(setup_dataframes["cat_filename"].columns_to_use) == 4


def test_filter_columns(load_config):
    """Make sure that filter_columns is working as expected"""

    # pick a column with a minimum value
    col_name = "f333w_corr_1"
    out_col_name = "abmag_f333w"

    # test data frame
    cat_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    df = dataproc.read_table(cat_path)

    # test that there were values less than min value
    assert df[col_name].min() < load_config[1][out_col_name]["filt_min_val"]

    filtered_col = dataproc.filter_column_values(
        df[col_name], load_config[1][out_col_name]
    )

    # make sure the nans were added and also that the minimum is now above the min
    assert np.isnan(filtered_col.min())
    assert np.nanmin(filtered_col) >= load_config[1][out_col_name]["filt_min_val"]


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
    assert len(setup_dataframes["cat_filename"].df.columns) > 4

    # make sure we have a copy of the original dataframe
    old_df = setup_dataframes["cat_filename"].df

    # convert any columns needed
    setup_dataframes["cat_filename"] = dataproc.convert_columns_in_df(
        setup_dataframes["cat_filename"], load_config[1]
    )

    assert "f333w_corr_1" not in setup_dataframes["cat_filename"].df.columns
    assert "abmag_f333w" in setup_dataframes["cat_filename"].df.columns
    assert len(setup_dataframes["cat_filename"].df.columns) == len(
        setup_dataframes["cat_filename"].columns_to_use
    )

    # make sure values stayed the same outside of filtering
    assert (
        setup_dataframes["cat_filename"].df["abmag_f444w"].iloc[10]
        == old_df["f444w_corr_1"].iloc[10]
    )
    # make sure new values are log of old ones
    assert setup_dataframes["cat_filename"].df["mass"].iloc[10] == np.log10(
        old_df["stellar_mass"].iloc[10]
    )

    # make sure that values in new dataframe match a converted value from old dataframe
    assert setup_dataframes["cat_filename"].df["abmag_f333w"].iloc[
        10
    ] == conv.flux_to_mag(
        old_df["f333w_corr_1"].iloc[10], load_config[1]["abmag_f333w"]
    )

    # make sure that filtering happened
    assert (
        setup_dataframes["cat_filename"].df["abmag_f444w"].min()
        > old_df["f444w_corr_1"].min()
    )


def test_log_convert_and_filter_columns(mock_data, mock_config, mock_fields):
    """Make sure that convert and filter columns work as expected"""

    # mock data
    old_df = mock_data.copy()
    file_name = mock_fields["mass"]["file_name"]
    config_cols = [value.get("input_column_name") for value in mock_fields.values()]

    cat_dict = {
        "cat_filename": dataproc.Catalogue(
            file_name=file_name,
            loaded=True,
            df=mock_data,
        )
    }

    # populate the catalogue values
    cat_dict = dataproc.populate_column_information(cat_dict, mock_config, mock_fields)

    # make sure that there are some columns that aren't converted
    assert None in cat_dict["cat_filename"].conversion_functions

    cat_dict["cat_filename"] = dataproc.convert_columns_in_df(
        cat_dict["cat_filename"], mock_fields
    )

    # make sure values stayed the same outside of filtering
    assert (
        cat_dict["cat_filename"].df["abmag_f444w"].iloc[10]
        == old_df["f444w_corr_1"].iloc[10]
    )
    # make sure new values are log of old ones
    assert cat_dict["cat_filename"].df["mass"].iloc[10] == np.log10(
        old_df["stellar_mass"].iloc[10]
    )

    # make sure that values in new dataframe match a converted value from old dataframe
    assert cat_dict["cat_filename"].df["abmag_f333w"].iloc[10] == conv.flux_to_mag(
        old_df["f333w_corr_1"].iloc[10], mock_fields["abmag_f333w"]
    )

    # make sure that filtering happened
    assert (
        cat_dict["cat_filename"].df["abmag_f444w"].min() > old_df["f444w_corr_1"].min()
    )


def test_process_data(load_config, test_output_path):
    """Make sure that process_data is working as expected."""

    cat_df = dataproc.process_data(load_config[0], load_config[1])

    assert len(load_config[0]["columns_to_use"]) == len(cat_df.columns)
