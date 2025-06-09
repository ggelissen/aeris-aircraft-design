# prelim_sizing_tail.py

import math
import numpy as np
import yaml
import os
import sys

# Allow imports from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
# Assuming wing sizing functions are in a separate, importable file
import class1.preliminary_sizing.prelim_sizing_wing as psw # Preliminary sizing wing functions

def calculate_decomposed_tail_sizing(params: object) -> tuple:
    """
    Calculate the tail sizing based on the design parameters.
    
    Parameters:
    params (DesignParameters): Design parameters containing empennage and wing specifications.

    Returns:
    tuple: Horizontal and vertical tail surface areas (S_h, S_v).
    """

    S_h = params.empennage.V_v * params.wing.b_w * params.wing.S_w / params.empennage.L_v
    S_v = params.empennage.V_h * params.wing.mac * params.wing.S_w / params.empennage.L_h

    return S_h, S_v


def calculate_tail_dihedral(S_h: float, S_v: float) -> float:
    """
    Calculate the dihedral angle for the V-tail.
    
    Parameters:
    S_h (float): Surface area of the horizontal tail.
    S_v (float): Surface area of the vertical tail.
    
    Returns:
    float: Dihedral angle in radians.
    """
    return math.atan(S_v / S_h)


def calculate_tail_sizing(S_h: float, S_v: float) -> float:
    """
    Perform tail sizing calculations based on the design parameters.
    
    Parameters:
    S_h (float): Surface area of the horizontal tail.
    S_v (float): Surface area of the vertical tail.
    
    Returns:
    float: total tail surface area.
    """
    dihedral_angle = calculate_tail_dihedral(S_h, S_v)
    S_t = S_h / math.cos(dihedral_angle)

    return S_t

def calculate_total_tail_area(S_h: float, dihedral_angle_rad: float) -> float:
    """Calculates the total V-tail surface area.
    
    Parameters:
    S_h (float): Surface area of the horizontal tail.
    dihedral_angle_rad (float): Dihedral angle in radians.
    
    Returns:
    float: Total V-tail surface area."""
    return S_h / math.cos(dihedral_angle_rad)

def perform_tail_sizing(params: DesignParameters) -> dict:
    """
    Performs all tail sizing calculations and returns results in a dictionary.
    """
    # Decompose tail areas based on volume coefficients
    S_h, S_v = calculate_decomposed_tail_sizing(params)
    
    # Calculate V-tail geometry
    dihedral_rad = calculate_tail_dihedral(S_h, S_v) #  Modified from the prelim_sizing_tail.py, to provide dihedral on the dict.
    S_t = calculate_total_tail_area(S_h, dihedral_rad)
    
    # Calculate detailed geometry for one side of the V-tail
    b_t_half = params.empennage.b_v / 2 # Span of one side of the V-tail
    A_t_half = (b_t_half**2) / (S_t / 2) # Aspect ratio of one side
    
    # Using wing formulas for the tail geometry
    # Note: These might need tail-specific versions if methodologies differ
    Lambda_025c_t = params.wing.Lambda_025c_w # Assuming same sweep for now
    taper_ratio_t = psw.calculate_taper_ratio(Lambda_025c_t)
    c_root_t, c_tip_t = psw.calculate_chord_lengths(S_t/2, b_t_half, taper_ratio_t)

    # Calculate the dihedral angle of the V-tail
    dihedral_angle_t_rad = psw.calculate_dihedral_angle_rad(Lambda_025c_t)
    results = {
        "S_h": S_h,
        "S_v": S_v,
        "S_t": S_t,
        "dihedral_rad (gamma)": dihedral_rad,
        "dihedral_deg (gamma)": np.rad2deg(dihedral_rad),
        "b_t": params.empennage.b_v,
        "c_root_t": c_root_t,
        "c_tip_t": c_tip_t,
        "taper_ratio_t": taper_ratio_t,
        "aspect_ratio_t": A_t_half * 2, # Or however total AR is defined
        "dihedral_t_rad": dihedral_angle_t_rad,
    }
    return results

if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    tail_results = perform_tail_sizing(params)

    print("--- Tail Sizing Results ---")
    for key, value in tail_results.items():
        print(f"{key:<15}: {value:.4f}")