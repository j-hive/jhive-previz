import pytest
import pandas as pd
import numpy as np

from jhive_previz import conversions as conv
from jhive_previz import dataproc


def test_get_conversion_function():
    """Make sure that get_conversion_function works as expected"""

    test = conv.get_conversion_function("microJansky", "magnitude")

    assert test == conv.flux_to_mag


def test_flux_to_mag(load_config):
    """Make sure that flux_to_mag works as expected"""

    file_path = dataproc.get_data_output_filepath(load_config[0])
    df = pd.read_csv(file_path)

    converted = conv.flux_to_mag(df["abmag_f444w"], load_config[1]["abmag_f444w"])

    test_result = (
        -2.5 * np.log10(df["abmag_f444w"].iloc[6])
        + load_config[1]["abmag_f444w"]["zero_point"]
    )
    assert converted.iloc[6] == test_result
    assert isinstance(converted, pd.Series)
