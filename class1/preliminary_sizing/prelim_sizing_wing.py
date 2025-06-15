import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from design_variables import DesignParameters
from utils.unit_conversions import *



def calculate_sweep_angle_025c_rad(Mach_cruise: float, Mach_cross: float = 0.935) -> float:
    """
    Calculate the sweep angle based on the cruise Mach number.
    Source: Torenbeek, "Advanced Aircraft Design: Conceptual Design, Analysis and Optimization of Subsonic Civil Airplanes"
    
    Parameters:
    Mach_cruise (float): Cruise Mach number
    
    Returns:
    float: Sweep angle in radians
    """
    Mach_dd = Mach_cruise + 0.015
    if Mach_cruise < 0.7:
        return np.arccos(1)
    else:
        #return np.arccos(0.75 * (Mach_cross / Mach_dd))
        return np.arccos(1.16  / (Mach_dd + 0.5)) # TODO, equation from PJ thesis
    

def calculate_taper_ratio(Lambda_025c: float) -> float:
    """
    Calculate the taper ratio based on the sweep angle at 0.25c.
    
    Parameters:
    Lambda_025c (float): Sweep angle at 0.25c in radians
    
    Returns:
    float: Taper ratio
    """
    return 0.2 * (2 - Lambda_025c)


def calculate_chord_lengths(S: float, b: float, taper_ratio: float) -> tuple:
    """
    Calculate the chord lengths based on the wing area, span, and sweep angle at 0.25c.
    
    Parameters:
    S (float): Wing area
    b (float): Wing span
    Lambda_025c (float): Sweep angle at 0.25c in radians
    
    Returns:
    tuple: Chord lengths (root chord, tip chord)
    """
    c_root = 2 * S / (b * (1 + taper_ratio))
    c_tip = c_root * taper_ratio
    return c_root, c_tip


def calculate_MAC_and_y_LEMAC(c_root: float, c_tip: float, b: float) -> tuple:
    """
    Calculate the Mean Aerodynamic Chord (MAC) and the y-position of the Leading Edge of MAC (y_LEMAC)
    for a trapezoidal wing using the graphical method.

    Parameters:
    c_root (float): Root chord length
    c_tip (float): Tip chord length
    b (float): Wing span

    Returns:
    tuple: (MAC, y_LEMAC)
    """
    taper = c_tip / c_root

    MAC = (2/3) * c_root * ((1 + taper + taper**2) / (1 + taper))
    y_LEMAC = (b / 6) * ((1 + 2 * taper) / (1 + taper))

    return MAC, y_LEMAC


def calculate_thickness_ratio(h: float, Mach_cruise: float, W_TO: float, S: float, Lambda_05c: float, Mach_cross: float = 0.935) -> float:
    """
    Calculate the thickness-to-chord ratio based on the altitude, critical Mach number, takeoff weight, wing area,
    and sweep angle at 0.5c.
    
    Parameters:
    h (float): Altitude in meters
    Mach_cruise (float): Cruise Mach number
    W_TO (float): Takeoff weight in Newtons
    S (float): Wing area in square meters
    Lambda_05c (float): Sweep angle at 0.5c in radians
    Mach_cross (float): Cross-over Mach number (default is 0.935)
    
    Returns:
    float: Thickness-to-chord ratio
    """
    constants = {'p0': 101325, 'T0': 288.15, 'R': 287.05, 'lambda': 0.0065, 'g0': 9.80665, 'gamma': 1.4}
    constants_11km = {'p': 22632.06, 'T': 216.65, 'rho': 0.36391}
    # Calculate pressure at altitude until 11 km
    if h <= 11000:
        p = constants['p0'] * (1 - constants['lambda'] * h / constants['T0']) ** (constants['g0'] / (constants['R'] * constants['lambda']))
    # Calculate pressure if altitude is above 11 km
    elif h > 11000:
        p = constants_11km['p'] * np.exp(-constants['g0'] * (h/1000 - 11) / (constants['R'] * constants_11km['T']))
    
    q = 0.5 * constants['gamma'] * p * Mach_cruise ** 2
    C_L = W_TO / (q * S)
    Mach_dd = Mach_cruise + 0.03

    # Calculate thickness-to-chord ratio using the Korn-Lock formula for Mdd
    t_c = min(((np.cos(Lambda_05c))**3 * (Mach_cross - Mach_dd * np.cos(Lambda_05c)) - 0.115 * C_L**(1.5))/((np.cos(Lambda_05c))**2), 0.18)
    return t_c


