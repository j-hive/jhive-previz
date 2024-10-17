import json
from pathlib import Path
import pandas as pd
from typing import Mapping, Union, Dict, List


def get_metadata_output_path(config_params: Mapping) -> Path:

    # turn output base path into Path object
    output_path = Path(config_params["output_path"])
    metadata_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".json"
    )
    return output_path / metadata_output_filename


# def read_json_file(file_path: Union[Path, str]) -> Mapping:
#     with open(file_path, "r") as f:
#         json_file = json.load(f)

#     return json_file


def read_csv_pandas(data_file_path: Union[Path, str]) -> pd.DataFrame:
    # read in the .csv
    whole_cat = pd.read_csv(data_file_path)
    return whole_cat


# def add_abmag_keys_to_json(initial_json_dict, whole_cat, filt_info):
#     # add in the abmag keys to the initial_json dictionary

#     # get the relevant column names
#     colnames = list(whole_cat.columns)

#     mag_col_names = [colname for colname in colnames if colname.startswith("abmag_")]

#     # iterate over each column name and add object to json metadata
#     for tmp_key in mag_col_names:
#         tmp_dict = filt_info[tmp_key.replace("abmag_", "")]
#         tmp_filt = tmp_dict["display"]
#         tmp_dict["display"] = f"Magnitude ({tmp_filt})"
#         tmp_dict["is_magnitude"] = True
#         tmp_dict["filt_name"] = tmp_filt
#         new_key = tmp_key
#         tmp_dict["data_type"] = "float"

#         initial_json_dict[new_key] = tmp_dict


#     return initial_json_dict


def get_desired_column_metadata(
    field_params: Mapping, columns_to_use: List[str]
) -> Dict:

    # TODO: do we care if one of the columns in columns_to_use is not in field_params?
    # I think this issue would likely be encountered in dataproc first
    # but check if we should add something here to check for that
    initial_json_dict = {c: field_params[c] for c in columns_to_use}

    return initial_json_dict
    # for c in columns_to_use:
    #     initial_json_dict[c] = field_params[c]


def add_min_max_val_to_json(initial_json_dict: Dict, whole_cat: pd.DataFrame):

    # Adding min_val and max_val to JSON

    for colname in initial_json_dict.keys():

        # only add in a min/max value if the column is an int or float type
        if initial_json_dict[colname]["data_type"] in ["float", "int"]:
            min_val = whole_cat[colname].min()
            max_val = whole_cat[colname].max()

            if initial_json_dict[colname]["data_type"] == "int":
                min_val = int(min_val)
                max_val = int(max_val)

        initial_json_dict[colname]["min_val"] = min_val
        initial_json_dict[colname]["max_val"] = max_val

    return initial_json_dict


def write_json(output_metadata_path, initial_json_dict):
    # write out json metadata file
    with open(output_metadata_path, "w") as f:
        json.dump(initial_json_dict, f, indent=4)


def create_metadata_file(
    config_params: Mapping, field_params: Mapping, whole_cat: pd.DataFrame
):
    # get the full path to write out metadata to
    output_metdata_path = get_metadata_output_path(config_params)

    # get the relevant columns in the json
    initial_json_dict = get_desired_column_metadata(
        field_params, config_params["columns_to_use"]
    )
    initial_json_dict = add_min_max_val_to_json(initial_json_dict, whole_cat)

    # write out file
    write_json(output_metdata_path, initial_json_dict)
