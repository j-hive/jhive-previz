import numpy as np
from typing import Tuple, object, Optional


# function that converts fluxes to magnitudes
def flux_to_mag(fluxes, field_params: dict):

    zp = field_params["zero_point"]
    # TODO: add in something that returns None if it's a nan?
    return -2.5 * np.log10(fluxes) + zp


def log_values(values, field_params: dict):
    return np.log10(values)


# Converting Required Cols to Log

# for tmp_col in ("Lv", "MLv", "mass", "LIR", "sfr"):
#     new_cat[tmp_col] = np.log10(new_cat[tmp_col])

#     tmp_inds = np.where(~np.isfinite(new_cat[tmp_col]))
#     new_cat[tmp_col][tmp_inds] = np.nan


# TODO turn this into a function that, if the units aren't here, checks if the difference is 'log' and then sends you to that function if true
conversions = {
    ("microJansky", "magnitude"): flux_to_mag,
}


def get_conversion_function(input_unit: str, output_unit: str) -> Optional[object]:

    # TODO: should I caseify these units? Just in case there are inconsistencies?
    if input_unit == output_unit:
        # no conversion needed
        return None
    elif input_unit != output_unit:

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
