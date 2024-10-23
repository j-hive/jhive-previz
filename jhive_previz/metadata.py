import json
from pathlib import Path
import pandas as pd
from typing import Mapping, Union, Dict, List


def get_metadata_output_path(config_params: Mapping) -> Path:
    """Uses the config parameters to generate the full path to the metadata
    output file.

    Parameters
    ----------
    config_params : Mapping
        The dictionary of config parameters.

    Returns
    -------
    Path
        The full path to the output metadata file.
    """

    # turn output base path into Path object
    output_path = Path(config_params["output_path"])
    metadata_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".json"
    )
    return output_path / metadata_output_filename


def get_desired_column_metadata(
    field_params: Mapping, columns_to_use: List[str]
) -> Dict:
    """Creates a metadata dictionary from the field parameters with only the desired columns from the main config.

    Parameters
    ----------
    field_params : Mapping
        The metadata for all columns.
    columns_to_use : List[str]
        The columns to be included in the metadata file.

    Returns
    -------
    Dict
        The dictionary of metadata for the desired columns.
    """
    # get the subsection of the field_params that matches the columns to use
    initial_json_dict = {c: field_params[c] for c in columns_to_use}

    return initial_json_dict


def add_min_max_val_to_json(initial_json_dict: Dict, whole_cat: pd.DataFrame) -> Dict:
    """Takes an existing metadata dictionary, and adds the min and max value of each column
    that contains ints or floats to the dictionary.

    Parameters
    ----------
    initial_json_dict : Dict
        The metadata dictionary for the pandas table, with a key for each column name.
    whole_cat : pd.DataFrame
        The pandas table with the data.

    Returns
    -------
    Dict
        The updated metadata dictionary.
    """

    for colname in initial_json_dict.keys():

        # only add in a min/max value if the column is an int or float type
        if initial_json_dict[colname]["data_type"] in ["float", "int"]:
            min_val = whole_cat[colname].min()
            max_val = whole_cat[colname].max()

            if initial_json_dict[colname]["data_type"] == "int":
                # make sure these values are integers if the column is an integer type
                min_val = int(min_val)
                max_val = int(max_val)

            # add ths min and max values to the metadata json
            initial_json_dict[colname]["min_val"] = min_val
            initial_json_dict[colname]["max_val"] = max_val

    return initial_json_dict


def write_json(output_metadata_path: Path, initial_json_dict: Dict):
    """Writes out a dictionary to a json file.

    Parameters
    ----------
    output_metadata_path : Path
        The full path to write the file to, including file name.
    initial_json_dict : Dict
        The dictionary to write to a json.
    """
    # write out json metadata file
    with open(output_metadata_path, "w") as f:
        json.dump(initial_json_dict, f, indent=4)


def create_metadata_file(
    config_params: Mapping, field_params: Mapping, whole_cat: pd.DataFrame
):
    """Creates a metadata file for the given datatable, using metadata from field_params and generating additional values as necessary.
      It has keys for each column, and is written as a json.

    Parameters
    ----------
    config_params : Mapping
        The config parameters dictionary.
    field_params : Mapping
        The field parameters dictionary.
    whole_cat : pd.DataFrame
        The dataframe to generate metadata for.
    """

    # get the full path to write out metadata to
    output_metdata_path = get_metadata_output_path(config_params)

    # get the relevant columns in the json
    initial_json_dict = get_desired_column_metadata(
        field_params, config_params["columns_to_use"]
    )
    initial_json_dict = add_min_max_val_to_json(initial_json_dict, whole_cat)

    # write out file
    write_json(output_metdata_path, initial_json_dict)
