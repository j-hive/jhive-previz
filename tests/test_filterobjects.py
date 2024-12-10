import pandas as pd
import numpy as np
from astropy.table import Table
from jhive_previz import filterobjects as fo


def test_filter_catalog(
    load_config,
):
    """Test that the filter_catalog function results in a dataframe of the correct size, and checks a few of the values to make sure they are as expected."""

    # load in the catalogue here to test they're the same
    test_df = pd.read_csv("./tests/test_data/test-data.csv")

    ingest_df = fo.filter_catalog(
        load_config[0]["columns_to_use"]["cat_filename"],
        load_config[1]["cat_filename"]["columns"],
        test_df,
    )

    assert len(ingest_df.columns) == 2
    # make sure that it's True and false in a couple of the correct places
    assert ingest_df.loc[3, "f333w_corr_1"] == False
    assert ingest_df.loc[3, "f444w_corr_1"] == False
    assert ingest_df.loc[4, "f444w_corr_1"] == True


def test_create_and_write_flag_file(load_config, create_output_path):
    """Test that the create_and_write_flag_file function writes the flag file out correctly. Also checks that some of the values are as expected."""

    fo.create_and_write_flag_file(load_config[0], load_config[1], create_output_path)

    # check that the file exists
    out_filepath = create_output_path / "ingest_flags.fits"
    assert out_filepath.is_file()

    # read in file
    tab = Table.read(out_filepath)

    # check some of the values
    assert tab["ingest_viz"][0] == True
    assert tab["ingest_viz"][3] == False
    assert tab["ingest_viz"][16] == True
