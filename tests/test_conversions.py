import pytest
import pandas as pd
import numpy as np

from jhive_previz import conversions as conv
from jhive_previz import dataproc


@pytest.mark.parametrize(
    "input_unit,output_unit,expected",
    [
        ("microJansky", "magnitude", conv.flux_to_mag),
        pytest.param("Jansky", "magnitude", conv.flux_to_mag, marks=pytest.mark.xfail),
    ],
)
def test_get_conversion_function(input_unit, output_unit, expected):
    """Make sure that get_conversion_function works as expected. Tests that it returns the flux_to_mag function when given the right input and output units, and fails when those units don't match any conversion functions."""

    test = conv.get_conversion_function(input_unit, output_unit)

    assert test == conv.flux_to_mag


def test_flux_to_mag(load_config):
    """Make sure that flux_to_mag works as expected. Test that the flux to mag conversion function converts the items in a column as expected."""

    # read in test data
    file_path = dataproc.get_cat_filepath("cat_filename", load_config[0])
    df = dataproc.read_table(file_path, "ascii.csv")

    # convert a column
    converted = conv.flux_to_mag(
        df["f444w_corr_1"], load_config[1]["cat_filename"]["columns"]["abmag_f444w"]
    )

    # test that the object returned is correct and the converted value matches
    test_result = (
        -2.5 * np.log10(df["f444w_corr_1"].iloc[6])
        + load_config[1]["cat_filename"]["columns"]["abmag_f444w"]["zero_point"]
    )
    assert converted.iloc[6] == test_result
    assert isinstance(converted, pd.Series)
