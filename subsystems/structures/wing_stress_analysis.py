import numpy as np
import math as m
import os
import sys

from casadi import interp1d

import openvsp as vsp
import pandas as pd
from scipy.interpolate import interp1d
try:
    from subsystems.structures.wing_structure_generation import *
    from subsystems.structures.vspfunctions import *
    from design_variables import DesignParameters
    from subsystems.structures.wing_structure_generation import cross_sectional_structure_along_span
    from subsystems.structures.ideal_cross_section_analysis import run_cross_section_analysis
    from subsystems.structures.loading_diagrams import WingLoadingDiagrams
    from subsystems.structures.utils_struct import *
    from subsystems.structures.buckling2 import  *
    from class2.master_design_loop import *
except:
    from wing_structure_generation import *
    from vspfunctions import *
    from design_variables import DesignParameters
    from wing_structure_generation import cross_sectional_structure_along_span
    from ideal_cross_section_analysis import run_cross_section_analysis
    from loading_diagrams import WingLoadingDiagrams
    from utils_struct import *
    from buckling2 import *



from scipy.integrate import cumulative_simpson


def perform_cross_section_analysis(designvars: DesignParameters, loading: dict, spanwise_position: float = 0.0):
    """
    Performs cross-sectional analysis of the wing structure at a given spanwise position.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - spanwise_position: Position along the span where the cross-section is generated as a fraction of the total span (0.0 to 1.0).
    """
    
    spar_points_array, stringer_array, _, _, _, _ = cross_sectional_structure_along_span(designvars, spanwise_position, plot=False)
    results = run_cross_section_analysis(designvars, spar_points_array, stringer_array, loading["moment_x"], loading["moment_z"],
                                         loading["torsion_y"], loading["shear_x"], loading["shear_z"], designvars.wing.wingsection.wingskin['thicness'], plot=False)
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
    deflection_der = -1 / E *   cumulative_simpson(M/I, dx=half_span / (np.shape(M)[0] - 1), initial=0) * 1e3
    deflection = cumulative_simpson(deflection_der, dx=half_span / (np.shape(M)[0] - 1), initial=0)
    return deflection


def calculate_angle_of_twist(T: np.ndarray, A_m: np.ndarray, G: float, skin_thickness: float, web_thickness: float, wingskin_length: np.ndarray, web_length:np.ndarray, half_span: float) -> np.ndarray:
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
    twist_angle = 1 / (4*G) * cumulative_simpson(np.array([((T[i] ) / (A_m[i])) * (wingskin_length[i]/skin_thickness + web_length[i]/web_thickness) for i in range(len(T))]), dx=half_span / (np.shape(T)[0] - 1), initial=0)
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

