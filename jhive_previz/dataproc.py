import numpy as np
from astropy.table import Table
import pandas as pd
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import Union, Mapping, List, Tuple, Optional, Dict, TypeVar

from . import conversions as conversions
from . import utils

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
    file_format: str
    loaded: bool = False
    df: PandasDataFrame | None = None
    df_good: PandasDataFrame | None = None
    input_columns: List = []
    output_columns: List = []
    conversion_functions: List = []
    decimals_to_round: Dict = {}


# Functions

## Utility functions


def get_data_output_filepath(output_path: Path, suffix: str) -> Path:
    """Returns the path to output the .csv to.

    Parameters
    ----------
    output_path : Path
        The path to the directory where the file will be saved.
    suffix : str
        The suffix string to add to the file name.

    Returns
    -------
    Path
        The full path (including file name) to write the .csv output to.
    """

    data_output_filename = "catalog_" + suffix + ".csv"

    return output_path / data_output_filename


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
            df = utils.read_table(cat.file_path, cat.file_format)

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

    # iterate through output columns for each catalog file
    for base_file, columns in config_params["columns_to_use"].items():
        if base_file not in data_frames.keys():

            # add the catalog to the dictionary of data frames
            data_frames[base_file] = Catalogue(
                file_name=config_params["file_names"][base_file],
                file_path=utils.get_cat_filepath(base_file, config_params),
                file_format=field_params[base_file]["file_format"],
            )

        for c in columns:

            # get column name that is in the input file and add to list of columns to use
            col_name = field_params[base_file]["columns"][c]["input_column_name"]
            data_frames[base_file].input_columns.append(col_name)
            data_frames[base_file].output_columns.append(c)

            # add to columns to round if there is a number of decimals supplied
            if field_params[base_file]["columns"][c]["output_num_decimals"] is not None:
                data_frames[base_file].decimals_to_round[c] = field_params[base_file][
                    "columns"
                ][c]["output_num_decimals"]

            # get any conversion functions needed for columns
            try:
                # add the function to the class
                data_frames[base_file].conversion_functions.append(
                    conversions.get_conversion_function(
                        field_params[base_file]["columns"][c]["input_units"],
                        field_params[base_file]["columns"][c]["output_units"],
                    )
                )
            except ValueError:
                # no conversion function exists for these units
                raise UnitConversionError(
                    f"Unit conversion failed for column {c}, no conversion function exists for {field_params[base_file][c]['input_units']} to {field_params[base_file][c]['output_units']}."
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
        column = np.where(((max_val >= column) & (column >= min_val)), column, np.nan)

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
        The field parameters dictionary for that catalog.

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
            # new_cols[cat.output_columns[i]] = pd.Series()
            print(
                f"Column {cat.input_columns[i]} not found in dataframe, {cat.output_columns[i]} will not be in output data file."
            )
            continue

        # only apply a function if conversion function is not None
        if cat.conversion_functions[i] is not None:
            # apply the conversion function to the associated column
            new_cols[cat.output_columns[i]] = cat.df[cat.input_columns[i]].apply(
                cat.conversion_functions[i],
                field_params=field_params["columns"][cat.output_columns[i]],
            )
        else:
            new_cols[cat.output_columns[i]] = cat.df[cat.input_columns[i]]

        # filter values in columns with floats to ensure they are finite and fall within the given range
        if field_params["columns"][cat.output_columns[i]]["data_type"] == "float":
            new_cols[cat.output_columns[i]] = filter_column_values(
                new_cols[cat.output_columns[i]],
                field_params["columns"][cat.output_columns[i]],
            )

    # replace catalogue dataframe with new dataframe
    cat.df = pd.DataFrame(new_cols)

    # round the relevant columns
    cat.df.round(cat.decimals_to_round)

    return cat


## Organizational functions


def process_data(
    config_params: Mapping,
    field_params: Mapping,
    output_path: Path,
    use_flag_file: bool,
    flag_file_path: Optional[Path] = None,
) -> pd.DataFrame:
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
    output_path : Path
        The full path to the directory where the output file will be saved.
    use_flag_file: bool
        If True, we will create two catalogues, a 'core' and a 'raw', where 'core' consists of objects that have 'ingest_viz' flags that are True.
    flag_file_path: Optional[Path]
        The full path to the flag file that has the 'ingest_viz' column. Required if use_flag_file is True, None if not.

    Returns
    -------
    pd.DataFrame
        The new dataframe.
    """

    # read in flag file if it's being used
    if use_flag_file:
        df_ingest = utils.read_table(flag_file_path, file_format="fits")

    # Create dictionary to store all file names and data frames once loaded
    data_frames: Dict[str, Catalogue] = {}

    # load in main catalogue file and populate columns to use per file and load in any additional data files
    data_frames["cat_filename"] = Catalogue(
        file_name=config_params["file_names"]["cat_filename"],
        file_path=utils.get_cat_filepath("cat_filename", config_params),
        file_format=field_params["cat_filename"]["file_format"],
    )
    data_frames = populate_column_information(data_frames, config_params, field_params)

    # read in main catalogue and convert and filter necessary columns
    data_frames["cat_filename"] = load_dataframe(
        "cat_filename", data_frames["cat_filename"]
    )

    data_frames["cat_filename"] = process_column_data(
        data_frames["cat_filename"], field_params["cat_filename"]
    )

    if use_flag_file:
        # get two catalogues, one with good object and one with raw
        df_core = data_frames["cat_filename"].df[df_ingest["ingest_viz"]]
        df_raw = data_frames["cat_filename"].df[~df_ingest["ingest_viz"]]

    else:
        # just get one catalogue with everything
        df_raw = data_frames["cat_filename"].df

    # if there is one or more additional dfs loaded
    if len(data_frames.keys()) > 1:

        for name in data_frames.keys():

            if name == "cat_filename":
                # skip, this one is already completed
                continue

            # load in data frame
            data_frames[name] = load_dataframe(name, data_frames[name])

            if data_frames[name].loaded:
                # if data frame is loaded, convert any columns needed and join to previous table
                data_frames[name] = process_column_data(
                    data_frames[name], field_params[name]
                )

                if use_flag_file:
                    # only add to the core dataframe if it exists
                    df_core = df_core.join(
                        data_frames[name].df.set_index("id"), on="id"
                    )

                df_raw = df_raw.join(data_frames[name].df.set_index("id"), on="id")

            else:
                # dataframe failed to load
                print(
                    f"{data_frames[name]} was not properly loaded, its columns will not be present in the final dataframe."
                )

    # write out the data to a csv file
    output_file_path_raw = get_data_output_filepath(output_path, "raw")
    utils.write_data(df_raw, output_file_path_raw)

    # write out core data if necessary
    if use_flag_file:
        output_file_path_core = get_data_output_filepath(output_path, "core")
        utils.write_data(df_core, output_file_path_core)

        return df_raw, df_core
    else:
        return df_raw
