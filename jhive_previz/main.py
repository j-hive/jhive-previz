from pathlib import Path
import yaml
from typing import Union, Mapping

from . import dataproc
from . import metadata


def validate_config_params(config_params):


    if isinstance(config_params["paths"]["cat_path"], str):
        cat_path = Path(config_params["paths"]["cat_path"])
        full_cat_path = cat_path / config_params["cat_filename"]
        if not full_cat_path.is_file():
            # make sure that the path given leads to the correct file
            raise ValueError(f"cat_path is not a valid path to the file {config_params["cat_filename"]}")
    else:
        # there is no path given to the cat_file
        raise ValueError("cat_path is a required argument, please enter the full path to the catalogue file.")

def read_yaml(file_path: Union[Path, str]) -> Mapping:
    """Function to read in yaml file as dictionary. This uses unsafe load and 
    so should only be done on yaml files in this code package.

    Parameters
    ----------
    file_path : Union[Path, str]
        Path to the file.

    Returns
    -------
    Mapping
        Contents of the file as a dictionary.
    """
    
    with open(file_path, mode="rt",encoding="utf-8") as file:
        config = yaml.unsafe_load(file)
    return config

def load_config():
    config_path = "./base_config.yaml"
    field_path = "./fields.yaml"
    config_params = read_yaml(config_path)
    field_params = read_yaml(field_path)

    return config_params, field_params


if __name__ == "__main__":
    # get the input file path and name of the field
    # and turn them into necessary output file names
    config_params, field_params = load_config()

    # create the csv file
    dataproc.process_data(config_params, field_params)

    # create the metadata json file
    metadata.create_metadata_file(config_params, field_params)
