import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

from design_variables import DesignParameters

def max_airspeed(params: DesignParameters):
    """
    Calculate the maximum airspeed based on the design parameters.
    
    Parameters:
    params (DesignParameters): Design parameters containing aircraft specifications.
    
    Returns:
    float: Maximum airspeed in m/s.
    """
    T_available = params.engine.T_TO *(params.cruise_density / 1.225)  
    C_L_opt = ( T_available/params.weight.W_TO - np.sqrt((T_available/params.weight.W_TO)**2 - 4 * params.wing.C_D0 * params.wing.k2))/(2*params.wing.k2)
    V_max = np.sqrt((params.weight.W_TO *2)/(params.wing.S_w * params.cruise_density * C_L_opt))
    return V_max

if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")
    
    max_speed = max_airspeed(params)
    print(f"Calculated maximum airspeed: {max_speed:.2f} m/s")

