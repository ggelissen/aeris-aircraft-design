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
        for inddd, (boom_stress, boom_number, boom_x, boom_y, boom_area, boom_shearflow) in enumerate(zip(results['bending_stresses'][:-1], nameslist, results['boom_x_coords_sorted'][:-1], results['boom_y_coords_sorted'][:-1], results['boom_areas_sorted'][:-1], results["final_shear_flows"][:-1])):
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
                if (nameslist[inddd-1] == 'Spar1' or nameslist[inddd-1] == 'Spar2') and (nameslist[inddd] == 'Spar1' or nameslist[inddd] == 'Spar2'):
                    if np.abs(1e3*(boom_shearflow+results['torsional_shear_flow'])/designvars.wing.wingsection.spars['Spar1']["t_web_mm"]) > designvars.materials.material_tau_max*1e6:
                        print(f"Warning: Spar web {boom_number} at spanwise position {spanwise_position:.2f} exceeds yield shear strength with {100*(boom_shearflow/designvars.wing.wingsection.spars['Spar1']['t_web_mm']-designvars.materials.material_tau_max)/boom_shearflow/designvars.wing.wingsection.spars['Spar1']['t_web_mm']} %")
                else:
                    if np.abs(1e3*(boom_shearflow+results['torsional_shear_flow'])/designvars.wing.wingsection.wingskin['thicness']) > designvars.materials.material_tau_max*1e6:
                        print(f"Warning: Wing Skin {boom_number} at spanwise position {spanwise_position:.2f} exceeds yield shear strength with {100*(boom_shearflow/designvars.wing.wingsection.wingskin['thicness']-designvars.materials.material_tau_max)/boom_shearflow/designvars.wing.wingsection.wingskin['thicness']} %")
                if not (boom_number == 'Spar1' or boom_number == 'Spar2'):
                    crit_stringer_buckling = calculate_critical_stringer_buckling_stress(designvars.materials.material_E*1e9, designvars.wing.wingsection.stringers[boom_number]['area_moment_of_inertia_m4'], designvars.wing.wingsection.stringers[boom_number]["crosssectionalarea_mm2"]/1000000, length_between_ribs, designvars.wing.wingsection.stringers[boom_number]['K'] )
                    if np.abs(boom_stress*1e6) > crit_stringer_buckling:
                        #print(f"Warning: Stringer {boom_number} at spanwise position {spanwise_position:.2f} exceeds critical buckling stress with {100*(boom_stress*1e6-crit_stringer_buckling)/(boom_stress*1e6)} % ")
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
                elif (boom_number == 'Spar1' and nameslist[inddd-1] == 'Spar1') or (boom_number == 'Spar2' and nameslist[inddd-1] == 'Spar2'):
                    slenderness_ratio = length_between_ribs/np.abs(results['boom_y_coords_sorted'][:-1][inddd] - results['boom_y_coords_sorted'][:-1][inddd-1])
                    base_height = np.abs(results['boom_y_coords_sorted'][:-1][inddd] - results['boom_y_coords_sorted'][:-1][inddd-1])
                    young = designvars.materials.material_E*1e9
                    thickness = designvars.wing.wingsection.spars[boom_number]["t_web_mm"] / 1000

                    spar_web_buckling_crit = skin_shear_buckling(young, slenderness_ratio, thickness, base_height)
                    if np.abs(boom_shearflow + results['torsional_shear_flow']) > spar_web_buckling_crit:
                        print(f"Warning: Spar web {boom_number} at spanwise position {spanwise_position:.2f} exceeds critical buckling stress with {100*(np.abs(boom_shearflow + results['torsional_shear_flow'])/spar_web_buckling_crit-1)} %")





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
    y_array = np.array([-0.167161, -0.181016, -0.19832, -0.220221, -0.248814, -0.285837, -0.330371,
 -0.395234, -0.490279, -0.539579, -0.59748, -0.657885, -0.72174, -0.78975,
 -0.862647, -0.94073, -1.02412, -1.110966, -1.199269, -1.281431, -1.347464,
 -1.384543, -1.374316, -1.304761, -1.164779, -0.918878])
    designvars.wing.CL_distribution = np.nan_to_num(interp1d(y_array, np.array([0.28188, 0.290282, 0.299745, 0.310382, 0.322649, 0.336443, 0.350593, 0.369578,
 0.387962, 0.387545, 0.391251, 0.394771, 0.398051, 0.401018, 0.40362, 0.405645,
 0.406848, 0.40646, 0.403992, 0.397873, 0.386845, 0.36981, 0.344648, 0.310145,
 0.264228, 0.198729]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CD_distribution = np.nan_to_num(interp1d(y_array, np.array([0.006406, 0.009293, 0.00918, 0.00954, 0.009478, 0.009296, 0.009052, 0.008448,
    0.009304, 0.009367, 0.009098, 0.008897, 0.008723, 0.008562, 0.008405, 0.008248,
    0.008088, 0.007936, 0.00778, 0.007644, 0.007521, 0.007345, 0.007193, 0.007059,
    0.007079, 0.007097]
       ), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CM_distribution = np.nan_to_num(interp1d(y_array, np.array([-0.167161, -0.181016, -0.19832, -0.220221, -0.248814, -0.285837, -0.330371,
  -0.395234, -0.490279, -0.539579, -0.59748, -0.657885, -0.72174, -0.78975,
  -0.862647, -0.94073, -1.02412, -1.110966, -1.199269, -1.281431, -1.347464,
  -1.384543, -1.374316, -1.304761, -1.164779, -0.918878]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)


    print(designvars.weight.W_wing)

    run_structures(designvars)

    print(designvars.structure_results)
    generate_wing_structure_3D(designvars)