def run_structures(designvars):
    vsp.ClearVSPModel()

    #### Add fuselage and change fuselage shape to make room for payload. This is done by changing the cross-sections of the fuselage.
    create_fuselage(designvars)

    ### Add wing
    create_wing(designvars)

    ### Add v_tail
    create_V_tail(designvars)

    ### Add engines
    create_engines(designvars)

    # Add fuel tank
    calculate_fuel_capacity(designvars)

    prev_cwd = os.getcwd()
    os.chdir(os.getcwd() + "/data")
    vsp.WriteVSPFile("aircraft_model2.vsp3")
    os.chdir(prev_cwd)

    ### Calculate specifications
    calculate_cg(designvars)
    calculate_wet_areas(designvars)

    ### Set up structure
    # wing_structure_generation(designvars)

    # Freeze geometry:

    vsp.UpdateGeom(designvars.wing.wingid)
    designvars.wing.b_w = vsp.GetParmVal(designvars.wing.wingid, "TotalSpan", "WingGeom")
    vsp.UpdateGeom(designvars.wing.wingid)
    vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom.csv")
    vsp.SetSetFlag(designvars.wing.wingid, 8, True)
    vsp.ComputeDegenGeom(8, vsp.DEGEN_GEOM_CSV_TYPE)
    data = pd.read_csv("data/DegenGeom.csv", header=None, skiprows=10, nrows=2211)
    datanp = data.to_numpy()
    designvars.structurecoords = np.round(datanp, decimals=6)
    weight_distribution(designvars)

    spanwise_position_lst = np.linspace(0.0, 1.0, len(designvars.wing.CL_distribution))


    wing_loading = WingLoadingDiagrams(designvars)

    wing_loading = wing_loading.run_analysis(PLOT=False)

    cross_sectional_results = []
    for i, spanwise_position in enumerate(spanwise_position_lst):
        results = perform_cross_section_analysis(designvars, wing_loading[i], spanwise_position)
        cross_sectional_results.append(results)
        spar_min = np.min(
            [designvars.wing.wingsection.spars[spar]['x_pos_frac'] for spar in designvars.wing.wingsection.spars.keys()])
        spar_max = np.max(
            [designvars.wing.wingsection.spars[spar]['x_pos_frac'] for spar in designvars.wing.wingsection.spars.keys()])
        filtered_stringers_top = []
        filtered_stringers_bottom = []
        for stringer_i, stringer in enumerate(designvars.wing.wingsection.stringers.keys()):
            if designvars.wing.wingsection.stringers[stringer]['pos_along_airfoil_side'] > spar_min and designvars.wing.wingsection.stringers[stringer]['pos_along_airfoil_side'] < spar_max:
                if designvars.wing.wingsection.stringers[stringer]['top_or_bottom_side'] == 'top':
                    filtered_stringers_top.append(stringer_i)
                else:
                    filtered_stringers_bottom.append(stringer_i)
        top_stringer_indices = np.array(filtered_stringers_top)[np.flip(np.array([designvars.wing.wingsection.stringers[f'Stringer{1+stringer_i}']["pos_along_airfoil_side"] for stringer_i in filtered_stringers_top]).argsort())]
        bottom_stringer_indices = np.array(filtered_stringers_bottom)[np.array([designvars.wing.wingsection.stringers[f'Stringer{1+stringer_i}']["pos_along_airfoil_side"] for stringer_i in filtered_stringers_bottom]).argsort()]

        if spanwise_position > np.min([designvars.wing.wingribs.ribs[rib]['y_pos_frac'] for rib in designvars.wing.wingribs.ribs.keys()]):
            closest_rib_under = np.max(
                [designvars.wing.wingribs.ribs[rib]['y_pos_frac'] for rib in designvars.wing.wingribs.ribs.keys() if
                 designvars.wing.wingribs.ribs[rib]['y_pos_frac'] <= spanwise_position])
        else:
            closest_rib_under = 0
        if spanwise_position < np.max([designvars.wing.wingribs.ribs[rib]['y_pos_frac'] for rib in designvars.wing.wingribs.ribs.keys()]):
            closest_rib_over = np.min(
                [designvars.wing.wingribs.ribs[rib]['y_pos_frac'] for rib in designvars.wing.wingribs.ribs.keys() if
                 designvars.wing.wingribs.ribs[rib]['y_pos_frac'] >= spanwise_position])
        else:
            closest_rib_over = 1.0
        length_between_ribs = (closest_rib_over - closest_rib_under) * designvars.wing.b_w * np.cos(
            designvars.wing.Gamma_w)
        nameslist = (['Spar1'] + [f'Stringer{index+1}' for index in bottom_stringer_indices.tolist()] + ['Spar2', 'Spar2'] + [f'Stringer{index+1}' for index in top_stringer_indices.tolist()] + ['Spar1'])
        nameslist.reverse()
        for boom_stress, boom_number, boom_x, boom_y, boom_area in zip(results['bending_stresses'][:-1], nameslist, results['boom_x_coords_sorted'][:-1], results['boom_y_coords_sorted'][:-1], results['boom_areas_sorted'][:-1]):
            if spanwise_position > 0.21:
                if np.abs(boom_stress) > designvars.materials.material_sigma_yield:
                    print(f"Warning: Boom {boom_number} at spanwise position {spanwise_position:.2f} exceeds yield strength with {100*(boom_stress-designvars.materials.material_sigma_yield)/boom_stress} % ")
                    if (np.abs(boom_stress)-designvars.materials.material_sigma_yield)/boom_stress > 0.3:
                        if boom_number == 'Spar1' or boom_number == 'Spar2':
                            designvars.structure_results.should_increase_sparcap_thickness_by_30_percent_in_nextround = True
                        else:
                            if boom_number not in designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround:
                                designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround.append(boom_number)
                    else:
                        if boom_number == 'Spar1' or boom_number == 'Spar2':
                            designvars.structure_results.should_increase_sparcap_thickness_by_10_percent_in_nextround = True
                        else:
                            if boom_number not in designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround:
                                designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround.append(boom_number)
                if not (boom_number == 'Spar1' or boom_number == 'Spar2'):
                    crit_stringer_buckling = calculate_critical_stringer_buckling_stress(designvars.materials.material_E*1e9, designvars.wing.wingsection.stringers[boom_number]['area_moment_of_inertia_m4'], designvars.wing.wingsection.stringers[boom_number]["crosssectionalarea_mm2"]/1000000, length_between_ribs, designvars.wing.wingsection.stringers[boom_number]['K'] )
                    if np.abs(boom_stress) > crit_stringer_buckling:
                        print(f"Warning: Stringer {boom_number} at spanwise position {spanwise_position:.2f} exceeds critical buckling stress with {100*(boom_stress-crit_stringer_buckling)/boom_stress} % ")
                        if (np.abs(boom_stress)-crit_stringer_buckling)/boom_stress > 0.3:
                            if boom_number not in designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround:
                                designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround.append(boom_number)
                        else:
                            if boom_number == 'Spar1' or boom_number == 'Spar2':
                                designvars.structure_results.should_increase_sparcap_thickness_by_10_percent_in_nextround = True
                            else:
                                if boom_number not in designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround:
                                    designvars.structure_results.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround.append(
                                        boom_number)

        # TODO: Check shearstress vs max shearstress



    x_bending = calculate_bending_distribution(
        np.array([wing_loading[i]['moment_x'] for i in range(len(spanwise_position_lst))]),
        np.array([cross_sectional_results[i]["Ixx"] for i in range(len(spanwise_position_lst))]), ##mm4
        designvars.materials.material_E,
        designvars.wing.b_w / 2 * np.cos(designvars.wing.Gamma_w))
    y_twist = calculate_angle_of_twist(
        np.array([wing_loading[i]["torsion_y"] for i in range(len(spanwise_position_lst))]),
        np.array([cross_sectional_results[i]["A_m"] for i in range(len(spanwise_position_lst))]),
        designvars.materials.material_G * 1e9, designvars.wing.wingsection.wingskin['thicness'] / 1000,
        designvars.wing.wingsection.spars["Spar1"]["t_web_mm"] / 1000,
        np.array([cross_sectional_results[i]["wingskin_length"] for i in range(len(spanwise_position_lst))]),
        np.array([cross_sectional_results[i]['web_length'] for i in range(len(spanwise_position_lst))]),
        designvars.wing.b_w / 2 * np.cos(designvars.wing.Gamma_w))
    z_bending = calculate_bending_distribution(
        np.array([wing_loading[i]["moment_z"] for i in range(len(spanwise_position_lst))]),
        np.array([cross_sectional_results[i]["Iyy"] for i in range(len(spanwise_position_lst))]), #mm4
        designvars.materials.material_E,
        designvars.wing.b_w / 2 * np.cos(designvars.wing.Gamma_w))
    x_bending_distribution = x_bending
    y_twist_distribution = y_twist
    z_bending_distribution = z_bending

    # Plotting the bending distributions
    plot_bending_distribution(spanwise_position_lst, x_bending_distribution, axis='x')
    plot_bending_distribution(spanwise_position_lst, z_bending_distribution, axis='z')
    designvars.structure_results.x_bending_distribution = x_bending_distribution
    designvars.structure_results.z_bending_distribution = z_bending_distribution
    designvars.structure_results.twist_distribution = y_twist_distribution
    designvars.structure_results.max_displacement_x = np.max(np.abs(designvars.structure_results.x_bending_distribution))
    designvars.structure_results.max_displacement_z = np.max(np.abs(designvars.structure_results.z_bending_distribution))
    designvars.structure_results.max_twist_angle = np.max(np.abs(designvars.structure_results.twist_distribution))

    if designvars.structure_results.max_displacement_x > designvars.wing.max_allowed_x_displacement:
        print(f"Warning: Maximum x displacement {designvars.structure_results.max_displacement_x:.4f} m exceeds allowed limit {designvars.wing.max_allowed_x_displacement:.4f} m.")
        designvars.structure_results.should_increase_sparweb_thickness_by_10_percent_in_nextround = True
    if designvars.structure_results.max_displacement_z > designvars.wing.max_allowed_z_displacement:
        print(f"Warning: Maximum z displacement {designvars.structure_results.max_displacement_z:.4f} m exceeds allowed limit {designvars.wing.max_allowed_z_displacement:.4f} m.")
        designvars.structure_results.should_increase_sparcap_thickness_by_10_percent_in_nextround = True
    if designvars.structure_results.max_twist_angle > designvars.wing.max_allowed_twist_angle:
        print(f"Warning: Maximum twist angle {designvars.structure_results.max_twist_angle:.4f} rad exceeds allowed limit {designvars.wing.max_allowed_twist_angle:.4f} rad.")
        designvars.structure_results.should_increase_wingskin_thickness_by_10_percent_in_nextround = True

