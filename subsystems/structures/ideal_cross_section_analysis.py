import math
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters


def calculate_panel_lengths_and_enclosed_area(boom_x_coords: list, boom_y_coords: list) -> tuple:
    """
    Calculates the length of each panel connecting sequential booms and the total enclosed area.
    Assumes booms are ordered sequentially around a single closed cell.

    Parameters:
        boom_x_coords (list of floats): X-coordinates of the booms.
        boom_y_coords (list of floats): Y-coordinates of the booms.

    Returns:
        tuple: (panel_lengths, enclosed_area_A_m)
            panel_lengths (list of float): Length of each panel.
            enclosed_area_A_m (float): Area enclosed by the booms (using Shoelace formula).
    """
    num_booms = len(boom_x_coords)
    if num_booms < 3:
        raise ValueError("At least 3 booms are required to form a closed cell.")
    if len(boom_y_coords) != num_booms:
        raise ValueError("boom_x_coords and boom_y_coords must have the same length.")

    panel_lengths = []
    enclosed_area_A_m = 0.0

    for i in range(num_booms):
        x1, y1 = boom_x_coords[i], boom_y_coords[i]
        x2, y2 = boom_x_coords[(i + 1) % num_booms], boom_y_coords[(i + 1) % num_booms]
        panel_lengths.append(math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
        enclosed_area_A_m += (x1 * y2 - x2 * y1)

    enclosed_area_A_m = 0.5 * abs(enclosed_area_A_m)

    return panel_lengths, enclosed_area_A_m


def calculate_centroid_idealized(boom_areas: list, boom_x_coords_abs: list, boom_y_coords_abs: list) -> tuple:
    """
    Calculates the centroid (x_c, y_c) of a group of booms.
    Formulas: x_c = (sum(B_i * x_i)) / sum(B_i), y_c = (sum(B_i * y_i)) / sum(B_i)

    Parameters:
        boom_areas (list of float): Areas of the booms (B_i).
        boom_x_coords_abs (list of float): Absolute X-coordinates of the booms.
        boom_y_coords_abs (list of float): Absolute Y-coordinates of the booms.

    Returns:
        tuple: (x_c, y_c) - coordinates of the centroid.
               Returns (None, None) if total boom area is zero.
    """
    if not (len(boom_areas) == len(boom_x_coords_abs) == len(boom_y_coords_abs)):
        raise ValueError("Input lists must have the same length.")
    if not boom_areas.any():
        raise ValueError("Input lists cannot be empty.")

    total_area = sum(boom_areas)
    if total_area == 0:
        return None, None # Avoid division by zero

    sum_B_x = sum(B * x for B, x in zip(boom_areas, boom_x_coords_abs))
    sum_B_y = sum(B * y for B, y in zip(boom_areas, boom_y_coords_abs))

    x_c = sum_B_x / total_area
    y_c = sum_B_y / total_area

    return x_c, y_c


def transform_coordinates_to_centroidal(boom_x_coords_abs: list, boom_y_coords_abs: list, x_c: float, y_c: float) -> tuple:
    """
    Transforms absolute boom coordinates to centroidal coordinates.

    Parameters:
        boom_x_coords_abs (list of float): Absolute X-coordinates of the booms.
        boom_y_coords_abs (list of float): Absolute Y-coordinates of the booms.
        x_c (float): X-coordinate of the centroid.
        y_c (float): Y-coordinate of the centroid.

    Returns:
        tuple: (boom_x_coords_cen, boom_y_coords_cen)
            boom_x_coords_cen (list of float): Centroidal X-coordinates.
            boom_y_coords_cen (list of float): Centroidal Y-coordinates.
    """
    boom_x_coords_cen = [x - x_c for x in boom_x_coords_abs]
    boom_y_coords_cen = [y - y_c for y in boom_y_coords_abs]
    return boom_x_coords_cen, boom_y_coords_cen


def calculate_moments_of_inertia_idealized(boom_areas: list, boom_x_coords: list, boom_y_coords: list) -> tuple:
    """
    Calculates moments of inertia (I_xx, I_yy, I_xy) for an idealized section with booms.
    Assumes boom_x_coords and boom_y_coords are with respect to the axes for which
    MOI are being calculated (typically centroidal axes).
    Formulas:
        I_xx = sum(B_i * y_i^2) (6.1)
        I_yy = sum(B_i * x_i^2) (6.2)
        I_xy = sum(B_i * x_i * y_i) (6.3)

    Parameters:
        boom_areas (list of float): Areas of the booms (B_i).
        boom_x_coords (list of float): X-coordinates of booms (w.r.t. calculation axes).
        boom_y_coords (list of float): Y-coordinates of booms (w.r.t. calculation axes).

    Returns:
        tuple: (I_xx, I_yy, I_xy)
    """
    if not (len(boom_areas) == len(boom_x_coords) == len(boom_y_coords)):
        raise ValueError("Input lists must have the same length.")

    I_xx = sum(B * y**2 for B, y in zip(boom_areas, boom_y_coords))
    I_yy = sum(B * x**2 for B, x in zip(boom_areas, boom_x_coords))
    I_xy = sum(B * x * y for B, x, y in zip(boom_areas, boom_x_coords, boom_y_coords))

    return I_xx, I_yy, I_xy


def calculate_skin_contribution_to_booms(t_skin: float, s_k_panel_length: float, sigma_1: float, sigma_2: float) -> tuple:
    """
    Calculates the effective area contribution from a skin panel to its two adjacent booms.
    Based on linear stress distribution in the skin panel.
    Formulas (6.6a, 6.6b):
        B1_contrib = (t_skin * s_k / 6) * (2 + sigma_2 / sigma_1)
        B2_contrib = (t_skin * s_k / 6) * (2 + sigma_1 / sigma_2)

    Parameters:
        t_skin (float): Thickness of the skin panel.
        s_k_panel_length (float): Length of the skin panel between the two booms.
        sigma_1 (float): Stress at boom 1 (connected to one end of the panel).
        sigma_2 (float): Stress at boom 2 (connected to the other end of the panel).

    Returns:
        tuple: (B1_contribution, B2_contribution)
               Contribution to boom 1 and boom 2 respectively.
    """
    if sigma_1 == 0 and sigma_2 == 0:
        print("Warning: Both sigma_1 and sigma_2 are zero. Skin contribution might need re-evaluation.")
        return 0.0, 0.0
        
    # Base term
    base_contrib = t_skin * s_k_panel_length / 6.0
    
    B1_contrib = 0.0
    if sigma_1 != 0:
        B1_contrib = base_contrib * (2 + sigma_2 / sigma_1)
    elif sigma_1 == 0 and sigma_2 != 0: 
        B1_contrib = t_skin * s_k_panel_length / 6.0 # Contribution to boom 1 (where sigma=0)

    B2_contrib = 0.0
    if sigma_2 != 0:
        B2_contrib = base_contrib * (2 + sigma_1 / sigma_2)
    elif sigma_2 == 0 and sigma_1 != 0: 
        B2_contrib = t_skin * s_k_panel_length / 6.0 # Contribution to boom 2 (where sigma=0)
        if sigma_1 != 0 and B1_contrib == 0.0: 
             B1_contrib = base_contrib * (2 + sigma_2 / sigma_1) 
             B1_contrib = base_contrib * 2.0

    if sigma_1 != 0 and sigma_2 == 0:
        B1_contrib = (t_skin * s_k_panel_length / 3.0)
        B2_contrib = (t_skin * s_k_panel_length / 6.0)
    elif sigma_2 != 0 and sigma_1 == 0:
        B1_contrib = (t_skin * s_k_panel_length / 6.0)
        B2_contrib = (t_skin * s_k_panel_length / 3.0)
    elif sigma_1 != 0 and sigma_2 != 0 : # Both non-zero, use original formulas
        B1_contrib = (t_skin * s_k_panel_length / 6.0) * (2 + sigma_2 / sigma_1)
        B2_contrib = (t_skin * s_k_panel_length / 6.0) * (2 + sigma_1 / sigma_2)
    else: # Both zero
        B1_contrib = t_skin * s_k_panel_length / 2.0
        B2_contrib = t_skin * s_k_panel_length / 2.0
        print("Warning: Both sigma_1 and sigma_2 are zero. Defaulting to equal split ts_k/2 for skin contribution.")

    return B1_contrib, B2_contrib


def calculate_bending_stress(Mx: float, My: float, I_xx: float, I_yy: float, I_xy: float, x_coord: float, y_coord: float) -> float:
    """
    Calculates bending stress (sigma_z) at a point (x, y) in a cross-section.
    Formula (2.4):
    sigma_z = ((Mx*I_yy - My*I_xy)*y + (My*I_xx - Mx*I_xy)*x) / (I_xx*I_yy - I_xy^2)

    Parameters:
        Mx (float): Bending moment about the x-axis.
        My (float): Bending moment about the y-axis.
        I_xx (float): Moment of inertia about the x-axis.
        I_yy (float): Moment of inertia about the y-axis.
        I_xy (float): Product of inertia.
        x_coord (float): X-coordinate of the point where stress is calculated.
        y_coord (float): Y-coordinate of the point where stress is calculated.

    Returns:
        float: Bending stress (sigma_z).
               Returns float('nan') if denominator is zero.
    """
    numerator = (Mx * I_yy - My * I_xy) * y_coord + (My * I_xx - Mx * I_xy) * x_coord
    denominator = I_xx * I_yy - I_xy**2

    if denominator == 0:
        print("Warning: Denominator (I_xx*I_yy - I_xy^2) is zero. Bending stress calculation failed.")
        return float('nan')
    
    sigma_z = numerator / denominator
    return sigma_z


def calculate_torsional_shear_flow_and_stress(T: float, A_m: float, t_panel: float) -> tuple:
    """
    Calculates torsional shear flow (q) and shear stress (tau) in a thin-walled closed section panel.
        q = T / (2 * A_m)
        tau = q / t_panel = T / (2 * A_m * t_panel) (based on 3.3)

    Parameters:
        T (float): Applied torque.
        A_m (float): Enclosed area by the median line of the thin wall.
        t_panel (float): Thickness of the panel where stress is calculated.

    Returns:
        tuple: (q_torsion, tau_torsion)
            q_torsion (float): Torsional shear flow.
            tau_torsion (float): Torsional shear stress.
            Returns (float('nan'), float('nan')) if A_m or t_panel is zero.
    """
    if A_m == 0:
        print("Warning: Enclosed area A_m is zero. Torsion calculation failed.")
        return float('nan'), float('nan')
    if t_panel == 0:
        print("Warning: Panel thickness t_panel is zero. Torsional stress calculation failed.")
        q_torsion = T / (2 * A_m)
        return q_torsion, float('nan')


    q_torsion = T / (2 * A_m)
    tau_torsion = q_torsion / t_panel
    return q_torsion, tau_torsion


def calculate_rate_of_twist(T: float, A_m: float, G: float, panel_lengths: list, panel_thicknesses: list) -> float:
    """
    Calculates the rate of twist (d_theta_dz) for a single-cell thin-walled closed section.
    d_theta_dz = (T / (4 * A_m^2 * G)) * sum(s_i / t_i)
    Assumes G (Shear Modulus) is constant for all panels.

    Parameters:
        T (float): Applied torque.
        A_m (float): Enclosed area by the median line.
        G (float): Shear modulus of the material.
        panel_lengths (list of float): Lengths of the panels (s_i).
        panel_thicknesses (list of float): Thicknesses of the panels (t_i).

    Returns:
        float: Rate of twist (d_theta_dz).
               Returns float('nan') if A_m or G is zero or if issues with panel data.
    """
    if A_m == 0 or G == 0:
        print("Warning: A_m or G is zero. Rate of twist calculation failed.")
        return float('nan')
    if not (len(panel_lengths) == len(panel_thicknesses)):
        raise ValueError("Panel lengths and thicknesses lists must have the same length.")
    if not panel_lengths:
        raise ValueError("Panel lists cannot be empty.")

    sum_s_over_t = 0
    for s, t in zip(panel_lengths, panel_thicknesses):
        if t == 0:
            print("Warning: Panel thickness is zero. Rate of twist calculation will be problematic.")
            return float('nan')
        sum_s_over_t += s / t
    
    d_theta_dz = (T / (4 * A_m**2 * G)) * sum_s_over_t

    return d_theta_dz


def calculate_basic_shear_flows(Vx: float, Vy: float, I_xx: float, I_yy: float, I_xy: float, boom_areas: list, boom_x_coords: list, boom_y_coords: list) -> list:
    """
    Calculates the basic shear flows (q_b) in the panels of an idealized closed section
    (booms connected by shear panels), assuming the section is 'cut' before the first boom.
    The booms must be ordered sequentially around the cell.
    q_b in panel after boom k = -Ky * sum_{r=0 to k}(B_r*y_r) - Kx * sum_{r=0 to k}(B_r*x_r)
    where:
        Ky = (Vx*I_yy - Vy*I_xy) / (I_xx*I_yy - I_xy^2)
        Kx = (Vy*I_xx - Vx*I_xy) / (I_xx*I_yy - I_xy^2)
    Coordinates (boom_x_coords, boom_y_coords) are w.r.t. centroidal axes,
    consistent with I_xx, I_yy, I_xy.

    Parameters:
        Vx (float): Shear force in x-direction.
        Vy (float): Shear force in y-direction.
        I_xx, I_yy, I_xy (float): Moments and product of inertia.
        boom_areas (list of float): Areas of booms [B_0, ..., B_{N-1}].
        boom_x_coords (list of float): Centroidal X-coords of booms [x_0, ..., x_{N-1}].
        boom_y_coords (list of float): Centroidal Y-coords of booms [y_0, ..., y_{N-1}].

    Returns:
        list of float: Basic shear flows [q_b0, q_b1, ..., q_b(N-1)] in panels.
                       q_bi is the flow in the panel connecting boom i to boom (i+1)%N.
                       Returns empty list or list of NaNs if denominator is zero.
    """
    num_booms = len(boom_areas)
    if not (num_booms == len(boom_x_coords) == len(boom_y_coords)):
        raise ValueError("Boom data lists must have the same length.")
    if num_booms == 0:
        return []

    denom_I = I_xx * I_yy - I_xy**2
    if denom_I == 0:
        print("Warning: Denominator (I_xx*I_yy - I_xy^2) is zero. Basic shear flow calculation failed.")
        return [float('nan')] * num_booms
    
    Ky_coeff = (Vx * I_yy - Vy * I_xy) / denom_I
    Kx_coeff = (Vy * I_xx - Vx * I_xy) / denom_I
    
    q_b_panels = [0.0] * num_booms
    current_sum_Br_yr = 0.0
    current_sum_Br_xr = 0.0

    for i in range(num_booms):
        current_sum_Br_yr += boom_areas[i] * boom_y_coords[i]
        current_sum_Br_xr += boom_areas[i] * boom_x_coords[i]
        q_b_panels[i] = -Ky_coeff * current_sum_Br_yr - Kx_coeff * current_sum_Br_xr
        
    return q_b_panels


def calculate_q_s0(q_b_panels: list, panel_lengths: list, panel_thicknesses: list, G_values=None) -> float:
    """
    Calculates the corrective shear flow q_s0 for a single closed cell.
    Formula (4.7 based): q_s0 = - (oint (q_b/t) ds) / (oint (1/t) ds) assuming G is constant.
    If G varies per panel (G_values is a list), then:
    q_s0 = - (sum(q_b_i * s_i / (G_i * t_i))) / (sum(s_i / (G_i * t_i)))

    Parameters:
        q_b_panels (list of float): Basic shear flows in each panel.
        panel_lengths (list of float): Lengths of each panel (s_i).
        panel_thicknesses (list of float): Thicknesses of each panel (t_i).
        G_values (list of float or float, optional): Shear modulus for each panel.
            If None or a single float, G is assumed constant and cancels out.
            If a list, must match length of panels.

    Returns:
        float: Corrective shear flow q_s0.
               Returns float('nan') if denominator sum is zero.
    """
    num_panels = len(q_b_panels)
    if not (num_panels == len(panel_lengths) == len(panel_thicknesses)):
        raise ValueError("Panel data lists must have the same length as q_b_panels.")
    if G_values is not None and isinstance(G_values, list) and len(G_values) != num_panels:
        raise ValueError("G_values list must match the number of panels.")

    numerator_sum = 0.0
    denominator_sum = 0.0

    for i in range(num_panels):
        if panel_thicknesses[i] == 0:
            print(f"Warning: Panel {i} thickness is zero. q_s0 calculation may fail.")
            return float('nan')

        term_G_t = panel_thicknesses[i]
        if G_values is not None:
            G_i = G_values[i] if isinstance(G_values, list) else G_values
            if G_i == 0:
                print(f"Warning: Panel {i} G value is zero. q_s0 calculation may fail.")
                return float('nan')
            term_G_t *= G_i
        
        if term_G_t == 0: # Should be caught by individual t or G checks already
            print(f"Warning: G*t product is zero for panel {i}. q_s0 calculation failed.")
            return float('nan')

        numerator_sum += (q_b_panels[i] * panel_lengths[i]) / term_G_t
        denominator_sum += panel_lengths[i] / term_G_t
            
    if denominator_sum == 0:
        print("Warning: Denominator sum for q_s0 is zero. Calculation failed.")
        return float('nan')

    q_s0 = -numerator_sum / denominator_sum
    return q_s0


def calculate_final_shear_flows(q_b_panels: list, q_s0: float) -> list:
    """
    Calculates the final shear flows (q_s) in the panels by adding q_s0 to q_b.
    Formula: q_s = q_b + q_s0

    Parameters:
        q_b_panels (list of float): Basic shear flows in each panel.
        q_s0 (float): Corrective shear flow.

    Returns:
        list of float: Final shear flows (q_s) in each panel.
    """
    q_s_panels = [qb + q_s0 for qb in q_b_panels]

    return q_s_panels


def convert_arrays_to_coordinates(spar_points: np.ndarray, stringer_points: np.ndarray) -> dict:
    """
    Convert spar and stringer points arrays to a dictionary of coordinates.

    Parameters:
        spar_points (np.ndarray): Array of spar points.
        stringer_points (np.ndarray): Array of stringer points.

    Returns:
        dict: Dictionary containing spar and stringer coordinates.
    """
    spar_x_coords = np.array([])
    spar_y_coords = np.array([])

    if spar_points:
        spar_combined_array = np.vstack(spar_points)
        spar_x_coords = spar_combined_array[:, 0]
        spar_y_coords = spar_combined_array[:, 1]

    stringer_x_coords = np.array([])
    stringer_y_coords = np.array([])

    if stringer_points:
        stringer_combined_array = np.array(stringer_points)
        stringer_x_coords = stringer_combined_array[:, 0]
        stringer_y_coords = stringer_combined_array[:, 1]

    return {
        'spar_x_coords': spar_x_coords,
        'spar_y_coords': spar_y_coords,
        'stringer_x_coords': stringer_x_coords,
        'stringer_y_coords': stringer_y_coords
    }


def run_cross_section_analysis(params: DesignParameters, spar_points: np.ndarray, stringer_points: np.ndarray,
                               Mx_applied: float, My_applied: float, T_applied: float, Vx_applied: float, 
                               Vy_applied: float, skin_thickness: float) -> dict:
    """
    Run the cross-section analysis, based on an idealised wing box structure. 
    """
    spar_boom_x = convert_arrays_to_coordinates(spar_points, stringer_points)['spar_x_coords']
    stringer_boom_x = convert_arrays_to_coordinates(spar_points, stringer_points)['stringer_x_coords']
    print(f"spar_boom_x: {spar_boom_x}")
    print(f"stringer_boom_x: {stringer_boom_x}")
    boom_x = np.concatenate((spar_boom_x, stringer_boom_x))
    boom_x_abs = abs(boom_x)

    spar_boom_y = convert_arrays_to_coordinates(spar_points, stringer_points)['spar_y_coords']
    stringer_boom_y = convert_arrays_to_coordinates(spar_points, stringer_points)['stringer_y_coords']
    boom_y = np.concatenate((spar_boom_y, stringer_boom_y))
    boom_y_abs = abs(boom_y)

    spar_boom_areas = np.zeros(params.wing.wingsection.num_spars)
    for i, spar in enumerate(params.wing.wingsection.spars.values()):
        spar_boom_areas[i] = spar["t_flange_1_mm"] * spar["flange_width_mm"]
        spar_boom_areas[i] = spar["t_flange_2_mm"] * spar["flange_width_mm"]

    stringer_boom_areas = np.zeros(params.wing.wingsection.num_stringers)
    for i, stringer in enumerate(params.wing.wingsection.stringers.values()):
        stringer_boom_areas[i] = stringer["crosssectionalarea_mm2"]

    boom_areas_initial = np.concatenate((spar_boom_areas, stringer_boom_areas))
    final_boom_areas = boom_areas_initial # Assuming final areas are equal to initial areas

    # 1. Calculate Centroid
    xc, yc = calculate_centroid_idealized(final_boom_areas, boom_x_abs, boom_y_abs)
    print(f"Centroid: ({xc}, {yc})")	

    # 2. Transform coordinates to centroidal
    boom_x_cen, boom_y_cen = transform_coordinates_to_centroidal(boom_x_abs, boom_y_abs, xc, yc)
    print(f"Centroidal Coordinates: ({boom_x_cen}, {boom_y_cen})")

    # 3. Calculate Moments of Inertia
    Ixx, Iyy, Ixy = calculate_moments_of_inertia_idealized(final_boom_areas, boom_x_cen, boom_y_cen)
    print(f"Moments of Inertia: Ixx={Ixx}, Iyy={Iyy}, Ixy={Ixy}")

    # 4. Bending Stress Calculation
    # Stress at boom 2 (top-right: x=1, y=1 centroidal)
    sigma_z_booms = np.zeros(len(boom_x_cen))

    for i, point in enumerate(zip(boom_x_cen, boom_y_cen)):
        x_point, y_point = point
        sigma_z_booms[i] = calculate_bending_stress(Mx_applied, My_applied, Ixx, Iyy, Ixy, x_point, y_point)
        print(f"Bending Stress at Boom {i+1}: {sigma_z_booms[i]}")


    # 5. Torsion Analysis
    G_material = params.shear_modulus

    panel_s, A_m_calc = calculate_panel_lengths_and_enclosed_area(boom_x_cen, boom_y_cen)
    q_tor, tau_tor = calculate_torsional_shear_flow_and_stress(T_applied, A_m_calc, skin_thickness)
    print(f"Torsional Shear Flow: {q_tor}, Torsional Shear Stress: {tau_tor}")

    skin_thicknesses_list = [skin_thickness] * len(panel_s)
    dtheta_dz = calculate_rate_of_twist(T_applied, A_m_calc, G_material, panel_s, skin_thicknesses_list) # Rate of Twist
    print(f"Rate of Twist: {dtheta_dz}")


    # 6. Shear Flow Analysis due to Shear Forces

    qb_panels = calculate_basic_shear_flows(Vx_applied, Vy_applied, Ixx, Iyy, Ixy, final_boom_areas, boom_x_cen, boom_y_cen)
    qs0 = calculate_q_s0(qb_panels, panel_s, skin_thicknesses_list) # G is assumed constant
    qs_panels = calculate_final_shear_flows(qb_panels, qs0)
    print(f"Basic Shear Flows: {qb_panels}")
    print(f"Corrective Shear Flow: {qs0}")
    print(f"Final Shear Flows: {qs_panels}")
