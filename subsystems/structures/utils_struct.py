import numpy as np
import math as m
import os
import sys
import matplotlib.pyplot as plt 

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


def calculate_Mohrs_circle_stress(sigma_x: float, sigma_y: float, tau_xy: float) -> tuple:
    """
    Calculate the principal stresses and maximum shear stress using Mohr's circle.

    Parameters:
    sigma_x (float): Normal stress in the x-direction.
    sigma_y (float): Normal stress in the y-direction.
    tau_xy (float): Shear stress in the xy-plane.

    Returns:
    tuple: Principal stresses (sigma_1, sigma_2) and maximum shear stress (tau_max).
    """
    
    R = np.sqrt(((sigma_x - sigma_y) / 2)**2 + tau_xy**2)
    sigma_avg = (sigma_x + sigma_y) / 2
    sigma_1 = sigma_avg + R
    sigma_2 = sigma_avg - R

    tau_max = R

    return sigma_1 / 1e6, sigma_2 / 1e6, tau_max / 1e6  # Convert to MPa


def plot_Mohrs_circle(sigma_x: float, sigma_y: float, tau_xy: float):
    """
    Plot Mohr's circle for the given stresses.

    Parameters:
    sigma_x (float): Normal stress in the x-direction.
    sigma_y (float): Normal stress in the y-direction.
    tau_xy (float): Shear stress in the xy-plane.
    """

    sigma_1, sigma_2, tau_max = calculate_Mohrs_circle_stress(sigma_x, sigma_y, tau_xy)

    fig, ax = plt.subplots()
    circle = plt.Circle(((sigma_1 + sigma_2) / 2, 0), tau_max, color='blue', fill=False)
    ax.add_artist(circle)

    ax.set_xlim(sigma_2 - 1 * tau_max, sigma_1 + 1 * tau_max)
    ax.set_ylim(-1.5 * tau_max, 1.5 * tau_max)
    
    ax.axhline(0, color='black', lw=0.5)
    ax.axvline(0, color='black', lw=0.5)

    ax.set_xlabel(r'Normal Stress $\sigma$ [MPa]')
    ax.set_ylabel(r'Shear Stress $\tau$ [MPa]')
    
    plt.grid()
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()


