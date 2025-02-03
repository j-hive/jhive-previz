import pytest
import pandas as pd
import numpy as np
from astropy.table import Table
from jhive_previz import filterobjects as fo
from jhive_previz import utils


@pytest.fixture
def change_SNR_cut(monkeypatch):
    monkeypatch.setattr(fo, "SNR_MAG", 4)
    monkeypatch.setattr(fo, "NUM_FLAGS", 1)


def test_filter_catalog(load_config, change_SNR_cut):
    """Test that the filter_catalog function results in a dataframe of the correct size, and checks a few of the values to make sure they are as expected."""

    # load in the catalogue here to test they're the same
    test_df = pd.read_csv("./tests/test_data/test-data.csv")

    ingest_df = fo.filter_catalog(
        load_config[0]["columns_to_use"]["cat_filename"],
        load_config[1]["cat_filename"]["columns"],
        test_df,
    )

    assert len(ingest_df.columns) == 3
    # make sure that it's True and false in a couple of the correct places
    assert ingest_df.loc[3, "ingest_f333w"] == False
    assert ingest_df.loc[3, "ingest_f444w"] == False
    assert ingest_df.loc[4, "ingest_f444w"] == True


def test_create_and_write_flag_file(load_config, create_output_path, change_SNR_cut):
    """Test that the create_and_write_flag_file function writes the flag file out correctly. Also checks that some of the values are as expected."""

    fo.create_and_write_flag_file(load_config[0], load_config[1], create_output_path)

    # check that the file exists
    out_filepath = create_output_path / "ingest_flags.fits"
    assert out_filepath.is_file()

    # read in file
    created_df = utils.read_table(out_filepath, "fits")

    # test that it's equal to the pre-created ingest_flags.fits
    test_df = utils.read_table("./tests/test_data/ingest_flags.fits", "fits")
    pd.testing.assert_frame_equal(created_df, test_df)
