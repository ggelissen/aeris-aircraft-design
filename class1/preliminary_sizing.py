import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




def calculate_thickness_ratio_method1(M_cr: float, gamma: float = 1.4) -> float:
    """
    Calculate the thickness-to-chord ratio based on the critical Mach number.
    (Method 1)
    
    Parameters:
    gamma (float): Specific heat ratio (default is 1.4 for air)
    M_cr (float): Critical Mach number
    
    Returns:
    float: Thickness-to-chord ratio
    """
    t_c_1 = 1 - ((2 + (gamma - 1) * M_cr ** 2) / (gamma + 1)) ** (gamma / (gamma - 1))
    t_c_2 = (2 / (gamma * M_cr ** 2)) * t_c_1 * np.sqrt(1 - M_cr ** 2)
    return t_c_2 ** (2/3)

def calculate_thickness_ratio_method2(Mach: float, Mach_star: float) -> float:
    """
    Calculate the thickness-to-chord ratio based on the Mach number and Mach star.
    (Method 2)
    
    Parameters:
    Mach (float): Mach number
    Mach_star (float): Mach number defining aerodynamic sophistication
    
    Returns:
    float: Thickness-to-chord ratio
    """
    t_c_1 = 1 - ((5 + Mach ** 2) / (5 + Mach_star ** 2)) ** (3.5)
    t_c_2 = (np.sqrt(1 - Mach ** 2)) / (Mach ** 2)
    return 0.3 * (t_c_1 * t_c_2) ** (2/3)

