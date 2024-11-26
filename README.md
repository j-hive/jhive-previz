# jhive-previz

This code processes input JWST catalogs from a given DJA field, and outputs a combined data table and metadata file in formats required for use in the J-HIVE Visualization Tool. For detailed documentation of the input and output data structures, visit the [J-HIVE Docs](https://j-hive.github.io/jhive-docs/previz/index.html).

## Installation
To install this code, clone the repository, enter it, and install using poetry as follows:
```
cd jhive-previz
poetry install
```


## Quickstart

This code will take a set of catalogues for a specific DJA field, grab the columns in `columns_to_use`, convert and filter the data as necessary, and then combine all the desired columns into one `.csv` data file. It will also write a metadata file that contains information about each column such as its display name, input and output units, and so on. 

To run the data processing for a specific field, follow the steps below:
1. Create a `data` folder in the outer `jhive_previz` directory.
2. Download the relevant catalogues for that field into the `data` directory. You need at least the DJA catalogue for that field.  
3. Provide the path to the `[field]_config.yaml` file from your working directory when running the following command (ideally, this should be the path from the outer directory of `jhive_previz` to the `config_files/[version]` folder.):
```
poetry run jhive_previz --config-path [config_path]
```
4. The output data `.csv` file and metadata `.json` file will be in the `output_path` directory provided in the `config.yaml` file. The files will be within the following path structure: `[output_path]/[version]/[field_key]/`. 


To run using config files other than the given defaults, run the same command as above, but provide the paths to both the `config.yaml` file and all of the desired `fields.yaml` files using the following format: 

```
poetry run jhive_previz --config-path [config_path] --field-paths [field_path_1] --field-paths [field_path_2]
```

You can add additional field paths as desired by adding an extra instance of the argument to the end of the command (i.e. `--field-paths [field_path_3]`).

For more help running this script, you can run:
```
poetry run jhive_previz --help
```


## How to update the schema documentation

The schema documentation `.csv` files are located in the `docs` folder. These are turned into Markdown files by the J-HIVE docs code, and should only be updated when one of the `[catalogue]_fields.yaml` files in the `metadata` folder is updated. 

To update the schema documentation for a specific fields file that has been changed, follow the steps below:
1. Run the following poetry script: 
```
poetry run make_docs_csv [path_to_yaml_file]
```
 where `path_to_yaml_file` is the full path to the `fields.yaml` file that you wish to update the schema for. This will create a new `.csv` file from the `yaml` file, and if there is an existing `csv` file for that catalogue in the `docs` folder, it will merge the descriptions column of the old `csv` with the new `csv`, and place the new merged `csv` file in the `docs` folder as `*_toedit.csv`. 

2. Check that the merged file in `*_toedit.csv` looks as expected, then edit the file as necessary. Make sure to add descriptions for any new rows in the table. 
3. Once you are happy with the new file, delete the old `csv` file and rename the `*_toedit.csv` file to match the name of the old `csv`.
4. Push the changes to the github repo. To immediately update the docs, run the `Build Sphinx Docs` Action on the `jhive-docs` repo. If you have added a new `fields.yaml` file, then you will have to update the `conf.py` of the `jhive-docs` to add this file to the list of files to convert from `csv` to `md`.