if __name__ == "__main__":
    designvars = master_design_process('design_config.yaml')[0]

    #### TODO: REPLACE THIS FOR AERODYNAMICS CALCULATED LOADS
    y_array = np.array([0.498246, 0.536841, 0.580293, 0.630283, 0.688325, 0.754001, 0.822189, 0.902446,
        1.010588, 1.105177, 1.192055, 1.276326, 1.36037,  1.445542, 1.532754, 1.622674,
        1.715753, 1.812118, 1.911301, 2.011758, 2.11037,  2.202617, 2.284359, 2.354186,
        2.413809, 2.466547, 0.498246, 0.536841, 0.580293, 0.630283, 0.688325, 0.754001,
        0.822189, 0.902446, 1.010588, 1.105177, 1.192055, 1.276326, 1.36037,  1.445542,
        1.532754, 1.622674, 1.715753, 1.812118, 1.911301, 2.011758, 2.11037,  2.202617,
        2.284359, 2.354186, 2.413809, 2.466547, 0.498246, 0.536841, 0.580293, 0.630283,
        0.688325, 0.754001, 0.822189, 0.902446, 1.010588, 1.105177, 1.192055, 1.276326,
        1.36037,  1.445542, 1.532754, 1.622674, 1.715753, 1.812118, 1.911301, 2.011758,
        2.11037,  2.202617, 2.284359, 2.354186, 2.413809, 2.466547, 0.498246, 0.536841,
        0.580293, 0.630283, 0.688325, 0.754001, 0.822189, 0.902446, 1.010588, 1.105177,
        1.192055, 1.276326, 1.36037,  1.445542, 1.532754, 1.622674, 1.715753, 1.812118,
        1.911301, 2.011758, 2.11037,  2.202617, 2.284359, 2.354186, 2.413809, 2.466547,
        0.498246, 0.536841, 0.580293, 0.630283, 0.688325, 0.754001, 0.822189, 0.902446,
        1.010588, 1.105177, 1.192055, 1.276326, 1.36037,  1.445542, 1.532754, 1.622674,
        1.715753, 1.812118, 1.911301, 2.011758, 2.11037,  2.202617, 2.284359, 2.354186,
        2.413809, 2.466547, 0.498246, 0.536841, 0.580293, 0.630283, 0.688325, 0.754001,
        0.822189, 0.902446, 1.010588, 1.105177, 1.192055, 1.276326, 1.36037,  1.445542,
        1.532754, 1.622674, 1.715753, 1.812118, 1.911301, 2.011758, 2.11037,  2.202617,
        2.284359, 2.354186, 2.413809, 2.466547, 0.498246, 0.536841, 0.580293, 0.630283,
        0.688325, 0.754001, 0.822189, 0.902446, 1.010588, 1.105177, 1.192055, 1.276326,
        1.36037,  1.445542, 1.532754, 1.622674, 1.715753, 1.812118, 1.911301, 2.011758,
        2.11037,  2.202617, 2.284359, 2.354186, 2.413809, 2.466547, 0.498246, 0.536841,
        0.580293, 0.630283, 0.688325, 0.754001, 0.822189, 0.902446, 1.010588, 1.105177,
        1.192055, 1.276326, 1.36037,  1.445542, 1.532754, 1.622674, 1.715753, 1.812118,
        1.911301, 2.011758, 2.11037,  2.202617, 2.284359, 2.354186, 2.413809, 2.466547,
        0.498246, 0.536841, 0.580293, 0.630283, 0.688325, 0.754001, 0.822189, 0.902446,
        1.010588, 1.105177, 1.192055, 1.276326, 1.36037,  1.445542, 1.532754, 1.622674,
        1.715753, 1.812118, 1.911301, 2.011758, 2.11037,  2.202617, 2.284359, 2.354186,
        2.413809, 2.466547])
    designvars.wing.CL_distribution = np.nan_to_num(interp1d(y_array, np.array([1.12940e-01, 1.16831e-01, 1.21249e-01, 1.26167e-01, 1.31768e-01,
 1.37913e-01, 1.43917e-01, 1.51167e-01, 1.55875e-01, 1.56766e-01,
 1.60266e-01, 1.63487e-01, 1.66429e-01, 1.69086e-01, 1.71464e-01,
 1.73485e-01, 1.75071e-01, 1.75914e-01, 1.75897e-01, 1.74469e-01,
 1.71270e-01, 1.66065e-01, 1.58047e-01, 1.46596e-01, 1.30589e-01,
 1.05043e-01, 2.33380e-01, 2.41202e-01, 2.50008e-01, 2.59962e-01,
 2.71460e-01, 2.84414e-01, 2.97762e-01, 3.15589e-01, 3.34094e-01,
 3.36610e-01, 3.41667e-01, 3.46354e-01, 3.50669e-01, 3.54567e-01,
 3.58015e-01, 3.60835e-01, 3.62839e-01, 3.63480e-01, 3.62378e-01,
 3.58351e-01, 3.50300e-01, 3.36910e-01, 3.16242e-01, 2.86631e-01,
 2.45719e-01, 1.85547e-01, 2.50462e-01, 2.58827e-01, 2.68245e-01,
 2.78905e-01, 2.91233e-01, 3.05146e-01, 3.19524e-01, 3.38829e-01,
 3.59218e-01, 3.61875e-01, 3.67120e-01, 3.71992e-01, 3.76482e-01,
 3.80541e-01, 3.84127e-01, 3.87050e-01, 3.89109e-01, 3.89727e-01,
 3.88488e-01, 3.84124e-01, 3.75440e-01, 3.60954e-01, 3.38568e-01,
 3.06406e-01, 2.61976e-01, 1.96780e-01, 3.19513e-01, 3.30153e-01,
 3.42073e-01, 3.55604e-01, 3.71288e-01, 3.89082e-01, 4.07642e-01,
 4.32947e-01, 4.60914e-01, 4.63690e-01, 4.69453e-01, 4.74872e-01,
 4.79866e-01, 4.84364e-01, 4.88281e-01, 4.91405e-01, 4.93452e-01,
 4.93866e-01, 4.92010e-01, 4.86467e-01, 4.75464e-01, 4.56574e-01,
 4.27183e-01, 3.84920e-01, 3.26459e-01, 2.40744e-01, 3.87621e-01,
 4.00504e-01, 4.14910e-01, 4.31281e-01, 4.50286e-01, 4.71918e-01,
 4.94623e-01, 5.25858e-01, 5.61480e-01, 5.64810e-01, 5.71273e-01,
 5.77379e-01, 5.83026e-01, 5.88101e-01, 5.92508e-01, 5.95954e-01,
 5.98100e-01, 5.98247e-01, 5.95585e-01, 5.88403e-01, 5.74488e-01,
 5.50899e-01, 5.14360e-01, 4.61968e-01, 3.89523e-01, 2.83049e-01,
 4.55345e-01, 4.70470e-01, 4.87352e-01, 5.06548e-01, 5.28848e-01,
 5.54283e-01, 5.81088e-01, 6.18152e-01, 6.61198e-01, 6.64823e-01,
 6.71775e-01, 6.78397e-01, 6.84527e-01, 6.90012e-01, 6.94727e-01,
 6.98321e-01, 7.00384e-01, 7.00092e-01, 6.96507e-01, 6.87564e-01,
 6.70696e-01, 6.42595e-01, 5.99234e-01, 5.37064e-01, 4.51204e-01,
 3.23785e-01, 7.85130e-02, 8.12950e-02, 8.44360e-02, 8.78930e-02,
 9.17820e-02, 9.59420e-02, 9.97950e-02, 1.03952e-01, 1.04441e-01,
 1.04181e-01, 1.06906e-01, 1.09425e-01, 1.11696e-01, 1.13720e-01,
 1.15512e-01, 1.17032e-01, 1.18241e-01, 1.19002e-01, 1.19245e-01,
 1.18709e-01, 1.17183e-01, 1.14487e-01, 1.10281e-01, 1.04328e-01,
 9.58880e-02, 8.03160e-02, 9.23600e-03, 9.67800e-03, 1.02490e-02,
 1.08260e-02, 1.13000e-02, 1.15160e-02, 1.11160e-02, 9.14100e-03,
 1.60300e-03, 1.42000e-04, 1.88600e-03, 3.47600e-03, 4.87900e-03,
 6.11300e-03, 7.22000e-03, 8.21100e-03, 9.10700e-03, 9.90000e-03,
 1.06800e-02, 1.15160e-02, 1.26580e-02, 1.45900e-02, 1.76150e-02,
 2.21000e-02, 2.79890e-02, 3.14630e-02, -9.49870e-02, -9.79510e-02,
 -1.01194e-01, -1.05060e-01, -1.09748e-01, -1.15494e-01, -1.22322e-01,
 -1.33556e-01, -1.53213e-01, -1.56674e-01, -1.56372e-01, -1.56170e-01,
 -1.56060e-01, -1.56002e-01, -1.55913e-01, -1.55715e-01, -1.55288e-01,
 -1.54466e-01, -1.52920e-01, -1.50097e-01, -1.45046e-01, -1.36277e-01,
 -1.22498e-01, -1.02464e-01, -7.51600e-02, -4.40780e-02]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CD_distribution = np.nan_to_num(interp1d(y_array, np.array([0.007184, 0.009864, 0.009706, 0.010005, 0.009917, 0.00972, 0.009462, 0.008831,
     0.009081, 0.008901, 0.008642, 0.008448, 0.008279, 0.008121, 0.007968, 0.007814,
     0.007657, 0.007496, 0.007331, 0.007172, 0.007021, 0.006876, 0.006763, 0.006682,
     0.006738, 0.006788, 0.007026, 0.009685, 0.009443, 0.00966, 0.009484, 0.009209,
     0.008896, 0.008288, 0.008882, 0.008915, 0.008683, 0.008503, 0.008345, 0.008194,
     0.008045, 0.007895, 0.007741, 0.007589, 0.007432, 0.007284, 0.007143, 0.006972,
     0.006826, 0.0067, 0.006704, 0.006708, 0.007177, 0.00984, 0.009594, 0.009801,
     0.009614, 0.009333, 0.009026, 0.008438, 0.009062, 0.009031, 0.0088, 0.008622,
     0.008464, 0.008314, 0.008167, 0.008017, 0.007863, 0.007711, 0.007553, 0.007404,
     0.007257, 0.007074, 0.00691, 0.00676, 0.006731, 0.006705, 0.006731, 0.009478,
     0.009242, 0.009469, 0.009287, 0.009003, 0.008685, 0.008128, 0.009056, 0.009227,
     0.009004, 0.00883, 0.008674, 0.008525, 0.008378, 0.008227, 0.008072, 0.007922,
     0.007766, 0.007621, 0.007478, 0.007275, 0.007093, 0.006921, 0.006875, 0.006834,
     0.006325, 0.009157, 0.008937, 0.009186, 0.009, 0.008702, 0.008358, 0.007818,
     0.009113, 0.009548, 0.009335, 0.009166, 0.009015, 0.008867, 0.00872, 0.008569,
     0.008413, 0.008269, 0.008118, 0.00799, 0.00787, 0.00765, 0.007455, 0.007252,
     0.007188, 0.00713, 0.005965, 0.008904, 0.008698, 0.008968, 0.008781, 0.008462,
     0.008069, 0.00753, 0.009272, 0.010028, 0.009836, 0.009683, 0.009545, 0.009406,
     0.009269, 0.009126, 0.008978, 0.008847, 0.008707, 0.008603, 0.0085, 0.008237,
     0.008005, 0.007777, 0.007615, 0.007471, 0.007532, 0.010131, 0.009877, 0.010076,
     0.009896, 0.009623, 0.009315, 0.008652, 0.008949, 0.00886, 0.008598, 0.008404,
     0.008237, 0.008081, 0.00793, 0.007778, 0.007623, 0.007458, 0.00729, 0.007122,
     0.00696, 0.00681, 0.006688, 0.006593, 0.00663, 0.006662, 0.00742, 0.010222,
     0.010161, 0.010371, 0.010172, 0.009878, 0.009551, 0.008852, 0.009126, 0.009079,
     0.008792, 0.008588, 0.008415, 0.008255, 0.008101, 0.007945, 0.007787, 0.007611,
     0.007431, 0.007242, 0.007061, 0.006914, 0.006796, 0.006705, 0.006746, 0.006783,
     0.007655, 0.010299, 0.010076, 0.010317, 0.01017, 0.009929, 0.009654, 0.009012,
     0.009559, 0.009729, 0.009376, 0.009141, 0.008945, 0.008768, 0.0086, 0.008429,
     0.008257, 0.008042, 0.007822, 0.007566, 0.007316, 0.007156, 0.007021, 0.006898,
     0.006884, 0.006872]
    ), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CM_distribution = np.nan_to_num(interp1d(y_array, np.array([-9.310600e-02, -9.984800e-02, -1.080730e-01, -1.182060e-01, -1.311530e-01,
 -1.475430e-01, -1.667250e-01, -1.937510e-01, -2.291760e-01, -2.494410e-01,
 -2.760700e-01, -3.040570e-01, -3.336710e-01, -3.651700e-01, -3.988860e-01,
 -4.349540e-01, -4.734820e-01, -5.137430e-01, -5.551850e-01, -5.950360e-01,
 -6.297780e-01, -6.550040e-01, -6.634110e-01, -6.493960e-01, -6.067790e-01,
 -5.114210e-01, -1.357210e-01, -1.478370e-01, -1.629720e-01, -1.821830e-01,
 -2.073030e-01, -2.398780e-01, -2.791550e-01, -3.364230e-01, -4.219810e-01,
 -4.697450e-01, -5.236100e-01, -5.796340e-01, -6.387100e-01, -7.015000e-01,
 -7.686820e-01, -8.405650e-01, -9.173360e-01, -9.977780e-01, -1.080375e+00,
 -1.159270e+00, -1.225910e+00, -1.267667e+00, -1.267819e+00, -1.212698e+00,
 -1.089481e+00, -8.625520e-01, -1.417090e-01, -1.545760e-01, -1.706820e-01,
 -1.911710e-01, -2.180040e-01, -2.528590e-01, -2.949610e-01, -3.564720e-01,
 -4.489810e-01, -5.004640e-01, -5.581010e-01, -6.180170e-01, -6.811850e-01,
 -7.483250e-01, -8.201620e-01, -8.970300e-01, -9.791360e-01, -1.065209e+00,
 -1.153603e+00, -1.238059e+00, -1.309343e+00, -1.353640e+00, -1.352900e+00,
 -1.292040e+00, -1.157454e+00, -9.113640e-01, -1.663860e-01, -1.823030e-01,
 -2.023220e-01, -2.279610e-01, -2.617000e-01, -3.057460e-01, -3.592530e-01,
 -4.379200e-01, -5.583800e-01, -6.239650e-01, -6.962610e-01, -7.713770e-01,
 -8.504930e-01, -9.345560e-01, -1.024428e+00, -1.120608e+00, -1.223290e+00,
 -1.331410e+00, -1.442614e+00, -1.549714e+00, -1.640246e+00, -1.694483e+00,
 -1.689490e+00, -1.606044e+00, -1.426171e+00, -1.101598e+00, -1.901730e-01,
 -2.090880e-01, -2.329570e-01, -2.636560e-01, -3.041820e-01, -3.572590e-01,
 -4.219860e-01, -5.175240e-01, -6.657500e-01, -7.460760e-01, -8.332550e-01,
 -9.237320e-01, -1.019007e+00, -1.120212e+00, -1.228422e+00, -1.344173e+00,
 -1.467694e+00, -1.597626e+00, -1.730973e+00, -1.858980e+00, -1.966296e+00,
 -2.028997e+00, -2.018843e+00, -1.912422e+00, -1.687278e+00, -1.283204e+00,
 -2.136030e-01, -2.354710e-01, -2.631340e-01, -2.988190e-01, -3.460320e-01,
 -4.080070e-01, -4.837770e-01, -5.958980e-01, -7.712350e-01, -8.656770e-01,
 -9.671640e-01, -1.072438e+00, -1.183246e+00, -1.300916e+00, -1.426666e+00,
 -1.561113e+00, -1.704480e+00, -1.855139e+00, -2.009578e+00, -2.157348e+00,
 -2.280545e+00, -2.351730e+00, -2.337175e+00, -2.208845e+00, -1.940767e+00,
 -1.456478e+00, -8.089200e-02, -8.607400e-02, -9.229600e-02, -9.980900e-02,
 -1.092410e-01, -1.209500e-01, -1.343010e-01, -1.525530e-01, -1.731200e-01,
 -1.842140e-01, -2.022790e-01, -2.214820e-01, -2.418240e-01, -2.634370e-01,
 -2.865280e-01, -3.111940e-01, -3.375260e-01, -3.652460e-01, -3.940460e-01,
 -4.224890e-01, -4.484300e-01, -4.688790e-01, -4.798250e-01, -4.783930e-01,
 -4.605090e-01, -4.028190e-01, -5.612800e-02, -5.817200e-02, -6.036600e-02,
 -6.262500e-02, -6.501600e-02, -6.736200e-02, -6.909100e-02, -6.984000e-02,
 -6.132400e-02, -5.605200e-02, -5.821100e-02, -6.101500e-02, -6.412500e-02,
 -6.742600e-02, -7.093100e-02, -7.462100e-02, -7.853300e-02, -8.262600e-02,
 -8.717400e-02, -9.238200e-02, -9.913400e-02, -1.093590e-01, -1.244930e-01,
 -1.463510e-01, -1.745930e-01, -1.882770e-01, -1.878700e-02, -1.616000e-02,
 -1.235900e-02, -6.714000e-03,  1.491000e-03,  1.323700e-02,  2.900600e-02,
  5.460200e-02,  1.069490e-01,  1.372690e-01,  1.589840e-01,  1.808340e-01,
  2.036300e-01,  2.278530e-01,  2.537880e-01,  2.816490e-01,  3.114670e-01,
  3.429760e-01,  3.750570e-01,  4.050800e-01,  4.276200e-01,  4.333480e-01,
  4.125440e-01,  3.564640e-01,  2.596180e-01,  1.440000e-01],
), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)


    print(designvars.weight.W_wing)

    run_structures(designvars)

    print(designvars.structure_results)
    generate_wing_structure_3D(designvars)