def plot_Mohrs_circle_subplots(sigma_x: float, sigma_y: float, sigma_z: float, tau_xy: float, tau_xz: float, tau_yz: float):
    """
    Plot Mohr's circle for the given stresses in subplots.

    Parameters:
    sigma_x (float): Normal stress in the x-direction.
    sigma_y (float): Normal stress in the y-direction.
    sigma_z (float): Normal stress in the z-direction.
    tau_xy (float): Shear stress in the xy-plane.
    tau_xz (float): Shear stress in the xz-plane.
    tau_yz (float): Shear stress in the yz-plane.
    """

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    # XY Plane
    sigma_1_xy, sigma_2_xy, tau_max_xy = calculate_Mohrs_circle_stress(sigma_x, sigma_y, tau_xy)
    circle_xy = plt.Circle(((sigma_1_xy + sigma_2_xy) / 2, 0), tau_max_xy, color='blue', fill=False)
    axs[0].add_artist(circle_xy)
    axs[0].set_title('XY Plane')
    axs[0].set_xlim(sigma_2_xy - 1 * tau_max_xy, sigma_1_xy + 1 * tau_max_xy)
    axs[0].set_ylim(-1.5 * tau_max_xy, 1.5 * tau_max_xy)
    
    # XZ Plane
    sigma_1_xz, sigma_2_xz, tau_max_xz = calculate_Mohrs_circle_stress(sigma_x, sigma_z, tau_xz)
    circle_xz = plt.Circle(((sigma_1_xz + sigma_2_xz) / 2, 0), tau_max_xz, color='red', fill=False)
    axs[1].add_artist(circle_xz)
    axs[1].set_title('XZ Plane')
    axs[1].set_xlim(sigma_2_xz - 1 * tau_max_xz, sigma_1_xz + 1 * tau_max_xz)
    axs[1].set_ylim(-1.5 * tau_max_xz, 1.5 * tau_max_xz)

    # YZ Plane
    sigma_1_yz, sigma_2_yz, tau_max_yz = calculate_Mohrs_circle_stress(sigma_y, sigma_z, tau_yz)
    circle_yz = plt.Circle(((sigma_1_yz + sigma_2_yz) / 2, 0), tau_max_yz, color='green', fill=False)
    axs[2].add_artist(circle_yz)
    axs[2].set_title('YZ Plane')
    axs[2].set_xlim(sigma_2_yz - 1 * tau_max_yz, sigma_1_yz + 1 * tau_max_yz)
    axs[2].set_ylim(-1.5 * tau_max_yz, 1.5 * tau_max_yz)

    # Add markers and dotted lines for XY Plane (axs[0])
    center_xy = (sigma_1_xy + sigma_2_xy) / 2
    radius_xy = tau_max_xy
    sigma_x_MPa = sigma_x / 1e6
    sigma_y_MPa = sigma_y / 1e6
    tau_xy_MPa = tau_xy / 1e6
    point_A = (sigma_x_MPa, tau_xy_MPa)
    point_B = (sigma_y_MPa, -tau_xy_MPa)
    center_point = (center_xy, 0)
    top_point = (center_xy, radius_xy)
    bottom_point = (center_xy, -radius_xy)
    axs[0].plot(*top_point, marker='D', color='red', markersize=8)
    axs[0].plot(*bottom_point, marker='D', color='red', markersize=8)
    axs[0].plot(*point_A, marker='X', color='red', markersize=8)
    axs[0].plot(*point_B, marker='X', color='red', markersize=8)
    axs[0].plot(*center_point, marker='o', color='black', markersize=5)
    axs[0].plot([point_A[0], point_B[0]], [point_A[1], point_B[1]], 'r--', linewidth=1, alpha=0.7)
    axs[0].plot([top_point[0], bottom_point[0]], [top_point[1], bottom_point[1]], 'r--', linewidth=1, alpha=0.7)
    axs[0].plot([center_point[0], point_B[0]], [center_point[1], point_B[1]], 'g--', linewidth=1, alpha=0.7)
    axs[0].plot([center_point[0], point_A[0]], [center_point[1], point_A[1]], color='orange', linestyle='--', linewidth=1, alpha=0.7)

    # Add markers and dotted lines for XZ Plane (axs[1])
    center_xz = (sigma_1_xz + sigma_2_xz) / 2
    radius_xz = tau_max_xz
    sigma_xz_MPa = sigma_x / 1e6
    sigma_z_MPa = sigma_z / 1e6
    tau_xz_MPa = tau_xz / 1e6
    point_A_xz = (sigma_xz_MPa, tau_xz_MPa)
    point_B_xz = (sigma_z_MPa, -tau_xz_MPa)
    center_point_xz = (center_xz, 0)
    top_point_xz = (center_xz, radius_xz)
    bottom_point_xz = (center_xz, -radius_xz)
    axs[1].plot(*top_point_xz, marker='D', color='red', markersize=8)
    axs[1].plot(*bottom_point_xz, marker='D', color='red', markersize=8)
    axs[1].plot(*point_A_xz, marker='X', color='red', markersize=8)
    axs[1].plot(*point_B_xz, marker='X', color='red', markersize=8)
    axs[1].plot(*center_point_xz, marker='o', color='black', markersize=5)
    axs[1].plot([point_A_xz[0], point_B_xz[0]], [point_A_xz[1], point_B_xz[1]], 'r--', linewidth=1, alpha=0.7)
    axs[1].plot([top_point_xz[0], bottom_point_xz[0]], [top_point_xz[1], bottom_point_xz[1]], 'r--', linewidth=1, alpha=0.7)
    axs[1].plot([center_point_xz[0], point_B_xz[0]], [center_point_xz[1], point_B_xz[1]], 'g--', linewidth=1, alpha=0.7)
    axs[1].plot([center_point_xz[0], point_A_xz[0]], [center_point_xz[1], point_A_xz[1]], color='orange', linestyle='--', linewidth=1, alpha=0.7)

    # Add markers and dotted lines for YZ Plane (axs[2])
    center_yz = (sigma_1_yz + sigma_2_yz) / 2
    radius_yz = tau_max_yz
    sigma_yz_MPa = sigma_y / 1e6
    tau_yz_MPa = tau_yz / 1e6
    point_A_yz = (sigma_yz_MPa, tau_yz_MPa)
    point_B_yz = (sigma_z_MPa, -tau_yz_MPa)
    center_point_yz = (center_yz, 0)
    top_point_yz = (center_yz, radius_yz)
    bottom_point_yz = (center_yz, -radius_yz)
    axs[2].plot(*top_point_yz, marker='D', color='red', markersize=8)
    axs[2].plot(*bottom_point_yz, marker='D', color='red', markersize=8)
    axs[2].plot(*point_A_yz, marker='X', color='red', markersize=8)
    axs[2].plot(*point_B_yz, marker='X', color='red', markersize=8)
    axs[2].plot(*center_point_yz, marker='o', color='black', markersize=5)
    axs[2].plot([point_A_yz[0], point_B_yz[0]], [point_A_yz[1], point_B_yz[1]], 'r--', linewidth=1, alpha=0.7)
    axs[2].plot([top_point_yz[0], bottom_point_yz[0]], [top_point_yz[1], bottom_point_yz[1]], 'r--', linewidth=1, alpha=0.7)
    axs[2].plot([center_point_yz[0], point_B_yz[0]], [center_point_yz[1], point_B_yz[1]], 'g--', linewidth=1, alpha=0.7)
    axs[2].plot([center_point_yz[0], point_A_yz[0]], [center_point_yz[1], point_A_yz[1]], color='orange', linestyle='--', linewidth=1, alpha=0.7)

    for ax in axs:
        ax.axhline(0, color='black', lw=0.5)
        ax.axvline(0, color='black', lw=0.5)
        ax.set_xlabel(r'Normal Stress $\sigma$ [MPa]')
        ax.set_ylabel(r'Shear Stress $\tau$ [MPa]')
        ax.grid()
        ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.show()


