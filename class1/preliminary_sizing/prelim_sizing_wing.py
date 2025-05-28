import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from design_variables import DesignParameters
from utils.unit_conversions import *



def calculate_Lambda_025c_rad(M_cr: float, M_cross: float = 0.935) -> float:
    """
    Calculate the sweep angle based on the critical Mach number.
    Source: Torenbeek, "Advanced Aircraft Design: Conceptual Design, Analysis and Optimization of Subsonic Civil Airplanes"
    
    Parameters:
    M_cr (float): Critical Mach number
    
    Returns:
    float: Sweep angle in radians
    """
    M_dd = M_cr + 0.03
    if M_cr < 0.7:
        return np.arccos(1)
    else:
        return np.arccos(0.75 * (M_cross / M_dd))
    

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


def calculate_thickness_ratio(h: float, M_cr: float, W_TO: float, S: float, Lambda_05c: float, M_cross: float = 0.935) -> float:
    """
    Calculate the thickness-to-chord ratio based on the altitude, critical Mach number, takeoff weight, wing area,
    and sweep angle at 0.5c.
    
    Parameters:
    h (float): Altitude in meters
    M_cr (float): Critical Mach number
    W_TO (float): Takeoff weight in Newtons
    S (float): Wing area in square meters
    Lambda_05c (float): Sweep angle at 0.5c in radians
    M_cross (float): Cross-over Mach number (default is 0.935)
    
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
        p = constants_11km['p'] * np.exp(-constants['g0'] * (h - 11000) / (constants['R'] * constants_11km['T']))
    
    q = 0.5 * constants['gamma'] * p * M_cr ** 2
    C_L = W_TO / (q * S)
    M_dd = M_cr + 0.03

    t_c = min(((np.cos(Lambda_05c))**3 * (M_cross - M_dd * np.cos(Lambda_05c)) - 0.115 * C_L**1.5)/((np.cos(Lambda_05c))**2), 0.18)
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
    Gamma_deg =  3 -  1 * np.round(np.rad2deg(Lambda_025c) / 10, 0) + 2
    return np.deg2rad(Gamma_deg)



if __name__ == "__main__":

    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    M_cr = 0.85
    M_cross = 0.935
    Lambda_025c = calculate_Lambda_025c_rad(M_cr, M_cross)
    taper_ratio = calculate_taper_ratio(Lambda_025c)
    
    S = 100  # Wing area in square meters
    b = 30   # Wing span in meters
    
    c_root, c_tip = calculate_chord_lengths(S, b, taper_ratio)
    MAC, y_LEMAC = calculate_MAC_and_y_LEMAC(c_root, c_tip, b)
    
    h = 10000  # Altitude in meters
    W_TO = 500000  # Takeoff weight in Newtons
    
    Lambda_05c = np.deg2rad(5)  # Example sweep angle at 0.5c in radians
    t_c = calculate_thickness_ratio(h, M_cr, W_TO, S, Lambda_05c, M_cross)
    
    dihedral_angle_rad = calculate_dihedral_angle_rad(Lambda_025c)
    
    print(f"Lambda_025c: {np.rad2deg(Lambda_025c)} degrees")
    print(f"Taper Ratio: {taper_ratio}")
    print(f"Root Chord: {c_root} m, Tip Chord: {c_tip} m")
    print(f"MAC: {MAC} m, y_LEMAC: {y_LEMAC} m")
    print(f"Thickness-to-Chord Ratio: {t_c}")
    print(f"Dihedral Angle: {np.rad2deg(dihedral_angle_rad)} degrees")