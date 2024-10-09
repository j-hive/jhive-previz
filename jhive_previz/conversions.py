import numpy as np


# function that converts fluxes to magnitudes
def flux_to_mag(fluxes, field_params: dict):

    zp = field_params["zero_point"]
    # TODO: add in something that returns None if it's a nan?
    return -2.5 * np.log10(fluxes) + zp


def log_values(values, field_params: dict):
    return np.log10(values)


conversions = {
    "magnitude": flux_to_mag,
    "log": log_values,
}
