import pandas as pd
from pathlib import Path
import yaml
import typer
from typing import List
from typing_extensions import Annotated
from importlib import resources as impresources
from rich import print
from . import docs

# get path to docs folder to write files to
out_filepath = impresources.files(docs)


def convert_yaml_metadata_to_csv(
    file_path: Annotated[
        str, typer.Argument(help="The full path to the .yaml file to convert.")
    ],
    output_path: Annotated[
        str,
        typer.Argument(help="The full path to the new .csv file to be written."),
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

    # save csv to file
    new_df.to_csv(output_path)


def convert_tables_to_markdown(
    file_names: Annotated[
        List[str],
        typer.Argument(help="The list of names of the .csv files to convert."),
    ],
    new_path: Annotated[
        str,
        typer.Argument(help="The full path for to write the new markdown files to."),
    ],
):
    """Converts a .csv file to a markdown file, excluding the numerical index.
    This should only be done on .csv files that have been properly edited to include descriptions, and are in the docs folder.

    Parameters
    ----------
    file_path : Path
        The full path to the .csv file.
    """

    new_path = Path(new_path)

    for name in file_names:
        file_path = out_filepath / name

        if not file_path.is_file():
            raise FileNotFoundError(
                f"File does not exist at {file_path}, could not be converted to markdown."
            )

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading in table at {file_path} due to {e}.")

        md_path = new_path / (file_path.stem + ".md")
        df.to_markdown(md_path, index=False)


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
    file_write: Annotated[
        str,
        typer.Argument(
            help="The full path to the file to write the merged .csv to. Must be a path that does not already exist."
        ),
    ],
):
    """Merge a new csv file with the 'description' column of the old csv file.

    Parameters
    ----------
    file_old : str
        The full path to the old .csv documentation file with descriptions.
    file_new : str
        The full path to the new .csv documentation file without descriptions.
    file_write : str
        The full path to the file to write the merged .csv to. Must be a path that does not already exist.
    """
    # read in tables

    df_old = pd.read_csv(file_old)
    df_new = pd.read_csv(file_new)

    # get description from old table and merge with new
    ind_colname = df_old[:, 0].name
    desc = df_old[[ind_colname, "description"]]
    merge_df = pd.merge(df_new, desc, on=ind_colname, how="left")

    # write out the new table, fails if file already exists
    merge_df.to_csv(file_write, mode="x")


def convert_yaml_to_csv_and_merge(
    file_path: Annotated[
        str, typer.Argument(help="The full path to the .yaml file to convert.")
    ]
):
    """Converts the given .yaml file to a .csv file for the documentation of the data schema. If there already exists a .csv file
    corresponding to that .yaml file in the docs/ folder, it merges the new file with the descriptions from the old file, and
    writes out the .csv file as a file named "*_toedit.csv"

    Parameters
    ----------
    file_path : str
        The full path to the .yaml file to convert.
    """

    file_path = Path(file_path)

    # get the path to write the csv file to
    file_name = file_path.stem
    file_part = file_name.split("_")[0]

    table_filename = file_part + "catalogue_fields_table.csv"
    new_filename = file_part + "catalogue_fields_table_tomerge.csv"
    merge_filename = file_part + "catalogue_fields_table_toedit.csv"

    table_path = out_filepath / table_filename
    write_path = out_filepath / new_filename
    merge_path = out_filepath / merge_filename

    if table_path.is_file():

        # convert the yaml and write the csv file
        convert_yaml_metadata_to_csv(file_path, write_path)
        print(f"Converted yaml file {file_path} to {write_path}")

        # merge with the old table file, keeping the descriptions, and write to a new csv
        merge_doc_csvs(write_path, table_path, merge_path)

        # tell user what to do next
        print(
            f"Merged {write_path.name} with {table_path.name} and wrote to {merge_path}."
        )
        print(
            f"To ensure this file ends up in the documentation, check {merge_path.name} looks as expected, and edit as desired, adding any additional descriptions necessary. Then delete the old {table_path.name} file and rename {merge_path.name} to {table_path.name}."
        )

    else:
        # write directly to the table filename, no need to merge
        convert_yaml_metadata_to_csv(file_path, table_path)
        print(
            f"Converted {file_path.name} and wrote to {table_path}. Please add a 'description' column if it does not already exist."
        )


def convert_yaml_metadata_to_csv_entrypoint():
    typer.run(convert_yaml_metadata_to_csv)


def convert_yaml_to_csv_and_merge_entrypoint():
    typer.run(convert_yaml_to_csv_and_merge)


def convert_tables_to_markdown_entrypoint():
    typer.run(convert_tables_to_markdown)
