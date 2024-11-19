import pytest
from jhive_previz import docsutil


def test_convert_yaml_metadata_to_csv():
    input_file = "./config_files/dja_fields.yaml"
    output_file = "./jhive_previz/docs/dja_catalogue_fields_table_tomerge.csv"

    docsutil.convert_yaml_metadata_to_csv(input_file, output_file)

    assert output_file.is_file()

    # read in file and check that it makes sense


def test_merge_doc_csvs():

    input_file = "./jhive_previz/docs/dja_catalogue_fields_table_tomerge.csv"
    new_file = "./jhive_previz/docs/dja_catalogue_fields_table.csv"
    write_file = "./jhive_previz/docs/dja_catalogue_fields_table_toedit.csv"
    docsutil.merge_doc_csvs(new_file, input_file, write_file)
