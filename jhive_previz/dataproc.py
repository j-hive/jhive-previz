import numpy as np
from astropy.table import Table
import pandas as pd
import re
from pathlib import Path
from pydantic import BaseModel
from typing import Union, Mapping, List, Tuple, Optional, Dict

from . import conversions as conversions

# variables

output_path = Path("../output/")


# classes


class Catalogue(BaseModel):
    file_name: str
    loaded: bool = False
    df: Optional[pd.DataFrame] = None
    columns_to_use: List = []
    config_colnames: List = []
    conversion_functions: List = []


def get_data_output_filepath(config_params: Mapping) -> Path:

    data_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".csv"
    )

    return output_path / data_output_filename


def read_table(data_file_path: Path, config_params: Mapping) -> pd.DataFrame:
    # # Since we want this to be pandas later, make pandas now
    phot_cat = Table.read(data_file_path)

    # now convert to pandas
    cat_df = phot_cat.to_pandas()

    return cat_df


# def get_filtered_table(phot_cat):
#     flux_cols = [
#         tmp_colname
#         for tmp_colname in phot_cat.colnames
#         if tmp_colname.endswith("_corr_1")
#     ]

#     flux_cols_filtered = []

#     for flux_col_name in flux_cols:
#         if re.search("^f[0-9]{3}[a-z]_corr_1", flux_col_name):

#             flux_cols_filtered.append(flux_col_name)

#     # filter the table down to the desired columns
#     filtered_cat = phot_cat[cat_keys + tuple(flux_cols_filtered)]

#     return filtered_cat, flux_cols_filtered


# def convert_flux_to_magnitude(filtered_cat, flux_cols_filtered):
#     new_cat = filtered_cat[cat_keys]

#     # converts columns and adds them to the new table
#     for flux_col_name in flux_cols_filtered:
#         filter_name = flux_col_name.split("_")[0]

#         mag_name = "abmag_" + filter_name

#         new_cat[mag_name] = flux_to_mag(filtered_cat[flux_col_name])

#     return new_cat


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


def load_dataframe(file_name: str, config_params: Mapping, cat: Catalogue) -> Catalogue:

    # get variable for the path
    file_path_var = file_name.split("_")[0] + "_path"
    if config_params[file_path_var] is not None:
        # try to load in file
        try:
            file_path = (
                Path(config_params[file_path_var])
                / config_params["file_names"][file_name]
            )
            df = read_table(file_path)

            # if successful, update the data_frames dictionary with the dataframe
            cat.loaded = True
            cat.df = df

        except:
            if file_path_var == "cat_path":
                # this file is required to run, so if not loaded raise error
                # TODO: change the error type here
                # also maybe move this error to the read table function?
                raise ValueError("Could not load dataframe")
            else:
                print(
                    f"Could not load {config_params[file_name]} at {config_params[file_path_var]}, columns requiring this file will be empty."
                )
    else:
        print(
            f"No path given for {config_params[file_name]}, columns requiring this file will be empty."
        )

    return cat


def populate_column_information(
    data_frames: Dict[str, Catalogue], config_params: Mapping, field_params: Mapping
) -> Tuple[Mapping, List]:

    # iterate through output columns
    for c in config_params["columns_to_use"]:

        # check for which file to look in for this column
        base_file = field_params[c]["file_name"]

        # check if that file is loaded in (will need to have a variable for this I think)
        if base_file not in data_frames.keys():

            # add the catalog to the dictionary of data frames
            data_frames[base_file] = Catalogue(
                file_name=config_params["file_names"][base_file]
            )

            # make sure that the id parameter is used for all files in addition to the main catalogue
            data_frames[base_file].columns_to_use.append("id")

        # get column name that is in the input file and add to list of columns to use
        col_name = field_params[c]["input_column_name"]
        data_frames[base_file].columns_to_use.append(col_name)
        data_frames[base_file].config_colnames.append(c)

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
            print(f"Unit {field_params[c]["input_units"]} conversion to {field_params[c]["output_units"]} not supported, keeping input units for {c}.")
            data_frames[base_file].conversion_functions.append(None)

    return data_frames


