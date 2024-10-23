import numpy as np
from astropy.table import Table
import pandas as pd
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import Union, Mapping, List, Tuple, Optional, Dict, TypeVar

from . import conversions as conversions

# Custom pandas datatype
PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")


# Classes


class UnitConversionError(Exception):
    pass


class Catalogue(BaseModel):

    # allow for custom types for the variables
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_name: str
    file_path: Optional[Path]
    loaded: bool = False
    df: PandasDataFrame | None = None
    input_columns: List = []
    output_columns: List = []
    conversion_functions: List = []
    decimals_to_round: Dict = {}


# Functions

## Utility functions


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


## Functional functions


def populate_column_information(
    data_frames: Dict[str, Catalogue], config_params: Mapping, field_params: Mapping
) -> Dict[str, Catalogue]:
    """This function iterates through the columns to use in the config file. It checks what file
    each column comes from, and if that file does not already have a Catalogue entry in the data_frames
    dictionary, it adds it in. Additionally, it adds to the input_columns, output_columns, and conversion_functions
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

        if base_file not in data_frames.keys():

            # add the catalog to the dictionary of data frames
            data_frames[base_file] = Catalogue(
                file_name=config_params["file_names"][base_file],
                file_path=get_cat_filepath(base_file, config_params),
            )

            # make sure that the id parameter is used for all files in addition to the main catalogue
            data_frames[base_file].input_columns.append("id")
            data_frames[base_file].output_columns.append("id")

        # get column name that is in the input file and add to list of columns to use
        col_name = field_params[c]["input_column_name"]
        data_frames[base_file].input_columns.append(col_name)
        data_frames[base_file].output_columns.append(c)

        # add to columns to round if there is a number of decimals supplied
        if field_params[c]["output_num_decimals"] is not None:
            data_frames[base_file].decimals_to_round[c] = field_params[c][
                "output_num_decimals"
            ]

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
            raise UnitConversionError(
                f"Unit conversion failed for column {c}, no conversion function exists for {field_params[c]['input_units']} to {field_params[c]['output_units']}."
            )

    return data_frames


def filter_column_values(column: pd.Series, col_field_params: Dict):
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
    column = np.where(np.isfinite(column), column, np.nan)

    min_val = col_field_params["filt_min_val"]
    max_val = col_field_params["filt_max_val"]

    # if there is a min or max value given for the column, replace any values outside this range with nans
    if min_val is not None and max_val is not None:
        # we have a min and a max
        column = np.where(max_val >= column >= min_val, column, np.nan)

    elif min_val is not None and max_val is None:
        # we have only a min
        column = np.where(column >= min_val, column, np.nan)

    elif max_val:
        # we only have a max
        column = np.where(max_val >= column, column, np.nan)

    return column


def process_column_data(cat: Catalogue, field_params: Dict) -> Catalogue:
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

    # dict of new columns
    new_cols = {}

    for i in range(0, len(cat.input_columns)):

        # if the column doesn't exist in the dataframe, add empty one to dictionary and move along
        if cat.input_columns[i] not in cat.df.columns:
            new_cols[cat.output_columns[i]] = pd.Series()
            print(
                f"Column {cat.input_columns[i]} not found in dataframe, creating empty column {cat.output_columns[i]}."
            )
            continue

        # only apply a function if conversion function is not None
        if cat.conversion_functions[i] is not None:
            # apply the conversion function to the associated column
            new_cols[cat.output_columns[i]] = cat.df[cat.input_columns[i]].apply(
                cat.conversion_functions[i],
                field_params=field_params[cat.output_columns[i]],
            )
        else:
            new_cols[cat.output_columns[i]] = cat.df[cat.input_columns[i]]

        # filter values in columns with floats to ensure they are finite and fall within the given range
        if field_params[cat.output_columns[i]]["data_type"] == "float":
            new_cols[cat.output_columns[i]] = filter_column_values(
                new_cols[cat.output_columns[i]], field_params[cat.output_columns[i]]
            )

    # replace catalogue dataframe with new dataframe
    cat.df = pd.DataFrame(new_cols)

    # round the relevant columns
    cat.df.round(cat.decimals_to_round)

    return cat


## Organizational functions


def process_data(config_params: Mapping, field_params: Mapping) -> pd.DataFrame:
    """This is the main function that processes the data file and writes out the processed
    version to a .csv. The function converts columns as desired, filters them to be NaNs outside
    of a certain range (if the range is given in fields.yaml), and then takes only the columns
    desired and creates a new dataframe. This dataframe is written to a .csv file in the output folder.

    Parameters
    ----------
    config_params : Mapping
        The config parameters from the config.yaml file
    field_params : Mapping
        The field parameters from the field.yaml file

    Returns
    -------
    pd.DataFrame
        The new dataframe.
    """

    # Create dictionary to store all file names and data frames once loaded
    data_frames: Dict[str, Catalogue] = {}

    # load in main catalogue file and populate columns to use per file and load in any additional data files
    data_frames["cat_filename"] = Catalogue(
        file_name=config_params["file_names"]["cat_filename"],
        file_path=get_cat_filepath("cat_filename", config_params),
    )
    data_frames = populate_column_information(data_frames, config_params, field_params)

    # read in main catalogue and convert and filter necessary columns
    data_frames["cat_filename"] = load_dataframe(
        "cat_filename", data_frames["cat_filename"]
    )
    data_frames["cat_filename"] = process_column_data(
        data_frames["cat_filename"], field_params
    )

    # start by making subtable of catalogue table columns
    new_df = data_frames["cat_filename"].df

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
                # if it is, convert any columns needed and join to previous table
                data_frames[name] = process_column_data(data_frames[name], field_params)
                new_df.join(data_frames[name].df.set_index("id"), on="id")

            else:
                # dataframe failed to load, all columns from it will be empty
                # get list of old columns + new columns and make new dataframe with old columns and empty columns
                old_columns = list(new_df.columns)
                new_columns = old_columns + data_frames[name].output_columns

                new_df = new_df.reindex(columns=new_columns)

    # write out the data to a csv file
    output_file_path = get_data_output_filepath(config_params)
    write_data(new_df, output_file_path)

    return new_df
