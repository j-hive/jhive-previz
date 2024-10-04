import numpy as np
from astropy import table
import pandas as pd
import re


# Since we want this to be pandas later, make pandas now
phot_cat = table.Table.read("../data/abell2744clu-grizli-v7.2-fix_phot_apcorr.fits")

cat_keys = (
    "id",
    "ra",
    "dec",
    "flux_radius",
)

flux_cols = [
    tmp_colname for tmp_colname in phot_cat.colnames if tmp_colname.endswith("_corr_1")
]

flux_cols_filtered = []

for flux_col_name in flux_cols:
    if re.search("^f[0-9]{3}[a-z]_corr_1", flux_col_name):

        flux_cols_filtered.append(flux_col_name)


# filter the table down to the desired columns
filtered_cat = phot_cat[cat_keys + tuple(flux_cols_filtered)]


# For all the flux columns:

# for tmp_col in flux_cols_filtered:

#     tmp_inds = np.where(filtered_cat[tmp_col] == -99.0)
#     filtered_cat[tmp_col][tmp_inds] = np.nan


# New Catalog

new_cat = filtered_cat[cat_keys]

# Converting Required Cols to Log

# for tmp_col in ("Lv", "MLv", "mass", "LIR", "sfr"):
#     new_cat[tmp_col] = np.log10(new_cat[tmp_col])

#     tmp_inds = np.where(~np.isfinite(new_cat[tmp_col]))
#     new_cat[tmp_col][tmp_inds] = np.nan


# function that converts fluxes to magnitudes
def flux_to_mag(fluxes, zp=28.9):
    return -2.5 * np.log10(fluxes) + zp


# converts columns and adds them to the new table
for flux_col_name in flux_cols_filtered:
    filter_name = flux_col_name.split("_")[0]

    mag_name = "abmag_" + filter_name

    new_cat[mag_name] = flux_to_mag(filtered_cat[flux_col_name])


# write data
new_cat.write(
    "../data/dja_abell2744clu-grizli-v7.2_jhive_viz.csv",
    format="ascii.csv",
    overwrite=True,
)
# df_cat.to_csv('../../dist/dja_abell2744clu-grizli-v7.2_jhive_viz.csv', float_format='%.6f', index=False)
