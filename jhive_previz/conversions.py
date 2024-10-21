import numpy as np
from typing import Tuple, Optional, Dict


# Conversion functions


def flux_to_mag(fluxes, field_params: Dict):
    """Function that converts fluxes to magnitudes.

    Parameters
    ----------
    fluxes : _type_
        A single value or array-like structure of fluxes.
    field_params : Dict
        The dictionary of metadata for that column or value.

    Returns
    -------
    The value or values converted to magnitudes.
    """

    # get the zero point from the column metadata
    zp = field_params["zero_point"]

    return -2.5 * np.log10(fluxes) + zp


def log_values(values, field_params: dict):
    """Returns the log of the given values or value."""
    return np.log10(values)


# Dictionary of conversions

conversions = {
    ("microJansky", "magnitude"): flux_to_mag,
}

# Organizational function


def get_conversion_function(input_unit: str, output_unit: str):
    """Takes the input and output unit of the columns, and returns the
    function that should be used to convert from the input to output units.

    Parameters
    ----------
    input_unit : str
        The input unit
    output_unit : str
        The output unit

    Returns
    -------
    The python function to use to convert between the two.

    Raises
    ------
    ValueError
        Raises an error if the units cannot be converted with current capabilities.
    """

    # TODO: should I caseify these units? Just in case there are inconsistencies?
    if input_unit.casefold == output_unit.casefold:
        # no conversion needed
        return None
    elif input_unit.casefold != output_unit.casefold:

        # get conversion needed
        if (input_unit, output_unit) in conversions.keys():
            # return the relevant function
            return conversions[(input_unit, output_unit)]
        else:
            # test if it's a log
            input_split = input_unit.split(" ")
            output_split = output_unit.split(" ")

            if "log" in output_split:
                # remove the log
                output_split.remove("log")
                if input_split == output_split:
                    return log_values

            # TODO: should we have an 'unlog' function too?
            # TODO: raise warning or cause code to break?
            raise ValueError(f"{input_unit} cannot be converted to {output_unit}")
