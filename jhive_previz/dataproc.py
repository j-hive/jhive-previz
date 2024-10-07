import numpy as np
from astropy import table
import pandas as pd
import re
from pathlib import Path

# variables

output_path = Path("../output/")


def get_data_output_filepath(config_params):
    data_output_filename = (
        config_params["field_name"] + config_params["output_file_suffix"] + ".csv"
    )

    return output_path / data_output_filename


def read_table(data_file_path: Path):
    # # Since we want this to be pandas later, make pandas now
    phot_cat = table.Table.read(data_file_path)

    return phot_cat


# function that converts fluxes to magnitudes
def flux_to_mag(fluxes, zp):
    return -2.5 * np.log10(fluxes) + zp


def get_filtered_table(phot_cat):
    flux_cols = [
        tmp_colname
        for tmp_colname in phot_cat.colnames
        if tmp_colname.endswith("_corr_1")
    ]

    flux_cols_filtered = []

    for flux_col_name in flux_cols:
        if re.search("^f[0-9]{3}[a-z]_corr_1", flux_col_name):

            flux_cols_filtered.append(flux_col_name)

    # filter the table down to the desired columns
    filtered_cat = phot_cat[cat_keys + tuple(flux_cols_filtered)]

    return filtered_cat, flux_cols_filtered


def convert_flux_to_magnitude(filtered_cat, flux_cols_filtered):
    new_cat = filtered_cat[cat_keys]

    # converts columns and adds them to the new table
    for flux_col_name in flux_cols_filtered:
        filter_name = flux_col_name.split("_")[0]

        mag_name = "abmag_" + filter_name

        new_cat[mag_name] = flux_to_mag(filtered_cat[flux_col_name])

    return new_cat


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


def process_data(data_file_path, output_file_path):

    # read in table
    phot_cat = read_table(data_file_path)

    # get the columns that we want
    filtered_cat, flux_cols_filtered = get_filtered_table(phot_cat)

    # convert fluxes to magnitudes
    new_cat = convert_flux_to_magnitude(filtered_cat, flux_cols_filtered)

    # write out the data to a csv file
    write_data(new_cat)


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
