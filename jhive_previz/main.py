from pathlib import Path
import yaml
from typing import Union, Mapping, Tuple

from . import dataproc
from . import metadata

# Paths to config files
# TODO: where these files are stored and how they are read in requires some thought
config_path = "./base_config.yaml"
field_path = "./fields.yaml"


# Validation functions
def validate_cat_path(config_params: Mapping):
    """Validate that the cat_path and cat_filename lead to an existing file.

    Parameters
    ----------
    config_params : Mapping
        The dictionary of config parameters.

    Raises
    ------
    ValueError
        Raises a ValueError if cat_path is not given, or if an invalid path is given.
    """

    if isinstance(config_params["paths"]["cat_path"], str):
        cat_path = Path(config_params["paths"]["cat_path"])
        full_cat_path = cat_path / config_params["cat_filename"]
        if not full_cat_path.is_file():
            # make sure that the path given leads to the correct file
            raise ValueError(
                f"cat_path is not a valid path to the file {config_params['cat_filename']}"
            )
    else:
        # there is no path given to the cat_file
        raise ValueError(
            "cat_path is a required argument in config.yaml, please enter the full path to the catalogue file."
        )


def validate_output_path(config_params: Mapping):
    """Validates that the output_path exists. If not, creates it.

    Parameters
    ----------
    config_params : Mapping
        The dictionary of config parameters.

    Raises
    ------
    ValueError
        Raises an error if no output path is given.
    """

    if isinstance(config_params["output_path"], str):
        output_path = Path(config_params["output_path"])
        # make sure that output file path exists
        if not output_path.is_dir():

            # if it doesn't, create it
            output_path.parent.mkdir()
    else:
        raise ValueError(
            "output_path is a required argument in config.yaml, please enter the path to the output directory."
        )


# Loading functions


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

    with open(file_path, mode="rt", encoding="utf-8") as file:
        config = yaml.unsafe_load(file)
    return config


def load_config() -> Tuple[Mapping, Mapping]:
    """Loads in the two config files and returns them as dictionaries.

    Returns
    -------
    Tuple[Mapping, Mapping]
        The config_params and field_params dictionaries.
    """

    # read in the files
    config_params = read_yaml(config_path)
    field_params = read_yaml(field_path)

    return config_params, field_params


# Organizational function


def main():
    """The main function. This reads in the two config files, validates that
    the required parameters exist, and then creates the new filtered and converted
    data table, writes it to a csv in the output folder, and writes the metadata
    json file to the same folder.
    """

    # get the config parameters
    config_params, field_params = load_config()

    # validate and create the output path if necessary
    validate_cat_path(config_params)
    validate_output_path(config_params)

    # create the csv file
    cat_df = dataproc.process_data(config_params, field_params)

    # create the metadata json file
    metadata.create_metadata_file(config_params, field_params, cat_df)
