import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import typer
from pathlib import Path
from typing_extensions import Annotated, Tuple, List

from . import utils

TO_PLOT = [("logSFRinst_50", "logM_50"), ("zfit_50", "logM_50")]


def read_files_to_dataframe(input_path: Path) -> Tuple[pd.DataFrame, List]:
    """Reads in all catalog files contained in the input path called 'catalog_core.csv' and concatenates them into one long dataframe.

    Parameters
    ----------
    input_path : Path
        The path to search for catalog files.

    Returns
    -------
    pd.DataFrame
        A dataframe of all the catalogs concatenated together (one on top of the other).
    List
        A list of the folders where catalog data was found (essentially the field keys).
    """

    # create generator of files to import
    core_datafile_list = input_path.glob("*/catalog_core.csv")

    # read in files and concat them to the main df
    full_df = pd.DataFrame()
    field_keys = []

    for datafile_path in core_datafile_list:
        # get the field name key from the path
        field_keys.append(str(datafile_path.parts[-2]))

        # read in file and add to end of master catalog
        tmp_df = pd.read_csv(datafile_path)

        full_df = pd.concat([full_df, tmp_df])

    return full_df, field_keys


def get_limits_and_bins(
    column: pd.Series, num_bins: int = 100
) -> Tuple[float, float, np.ndarray]:
    """Takes a column and returns the maximum and minimum non-Nan values, and an array of bins generated between those two limits. The number of bins is set by num_bins.

    Parameters
    ----------
    column : pd.Series
        A column of float or int data from a pandas dataframe.
    num_bins : int, optional
        The number of bins to generate, by default 100

    Returns
    -------
    Tuple[float, float, np.ndarray]
        The minimum, maximum, and array of bins.
    """

    min = np.nanmin(column)
    max = np.nanmax(column)
    bins = np.linspace(min, max, num_bins)

    return min, max, bins


def plot_2d_distribution(
    col_x: pd.Series, col_y: pd.Series, base_output_path: Path, cmap: str = "bone_r"
) -> Path:
    """Function that takes two columns of float data from a pandas dataframe, plots them as a contour plot, and saves the plot as an svg.

    Parameters
    ----------
    col_x : pd.Series
        The x column.
    col_y : pd.Series
        The y column.
    base_output_path : Path
        The path of the folder to write the plots to.
    cmap : str, optional
        The cmap to use for the contour plot, by default "bone_r"

    Returns
    -------
    Path
        The path that the plot was written to.
    """

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


def create_dist_csvs(
    df_data: pd.DataFrame, base_output_path: Path, metadata_dict: dict
):
    """Given a dataframe, iterates through the columns and gets the histogrammed frequency distribution of the values in that column, and saves it and the bin centers as a csv.

    Parameters
    ----------
    df_data : pd.DataFrame
        The dataframe of data.
    base_output_path : Path
        The path to the folder where distribution csvs will be written.
    metadata_dict : dict
        The metadata dictionary to add to.
    """
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
        metadata_dict["dist"][c] = str(out_path.relative_to("output"))
        metadata_dict["limits"][c] = [int(min), int(max)]


def generate_distributions_and_write_output(
    input_path: Annotated[
        str, typer.Option(help="The path to the output for this version of the code.")
    ] = "./output/v1.0/"
):
    """This function generates plots and data for the JHIVE Visualization Tool's details pane and the detail page. It generates contour plots of the given columns in 'TO_PLOT', and saves those as SVGs. It also saves histograms of the distributions of data in each column of the core catalog as csvs. Finally, it generates and writes a metadata.json file which contains paths to all of these files, as well as the minimum and maximum values of the distributions for each of the columns.

    Parameters
    ----------
    input_path : Annotated[ str, typer.Option, optional
        The path to the output for this version of the code, where the catalog_core.csv files are stored, by default ="./output/v1.0/"

    Raises
    ------
    FileNotFoundError
        Raises a FileNotFoundError if there are no catalog_core.csv files found within the file structure of the input path folder.
    """

    # create and validate output and input paths
    input_path = utils.validate_dir_path(input_path)
    output_path = input_path / "distributions"
    dist_output_path = utils.validate_dir_path(output_path / "data_files")
    plot_output_path = utils.validate_dir_path(output_path / "plots")

    df_data, field_keys = read_files_to_dataframe(input_path)

    if len(df_data) == 0:
        raise FileNotFoundError(f"No core data files found in {input_path}")

    # create metadata dict and put information in
    metadata_dict = {"dist": {}, "limits": {}, "plots": {}}
    metadata_dict["field_keys_included"] = field_keys
    metadata_dict["num_objects"] = len(df_data)

    # get the distribution csvs
    create_dist_csvs(df_data, dist_output_path, metadata_dict)

    # make plots

    for i in range(0, len(TO_PLOT)):
        plot_path = plot_2d_distribution(
            df_data[TO_PLOT[i][0]], df_data[TO_PLOT[i][1]], plot_output_path
        )

        # add to metadata file
        metadata_dict["plots"][f"{TO_PLOT[i][0]}-{TO_PLOT[i][1]}"] = str(
            plot_path.relative_to("output")
        )

    # write out metadata file
    utils.write_json(metadata_dict, output_path, "metadata")


def generate_distributions_and_write_output_entrypoint():
    typer.run(generate_distributions_and_write_output)
