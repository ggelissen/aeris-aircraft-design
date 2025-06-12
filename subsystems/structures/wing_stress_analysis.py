import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from design_variables import DesignParameters
from wing_structure_generation import cross_sectional_structure_along_span
from ideal_cross_section_analysis import run_cross_section_analysis
from loading_diagrams import WingLoadingDiagrams
from utils_struct import *


def perform_cross_section_analysis(designvars: DesignParameters, loading: dict, spanwise_position: float = 0.0):
    """
    Performs cross-sectional analysis of the wing structure at a given spanwise position.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - spanwise_position: Position along the span where the cross-section is generated as a fraction of the total span (0.0 to 1.0).
    """
    
    spar_points_array, stringer_array, _, _, _, _ = cross_sectional_structure_along_span(designvars, spanwise_position, plot=False)
    results = run_cross_section_analysis(designvars, spar_points_array, stringer_array, loading["moment_x"], loading["moment_z"],
                                         loading["torque_y"], loading["shear_x"], loading["shear_z"], designvars.wing.skin_thickness, plot=False)
    return results


def calculate_bending_distribution(M: np.ndarray, I: np.ndarray, E: float, half_span: float) -> np.ndarray:
    """
    Calculates the bending distribution along the span of the wing based on the applied bending moment and structural properties.

    Parameters:
    - M: Bending moment at the section.
    - I: Area moment of inertia of the wing section.
    - E: Young's modulus of the material.
    - half_span: Half span of the wing.

    Returns:
    - Bending stress distribution along the span.
    """
    deflection = -1 / E * np.cumulative_trapezoid(M/I, dx=half_span / (len(M) - 1), initial=0)
    return deflection


def calculate_angle_of_twist(T: np.ndarray, A_m: np.ndarray, G: float, skin_thickness: float, perimeter: float, half_span: float) -> np.ndarray:
    """
    Calculates the angle of twist for a wing section based on the applied torque and structural properties.

    Parameters:
    - T: Applied torque at the section.
    - A_m: Area moment of inertia of the wing section.
    - G: Shear modulus of the material.
    - skin_thickness: Thickness of the wing skin.
    - half_span: Half span of the wing.

    Returns:
    - Angle of twist distribution in radians.
    """
    twist_angle = 1 / (4*G) * np.cumulative_trapezoid((T * perimeter) / (A_m * skin_thickness), dx=half_span / (len(T) - 1), initial=0)
    return twist_angle


def plot_bending_distribution(spanwise_position_lst: np.ndarray, bending_distribution: np.ndarray, axis: str = 'x'):
    """
    Plots the bending distribution along the span of the wing.

    Parameters:
    - spanwise_position_lst: List of spanwise positions.
    - bending_distribution: Bending distribution
    """

    plt.figure(figsize=(12, 6))
    plt.plot(spanwise_position_lst, bending_distribution, color='blue')
    plt.xlabel('Spanwise Position (y) [m]')
    if axis == 'x':
        plt.ylabel(f'Bending Deflection (z) [m]')
    elif axis == 'z':
        plt.ylabel(f'Bending Deflection (x) [m]')
    plt.grid()
    plt.show()


def plot_twist_distribution(spanwise_position_lst: np.ndarray, twist_distribution: np.ndarray):
    """
    Plots the angle of twist distribution along the span of the wing.

    Parameters:
    - spanwise_position_lst: List of spanwise positions.
    - twist_distribution: Angle of twist distribution in radians.
    """
    
    plt.figure(figsize=(12, 6))
    plt.plot(spanwise_position_lst, twist_distribution, color='blue')
    plt.xlabel('Spanwise Position (y) [m]')
    plt.ylabel('Angle of Twist [rad]')
    plt.grid()
    plt.show()



if __name__ == "__main__":

    designvars = DesignParameters()
    designvars.load_from_yaml("design_config.yaml")
    wing_loading = WingLoadingDiagrams()
    wing_loading = wing_loading.run_analysis(PLOT=False)
    spanwise_position_lst = np.linspace(0.0, 1.0, 1000)

    cross_sectional_results = np.array([])
    for i, spanwise_position in enumerate(spanwise_position_lst):
        results = perform_cross_section_analysis(designvars, wing_loading[i], spanwise_position)
        cross_sectional_results = np.append(cross_sectional_results, results)

    x_bending_distribution = np.array([])
    y_twist_distribution = np.array([])
    z_bending_distribution = np.array([])

    for i in range(len(spanwise_position_lst)):
        x_bending = calculate_bending_distribution(wing_loading[i]["moment_x"], cross_sectional_results[i]["Ixx"],
                                                    designvars.materials.elastic_modulus, designvars.wing.b_w/2)
        y_twist = calculate_angle_of_twist(wing_loading[i]["torque_y"], cross_sectional_results[i]["A_m"],
                                            designvars.materials.shear_modulus, designvars.wing.skin_thickness,
                                            cross_sectional_results[i]["perimeter"], designvars.wing.b_w/2)
        z_bending = calculate_bending_distribution(wing_loading[i]["moment_z"], cross_sectional_results[i]["Iyy"],
                                                    designvars.materials.elastic_modulus, designvars.wing.b_w/2)
        x_bending_distribution = np.append(x_bending_distribution, x_bending)
        y_twist_distribution = np.append(y_twist_distribution, y_twist)
        z_bending_distribution = np.append(z_bending_distribution, z_bending)

    # Plotting the bending distributions
    plot_bending_distribution(spanwise_position_lst, x_bending_distribution, axis='x')
    plot_bending_distribution(spanwise_position_lst, z_bending_distribution, axis='z')