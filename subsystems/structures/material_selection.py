import numpy as np
from scipy import integrate
import math as m
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from design_variables import DesignParameters
try:
    from loading_diagrams import WingLoadingDiagrams
except:
    from subsystems.structures.loading_diagrams import WingLoadingDiagrams
try:
    from wing_structure_generation import cross_sectional_structure_along_span
except:
    from subsystems.structures.wing_structure_generation import cross_sectional_structure_along_span
try:
    from ideal_cross_section_analysis import calculate_panel_lengths_and_enclosed_area
except:
    from subsystems.structures.ideal_cross_section_analysis import calculate_panel_lengths_and_enclosed_area


def obtain_spar_coordinates(designvars: DesignParameters, span_lst: np.ndarray) -> tuple:
    """
    Obtains the coordinates of the spars at a given spanwise position.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - span_lst: Array of spanwise positions.

    Returns:
    - Tuple containing x and y coordinates of the spars.
    """
    x_coordinates = np.array([])
    y_coordinates = np.array([])

    for i in range(len(span_lst)):
        coordinates = np.array(cross_sectional_structure_along_span(designvars, span_lst[i])[0])
        x1, y1 = coordinates[0,0]
        x2, y2 = coordinates[0,1]
        x3, y3 = coordinates[1,0]
        x4, y4 = coordinates[1,1]
        x_coordinates = np.append(x_coordinates, [x2, x3, x4, x1])
        y_coordinates = np.append(y_coordinates, [y2, y3, y4, y1])

    return x_coordinates, y_coordinates


