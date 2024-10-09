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
    conversion_functions: List = []


def get_data_output_filepath(config_params):

    data_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".csv"
    )

    return output_path / data_output_filename


def read_table(data_file_path: Path, config_params):
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


def write_data(new_cat, output_file_path: Path):

    # make sure that output file path exists
    # if it doesn't, create it

    # write data
    new_cat.write(
        output_file_path,
        format="ascii.csv",
        overwrite=True,
    )
    # df_cat.to_csv('../output/dja_abell2744clu-grizli-v7.2_jhive_viz.csv', float_format='%.6f', index=False)


def load_dataframe(
    file_name: str, config_params: Mapping, data_frames: Dict[str, Catalogue]
) -> Dict[str, Catalogue]:

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
            data_frames[file_name].loaded = True
            data_frames[file_name].df = df

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

    return data_frames


def populate_columns_to_use(
    data_frames: Dict[str, Catalogue], config_params: Mapping, field_params: Mapping
) -> Tuple[Mapping, List]:

    list_of_loaded_dfs = []

    # iterate through output columns
    for c in config_params["columns_to_use"]:

        # check for which file to look in for this column
        base_file = field_params[c]["file_name"]

        # check if that file is loaded in (will need to have a variable for this I think)
        if not data_frames[base_file].loaded:
            # check if column exists in file

            # load file
            # TODO: do this separately
            data_frames = load_dataframe(base_file, config_params, data_frames)

            # TODO: check that id will always be the correct one - if not update so that it uses the appropriate value
            data_frames[base_file].columns_to_use.append("id")

        # get column name that is in the input file and add to list of columns to use
        col_name = field_params[c]["input_column_name"]
        data_frames[base_file].columns_to_use.append(col_name)
        list_of_loaded_dfs.append(base_file)

        # TODO: could also convert columns here instead of doing another loop?

    return list_of_loaded_dfs, data_frames


def process_data(config_params: Mapping, field_params: Mapping):

    # Create dictionary to store all file names and data frames once loaded
    data_frames: Dict[str, Catalogue] = {}
    for name in config_params["file_names"].keys():
        data_frames[name] = Catalogue(file_name=config_params["file_names"][name])

    # populate columns to use per file and load in any additional data files
    list_of_loaded_dfs, data_frames = populate_columns_to_use(
        data_frames, config_params, field_params
    )

    # create subtables for all tables that we need

    # read in main catalogue
    data_frames = load_dataframe("cat_filename", config_params, data_frames)

    # convert relevant columns

    # start by making subtable of catalogue table columns
    new_df = data_frames["cat_filename"].df[data_frames["cat_filename"].columns_to_use]

    # if there is one or more additional dfs loaded
    if len(list_of_loaded_dfs) >= 1:
        for name in data_frames.keys():
            if name == "cat_filename":
                # skip, this one is already completed
                pass
            elif len(data_frames[name].columns_to_use) > 0:
                # make sure data frame is loaded
                if data_frames[name].loaded:

                    # update the dataframe to only include the columns that we want to use
                    data_frames[name].df = data_frames[name].df[
                        data_frames[name].columns_to_use
                    ]

                    # join to previous table here
                    new_df.join(data_frames[name].df.set_index("id"), on="id")
                else:
                    # dataframe failed to load, all columns from it will be empty

                    # get list of old columns + new columns
                    old_columns = list(new_df.columns)
                    new_columns = old_columns + data_frames[name].columns_to_use

                    # creates a new dataframe with all old columns and empty new columns
                    new_df = new_df.reindex(columns=new_columns)

    # now we need to convert any columns that need converting

    for c in config_params["columns_to_use"]:
        if field_params[c]["input_units"] != field_params[c]["output_units"]:
            # we need to convert columns
            conversions.conversions[field_params[c]["output_units"]](
                new_df[field_params[c]["input_column_name"]],
                field_params[c],
            )

    # get the columns that we want
    # filtered_cat, flux_cols_filtered = get_filtered_table(cat_df)

    # convert fluxes to magnitudes
    # new_cat = convert_flux_to_magnitude(filtered_cat, flux_cols_filtered)

    # write out the data to a csv file
    write_data(new_cat)


# structure


# read in the main catalogue file
# could also read in any other files we have paths to here?
# and get list of their columns? That way we read in whatever first

# get a list of the columns


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


# Converting Required Cols to Log

# for tmp_col in ("Lv", "MLv", "mass", "LIR", "sfr"):
#     new_cat[tmp_col] = np.log10(new_cat[tmp_col])

#     tmp_inds = np.where(~np.isfinite(new_cat[tmp_col]))
#     new_cat[tmp_col][tmp_inds] = np.nan
