import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from jhive_previz import dataproc, utils
from jhive_previz import main as main
from jhive_previz import conversions as conv


@pytest.fixture
def setup_dataframes(load_config):
    """Create the dictionary to store all Catalogue objects."""
    data_frames = {}
    # load in main catalogue file
    data_frames["cat_filename"] = dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"],
        file_path=utils.get_cat_filepath("cat_filename", load_config[0]),
        file_format=load_config[1]["cat_filename"]["file_format"],
    )
    return data_frames


@pytest.fixture
def create_cat(load_config):
    """Creates a catalogue object for the cat_filename catalogue."""
    file_path = utils.get_cat_filepath("cat_filename", load_config[0])
    return dataproc.Catalogue(
        file_name=load_config[0]["file_names"]["cat_filename"],
        file_path=file_path,
        file_format=load_config[1]["cat_filename"]["file_format"],
    )


def test_load_dataframe(create_cat):
    """Test that load_dataframe works as expected. Tests that it updates the loaded parameter, and that the loaded dataframe in the catalogue matches the dataframe loaded in just via pandas in the test."""

    create_cat = dataproc.load_dataframe("cat_filename", create_cat)

    # load in the catalogue here to test they're the same
    test_df = pd.read_csv("./tests/test_data/test-data.csv")

    pd.testing.assert_frame_equal(test_df, create_cat.df)

    # test that the catalog has been updated
    assert create_cat.loaded == True


def test_populate_columns(setup_dataframes, load_config):
    """Make sure populate columns works as expected. Test that the Catalogue variables are all being populated as expected for the main catalogue file."""

    setup_dataframes = dataproc.populate_column_information(
        setup_dataframes, load_config[0], load_config[1]
    )

    assert "stellar_mass" in setup_dataframes["cat_filename"].input_columns
    assert len(setup_dataframes["cat_filename"].input_columns) == 4
    assert setup_dataframes["cat_filename"].decimals_to_round["abmag_f444w"] == 3
    assert len(setup_dataframes["cat_filename"].conversion_functions) == 4
    assert setup_dataframes["cat_filename"].conversion_functions[0] == None
    assert "abmag_f480w" not in setup_dataframes["cat_filename"].output_columns


def test_filter_columns(load_config):
    """Make sure that filter_columns is working as expected when given a minimum value. Tests that the column minimum becomes nan when filtering, and that the minimum value that is not nan is above the minimum given when filtering."""

    # pick a column with a minimum value
    col_name = "f333w_corr_1"
    out_col_name = "abmag_f333w"

    # test data frame
    cat_path = utils.get_cat_filepath("cat_filename", load_config[0])
    df = utils.read_table(cat_path, load_config[1]["cat_filename"]["file_format"])

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
    """Make sure that process_columns converts and filters the column data for the main catalogue file as expected."""

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
    """Make sure that the processed catalogue has the same number of columns as given in the columns_to_use parameter."""

    assert len(load_config[0]["columns_to_use"]["cat_filename"]) == len(
        get_processed_data.columns
    )


def test_with_two_catalogues(load_config, test_output_path, create_output_path):
    """Making sure that the process data function works as expected when using two catalogues"""

    # alter the config to include columns from second data file
    load_config[0]["columns_to_use"]["ez_filename"] = ["id", "abmag_f480w"]

    new_df = dataproc.process_data(
        load_config[0], load_config[1], create_output_path, use_flag_file=False
    )

    # make sure the column was added to the table correctly and there are blanks where there was no data
    assert "abmag_f480w" in new_df.columns
    assert np.isnan(new_df["abmag_f480w"].iloc[27])
    assert "mass" in new_df.columns


def test_with_ingest_flags(load_config, test_output_path, create_output_path):
    """Test that the process data function works as expected when use_flag_file = True."""

    flag_file_path = Path("./tests/test_data/ingest_flags.fits")
    df_raw, df_core = dataproc.process_data(
        load_config[0],
        load_config[1],
        create_output_path,
        use_flag_file=True,
        flag_file_path=flag_file_path,
    )

    assert len(df_core) == 49
    assert len(df_raw) == 2
    assert 1 in df_raw["id"].values
    assert 51 in df_core["id"].values
