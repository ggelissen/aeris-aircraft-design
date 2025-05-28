import math
import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 

def tail_sizing (params: DesignParameters):
    """
    Calculate the tail sizing based on the design parameters.
    This function is a placeholder and should be implemented with actual calculations.
    """
    #horizontal tail surface area
    S_h = params.empennage.V_v * params.wing.b_w * params.wing.S_w / params.empennage.L_v
    #vertical tail surface area
    S_v = params.empennage.V_h * params.wing.mac * params.wing.S_w / params.empennage.L_h
    # Update the empennage parameters with calculated areas
    params.empennage.S_h = S_h
    params.empennage.S_v = S_v
    return S_h, S_v

if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    # Perform tail sizing calculations
    S_h, S_v = tail_sizing(params)

    # Print the results
    print(f"Horizontal Tail Surface Area (S_h): {S_h:.2f} m^2")
    print(f"Vertical Tail Surface Area (S_v): {S_v:.2f} m^2")