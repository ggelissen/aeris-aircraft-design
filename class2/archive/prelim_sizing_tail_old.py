# prelim_sizing_tail.py

import math
import numpy as np
import yaml
import os
import sys

# Allow imports from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.design_variables import DesignParameters
# Assuming wing sizing functions are in a separate, importable file
import class1.prelim_sizing_wing as psw # Preliminary sizing wing functions

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
    A_t = params.empennage.A_t  # Aspect ratio of the tail, defined in the design parameters
    # Calculate detailed geometry for one side of the V-tail
    b_t = math.sqrt(S_t * A_t)
    
    # Using wing formulas for the tail geometry
    # Note: These might need tail-specific versions if methodologies differ
    Mach_cruise = params.cruise_mach + 0.05 # Adjusted for tail TODO, add Torenbeek source.
    Mach_cross = params.wing.Mach_cross # 0.935, for supercritical airfoil
    Lambda_025c_t = psw.calculate_sweep_angle_025c_rad(Mach_cruise, Mach_cross)
    taper_ratio_t = psw.calculate_taper_ratio(Lambda_025c_t)
    c_root_t, c_tip_t = psw.calculate_chord_lengths(S_t, b_t, taper_ratio_t)
    MAC_t, y_LEMAC_t = psw.calculate_MAC_and_y_LEMAC(c_root_t, c_tip_t, b_t)
    
    h = params.cruise_altitude  # Altitude in meters
    W_TO = params.weight.W_TO  # Takeoff weight in Newtons
    
    Lambda_LE_t = psw.calculate_sweep_angle_LE(Lambda_025c_t, c_root_t, b_t, taper_ratio_t)
    Lambda_05c_t = psw.calculate_sweep_angle_x_c(Lambda_LE_t, c_root_t, b_t, 0.5, taper_ratio_t)
    t_c_t = psw.calculate_thickness_ratio(h, Mach_cruise, W_TO, S_t, Lambda_05c_t, Mach_cross) # TODO, revise implementation, use Aerodynamics module.
    
    results = {
        "S_h": S_h,
        "S_v": S_v,
        "S_t": S_t,
        "dihedral_rad (gamma)": dihedral_rad,
        "dihedral_deg (gamma)": np.rad2deg(dihedral_rad),
        "b_t": b_t,
        "c_root_t": c_root_t,
        "c_tip_t": c_tip_t,
        "taper_ratio_t": taper_ratio_t,
        "aspect_ratio_t": A_t, # Or however total AR is defined
        "Lambda_025c_t": Lambda_025c_t,	
        "Lambda_LE_t": Lambda_LE_t,
        "Lambda_05c_t": Lambda_05c_t,
        "MAC_t": MAC_t,
        "y_LEMAC_t": y_LEMAC_t,
        "t_c_t": t_c_t,
    }
    return results

if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    tail_results = perform_tail_sizing(params)

    print("--- Tail Sizing Results ---")
    for key, value in tail_results.items():
        print(f"{key:<15}: {value:.4f}")