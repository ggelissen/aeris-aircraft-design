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
    y_array = np.array([0.497939, 0.535395, 0.57604,  0.620787, 0.670717, 0.727033, 0.790755, 0.861757,
         0.937167, 1.011241, 1.103243, 1.231024, 1.338539, 1.437229, 1.533112, 1.628782,
         1.72558,  1.824164, 1.924557, 2.02589,  2.125973, 2.221131, 2.307192, 2.381746,
         2.445554, 2.501704, 0.497939, 0.535395, 0.57604,  0.620787, 0.670717, 0.727033,
         0.790755, 0.861757, 0.937167, 1.011241, 1.103243, 1.231024, 1.338539, 1.437229,
         1.533112, 1.628782, 1.72558,  1.824164, 1.924557, 2.02589,  2.125973, 2.221131,
         2.307192, 2.381746, 2.445554, 2.501704, 0.497939, 0.535395, 0.57604,  0.620787,
         0.670717, 0.727033, 0.790755, 0.861757, 0.937167, 1.011241, 1.103243, 1.231024,
         1.338539, 1.437229, 1.533112, 1.628782, 1.72558,  1.824164, 1.924557, 2.02589,
         2.125973, 2.221131, 2.307192, 2.381746, 2.445554, 2.501704, 0.497939, 0.535395,
         0.57604,  0.620787, 0.670717, 0.727033, 0.790755, 0.861757, 0.937167, 1.011241,
         1.103243, 1.231024, 1.338539, 1.437229, 1.533112, 1.628782, 1.72558,  1.824164,
         1.924557, 2.02589,  2.125973, 2.221131, 2.307192, 2.381746, 2.445554, 2.501704,
         0.497939, 0.535395, 0.57604,  0.620787, 0.670717, 0.727033, 0.790755, 0.861757,
         0.937167, 1.011241, 1.103243, 1.231024, 1.338539, 1.437229, 1.533112, 1.628782,
         1.72558,  1.824164, 1.924557, 2.02589,  2.125973, 2.221131, 2.307192, 2.381746,
         2.445554, 2.501704, 0.497939, 0.535395, 0.57604,  0.620787, 0.670717, 0.727033,
         0.790755, 0.861757, 0.937167, 1.011241, 1.103243, 1.231024, 1.338539, 1.437229,
         1.533112, 1.628782, 1.72558,  1.824164, 1.924557, 2.02589,  2.125973, 2.221131,
         2.307192, 2.381746, 2.445554, 2.501704, 0.497939, 0.535395, 0.57604,  0.620787,
         0.670717, 0.727033, 0.790755, 0.861757, 0.937167, 1.011241, 1.103243, 1.231024,
         1.338539, 1.437229, 1.533112, 1.628782, 1.72558,  1.824164, 1.924557, 2.02589,
         2.125973, 2.221131, 2.307192, 2.381746, 2.445554, 2.501704])
    designvars.wing.CL_distribution = np.nan_to_num(interp1d(y_array, np.array([0.333681, 0.342687, 0.352582, 0.363059, 0.374406, 0.386695, 0.399927, 0.413718,
         0.426826, 0.434217, 0.432003, 0.433442, 0.434596, 0.434468, 0.433142, 0.430456,
         0.426152, 0.419777, 0.410784, 0.398139, 0.380995, 0.358208, 0.32878,  0.292299,
         0.247394, 0.185865, 0.380517, 0.390758, 0.401983, 0.413918, 0.426913, 0.441097,
         0.45655,  0.472926, 0.488994, 0.499721, 0.498431, 0.500764, 0.502754, 0.503329,
         0.502635, 0.500518, 0.496709, 0.490706, 0.481893, 0.469043, 0.451084, 0.426273,
         0.393083, 0.350486, 0.295848, 0.220308, 0.428039, 0.439531, 0.452149, 0.465632,
         0.480366, 0.496562, 0.514391, 0.533563, 0.552802, 0.566924, 0.566585, 0.570025,
         0.573075, 0.57456,  0.574654, 0.573184, 0.569838, 0.564069, 0.555084, 0.541372,
         0.521787, 0.49401,  0.456332, 0.407148, 0.343062, 0.253569, 0.451977, 0.464107,
         0.477402, 0.491659, 0.507263, 0.524471, 0.543503, 0.564094, 0.584966, 0.60091,
         0.60114,  0.605234, 0.60888,  0.610912, 0.611547, 0.610504, 0.607409, 0.601645,
         0.59254,  0.578555, 0.558155, 0.52883,  0.488376, 0.435154, 0.36583,  0.26927,
         0.475923, 0.488701, 0.50269,  0.517756, 0.534225, 0.552449, 0.572676, 0.594681,
         0.617206, 0.634992, 0.635757, 0.640487, 0.644775, 0.647183, 0.647985, 0.64724,
         0.644357, 0.638746, 0.62974,  0.61505,  0.59352,  0.56262,  0.519568, 0.462792,
         0.387713, 0.284271, 0.499921, 0.513338, 0.52802,  0.54378,  0.561084, 0.580283,
         0.601715, 0.625106, 0.649272, 0.668852, 0.669996, 0.675178, 0.679705, 0.6823,
         0.683431, 0.682458, 0.679285, 0.67337,  0.663825, 0.648681, 0.626194, 0.59323,
         0.547466, 0.486999, 0.407026, 0.297361, 0.240343, 0.246839, 0.253991, 0.261459,
         0.269397, 0.277773, 0.286567, 0.295078, 0.302213, 0.302911, 0.298522, 0.297946,
         0.297229, 0.295498, 0.292727, 0.288745, 0.283328, 0.276126, 0.266773, 0.254662,
         0.239477, 0.221054, 0.199605, 0.175849, 0.149349, 0.115475]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CD_distribution = np.nan_to_num(interp1d(y_array, np.array([0.006946, 0.009942, 0.009848, 0.010294, 0.010359, 0.010329, 0.010131, 0.009778,
 0.009258, 0.01044,  0.010215, 0.009829, 0.009463, 0.009151, 0.008859, 0.008575,
 0.008292, 0.008003, 0.007709, 0.007431, 0.007166, 0.006922, 0.006742, 0.0066,
 0.00656,  0.006525, 0.006517, 0.009591, 0.009568, 0.010078, 0.010203, 0.01024,
 0.01012,  0.009825, 0.009327, 0.010572, 0.010418, 0.010058, 0.00971,  0.009413,
 0.009127, 0.00884,  0.008545, 0.008237, 0.007913, 0.007604, 0.007292, 0.006995,
 0.006758, 0.006542, 0.006616, 0.006682, 0.006085, 0.009299, 0.009244, 0.009723,
 0.009804, 0.009794, 0.009609, 0.00923,  0.008691, 0.010464, 0.010605, 0.010267,
 0.009935, 0.009646, 0.009372, 0.009092, 0.008806, 0.008516, 0.008222, 0.007963,
 0.007667, 0.007392, 0.007153, 0.006883, 0.006944, 0.006998, 0.00594,  0.009234,
 0.009173, 0.009645, 0.009715, 0.009684, 0.009449, 0.009056, 0.00852,  0.010448,
 0.010703, 0.010382, 0.010072, 0.0098,   0.009576, 0.009337, 0.009051, 0.008754,
 0.008476, 0.008079, 0.007878, 0.007592, 0.007409, 0.007195, 0.007409, 0.007597,
 0.005869, 0.009139, 0.009163, 0.009612, 0.009689, 0.009623, 0.00936,  0.008982,
 0.008431, 0.0105,   0.01086,  0.010573, 0.010301, 0.01013,  0.009892, 0.009613,
 0.009562, 0.009302, 0.008892, 0.008551, 0.008368, 0.008078, 0.007794, 0.007695,
 0.008078, 0.008415, 0.005686, 0.008931, 0.008909, 0.009464, 0.00962,  0.009627,
 0.009351, 0.008979, 0.008406, 0.010611, 0.011079, 0.010872, 0.010749, 0.010588,
 0.010629, 0.010454, 0.010182, 0.009882, 0.009583, 0.009375, 0.009011, 0.008697,
 0.008614, 0.008436, 0.009025, 0.009543, 0.007053, 0.010221, 0.010309, 0.010879,
 0.011063, 0.011128, 0.010805, 0.010429, 0.009874, 0.010604, 0.010138, 0.009728,
 0.009355, 0.00904,  0.008749, 0.008469, 0.008191, 0.007911, 0.00763,  0.007347,
 0.007081, 0.006836, 0.006658, 0.006543, 0.006669, 0.00678]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)
    designvars.wing.CM_distribution = np.nan_to_num(interp1d(y_array, np.array([-0.109932, -0.119723, -0.131979, -0.147105, -0.166202, -0.190691, -0.22254,
 -0.263743, -0.314624, -0.366971, -0.416484, -0.50352, -0.585205, -0.665601,
 -0.748369, -0.835045, -0.926282, -1.02163, -1.119338, -1.214046, -1.297207,
 -1.354081, -1.366448, -1.320033, -1.202251, -0.970036, -0.11549, -0.126469,
 -0.140221, -0.157259, -0.178819, -0.206541, -0.242712, -0.289714, -0.348186,
 -0.409918, -0.468532, -0.569523, -0.664481, -0.75828, -0.855313, -0.957553,
 -1.065993, -1.1804, -1.299093, -1.416149, -1.521703, -1.597246, -1.619652,
 -1.568952, -1.424194, -1.138092, -0.121027, -0.133193, -0.148459, -0.167435,
 -0.191501, -0.222517, -0.263094, -0.316023, -0.382225, -0.453422, -0.521182,
 -0.636424, -0.745055, -0.852712, -0.964468, -1.082672, -1.208605, -1.342194,
 -1.481692, -1.619548, -1.745248, -1.836194, -1.865596, -1.8085, -1.638307,
 -1.298837, -0.123741, -0.136488, -0.152498, -0.172427, -0.197721, -0.230358,
 -0.273111, -0.328968, -0.39901, -0.474983, -0.547433, -0.669925, -0.785536,
 -0.900414, -1.020176, -1.147061, -1.282134, -1.425149, -1.574475, -1.723179,
 -1.859301, -1.958113, -1.989202, -1.925509, -1.740226, -1.373774, -0.126425,
 -0.139751, -0.156482, -0.177341, -0.203844, -0.238076, -0.282974, -0.341715,
 -0.415566, -0.496281, -0.573361, -0.703086, -0.825788, -0.947727, -1.0742,
 -1.20907, -1.353024, -1.50589, -1.666193, -1.825372, -1.969516, -2.075392,
 -2.108467, -2.040888, -1.837733, -1.444575, -0.12905, -0.142954, -0.160412,
 -0.182178, -0.20984, -0.2456, -0.29258, -0.35414, -0.431738, -0.517093,
 -0.598626, -0.735268, -0.864663, -0.993047, -1.127615, -1.269761, -1.421153,
 -1.5821, -1.750635, -1.918235, -2.071932, -2.182104, -2.215152, -2.140987,
 -1.92292, -1.50541, -0.098672, -0.106013, -0.115153, -0.12631, -0.14029,
 -0.158078, -0.181049, -0.210323, -0.245653, -0.2787, -0.309316, -0.367558,
 -0.421828, -0.474521, -0.527851, -0.582518, -0.638535, -0.695066, -0.750358,
 -0.800418, -0.839733, -0.8605, -0.85492, -0.819707, -0.750884, -0.624756]), fill_value='extrapolate')(np.linspace(0.0, np.max(y_array), 1000)), neginf=0, posinf=0)

    wingloading = WingLoadingDiagrams(designvars)
    wingloading = wingloading.run_analysis(False)

    print(designvars.weight.W_wing)

    run_structures(designvars)

    print(designvars.structure_results)
    generate_wing_structure_3D(designvars)
