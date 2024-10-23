from pathlib import Path
import yaml
from typing import Union, Mapping, Tuple
import typer
from typing_extensions import Annotated

from . import dataproc
from . import metadata


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
        full_cat_path = cat_path / config_params["file_names"]["cat_filename"]
        if not full_cat_path.is_file():
            # make sure that the path given leads to the correct file
            raise ValueError(
                f"cat_path is not a valid path to the file {config_params['file_names']['cat_filename']}"
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


def load_config(config_path: Path, field_path: Path) -> Tuple[Mapping, Mapping]:
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


def validate_config_paths(config_path: str, field_path: str):
    """Validates that the provided paths lead to files that exist.

    Parameters
    ----------
    config_path : str
        The full path to the config yaml file.
    field_path : str
        The full path to the fields yaml file.

    Raises
    ------
    FileExistsError
        Raises an error if either of the files do not exist at the given path.
    """

    config_path = Path(config_path)
    field_path = Path(field_path)

    if not config_path.is_file():
        raise FileExistsError(f"Config file at {config_path} does not exist.")
    if not field_path.is_file():
        raise FileExistsError(f"Fields file at {field_path} does not exist.")


# Organizational function
def process_data_and_write_metadata(
    config_path: Annotated[
        str, typer.Option(help="The full path and file name of the base config file.")
    ] = "./base_config.yaml",
    field_path: Annotated[
        str, typer.Option(help="The full path and file name of the fields config file.")
    ] = "./fields.yaml",
):
    """The main function. This reads in the two config files, validates that
    the required parameters exist, and then creates the new filtered and converted
    data table, writes it to a csv in the output folder, and writes the metadata
    json file to the same folder.

    Parameters
    ----------
    config_path: str, default = './base_config.yaml'
        The full path and file name of the base config yaml file.
    field_path: str, default = './fields.yaml'
        The full path and file name of the fields yaml file.
    """

    # get the config parameters
    validate_config_paths(config_path, field_path)
    config_params, field_params = load_config(config_path, field_path)

    # validate and create the output path if necessary
    validate_cat_path(config_params)
    validate_output_path(config_params)

    # create the csv file
    cat_df = dataproc.process_data(config_params, field_params)

    # create the metadata json file
    metadata.create_metadata_file(config_params, field_params, cat_df)


def main():
    typer.run(process_data_and_write_metadata)
