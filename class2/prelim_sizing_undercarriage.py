# prelim_sizing_undercarriage.py

import numpy as np
import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters

def perform_undercarriage_positioning(params: DesignParameters) -> dict:
    """
    Calculate the undercarriage positioning based on design parameters.

    Parameters:
    params (DesignParameters): Design parameters object containing aircraft specifications.
    
    from Roskam p.218 part 2
    """
    # Static load fraction on nose landing gear
    static_frac_nlg = params.landing_gear.static_frac_nlg
    
    # Calculate distances from CG
    l_m = params.cg.z_cg * math.tan(params.landing_gear.tipback_angle)
    l_n = ((1 / static_frac_nlg) - 1) * l_m
    
    # Assuming cg.x_cg_OEW is the longitudinal position of the CG at OEW
    # This needs to be calculated and available in the params object. Using a placeholder for now.
    x_cg_OEW = 5.01 # Placeholder
    P_n = (params.weight.W_TO*l_m)/(l_m+l_n)
    n_s = 2
    P_m = (params.weight.W_TO*l_n)/(n_s*(l_m+l_n))
    nose_load = P_n / params.weight.W_TO
    main_load = n_s*P_m / params.weight.W_TO
    
    # Calculate positions
    x_nlg = x_cg_OEW - l_n
    x_mlg = x_cg_OEW + l_m
    y_mlg = (l_n+l_m)/(math.sqrt(((l_n**2) * (math.tan(params.landing_gear.overturn_angle)**2))/(params.cg.z_cg**2) -1))

    tire_pressure = (430*math.log(params.landing_gear.LCN) -680) * 10e3 # in Pa
    tire_pressure_kg_cm2 = tire_pressure / 10  # Convert Pa to kg/cm^2

    static_load_nlg = P_n / 9.80665  # Convert N to kg
    static_load_mlg = P_m / 9.80665  # Convert N to kg

    results = {
        "x_nlg": x_nlg,
        "x_mlg": x_mlg,
        "y_mlg": y_mlg,
        "l_m": l_m,
        "l_n": l_n,
        "P_n": P_n,
        "P_m": P_m,
        "nose_load": nose_load,
        "main_load": main_load,
        "tire_pressure_kg_cm2": tire_pressure_kg_cm2,
        "static_load_nlg": static_load_nlg,
        "static_load_mlg": static_load_mlg
    }
    return results

if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    undercarriage_results = perform_undercarriage_positioning(params)

    print("--- Undercarriage Positioning Results ---")
    for key, value in undercarriage_results.items():
        print(f"{key:<10}: {value:.3f} m")