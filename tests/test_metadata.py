import pytest
import pandas as pd

from jhive_previz import metadata
from jhive_previz import dataproc


def test_get_desired_column_metadata(load_config, get_processed_data):
    """Make sure that get_desired_column_metadata works as expected"""

    new_metadata = metadata.get_desired_column_metadata(
        load_config[1], load_config[0]["columns_to_use"], get_processed_data
    )

    # make sure we got all the metadata we wanted
    assert set(new_metadata.keys()) == set(
        load_config[0]["columns_to_use"]["cat_filename"]
    )
    assert "display" in new_metadata["id"]


@pytest.mark.xfail
def test_fail_get_desired_column_metadata(load_config):
    """Test that the function fails when calling for a column that doesn't exist"""

    # try other columns to use
    new_cols_to_use = load_config[0]["columns_to_use"]
    new_cols_to_use.append("testcol")
    error_metadata = metadata.get_desired_column_metadata(
        load_config[1], new_cols_to_use
    )

    assert set(error_metadata.keys()) != set(new_cols_to_use)


def test_add_min_max_val_to_json(load_config, get_processed_data):
    """Test that add_min_max_val_to_json works as expected"""

    # turn config file into json
    new_metadata = metadata.get_desired_column_metadata(
        load_config[1], load_config[0]["columns_to_use"], get_processed_data
    )

    # add min and max to json
    updated_metadata = metadata.add_min_max_val_to_json(
        new_metadata, get_processed_data
    )

    # check that min and max val keys exist in the new metadata json
    assert "min_val" in updated_metadata["abmag_f333w"].keys()
    assert "max_val" in updated_metadata["mass"].keys()

    # check that the max value in the metadata matches what we expect
    assert updated_metadata["mass"]["max_val"] == get_processed_data["mass"].max()


def test_add_top_level_metadata(load_config, get_processed_data):
    """Test that add_top_level_metadata works as expected."""

    new_metadata = metadata.get_desired_column_metadata(
        load_config[1], load_config[0]["columns_to_use"], get_processed_data
    )

    final_metadata = metadata.add_top_level_metadata(
        new_metadata, load_config[0], get_processed_data
    )

    # make sure metadata output is formatted as expected
    assert "columns" in final_metadata.keys()
    assert final_metadata["field_name"] == load_config[0]["field_name"]
    assert set(final_metadata["columns"].keys()) == set(
        load_config[0]["columns_to_use"]["cat_filename"]
    )
