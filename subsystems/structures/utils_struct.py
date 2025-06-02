import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from design_variables import DesignParameters
from utils.unit_conversions import *


def calculate_normal_strains(sigma_x: float, sigma_y: float, sigma_z: float, dT: float, E: float, nu: float, alpha: float) -> tuple:
    """
    Calculate the normal strains based on the stresses, temperature change, Young's modulus, Poisson's ratio, and thermal expansion coefficient.

    Parameters:
    sigma_x (float): Stress in the x-direction.
    sigma_y (float): Stress in the y-direction.
    sigma_z (float): Stress in the z-direction.
    dT (float): Temperature change.
    E (float): Young's modulus.
    nu (float): Poisson's ratio.
    alpha (float): Thermal expansion coefficient.

    Returns:
    tuple: Strains in the x, y, and z directions.
    """
    
    strain_x = 1 / E * (sigma_x - nu * (sigma_y + sigma_z)) + alpha * dT
    strain_y = 1 / E * (sigma_y - nu * (sigma_x + sigma_z)) + alpha * dT
    strain_z = 1 / E * (sigma_z - nu * (sigma_x + sigma_y)) + alpha * dT

    return {'x': strain_x, 'y': strain_y, 'z': strain_z}


def calculate_shear_strains(tau_xy: float, tau_xz: float, tau_yz: float, G: float) -> tuple:
    """
    Calculate the shear strains based on the shear stresses and shear modulus.

    Parameters:
    tau_xy (float): Shear stress in the xy-plane.
    tau_xz (float): Shear stress in the xz-plane.
    tau_yz (float): Shear stress in the yz-plane.
    G (float): Shear modulus.

    Returns:
    tuple: Shear strains in the xy, xz, and yz planes.
    """
    
    shear_strain_xy = tau_xy / G
    shear_strain_xz = tau_xz / G
    shear_strain_yz = tau_yz / G

    return {'xy': shear_strain_xy, 'xz': shear_strain_xz, 'yz': shear_strain_yz}


def calculate_axial_stress(F_axial: float, A: float) -> float:
    """
    Calculate the axial stress based on the axial force and cross-sectional area.

    Parameters:
    F_axial (float): Axial force.
    A (float): Cross-sectional area.

    Returns:
    float: Axial stress.
    """
    
    return F_axial / A


def calculate_axial_deformation(F_axial: float, L: float, E: float, A: float) -> float:
    """
    Calculate the axial deformation based on the axial force, length, Young's modulus, and cross-sectional area.

    Parameters:
    F_axial (float): Axial force.
    L (float): Length of the member.
    E (float): Young's modulus.
    A (float): Cross-sectional area.

    Returns:
    float: Axial deformation.
    """
    
    return (F_axial * L) / (E * A)


def calculate_torsional_stress_circ(T: float, J: float, r: float) -> float:
    """
    Calculate the torsional stress based on the torque, polar moment of inertia, and radius.

    Parameters:
    T (float): Torque.
    J (float): Polar moment of inertia.
    r (float): Radius.

    Returns:
    float: Torsional stress.
    """
    
    return (T * r) / J


def calculate_torsional_deformation_circ(T: float, L: float, G: float, J: float) -> float:
    """
    Calculate the torsional deformation based on the torque, length, shear modulus, and polar moment of inertia.

    Parameters:
    T (float): Torque.
    L (float): Length of the member.
    G (float): Shear modulus.
    J (float): Polar moment of inertia.

    Returns:
    float: Torsional deformation.
    """
    
    return (T * L) / (G * J)


def calculate_torsional_stress_thin(T: float, t: float, A_m: float) -> float:
    """
    Calculate the torsional stress for a thin-walled tube based on the torque, wall thickness, and mean area.

    Parameters:
    T (float): Torque.
    t (float): Wall thickness.
    A_m (float): Mean area.

    Returns:
    float: Torsional stress.
    """
    
    return T / (2 * t * A_m)


def calculate_torsional_deformation_thin(T: float, L: float, A_m: float, G: float, t: float, L_m: float) -> float:
    """
    Calculate the torsional deformation for a thin-walled tube based on the torque, length, mean area, shear modulus, wall thickness, and mean length.

    Parameters:
    T (float): Torque.
    L (float): Length of the member.
    A_m (float): Mean area.
    G (float): Shear modulus.
    t (float): Wall thickness.
    L_m (float): Mean perimeter length.

    Returns:
    float: Torsional deformation.
    """
    
    return (T * L) / (4 * A_m**2 * G) * np.integrate.quad(lambda t: 1 / t, 0, L_m)[0]


def calculate_bending_stress(M: float, y: float, I: float) -> float:
    """
    Calculate the bending stress based on the bending moment, distance from the neutral axis, and moment of inertia.

    Parameters:
    M (float): Bending moment.
    y (float): Distance from the neutral axis.
    I (float): Moment of inertia.

    Returns:
    float: Bending stress.
    """
    
    return (M * y) / I


def calculate_transverse_shear_stress(V: float, Q: float, I: float, t: float) -> float:
    """
    Calculate the transverse shear stress based on the shear force, first moment of area, moment of inertia, and thickness.

    Parameters:
    V (float): Shear force.
    Q (float): First moment of area.
    I (float): Moment of inertia.
    t (float): Thickness.

    Returns:
    float: Transverse shear stress.
    """
    
    return (V * Q) / (I * t)