def calculate_panel_angles(x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
    """
    Calculates the angles of the panels defined by their vertices.

    Parameters:
    - x_coords: x-coordinates of the polygon vertices.
    - y_coords: y-coordinates of the polygon vertices.

    Returns:
    - Numpy array containing the angles of the panels in radians.
    """
    angles = np.zeros(4)
    for i in range(4):
        dx = x_coords[i + 1] - x_coords[i]
        dy = y_coords[i + 1] - y_coords[i]
        angles[i] = m.atan2(dy, dx)

    return angles


def calculate_individual_centroids(x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
    """
    Calculates the centroids of individual panels defined by their vertices.

    Parameters:
    - x_coords: x-coordinates of the polygon vertices.
    - y_coords: y-coordinates of the polygon vertices.

    Returns:
    - Numpy array containing the x and y coordinates of the centroids for each panel.
    """
    x_centroid_spar_1 = np.average(x_coords[0:2])
    y_centroid_spar_1 = np.average(y_coords[0:2])
    x_centroid_skin_1 = np.average(x_coords[1:3])
    y_centroid_skin_1 = np.average(y_coords[1:3])
    x_centroid_spar_2 = np.average(x_coords[2:4])
    y_centroid_spar_2 = np.average(y_coords[2:4])
    x_centroid_skin_2 = np.average(x_coords[3], x_coords[4])
    y_centroid_skin_2 = np.average(y_coords[3], y_coords[4])

    return np.array([(x_centroid_spar_1, y_centroid_spar_1), (x_centroid_skin_1, y_centroid_skin_1),
                     (x_centroid_spar_2, y_centroid_spar_2), (x_centroid_skin_2, y_centroid_skin_2)])

def calculate_centroid(centroids: np.ndarray, panel_areas: np.ndarray) -> tuple:
    """
    Calculates the centroid of a polygon defined by its vertices.

    Parameters:
    - x_coords: x-coordinates of the polygon vertices.
    - y_coords: y-coordinates of the polygon vertices.
    - panel_areas: Areas of the panels defined by the vertices.

    Returns:
    - Tuple containing the x and y coordinates of the centroid.
    """

    x_centroid = (panel_areas[0] * centroids[0, 0] + panel_areas[1] * centroids[1, 0] +
                   panel_areas[2] * centroids[2, 0] + panel_areas[3] * centroids[3, 0]) / np.sum(panel_areas)
    y_centroid = (panel_areas[0] * centroids[0, 1] + panel_areas[1] * centroids[1, 1] +
                   panel_areas[2] * centroids[2, 1] + panel_areas[3] * centroids[3, 1]) / np.sum(panel_areas)

    return x_centroid, y_centroid


def calculate_moment_of_inertia(centroids: np.ndarray, t_spar: float, t_skin: float, panel_lengths: np.ndarray, panel_angles: np.ndarray, centroid: tuple) -> float:
    """
    Calculates the area moment of inertia for a given set of coordinates.

    Parameters:
    - centroids: Numpy array containing the x and y coordinates of the centroids for each panel.
    - panel_areas: Areas of the panels defined by the vertices.
    - panel_lengths: Lengths of the panels defined by the vertices.
    - panel_angles: Angles of the panels defined by the vertices.
    - centroid: Tuple containing the x and y coordinates of the centroid of the polygon.

    Returns:
    - Area moment of inertia.
    """
    I_xx = 0.0
    I_yy = 0.0
    I_xy = 0.0

    panel_thickness = np.array([t_spar, t_skin, t_spar, t_skin])

    for panel in range(len(panel_areas)):
        I_xx += (panel_thickness[panel] * panel_lengths[panel]**3 * np.sin(panel_angles[panel])) / 12 
        I_yy += (panel_thickness[panel] * panel_lengths[panel]**3 * np.cos(panel_angles[panel])) / 12
        I_xy += (panel_thickness[panel] * panel_lengths[panel]**3 * np.sin(panel_angles[panel]) * np.cos(panel_angles[panel])) / 12

        I_xx += panel_thickness[panel] * panel_lengths[panel] * (centroids[panel, 1] - centroid[1])**2
        I_yy += panel_thickness[panel] * panel_lengths[panel] * (centroids[panel, 0] - centroid[0])**2
        I_xy += panel_thickness[panel] * panel_lengths[panel] * (centroids[panel, 0] - centroid[0]) * (centroids[panel, 1] - centroid[1])

    return I_xx, I_yy, I_xy


def calculate_max_bending_stress(Mx: float, My: float, I_xx: float, I_yy: float, I_xy: float, x_coords: np.ndarray, y_coord: np.ndarray, centroid: tuple) -> float:
    """
    Calculates max bending stress (sigma_max) at a point (x, y) in a cross-section.
    Formula (2.4):
    sigma_z = ((Mx*I_yy - My*I_xy)*y + (My*I_xx - Mx*I_xy)*x) / (I_xx*I_yy - I_xy^2)

    Parameters:
        Mx (float): Bending moment about the x-axis in Nm.
        My (float): Bending moment about the y-axis in Nm.
        I_xx (float): Moment of inertia about the x-axis in m4.
        I_yy (float): Moment of inertia about the y-axis in m4.
        I_xy (float): Product of inertia in m4.
        x_coord (float): X-coordinate of the point where stress is calculated in m.
        y_coord (float): Y-coordinate of the point where stress is calculated in m.

    Returns:
        float: Max bending stress (sigma_max).
               Returns float('nan') if denominator is zero.
    """
    # Find furthest point from the centroid
    x_diff = x_coords - centroid[0]
    y_diff = y_coord - centroid[1]
    distances = np.sqrt(x_diff**2 + y_diff**2)
    x_coord_max = x_coords[np.argmax(distances)]
    y_coord_max = y_coord[np.argmax(distances)]

    numerator = (Mx * I_yy - My * I_xy) * y_coord_max + (My * I_xx - Mx * I_xy) * x_coord_max
    denominator = I_xx * I_yy - I_xy**2

    if denominator == 0:
        print("Warning: Denominator (I_xx*I_yy - I_xy^2) is zero. Bending stress calculation failed.")
        return float('nan')
    
    sigma_max = numerator / denominator
    return sigma_max


def calculate_torsional_shear_flow_and_stress(T: float, A_m: float, panel_thickness: np.ndarray) -> tuple:
    """
    Calculates torsional shear flow (q) and shear stress (tau) in a thin-walled closed section panel.
        q = T / (2 * A_m)
        tau = q / t_panel = T / (2 * A_m * panel_thickness) (based on 3.3)

    Parameters:
        T (float): Applied torque.
        A_m (float): Enclosed area by the median line of the thin wall.
        panel_thickness (np.ndarray): Thickness of the panel where stress is calculated.

    Returns:
        tuple: (q_torsion, tau_torsion)
            q_torsion (float): Torsional shear flow.
            tau_torsion (float): Torsional shear stress.
            Returns (float('nan'), float('nan')) if A_m or panel_thickness is zero.
    """
    if A_m == 0:
        print("Warning: Enclosed area A_m is zero. Torsion calculation failed.")
        return float('nan'), float('nan')
    if panel_thickness == 0:
        print("Warning: Panel thickness panel_thickness is zero. Torsional stress calculation failed.")
        q_torsion = T / (2 * A_m)
        return q_torsion, float('nan')
    
    min_thickness = np.min(panel_thickness)

    q_max = T / (2 * A_m)
    tau_max = q_max / (min_thickness)
    return q_max, tau_max






def run_material_selection_analysis(designvars: DesignParameters):
    """
    Run the material selection analysis for the wing structure based on the design variables.
    This function calculates the optimal skin and spar thicknesses based on the maximum bending and torsional stresses,
    and evaluates the feasibility of the design based on material properties.

    Parameters:
    - designvars: An instance of DesignParameters containing the design variables.

    Returns:
    - None: Prints the results of the analysis.
    """

    loading = WingLoadingDiagrams(designvars).run_analysis(PLOT=False)

    span_lst = np.linspace(0, designvars.wing.b_w/2, 1000)

    x_coords, y_coords = obtain_spar_coordinates(designvars, span_lst)

    # Obtain material properties
    sigma_max_mat = designvars.materials.material_sigma_yield
    tau_max_mat = designvars.materials.material_tau_yield

    # Define skin and spar thicknesses
    t_skin_lst = np.arange(0.5e-3, 10e-3, 0.5e-3)       # Skin thickness in meters
    t_spar_lst = np.arange(1e-3, 20e-3, 1e-3)           # Spar thickness in meters

    # Empty arrays
    feasible_sigma_max_lst = np.array([])
    feasible_tau_max_lst = np.array([])
    feasible_t_spar_lst = np.array([])
    feasible_t_skin_lst = np.array([])
    feasible_panel_areas_lst = np.array([])


    for t_skin in t_skin_lst:
        print("im here")
        for t_spar in t_spar_lst:
            print("im here")
            if t_skin > t_spar:
                print(f"Skipping: t_skin ({t_skin:.3f} m) > t_spar ({t_spar:.3f} m)")
                continue
            sigma_max_lst = np.array([])
            tau_max_lst = np.array([])
            panel_areas_lst = np.array([])
            for i in range(len(span_lst)):
                
                panel_lengths, enclosed_area = calculate_panel_lengths_and_enclosed_area(x_coords[i], y_coords[i])
                panel_areas = np.array([panel_lengths[0] * t_skin, panel_lengths[1] * t_spar, panel_lengths[2] * t_skin, panel_lengths[3] * t_spar])
                panel_angles = calculate_panel_angles(x_coords[i], y_coords[i])
                centroids = calculate_individual_centroids(x_coords[i], y_coords[i])
                centroid = calculate_centroid(centroids, panel_areas)
                I_xx, I_yy, I_xy = calculate_moment_of_inertia(centroids, t_spar, t_skin, panel_lengths, panel_angles, centroid)
                sigma_max = calculate_max_bending_stress(loading[i]["moment_x"], loading[i]["moment_z"], I_xx, I_yy, I_xy, x_coords[i], y_coords[i], centroid)
                q_max, tau_max = calculate_torsional_shear_flow_and_stress(loading[i]["torque_y"], enclosed_area, np.array([t_skin, t_spar, t_skin, t_spar]))

                sigma_max_lst = np.append(sigma_max_lst, sigma_max)
                tau_max_lst = np.append(tau_max_lst, tau_max)
                panel_areas_lst = np.append(panel_areas_lst, enclosed_area)

            max_sigma_max_index = np.argmax(sigma_max_lst)
            max_sigma_max = np.max(sigma_max_lst)
            max_tau_max = np.max(tau_max_lst)
            max_panel_area = panel_areas_lst[max_sigma_max_index]

            if max_sigma_max > sigma_max_mat or max_tau_max > tau_max_mat:
                print(f"Skipping: t_skin = {t_skin:.3f} m, t_spar = {t_spar:.3f} m, max_sigma_max = {max_sigma_max:.2f} Pa, max_tau_max = {max_tau_max:.2f} Pa")
                print(f"Material limits: sigma_max_mat = {sigma_max_mat:.2f} Pa, tau_max_mat = {tau_max_mat:.2f} Pa")
                continue
            else:
                feasible_sigma_max_lst = np.append(feasible_sigma_max_lst, max_sigma_max)
                feasible_tau_max_lst = np.append(feasible_tau_max_lst, max_tau_max)
                feasible_panel_areas_lst = np.append(feasible_panel_areas_lst, max_panel_area)
                feasible_t_spar_lst = np.append(feasible_t_spar_lst, t_spar)
                feasible_t_skin_lst = np.append(feasible_t_skin_lst, t_skin)
                print(f"Feasible design found: t_skin = {t_skin:.3f} m, t_spar = {t_spar:.3f} m")

    optimal_index = np.argmin(feasible_panel_areas_lst)
    opt_panel_area = feasible_panel_areas_lst[optimal_index]
    opt_t_spar = feasible_t_spar_lst[optimal_index]
    opt_t_skin = feasible_t_skin_lst[optimal_index]
    opt_sigma_max = feasible_sigma_max_lst[optimal_index]
    opt_tau_max = feasible_tau_max_lst[optimal_index]

    opt_panel_areas = np.array([])
    for i in range(len(span_lst)):
        panel_lengths, enclosed_area = calculate_panel_lengths_and_enclosed_area(x_coords[i], y_coords[i])
        panel_areas = np.array([panel_lengths[0] * opt_t_skin, panel_lengths[1] * opt_t_spar, panel_lengths[2] * opt_t_skin, panel_lengths[3] * opt_t_spar])
        opt_panel_areas = np.append(opt_panel_areas, np.sum(panel_areas))

    total_volume = integrate.cumulative_trapezoid(opt_panel_areas, span_lst, initial=0)     # in m^3
    total_mass = total_volume * designvars.materials.material_density                       # in kg   
    total_cost = total_mass * designvars.materials.material_price_kg                        # in EUR
    total_co2eq = total_mass * designvars.materials.material_co2_eq                         # in kg CO2eq

    print(f"Maximum Bending Stress (sigma_max): {opt_sigma_max:.2f} Pa")
    print(f"Maximum Torsional Shear Stress (tau_max): {opt_tau_max:.2f} Pa")
    print(f"Optimal Spar Thickness (t_spar): {opt_t_spar:.3f} m")
    print(f"Optimal Skin Thickness (t_skin): {opt_t_skin:.3f} m")

    print(f"Total Mass: {total_mass:.2f} kg")
    print(f"Total Cost: {total_cost:.2f} EUR")
    print(f"Total CO2eq: {total_co2eq:.2f} kg CO2eq")



if __name__ == "__main__":
    from main_struct import struct_main

    designvars = DesignParameters()
    designvars.load_from_yaml("design_config.yaml")

    struct_main(designvars)

    run_material_selection_analysis(designvars)