from pathlib import Path
import yaml

from . import dataproc
from . import metadata


def load_config():
    config_path = "./base_config.yaml"
    config_params = yaml.load(config_path)

    return config_params


if __name__ == "__main__":
    # get the input file path and name of the field
    # and turn them into necessary output file names
    config_params, field_params = load_config()

    # create the csv file
    dataproc.process_data(config_params)

    # create the metadata json file
    metadata.create_metadata_file(config_params)
