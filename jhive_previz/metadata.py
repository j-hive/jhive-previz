import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Mapping, Union, Dict, List


def get_metadata_output_path(output_path: Path) -> Path:
    """Uses the config parameters to generate the full path to the metadata
    output file.

    Parameters
    ----------
    output_path : Path
        The full path to the directory where the file will be saved.

    Returns
    -------
    Path
        The full path to the output metadata file.
    """

    metadata_output_filename = "metadata.json"
    return output_path / metadata_output_filename


def get_desired_column_metadata(
    field_params: Mapping, columns_to_use: Dict, whole_cat: pd.DataFrame
) -> Dict:
    """Creates a metadata dictionary from the field parameters with only the desired columns from the main config.

    Parameters
    ----------
    field_params : Mapping
        The metadata for all columns.
    columns_to_use : Dict[str]
        The dictionary of columns to be included in the metadata file.

    Returns
    -------
    Dict
        The dictionary of metadata for the desired columns.
    """
    # get the subsection of the field_params that matches the columns to use for each fields file
    # where those columns also exist in the dataframe
    initial_json_dict = {}

    for filename, columns in columns_to_use.items():
        for c in columns:
            if c in whole_cat.columns:
                initial_json_dict[c] = field_params[filename]["columns"][c]

    return initial_json_dict


def add_min_max_val_to_json(initial_json_dict: Dict, whole_cat: pd.DataFrame) -> Dict:
    """Takes an existing metadata dictionary, and adds the min and max value of each column
    that contains ints or floats to the dictionary. It also removes any metadata columns from the
    dictionary that don't exist in the dataframe.

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

            if whole_cat[colname].dropna().empty:
                # add in a min and max of 0 if the column is empty
                min_val = 0.0
                max_val = 0.0
            else:
                # calculate the max and min
                min_val = whole_cat[colname].min()
                max_val = whole_cat[colname].max()

            if initial_json_dict[colname]["data_type"] == "int":
                # make sure these values are integers if the column is an integer type
                min_val = int(min_val)
                max_val = int(max_val)

            # add the min and max values to the metadata json
            initial_json_dict[colname]["min_val"] = min_val
            initial_json_dict[colname]["max_val"] = max_val

    return initial_json_dict


def add_top_level_metadata(
    initial_json_dict: Dict, config_params: Mapping, whole_cat: pd.DataFrame
) -> Dict:
    """Adds the top level metadata to the final output dictionary. Currently adds the field name and number of objects in the final dataframe.

    Parameters
    ----------
    initial_json_dict : Dict
        Dictionary of column metadata.
    config_params : Mapping
        Dictionary of configuration parameters.
    whole_cat : pd.DataFrame
        The dataframe of data.

    Returns
    -------
    Dict
        The final dictionary of metadata with top level metadata and column metadata under 'columns' key.
    """

    final_json_dict = {
        "field_name": config_params["field_name"],
        "columns": initial_json_dict,
    }

    # add number of objects
    final_json_dict["num_objects"] = len(whole_cat)

    return final_json_dict


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
    config_params: Mapping,
    field_params: Mapping,
    whole_cat: pd.DataFrame,
    output_path: Path,
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
    output_path : Path
        The full path to the directory where the output files will be saved.
    """

    # get the full path to write out metadata to
    output_metdata_path = get_metadata_output_path(output_path)

    # get the relevant columns in the json
    initial_json_dict = get_desired_column_metadata(
        field_params, config_params["columns_to_use"], whole_cat
    )
    initial_json_dict = add_min_max_val_to_json(initial_json_dict, whole_cat)

    # add top level metadata
    final_json_dict = add_top_level_metadata(
        initial_json_dict, config_params, whole_cat
    )

    # write out file
    write_json(output_metdata_path, final_json_dict)
