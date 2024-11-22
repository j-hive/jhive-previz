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
        file_format=load_config[1]["cat_filename"]["file_format"],
    )
    return data_frames


@pytest.fixture
def create_cat(load_config):
    file_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    return dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"],
        file_path=file_path,
        file_format=load_config[1]["cat_filename"]["file_format"],
    )


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

    assert "stellar_mass" in setup_dataframes["cat_filename"].input_columns
    assert len(setup_dataframes["cat_filename"].input_columns) == 4


def test_filter_columns(load_config):
    """Make sure that filter_columns is working as expected"""

    # pick a column with a minimum value
    col_name = "f333w_corr_1"
    out_col_name = "abmag_f333w"

    # test data frame
    cat_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    df = dataproc.read_table(cat_path, load_config[1]["cat_filename"]["file_format"])

    # test that there were values less than min value
    assert (
        df[col_name].min()
        < load_config[1]["cat_filename"]["columns"][out_col_name]["filt_min_val"]
    )

    filtered_col = dataproc.filter_column_values(
        df[col_name], load_config[1]["cat_filename"]["columns"][out_col_name]
    )

    # make sure the nans were added and also that the minimum is now above the min
    assert np.isnan(filtered_col.min())
    assert (
        np.nanmin(filtered_col)
        >= load_config[1]["cat_filename"]["columns"][out_col_name]["filt_min_val"]
    )


def test_process_column_data(load_config, setup_dataframes):
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
    setup_dataframes["cat_filename"] = dataproc.process_column_data(
        setup_dataframes["cat_filename"], load_config[1]["cat_filename"]
    )

    assert "f333w_corr_1" not in setup_dataframes["cat_filename"].df.columns
    assert "abmag_f333w" in setup_dataframes["cat_filename"].df.columns
    assert len(setup_dataframes["cat_filename"].df.columns) == len(
        setup_dataframes["cat_filename"].input_columns
    )

    # make sure new values are log of old ones
    assert setup_dataframes["cat_filename"].df["mass"].iloc[10] == np.log10(
        old_df["stellar_mass"].iloc[10]
    )

    # make sure that values in new dataframe match a converted value from old dataframe
    assert setup_dataframes["cat_filename"].df["abmag_f333w"].iloc[
        10
    ] == conv.flux_to_mag(
        old_df["f333w_corr_1"].iloc[10],
        load_config[1]["cat_filename"]["columns"]["abmag_f333w"],
    )

    # make sure that filtering happened
    assert (
        setup_dataframes["cat_filename"].df["abmag_f444w"].min()
        > old_df["f444w_corr_1"].min()
    )


def test_process_data(get_processed_data, load_config):
    """Make sure that process_data is working as expected."""

    assert len(load_config[0]["columns_to_use"]["cat_filename"]) == len(
        get_processed_data.columns
    )


def test_with_two_catalogues(load_config, test_output_path, create_output_path):
    """Making sure that the process data function works as expected when using two catalogues"""

    # alter the config to include columns from second data file
    load_config[0]["columns_to_use"]["ez_filename"] = ["id", "abmag_f480w"]

    new_df = dataproc.process_data(load_config[0], load_config[1], create_output_path)

    # make sure the column was added to the table correctly and there are blanks where there was no data
    assert "abmag_f480w" in new_df.columns
    assert np.isnan(new_df["abmag_f480w"].iloc[27])
    assert "mass" in new_df.columns
