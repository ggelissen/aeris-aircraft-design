import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.design_variables import DesignParameters
from utils.unit_conversions import *

# This function will remain empty, and the fuselage sizing comes from OpenVSP
def run_preliminary_sizing_fuselage(params: DesignParameters) -> dict:
    """
    Perform preliminary sizing of the fuselage based on the design parameters.
    
    Parameters:
        params (DesignParameters): An instance of DesignParameters containing the design variables.
    
    Returns:
        DesignParameters: The updated design parameters object after fuselage sizing.
    """
    
    return {}