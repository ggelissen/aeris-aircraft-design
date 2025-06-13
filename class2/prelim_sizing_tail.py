# prelim_sizing_tail.py

import math
import numpy as np
import os
import sys

# Allow imports from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from utils.unit_conversions import *
# Import the entire wing sizing module to use its calculation functions
import class1.preliminary_sizing.prelim_sizing_wing as psw

def calculate_decomposed_tail_sizing(params: DesignParameters) -> tuple:
    """
    Calculate the tail sizing based on the design parameters, using the specific
    formulas from the original script. Note the swapped use of V_h and V_v.
    
    Parameters:
    params (DesignParameters): Design parameters object.

    Returns:
    tuple: Horizontal and vertical tail surface areas (S_h, S_v) in m^2.
    """
    if any(v is None for v in [params.empennage.V_h, params.wing.mac, params.wing.S_w, params.empennage.L_h, 
                               params.empennage.V_v, params.wing.b_w, params.empennage.L_v]):
         print("Warning: Missing parameters for tail area calculation. Returning (0, 0).")
         return 0, 0
    
    # NOTE: The following formulas are implemented exactly as in the user's original script.
    # S_h is calculated using the vertical volume coefficient and wing span.
    S_h = (params.empennage.V_v * params.wing.b_w * params.wing.S_w) / params.empennage.L_v
    # S_v is calculated using the horizontal volume coefficient and MAC.
    S_v = (params.empennage.V_h * params.wing.mac * params.wing.S_w) / params.empennage.L_h

    return S_h, S_v

def calculate_tail_dihedral(S_h: float, S_v: float) -> float:
    """
    Calculate the dihedral angle for the V-tail using the formula from the original script.
    
    Parameters:
    S_h (float): Surface area of the horizontal tail projection.
    S_v (float): Surface area of the vertical tail projection.
    
    Returns:
    float: Dihedral angle in radians.
    """
    if S_h <= 0: return 0
    # NOTE: Using atan(S_v / S_h) as per the original script.
    return math.atan(S_v / S_h)

def calculate_total_tail_area(S_h: float, dihedral_angle_rad: float) -> float:
    """
    Calculates the total V-tail wetted surface area using the formula from the original script.
    
    Parameters:
    S_h (float): Surface area of the horizontal tail projection.
    dihedral_angle_rad (float): Dihedral angle in radians.
    
    Returns:
    float: Total V-tail surface area.
    """
    if math.cos(dihedral_angle_rad) == 0: return float('inf')
    # NOTE: Using S_h / cos(dihedral) as per the original script.
    return S_h / math.cos(dihedral_angle_rad)


def run_preliminary_sizing_tail(params: DesignParameters) -> dict:
    """
    Orchestrates the preliminary sizing of the V-tail surfaces by calculating all key 
    geometric properties, precisely following the logic of the original user script.
    This version serves as the standardized, callable function for this module.

    Parameters:
        params (DesignParameters): The main design parameters object.

    Returns:
        dict: A dictionary containing the calculated tail geometry parameters.
    """
    print("\nRunning Preliminary Tail Sizing (Corrected Logic)...")
    
    # Step 1: Calculate decomposed tail areas using the original script's formulas
    S_h, S_v = calculate_decomposed_tail_sizing(params)

    # Step 2: Calculate V-tail dihedral and total area using original formulas
    dihedral_rad = calculate_tail_dihedral(S_h, S_v)
    S_t = calculate_total_tail_area(S_h, dihedral_rad)
    
    # Step 3: Calculate tail span
    A_t = params.empennage.A_t
    b_t = math.sqrt(S_t * A_t)
    
    # Step 4: Calculate tail geometry using an adjusted Mach number, as per original script
    Mach_cruise_tail = params.cruise_mach + 0.05
    Mach_cross = params.wing.Mach_cross
    
    # Step 5: Calculate sweep, taper, and other geometric properties based on the adjusted Mach
    Lambda_025c_t = psw.calculate_sweep_angle_025c_rad(Mach_cruise_tail, Mach_cross)
    taper_ratio_t = psw.calculate_taper_ratio(Lambda_025c_t)
    c_root_t, c_tip_t = psw.calculate_chord_lengths(S_t, b_t, taper_ratio_t)
    MAC_t, y_LEMAC_t = psw.calculate_MAC_and_y_LEMAC(c_root_t, c_tip_t, b_t)
    
    Lambda_LE_t = psw.calculate_sweep_angle_LE(Lambda_025c_t, c_root_t, b_t, taper_ratio_t)
    Lambda_05c_t = psw.calculate_sweep_angle_x_c(Lambda_LE_t, c_root_t, b_t, 0.5, taper_ratio_t)
    
    t_c_t = psw.calculate_thickness_ratio(params.cruise_altitude, Mach_cruise_tail, params.weight.W_TO, S_t, Lambda_05c_t, Mach_cross)

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
        "aspect_ratio_t": A_t,
        "Lambda_025c_t": Lambda_025c_t, 
        "Lambda_LE_t": Lambda_LE_t,
        "Lambda_05c_t": Lambda_05c_t,
        "MAC_t": MAC_t,
        "y_LEMAC_t": y_LEMAC_t,
        "t_c_t": t_c_t,
    }
    print(f"  - Tail Sizing Complete: S_t={S_t:.2f} m^2, b_t={b_t:.2f} m, taper={taper_ratio_t:.3f}")
    return results

if __name__ == '__main__':
    # This block allows for standalone testing of this module
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')  # Adjust the path as needed

    # For standalone test, we need wing area, span, mac, etc., from Class I
    params.wing.S_w = params.weight.W_TO / params.weight.W_S
    params.wing.b_w = math.sqrt(params.wing.A_w_target * params.wing.S_w)
    
    # A simple MAC calculation for the test run if it's not already defined
    if params.wing.mac is None: 
        _, _, _, _, c_root_w, c_tip_w, _, _, _, _ = psw.run_preliminary_sizing_wing(params)
        params.wing.mac, _ = psw.calculate_MAC_and_y_LEMAC(c_root_w, c_tip_w, params.wing.b_w)

    tail_results = run_preliminary_sizing_tail(params)
    
    print("\n--- Standalone Tail Sizing Results ---")
    for key, value in tail_results.items():
        if isinstance(value, float):
            print(f"{key:<25}: {value:.4f}")
        else:
            print(f"{key:<25}: {value}")
