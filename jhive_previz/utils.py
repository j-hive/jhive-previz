from pathlib import Path
from astropy.table import Table
import pandas as pd
import json

from typing_extensions import Mapping, Union


def get_cat_filepath(filename_key: str, config_params: Mapping) -> Path:
    """Function to get the full path to the catalogue as given in the config file.

    Parameters
    ----------
    filename_key : str
        The filename key used in the config file
    config_params : Mapping
        The dictionary of config parameters from the config file.

    Returns
    -------
    Path
        The full path as a Path object to the relevant file.
    """

    filepath_key = filename_key.split("_")[0] + "_path"

    if config_params["paths"][filepath_key] is not None:
        file_path = (
            Path(config_params["paths"][filepath_key])
            / config_params["file_names"][filename_key]
        )
    else:
        file_path = None

    return file_path


def read_table(data_file_path: Path, file_format: str) -> pd.DataFrame:
    """Reads the data fits file into a pandas dataframe via astropy.

    Parameters
    ----------
    data_file_path : Path
        The full path to the data file.

    Returns
    -------
    pd.DataFrame
        A dataframe with the data from the file.
    """

    # read in table as astropy table
    phot_cat = Table.read(data_file_path, format=file_format)

    # now convert to pandas
    cat_df = phot_cat.to_pandas()

    return cat_df


def write_pd_to_fits(df: pd.DataFrame, output_path: Path):

    # convert pandas table to fits
    tab = Table.from_pandas(df)

    # write out file to output path
    tab.write(output_path)


def write_data(
    df_cat: pd.DataFrame, output_file_path: Path, float_format: str = "%.6f"
):
    """Writes out the dataframe to a csv file at the given output path. Ensures the parent directory exists. The csv is written without the pandas index, and cuts off all floats at 6 decimal places.

    Parameters
    ----------
    df_cat : pd.DataFrame
        The pandas dataframe to write out.
    output_file_path : Path
        The full path of the csv file to write to.
    """

    # make sure that output file path exists
    if not output_file_path.parent.is_dir():
        # if it doesn't, create it
        output_file_path.parent.mkdir()

    # write data and set floats to have no more than 6 decimal places
    df_cat.to_csv(
        output_file_path,
        float_format=float_format,
        index=False,
    )


def write_json(data: dict, base_output_path: Path, filename: str):

    write_path = base_output_path / f"{filename}.json"
    with open(write_path, "w") as f:
        json.dump(data, f, indent=4)


def validate_path(given_path: Union[str, Path]):

    if isinstance(given_path, str):
        given_path = Path(given_path)

    if not given_path.exists():
        given_path.mkdir(parents=True)
    elif given_path.is_file():
        raise FileExistsError(
            f"There is a file at {given_path}, cannot make directory. Please provide a new path or move the file."
        )

    return given_path