def filter_column_values(df: pd.DataFrame, col_name: str, col_field_params: Dict):

    # replace any infs with nans
    # filter so values are finite 
    df[col_name] = np.where(np.isfinite(df[col_name]), df[col_name],  np.nan)

    # if there is a min or max value given for the column, replace any values outside this range with nans
    min_max = (col_field_params["min_value"], col_field_params["max_value"])
    if all(min_max):
        # we have a min and a max
        # where the column falls within the range, keep values, and replace with nans outside that 
        df[col_name] = np.where(min_max[1] >= df[col_name] >= min_max[0], df[col_name], np.nan)

    elif min_max[0]:
        # we have only a min

        df[col_name] = np.where(df[col_name] >= min_max[0], df[col_name], np.nan)
        
    elif min_max[1]:
        # we only have a max
        df[col_name] = np.where(min_max[1] >= df[col_name], df[col_name], np.nan)

        


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
                raw=True,
                args=(field_params[cat.config_colnames[i]]),
            )

        # filter values in columns with floats to ensure they are finite and fall within the given range
        if field_params[cat.config_colnames[i]]["data_type"] == "float":
            filter_column_values(cat.df, cat.config_colnames[i], field_params[cat.config_colnames[i]])

        #TODO: if we are rounding also put that here


        if cat.columns_to_use[i] != cat.config_colnames[i]:
            # rename the column in the database if necessary
            cat.df.rename(columns={cat.columns_to_use[i]: cat.config_colnames[i]}, inplace=True)

    #TODO: also replace values with nans here?

    return cat


def process_data(config_params: Mapping, field_params: Mapping):

    # Create dictionary to store all file names and data frames once loaded
    data_frames: Dict[str, Catalogue] = {}
    # load in main catalogue file
    data_frames["cat_filename"] = Catalogue(
        file_name=config_params["file_names"]["cat_filename"]
    )

    # populate columns to use per file and load in any additional data files
    data_frames = populate_column_information(data_frames, config_params, field_params)

    # create subtables for all tables that we need

    # read in main catalogue
    data_frames["cat_filename"] = load_dataframe(
        "cat_filename", config_params, data_frames
    )

    # convert necessary columns
    data_frames["cat_filename"] = convert_columns_in_df(
        data_frames["cat_filename"], field_params
    )

    # TODO: convert any necessary values to NANs

    # start by making subtable of catalogue table columns
    new_df = data_frames["cat_filename"].df[data_frames["cat_filename"].columns_to_use]

    # if there is one or more additional dfs loaded
    if len(data_frames.keys()) > 1:
        for name in data_frames.keys():
            if name == "cat_filename":
                # skip, this one is already completed
                pass
            elif len(data_frames[name].columns_to_use) > 0:

                # load in data frame
                data_frames[name] = load_dataframe(
                    data_frames[name], config_params, data_frames[name]
                )

                # make sure data frame is loaded
                if data_frames[name].loaded:

                    # update the dataframe to only include the columns that we want to use
                    data_frames[name].df = data_frames[name].df[
                        data_frames[name].columns_to_use
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
                    new_columns = old_columns + data_frames[name].columns_to_use

                    # creates a new dataframe with all old columns and empty new columns
                    new_df = new_df.reindex(columns=new_columns)

    # write out the data to a csv file
    output_file_path = get_data_output_filepath(config_params)
    write_data(new_df, output_file_path)


# check the list of the desired columns
# go through one by one?
# if that column is not in the list (specifically the input column name)
# then try to read in the associated file
# if there is no path to the associated file
# then put a warning that the column will be empty
# while doing this loop, construct the new table with the columns we want
# as we input a column, we also do any conversions necessary? We can also do mass conversion later for the fluxes
# not sure which is faster
# the nice thing about doing it this way is it's easy access for all of the information
# i.e. you'll have the zero point, etc

# in this loop should we also do other things? I don't think it's necessary,
# we don't need excessive speed here


# code for the columns we don't currently use
# For all the flux columns:

# for tmp_col in flux_cols_filtered:

#     tmp_inds = np.where(filtered_cat[tmp_col] == -99.0)
#     filtered_cat[tmp_col][tmp_inds] = np.nan
