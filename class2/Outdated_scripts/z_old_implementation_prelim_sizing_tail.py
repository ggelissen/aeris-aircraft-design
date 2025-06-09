import math
import yaml
import os
import sys

# Allow imports from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from utils.unit_conversions import * 
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
    dihedral_angle = calculate_tail_dihedral(S_h, S_v) # Here defined as dihedral, before defined as Gamma
    S_t = S_h / math.cos(dihedral_angle)

    return S_t

# def perform_tail_positioning(params: DesignParameters):
    

if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    # Perform tail sizing calculations
    S_h, S_v = calculate_decomposed_tail_sizing(params)
    Gamma = calculate_tail_dihedral(S_h, S_v)
    S_t = calculate_tail_sizing(S_h, S_v)

    # Print the results
    print(f"Horizontal Tail Surface Area (S_h): {S_h:.2f} m^2")
    print(f"Vertical Tail Surface Area (S_v): {S_v:.2f} m^2")
    print(f"Dihedral Angle (Gamma): {Gamma:.4f} radians")
    print(f"Total Tail Surface Area (S_t): {S_t:.2f} m^2")

    Mach_cruise = params.cruise_mach + 0.05 # Adjusted for tail TODO, add Torenbeek source.
    Mach_cross = params.wing.Mach_cross # 0.935, for supercritical airfoil
    Lambda_025c_t = psw.calculate_sweep_angle_025c_rad(Mach_cruise, Mach_cross)
    taper_ratio_t = psw.calculate_taper_ratio(Lambda_025c_t)

    b_t = math.sqrt(S_t * params.empennage.A_t)
    
    c_root_t, c_tip_t = psw.calculate_chord_lengths(S_t, b_t, taper_ratio_t)
    MAC_t, y_LEMAC_t = psw.calculate_MAC_and_y_LEMAC(c_root_t, c_tip_t, b_t)
    
    h = params.cruise_altitude  # Altitude in meters
    W_TO = params.weight.W_TO  # Takeoff weight in Newtons
    
    Lambda_LE_t = psw.calculate_sweep_angle_LE(Lambda_025c_t, c_root_t, b_t, taper_ratio_t)
    Lambda_05c_t = psw.calculate_sweep_angle_x_c(Lambda_LE_t, c_root_t, b_t, 0.5, taper_ratio_t)
    t_c_t = psw.calculate_thickness_ratio(h, Mach_cruise, W_TO, S_t, Lambda_05c_t, Mach_cross)
    
    #dihedral_angle_t_rad = psw.calculate_dihedral_angle_rad(Lambda_025c_t)
    
    print(f"Sweep Angle at 0.25c: {np.round(Lambda_025c_t,4)} radians")
    print(f"Taper Ratio: {np.round(taper_ratio_t,4)}")
    print(f"Root Chord: {np.round(c_root_t,4)} m, Tip Chord: {np.round(c_tip_t,4)} m")
    print(f"Tail Span: {np.round(b_t,4)} m")
    print(f"MAC: {np.round(MAC_t,4)} m, y_LEMAC: {np.round(y_LEMAC_t,4)} m")
    print(f"Thickness-to-Chord Ratio: {np.round(t_c_t,4)}")
    #print(f"Dihedral Angle: {np.round(dihedral_angle_t_rad,4)} radians")