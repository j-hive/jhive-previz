import pytest
import pandas as pd
from jhive_previz import docsutil


def test_convert_yaml_metadata_to_csv(tmp_path):
    """Make sure that convert_yaml_metadata_to_csv is working as intended."""
    input_file = "./tests/test_fields.yaml"
    output_path = tmp_path / "dja_catalogue_fields_table_tomerge.csv"

    docsutil.convert_yaml_metadata_to_csv(input_file, output_path)

    assert output_path.is_file()

    # read in file and check that it makes sense
    # alternatively have a file that is what the merged file shoud look like and compare to that
    df = pd.read_csv(output_path)
    assert "data type" in df.columns
    assert "abmag_f444w" in df["column name"].values
    l = len(df)
    assert df["display"].iloc[l - 1] == "Magnitude (F480W)"


def test_merge_doc_csvs(tmp_path):
    """Testing that merge_doc_csvs is working as intended"""

    input_path = "./tests/test_catalogue_fields_table.csv"
    old_path = tmp_path / "test_catalogue_fields_table.csv"

    df = pd.read_csv(input_path)

    # add a description column and overwrite old file
    l = len(df)
    df["description"] = ["descriptions here"] * l
    df.to_csv(old_path, index=False)

    # add a new column to original df
    test_df = df.drop("description", axis=1)
    test_df["test_col"] = ["testing"] * l
    row_dict = {
        "column name": ["abmag_f090w"],
        "display": ["Magnitude (F090W)"],
        "data type": ["float"],
        "output units": ["magnitudes"],
        "input column name": ["f090w_corr_1"],
        "input units": ["uJy"],
        "test_col": ["testing1"],
    }
    new_row = pd.DataFrame(row_dict)
    new_df = pd.concat([test_df, new_row])
    new_path = tmp_path / "test_catalogue_fields_table_tomerge.csv"
    new_df.to_csv(new_path, index=False)

    # add a new row

    write_file = tmp_path / "test_catalogue_fields_table_toedit.csv"
    docsutil.merge_doc_csvs(old_path, new_path, write_file)

    # test that file exists and has appropriate contents
    assert write_file.is_file()

    test_df = pd.read_csv(write_file)
    assert "description" in test_df.columns
    assert "test_col" in test_df.columns
    assert "abmag_f090w" in test_df["column name"].values
    assert "abmag_f444w" in test_df["column name"].values
    assert len(test_df.columns) == 8
