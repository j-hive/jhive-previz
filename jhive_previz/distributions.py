import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import typer
from pathlib import Path
from typing_extensions import Annotated

from . import utils

TO_PLOT = [("logSFRinst_50", "logM_50"), ("zfit_50", "logM_50")]


def read_files_to_dataframe(input_path: Path):
    # function to read in all the catalog files into one large file

    # create generator of files to import
    core_datafile_list = input_path.glob("*/catalog_core.csv")

    # read in files and concat them to the main df
    full_df = pd.DataFrame()

    for datafile_path in core_datafile_list:
        tmp_df = pd.read_csv(datafile_path)

        full_df = pd.concat([full_df, tmp_df])

    # if the dataframe is still empty, do something here or in main function?
    return full_df


# function to get the minimum and maximum of a given column
def get_limits_and_bins(column: pd.Series, num_bins: int = 100):

    min = np.nanmin(column)
    max = np.nanmax(column)
    bins = np.linspace(min, max, num_bins)

    return min, max, bins


# for the plotting:
# function to get the contour levels for the distribution
# function to plot the whole thing and save it
def plot_2d_distribution(col_x, col_y, base_output_path: Path, cmap: str = "bone_r"):

    # get the contour levels
    x_min, x_max, x_bins = get_limits_and_bins(col_x)
    y_min, y_max, y_bins = get_limits_and_bins(col_y)

    hist_data = np.histogram2d(col_x, col_y, bins=(x_bins, y_bins))[0]
    flat_hist_data = hist_data.flatten()

    contour_limits = np.sqrt(len(col_x) / (100**2)), flat_hist_data.max()
    contour_levels = np.logspace(*np.log10(contour_limits), 10)

    # plot and save figure
    fig = plt.figure(dpi=300)

    ax = fig.add_axes([0, 0, 1, 1])
    plt.contourf(
        hist_data.T,
        extent=(x_min, x_max, y_min, y_max),
        levels=contour_levels,
        cmap=cmap,
    )
    plt.axis("off")
    ax.set_position([0, 0, 1, 1])
    ax.set_alpha(0.0)

    # save and close figure
    output_path = base_output_path / f"{col_x.name}_{col_y.name}_contours.svg"
    plt.savefig(output_path, facecolor="None")
    plt.close()

    return output_path


# for the distribution csvs:
# function to get the histogram bin values
# maybe turn 'write_data' from dataproc into a utils function and use that


# function that creates the distribution plots


def create_dist_csvs(
    df_data: pd.DataFrame, base_output_path: Path, metadata_dict: dict
):
    # function that creates the distribution csvs

    for c in df_data.columns:
        min, max, bins = get_limits_and_bins(df_data[c])
        hist_data, bin_edges = np.histogram(df_data[c], bins=bins)
        bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2

        # make it into a pandas table
        data_dict = {"bin_centres": bin_centres, "bin_values": hist_data}
        df_dist = pd.DataFrame.from_dict(data_dict)

        # write out the file
        out_path = base_output_path / f"{c}_dist.csv"
        utils.write_data(df_dist, out_path)

        # update the metadata dict
        metadata_dict["dist"][c] = str(out_path)
        metadata_dict["limits"][c] = [min, max]


def generate_distributions_and_write_output(
    input_path: Annotated[
        str, typer.Option(help="The path to the output for this version of the code.")
    ] = "./output/v1.0/"
):

    # create and validate output and input paths
    input_path = utils.validate_path(input_path)
    output_path = input_path / "distributions"
    dist_output_path = utils.validate_path(output_path / "data_files")
    plot_output_path = utils.validate_path(output_path / "plots")

    df_data = read_files_to_dataframe(input_path)

    if len(df_data) == 0:
        raise FileNotFoundError(f"No core data files found in {input_path}")

    # create metadata dict
    metadata_dict = {"dist": {}, "limits": {}, "plots": {}}

    # get the distribution csvs
    create_dist_csvs(df_data, dist_output_path, metadata_dict)

    # make plots

    for i in range(0, len(TO_PLOT)):
        plot_path = plot_2d_distribution(
            df_data[TO_PLOT[i][0]], df_data[TO_PLOT[i][1]], plot_output_path
        )

        # add to metadata file
        metadata_dict["plots"][f"{TO_PLOT[i][0]}_{TO_PLOT[i][1]}"] = str(plot_path)

    # write out metadata file
    utils.write_json(metadata_dict, output_path, "metadata")


def generate_distributions_and_write_output_entrypoint():
    typer.run(generate_distributions_and_write_output)
