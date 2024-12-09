from pathlib import Path
import yaml
from typing import Union, Mapping, Tuple, List, Dict
import typer
from typing_extensions import Annotated

from . import dataproc
from . import metadata
from . import filterobjects


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


def create_and_validate_output_path(config_params: Mapping) -> Path:
    """Validates that the output_path exists. If not, creates it.

    Parameters
    ----------
    config_params : Mapping
        The dictionary of config parameters.

    Returns
    -------
    output_path : Path
        The full path to the directory where the output files will be saved.

    Raises
    ------
    ValueError
        Raises an error if no output path is given.
    """

    if isinstance(config_params["output_path"], str) or isinstance(
        config_params["output_path"], Path
    ):
        output_path = (
            Path(config_params["output_path"])
            / config_params["version"]
            / config_params["field_name"]
        )
        # make sure that output file path exists
        if not output_path.is_dir():

            # if it doesn't, create it
            output_path.mkdir(parents=True)
    else:
        raise ValueError(
            "output_path is a required argument in config.yaml, please enter the path to the output directory."
        )

    return output_path


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


def load_config(
    config_path: Path, field_paths: List[Path]
) -> Tuple[Mapping, List[Mapping]]:
    """Loads in the two config files and returns them as dictionaries.

    Parameters
    ----------
    config_path: Path
        The full path to the base config yaml file.
    field_paths: List[Path]
        The full paths to the fields yaml files.

    Returns
    -------
    Tuple[Mapping, Dict[Mapping]]
        The config_params and field_params dictionaries.
    """

    # read in the config file
    config_params = read_yaml(config_path)

    # read the field params files into a dictionary
    field_params = {}

    for i in range(0, len(field_paths)):
        field_param = read_yaml(field_paths[i])
        field_params[field_param["file_name"]] = field_param

    return config_params, field_params


def validate_config_paths(
    config_path: str, field_paths: List[str]
) -> Tuple[Path, List[Path]]:
    """Validates that the provided paths lead to files that exist.

    Parameters
    ----------
    config_path : str
        The full path to the config yaml file.
    field_paths : List[str]
        The full paths to the fields yaml files.

    Returns
    -------
    config_path : Path
        The full path to the config yaml file as a Path object.
    field_paths : List[Path]
        The full paths to the fields yaml files as Path objects.

    Raises
    ------
    FileExistsError
        Raises an error if either of the files do not exist at the given path.
    """

    config_path = Path(config_path)
    new_field_paths = []

    # validate the config file exists
    if not config_path.is_file():
        raise FileExistsError(f"Config file at {config_path} does not exist.")

    # make sure a field path is given and that it exists
    if len(field_paths) <= 0:
        raise ValueError("No field paths given")

    if len(field_paths) == 1:
        new_field_paths = [Path(field_paths[0])]

        if not new_field_paths[0].is_file():
            raise FileExistsError(f"Fields file at {field_paths} does not exist.")

    else:
        # iterate through given field paths and check if they exist
        for fp in field_paths:
            field_path = Path(fp)
            if not field_path.is_file():
                raise FileExistsError(f"Fields file at {field_path} does not exist.")

            new_field_paths.append(field_path)

    return config_path, new_field_paths


# Organizational functions
def process_data_and_write_metadata(
    config_path: Annotated[
        str, typer.Option(help="The full path and file name of the base config file.")
    ] = "./config_files/v1.0/abell2744_config.yaml",
    field_paths: Annotated[
        List[str],
        typer.Option(help="A list of full paths to the field config files."),
    ] = [
        "./metadata_files/v1.0/dja_fields.yaml",
        "./metadata_files/v1.0/db_fields.yaml",
        "./metadata_files/v1.0/mf_fields.yaml",
        "./metadata_files/v1.0/umap_fields.yaml",
    ],
):
    """The main function. This reads in the two config files, validates that
    the required parameters exist, and then creates the new filtered and converted
    data table, writes it to a csv in the output folder, and writes the metadata
    json file to the same folder.

    Parameters
    ----------
    config_path: str, default = './config_files/v1.0/abell2744_config.yaml'
        The full path and file name of the base config yaml file.
    field_path: List[str], default = ["./metadata_files/v1.0/dja_fields.yaml",
        "./metadata_files/v1.0/db_fields.yaml",
        "./metadata_files/v1.0/mf_fields.yaml",
        "./metadata_files/v1.0/umap_fields.yaml",]
        The full path and file name of the fields yaml file.
    """

    # get the config parameters
    config_path, field_paths = validate_config_paths(config_path, field_paths)
    config_params, field_params = load_config(config_path, field_paths)

    # validate and create the output path if necessary
    validate_cat_path(config_params)
    output_path = create_and_validate_output_path(config_params)

    # create the csv file
    cat_df = dataproc.process_data(config_params, field_params, output_path)

    # create the metadata json file
    metadata.create_metadata_file(config_params, field_params, cat_df, output_path)


def generate_flag_file(
    config_path: Annotated[
        str, typer.Option(help="The full path and file name of the base config file.")
    ] = "./config_files/v1.0/abell2744_config.yaml",
    field_path: Annotated[
        str, typer.Option(help="The full path and file name of the DJA fields file.")
    ] = "./metadata_files/v1.0/dja_fields.yaml",
):

    # get the config parameters
    config_path, [field_paths] = validate_config_paths(config_path, field_paths)
    config_params, field_params = load_config(config_path, field_paths)

    # validate and create the output path if necessary
    validate_cat_path(config_params)
    output_path = create_and_validate_output_path(config_params)

    filterobjects.create_and_write_flag_file(config_params, field_params, output_path)

    pass


def process_data_and_write_metadata_entrypoint():
    typer.run(process_data_and_write_metadata)