def plot_Mohrs_circle_complete(sigma_x: float, sigma_y: float, sigma_z: float, tau_xy: float, tau_xz: float, tau_yz: float):
    """
    Plot Mohr's circle for the given stresses.

    Parameters:
    sigma_x (float): Normal stress in the x-direction.
    sigma_y (float): Normal stress in the y-direction.
    sigma_z (float): Normal stress in the z-direction.
    tau_xy (float): Shear stress in the xy-plane.
    tau_xz (float): Shear stress in the xz-plane.
    tau_yz (float): Shear stress in the yz-plane.
    """

    xy_sigma_1, xy_sigma_2, xy_tau_max = calculate_Mohrs_circle_stress(sigma_x, sigma_y, tau_xy) 
    xz_sigma_1, xz_sigma_2, xz_tau_max = calculate_Mohrs_circle_stress(sigma_x, sigma_z, tau_xz) 
    yz_sigma_1, yz_sigma_2, yz_tau_max = calculate_Mohrs_circle_stress(sigma_y, sigma_z, tau_yz)

    sigma_1_min = min(xy_sigma_1, xz_sigma_1, yz_sigma_1)
    sigma_1_max = max(xy_sigma_1, xz_sigma_1, yz_sigma_1)
    sigma_2_min = min(xy_sigma_2, xz_sigma_2, yz_sigma_2)
    sigma_2_max = max(xy_sigma_2, xz_sigma_2, yz_sigma_2)
    tau_max_max = max(xy_tau_max, xz_tau_max, yz_tau_max)

    fig, ax = plt.subplots()
    circle_xy = plt.Circle(((xy_sigma_1 + xy_sigma_2) / 2, 0), xy_tau_max, color='blue', fill=False)
    circle_xz = plt.Circle(((xz_sigma_1 + xz_sigma_2) / 2, 0), xz_tau_max, color='red', fill=False)
    circle_yz = plt.Circle(((yz_sigma_1 + yz_sigma_2) / 2, 0), yz_tau_max, color='green', fill=False)
    ax.add_artist(circle_xy)
    ax.add_artist(circle_xz)
    ax.add_artist(circle_yz)

    ax.set_xlim(sigma_2_min - 1 * tau_max_max, sigma_1_max + 1 * tau_max_max)
    ax.set_ylim(-1.5 * tau_max_max, 1.5 * tau_max_max)
    
    ax.axhline(0, color='black', lw=0.5)
    ax.axvline(0, color='black', lw=0.5)

    ax.set_xlabel(r'Normal Stress $\sigma$ [MPa]')
    ax.set_ylabel(r'Shear Stress $\tau$ [MPa]')
    
    plt.grid()
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()


if __name__ == "__main__":
    # Example usage
    sigma_x = 100e6     # Pa
    sigma_y = 0         # Pa
    sigma_z = 30e6      # Pa
    tau_xy = 10e6          # Pa
    tau_xz = 25e6          # Pa
    tau_yz = 10e6          # Pa

    E = 200e9  # Pa
    nu = 0.3
    alpha = 1.2e-5  # /K
    dT = 50  # K

    plot_Mohrs_circle_subplots(sigma_x, sigma_y, sigma_z, tau_xy, tau_xz, tau_yz)
    plot_Mohrs_circle_complete(sigma_x, sigma_y, sigma_z, tau_xy, tau_xz, tau_yz)