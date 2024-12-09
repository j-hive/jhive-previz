## Script to filter objects in all the catalogues and determine which are 'good'
from pathlib import Path
from typing_extensions import List
import pandas as pd

from . import utils

SNR_MAG = 5


def get_flagfile_filepath(output_path: Path) -> Path:
    """Returns the path to output the flag .fits file to.

    Parameters
    ----------
    output_path : Path
        The path to the directory where the file will be saved.

    Returns
    -------
    Path
        The full path (including file name) to write the .fits output to.
    """

    data_output_filename = "ingest_flags.fits"

    return output_path / data_output_filename


def get_err_column_name(flux_col_name: str) -> str:
    # get the error column name for a given normal column name or a list of column names
    # pick one

    # split name into components
    colname_split = flux_col_name.split("_")

    err_colname = colname_split[0] + "_ecorr_" + colname_split[2]
    return err_colname


def filter_catalog(columns: dict, cat: pd.DataFrame) -> pd.DataFrame:

    # dict for new table
    flag_dict = {}

    # iterate through the list of flux columns to use and get mask of column
    for c in columns:

        if not c["is_magnitude"]:
            # skip columns that are not magnitudes calculated from fluxes
            continue

        # get the relevant error column name
        err_colname = get_err_column_name(c["input_column_name"])

        # check if flux column is SNR_MAG times the error column and put that data in to the dict
        flag_col = cat[c["input_column_name"]] > (cat[err_colname] * SNR_MAG)
        flag_dict[c["input_column_name"]] = flag_col

    df_ingest = pd.DataFrame.from_dict(flag_dict)

    return df_ingest


def create_and_write_flag_file(
    config_params: dict, field_params: dict, output_path: Path
):

    # I think the easiest way to do this is to take all columns that are magnitudes (since they come from flux columns)
    # from the config file
    # and have a function that gives the flux error column name of a particular flux column

    # read in fits catalog for a field
    file_path = utils.get_cat_filepath("cat_filename", config_params)
    file_format = field_params["cat_filename"]["file_format"]

    cat = utils.read_table(file_path, file_format)

    df_ingest = filter_catalog(config_params["columns"], cat)

    # then we sum up the dataframe on axis=1
    # this will give you a column that has the number of truth values in that row
    # then we can filter that so that if
    flag_values = df_ingest.sum(axis=1)

    # here is where we calculate how many flags need to be positive
    viz_flag = flag_values >= 1

    df_ingest["ingest_viz"] = viz_flag
    pass


# do I just check all columns with _corr
# or do I just do it for the columns in config
# I believe there was also some discussion as to just doing it with JWST filters
# essentially grab the list of filters we want in some way


# I think we want to do a mask on a per-column basis - this will be the per filter flag columns
# then put them all together somehow and identify the objects where any of the flags are true
# one option was to have it where multiple are true but I'll start with that
