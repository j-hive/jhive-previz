import pandas as pd
from pathlib import Path
import yaml
import typer
from typing_extensions import Annotated


def convert_yaml_metadata_to_csv(
    file_path: Annotated[
        str, typer.Argument(help="The full path to the .yaml file to convert.")
    ],
    output_filename: Annotated[
        str, typer.Argument(help="The name of the new .csv file with the extension.")
    ],
):
    """Takes the given yaml file and converts it into a .csv file where the keys in each set of dictionaries become the columns.
    The code then takes a subset of these fields ("display", "data_type", "output_units", "input_column_name", "input_units") and
    writes out the resulting .csv file to the output directory.

    Parameters
    ----------
    file_path : Path
        Path to the yaml file you want converted to a csv file.
    """

    file_path = Path(file_path)

    # read in config from yaml file
    with open(file_path, mode="rt", encoding="utf-8") as file:
        config = yaml.unsafe_load(file)

    # convert to csv with a subset of columns
    df = pd.DataFrame.from_dict(config["columns"], orient="index")
    new_df = df[
        ["display", "data_type", "output_units", "input_column_name", "input_units"]
    ]

    # create new file path and save csv to file
    out_path = Path("./output/")
    write_path = out_path / output_filename
    new_df.to_csv(write_path)


def convert_table_to_markdown(
    file_path: Annotated[
        str, typer.Argument(help="The full path to the .csv file to convert.")
    ],
    new_path: Annotated[
        str,
        typer.Argument(
            help="The full path for to write the new markdown file, including filename."
        ),
    ],
):
    """Converts a .csv file to a markdown file, excluding the numerical index.
    This should only be done on .csv files that have been properly edited to include descriptions, and are in the docs folder.

    Parameters
    ----------
    file_path : Path
        The full path to the .csv file.
    """

    # file_path = Path(file_path)
    df = pd.read_csv(file_path)

    # md_path = file_path.with_suffix(".md")
    df.to_markdown(new_path, index=False)


def merge_doc_csvs(
    file_old: Annotated[
        str,
        typer.Argument(
            help="The full path to the old .csv documentation file with descriptions."
        ),
    ],
    file_new: Annotated[
        str,
        typer.Argument(
            help="The full path to the new .csv documentation file without descriptions."
        ),
    ],
):
    # read in tables

    df_old = pd.read_csv(file_old)
    df_new = pd.read_csv(file_new)

    # get description from old table and merge with new
    ind_colname = df_old[:, 0].name
    desc = df_old[[ind_colname, "description"]]
    merge_df = pd.merge(df_new, desc, on=ind_colname, how="left")

    # write out the new table
    merge_df.to_csv(file_new)


def convert_yaml_metadata_to_csv_entrypoint():
    typer.run(convert_yaml_metadata_to_csv)


def convert_table_to_markdown_entrypoint():
    typer.run(convert_table_to_markdown)
