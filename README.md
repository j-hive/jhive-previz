# jhive-previz

This code processes input JWST catalogs from a given DJA field, and outputs a combined data table and metadata file in formats required for use in the J-HIVE Visualization Tool. For detailed documentation of the input and output data structures, visit the [J-HIVE Docs](https://j-hive.github.io/jhive-docs/previz/index.html).

## Installation
To install this code, clone the repository, enter it, and install using poetry as follows:
```
cd jhive-previz
poetry install
```


## Quickstart

To process the data with the default configuration files in the package, run the following command:
```
poetry run jhive_previz
```

To run the data processing with a configuration file for a specific field, choose the appropriate `config.yaml` file from the `config_files` directory, and provide the path to it from your directory when running the same command as above:
```
poetry run jhive_previz --config-path [config_path]
```

To run using config files other than the defaults, run the same command as above, but provide the paths to the `config.yaml` file and all of the desired `fields.yaml` files using the following format: 

```
poetry run jhive_previz --config-path [config_path] --field-paths [field_path_1] --field-paths [field_path_2]
```

You can add additional field paths as desired by adding an extra instance of the argument to the end of the command (i.e. `--field-paths [field_path_3]`).

For more help running this script, you can run:
```
poetry run jhive_previz --help
```