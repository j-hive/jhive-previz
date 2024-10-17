import numpy as np
from astropy.table import Table
import pandas as pd
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import Union, Mapping, List, Tuple, Optional, Dict, TypeVar

from . import conversions as conversions

# setting up pandas datatype
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")


# classes


class Catalogue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_name: str
    file_path: Optional[Path]
    loaded: bool = False
    df: PandasDataFrame | None = None
    columns_to_use: List = []
    config_colnames: List = []
    conversion_functions: List = []
    columns: Dict = {}


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


def get_data_output_filepath(config_params: Mapping) -> Path:
    """Returns the path to output the .csv to.

    Parameters
    ----------
    config_params : Mapping
        The dictionary of config parameters from the config file.

    Returns
    -------
    Path
        The full path (including file name) to write the .csv output to.
    """

    # turn the output base path into Path object
    output_path = Path(config_params["output_path"])

    data_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".csv"
    )

    return output_path / data_output_filename


def read_table(data_file_path: Path) -> pd.DataFrame:

    # read in table as astropy table
    phot_cat = Table.read(data_file_path)

    # now convert to pandas
    cat_df = phot_cat.to_pandas()

    return cat_df


def write_data(df_cat: pd.DataFrame, output_file_path: Path):
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
        float_format="%.6f",
        index=False,
    )


def load_dataframe(file_name: str, cat: Catalogue) -> Catalogue:
    """Loads in a dataframe as a variable of a Catalogue object, and updates the 'loaded' variable.

    Parameters
    ----------
    file_name : str
        The key associated with the file name in the config file, i.e. 'cat_filename'
    cat : Catalogue
        The Catalogue object to load the dataframe to.

    Returns
    -------
    Catalogue
        The updated Catalogue object.

    Raises
    ------
    RuntimeError
        Raises an error if the main catalogue dataframe fails to load.
    """

    # get variable for the path
    if cat.file_path is not None:
        # try to load in file
        try:
            df = read_table(cat.file_path)

            # if successful, update the data_frames dictionary with the dataframe
            cat.loaded = True
            cat.df = df

        except:
            if file_name == "cat_filename":
                # this file is required to run, so if not loaded raise error

                # TODO: maybe move this error to the read table function?
                raise RuntimeError("Could not load dataframe for the main cat file")
            else:
                print(
                    f"Could not load {cat.file_name} at {cat.file_path}, columns requiring this file will be empty."
                )
    else:
        print(
            f"No path given for {cat.file_name}, columns requiring this file will be empty."
        )

    return cat


def populate_column_information(
    data_frames: Dict[str, Catalogue], config_params: Mapping, field_params: Mapping
) -> Dict[str, Catalogue]:
    """This function iterates through the columns to use in the config file. It checks what file
    each column comes from, and if that file does not already have a Catalogue entry in the data_frames
    dictionary, it adds it in. Additionally, it adds to the columns_to_use, config_colnames, and conversion_functions
    lists for the relevant Catalogue objects.

    Parameters
    ----------
    data_frames : Dict[str, Catalogue]
        The dictionary of Catalogue objects, one for each of the required catalogue files.
    config_params : Mapping
        The dictionary of parameters from the config file.
    field_params : Mapping
        The dictionary of parameters from the fields file.

    Returns
    -------
    Dict[str, Catalogue]
        Returns the data frames dictionary with updated values.
    """

    # iterate through output columns
    for c in config_params["columns_to_use"]:

        # check for which file to look in for this column
        base_file = field_params[c]["file_name"]

        # check if that file is loaded in (will need to have a variable for this I think)
        if base_file not in data_frames.keys():

            # add the catalog to the dictionary of data frames
            data_frames[base_file] = Catalogue(
                file_name=config_params["file_names"][base_file],
                file_path=get_cat_filepath(base_file, config_params),
            )

            # make sure that the id parameter is used for all files in addition to the main catalogue
            data_frames[base_file].columns_to_use.append("id")
            data_frames[base_file].config_colnames.append("id")

        # get column name that is in the input file and add to list of columns to use
        col_name = field_params[c]["input_column_name"]
        data_frames[base_file].columns_to_use.append(col_name)
        data_frames[base_file].config_colnames.append(c)
        data_frames[base_file].columns[col_name] = c

        # get any conversion functions needed for columns
        try:
            # add the function to the class
            data_frames[base_file].conversion_functions.append(
                conversions.get_conversion_function(
                    field_params[c]["input_units"], field_params[c]["output_units"]
                )
            )
        except ValueError:

            # no conversion function exists for these units
            print(
                f"Unit {field_params[c]['input_units']} conversion to {field_params[c]['output_units']} not supported, keeping input units for {c}."
            )
            data_frames[base_file].conversion_functions.append(None)

    return data_frames