def calculate_dihedral_angle_rad(Lambda_025c: float) -> float:
    """
    Calculate the dihedral angle based on the sweep angle at 0.25c.
    Guidelines for determining dihedral angle:
        • Default: 3 degrees for unswept wings at mid-wing location
        • For every 10 degrees of quarter-chord sweep angle, reduce dihedral angle by 1 degree*
        • For high-wing/low-wing aircraft: subtract/add 2 degrees, respectively
        • If dihedral angle needs to be increased due to clearance constraints: add yaw damper
    
    Parameters:
    Lambda_025c (float): Sweep angle at 0.25c in radians
    
    Returns:
    float: Dihedral angle in radians
    """
    Gamma_deg =  3 -  1 * np.round(np.rad2deg(Lambda_025c) / 10, 0) + 0
    return np.deg2rad(Gamma_deg)


def calculate_sweep_angle_LE(Lambda_025c: float, c_root: float, b: float, taper_ratio: float) -> float:
    """
    Calculate the sweep angle at LE based on the sweep angle at 0.25c.
    
    Parameters:
    Lambda_025c (float): Sweep angle at 0.25c in radians
    
    Returns:
    float: Sweep angle at LE in radians
    """
    return np.arctan2(np.tan(Lambda_025c) + 0.25 * 2 * c_root / b * (1 - taper_ratio), 1)


def calculate_sweep_angle_x_c(Lambda_LE: float, c_root: float, b: float, x_c: float, taper_ratio: float) -> float:
    """
    Calculate the sweep angle at a specific x/c location based on the sweep angle at LE.
    
    Parameters:
    Lambda_LE (float): Sweep angle at LE in radians
    c_root (float): Root chord length
    b (float): Wing span
    x_c (float): x/c location
    taper_ratio (float): Taper ratio
    
    Returns:
    float: Sweep angle at x/c in radians
    """
    return np.arctan2(np.tan(Lambda_LE) - x_c * 2 * c_root / b * (1 - taper_ratio), 1)


def run_preliminary_sizing_wing(params: DesignParameters) -> dict: # pragma: no cover
    """
    Run preliminary sizing calculations for the wing based on design parameters.

    Parameters:
    params (DesignParameters): An instance of DesignParameters containing the design variables.

    Returns:
    dict: A dictionary containing the results of the preliminary sizing calculations.
    """

    Mach_cruise = params.cruise_mach
    Mach_cross = 0.935
    Lambda_025c = calculate_sweep_angle_025c_rad(Mach_cruise, Mach_cross)
    #print(f"Calculated sweep angle at 0.25c (Lambda_025c): {(Lambda_025c)} degrees")
    taper_ratio = calculate_taper_ratio(Lambda_025c)
    
    S = params.wing.S_w 
    b = params.wing.b_w   
    
    c_root, c_tip = calculate_chord_lengths(S, b, taper_ratio)
    MAC, y_LEMAC = calculate_MAC_and_y_LEMAC(c_root, c_tip, b)
    
    h = params.cruise_altitude 
    W_TO = params.weight.W_TO 
    
    Lambda_LE = calculate_sweep_angle_LE(Lambda_025c, c_root, b, taper_ratio)
    Lambda_05c = calculate_sweep_angle_x_c(Lambda_LE, c_root, b, 0.5, taper_ratio)
    t_c = calculate_thickness_ratio(h, Mach_cruise, W_TO, S, Lambda_05c, Mach_cross)
    
    dihedral_angle_rad = calculate_dihedral_angle_rad(Lambda_025c)

    results = {
        'Lambda_025c_w': Lambda_025c,
        'Lambda_05c_w': Lambda_05c,
        'Lambda_LE_w': Lambda_LE,
        'lambda_w': taper_ratio,
        'root_chord': c_root,
        'tip_chord': c_tip,
        'mac': MAC,
        'y_LEMAC': y_LEMAC,
        't_c_w_max': t_c,
        'Gamma_w': dihedral_angle_rad,
    }
    return results