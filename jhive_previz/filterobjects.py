## Script to filter objects in all the catalogues and determine which are 'good'
from pathlib import Path
from typing_extensions import List
import pandas as pd

from . import utils

SNR_MAG = 5
NUM_FLAGS = 4


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
    """Gets the column name of the flux error associated with the given flux column.

    Parameters
    ----------
    flux_col_name : str
        The flux column name.

    Returns
    -------
    str
        The associated flux error column name.
    """

    # split name into components
    colname_split = flux_col_name.split("_")

    err_colname = colname_split[0] + "_ecorr_" + colname_split[2]
    return err_colname


def filter_catalog(
    columns: List[str], col_field_params: dict, cat: pd.DataFrame
) -> pd.DataFrame:
    """Takes the given catalog, and the list of columns to use. Iterates through the columns to use, and for those that are magnitudes (fluxes in the input catalog), it then finds the associated error column, and checks if the flux is SNR_MAG times the flux error. A column of flags is created for this, and the flag columns are then compiled into a dataframe and returned.

    Parameters
    ----------
    columns : List[str]
        The list of columns to use for the DJA catalog.
    col_field_params : dict
        The dictionaries of parameters for the columns.
    cat : pd.DataFrame
        The DJA catalog dataframe for the field.

    Returns
    -------
    pd.DataFrame
        The dataframe of flags.
    """

    # dict for new table
    flag_dict = {}

    # iterate through the list of flux columns to use and get mask of column
    for c in columns:

        if not col_field_params[c]["is_magnitude"]:
            # skip columns that are not magnitudes calculated from fluxes
            continue

        col_name = col_field_params[c]["input_column_name"]
        # get the relevant error column name
        err_colname = get_err_column_name(col_name)

        # replace negative fluxes with nans
        data_col = cat[col_name].mask(cat[col_name] <= 0, pd.NA)

        # check if flux column is SNR_MAG times the error column and put that data in to the dict
        flag_col = data_col > (cat[err_colname] * SNR_MAG)
        flag_dict[col_name] = flag_col

    df_ingest = pd.DataFrame.from_dict(flag_dict)

    return df_ingest


def create_and_write_flag_file(
    config_params: dict, field_params: dict, output_path: Path
):
    """This function creates a file that flags if each object in the DJA catalog for the given field has high enough SNR in all of the filters available for that field, and also generates an overall flag that identifies if the object should be considered part of the 'good' objects in the JHIVE Visualization Tool. This is done by checking if the flux of the object is SNR_MAG times greater than the error on the flux. The overall flag is True if the object has high enough SNR in NUM_FLAGS or more filters.

    Parameters
    ----------
    config_params : dict
        The dictionary of configuration parameters for the field.
    field_params : dict
        The dictionary of field parameters for the DJA catalogue.
    output_path : Path
        The full path to the directory where the file will be written.
    """

    # read in fits catalog for DJA
    file_path = utils.get_cat_filepath("cat_filename", config_params)
    file_format = field_params["cat_filename"]["file_format"]
    cat = utils.read_table(file_path, file_format)

    # create a dataframe of flags that identify which objects have high enough SNR in each filter
    df_ingest = filter_catalog(
        config_params["columns_to_use"]["cat_filename"],
        field_params["cat_filename"]["columns"],
        cat,
    )

    # get a column that has the number of truth values in that row
    # TODO: might need to do a dropna before this if this is the line causing the problem
    flag_values = df_ingest.sum(axis=1)

    # create viz flag column based on the number of positive flags in flag_values
    viz_flag = flag_values >= NUM_FLAGS

    df_ingest["ingest_viz"] = viz_flag

    # write out the file
    output_filepath = get_flagfile_filepath(output_path)
    utils.write_pd_to_fits(df_ingest, output_filepath)