def filter_column_values(df: pd.DataFrame, col_name: str, col_field_params: Dict):
    """Filters values in a Pandas column (a Series) such that all values are finite. It also filters
    values so that they are NaNs if they are outside the range given for that column in the fields.yaml
    file. If no range is given, no filtering is done.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe that has the desired column.
    col_name : str
        The name of the column to filter.
    col_field_params : Dict
        The dictionary of parameters for the column to filter.
    """

    # filter so values are finite
    df[col_name] = np.where(np.isfinite(df[col_name]), df[col_name], np.nan)

    min_val = col_field_params["filt_min_val"]
    max_val = col_field_params["filt_max_val"]

    # if there is a min or max value given for the column, replace any values outside this range with nans
    if min_val is not None and max_val is not None:
        # we have a min and a max
        df[col_name] = np.where(
            max_val >= df[col_name] >= min_val, df[col_name], np.nan
        )

    elif min_val is not None and max_val is None:
        # we have only a min
        df[col_name] = np.where(df[col_name] >= min_val, df[col_name], np.nan)

    elif max_val:
        # we only have a max
        df[col_name] = np.where(max_val >= df[col_name], df[col_name], np.nan)


def convert_columns_in_df(cat: Catalogue, field_params: Dict) -> Catalogue:
    """Iterates through the columns to use and applies the associated conversion function
    to the column.

    Parameters
    ----------
    cat : Catalogue
        The class object that stores the dataframe and the columns to use and conversion function lists.
    field_params : Dict
        The field parameters dictionary for that column.

    Returns
    -------
    Catalogue
        The same class object as above, modified by the function.
    """

    for i in range(0, len(cat.columns_to_use)):

        # only apply a function if conversion function is not None
        if cat.conversion_functions[i] is not None:
            # apply the conversion function to the associated column
            cat.df[cat.columns_to_use[i]].apply(
                cat.conversion_functions[i],
                field_params=field_params[cat.config_colnames[i]],
            )

        # filter values in columns with floats to ensure they are finite and fall within the given range
        if field_params[cat.config_colnames[i]]["data_type"] == "float":
            filter_column_values(
                cat.df, cat.columns_to_use[i], field_params[cat.config_colnames[i]]
            )

        # TODO: if we are rounding also put that here

        if cat.columns_to_use[i] != cat.config_colnames[i]:
            # rename the column in the database if necessary
            cat.df.rename(
                columns={cat.columns_to_use[i]: cat.config_colnames[i]}, inplace=True
            )

    return cat


def process_data(config_params: Mapping, field_params: Mapping):

    # Create dictionary to store all file names and data frames once loaded
    data_frames: Dict[str, Catalogue] = {}

    # load in main catalogue file
    data_frames["cat_filename"] = Catalogue(
        file_name=config_params["file_names"]["cat_filename"],
        file_path=get_cat_filepath("cat_filename", config_params),
    )

    # populate columns to use per file and load in any additional data files
    data_frames = populate_column_information(data_frames, config_params, field_params)

    # create subtables for all tables that we need

    # read in main catalogue
    data_frames["cat_filename"] = load_dataframe(
        "cat_filename", data_frames["cat_filename"]
    )

    # convert necessary columns
    data_frames["cat_filename"] = convert_columns_in_df(
        data_frames["cat_filename"], field_params
    )

    # start by making subtable of catalogue table columns
    new_df = data_frames["cat_filename"].df[data_frames["cat_filename"].config_colnames]

    # if there is one or more additional dfs loaded
    if len(data_frames.keys()) > 1:
        for name in data_frames.keys():
            if name == "cat_filename":
                # skip, this one is already completed
                continue

            # load in data frame
            data_frames[name] = load_dataframe(data_frames[name], data_frames[name])

            # make sure data frame is loaded
            if data_frames[name].loaded:

                # update the dataframe to only include the columns that we want to use
                data_frames[name].df = data_frames[name].df[
                    data_frames[name].config_colnames
                ]

                # convert any columns needed
                data_frames[name] = convert_columns_in_df(
                    data_frames[name], field_params
                )

                # join to previous table here
                new_df.join(data_frames[name].df.set_index("id"), on="id")
            else:
                # dataframe failed to load, all columns from it will be empty

                # get list of old columns + new columns
                old_columns = list(new_df.columns)
                new_columns = old_columns + data_frames[name].config_colnames

                # creates a new dataframe with all old columns and empty new columns
                new_df = new_df.reindex(columns=new_columns)

    # write out the data to a csv file
    output_file_path = get_data_output_filepath(config_params)
    write_data(new_df, output_file_path)

    return new_df
