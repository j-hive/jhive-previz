from pathlib import Path
from astropy.table import Table
import pandas as pd

from typing_extensions import Mapping


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
