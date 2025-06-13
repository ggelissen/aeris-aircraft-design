# performance_diagram_module.py
import math
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters

# --- ISA Atmospheric Conditions ---
G = 9.80665  # Gravitational acceleration (m/s^2)
RHO_0_ISA_C1 = 1.225  # Sea level standard density (kg/m^3)
R_AIR_ISA_PD = 287.05  # Specific gas constant for dry air (J/kgK)
T_0_ISA_PD = 288.15  # Sea level standard temperature (K)
P_0_ISA_PD = 101325 # Sea level standard pressure (Pa)
LAPSE_RATE_ISA_PD = 0.0065 # Temperature lapse rate in troposphere (K/m)
RHO_0_ISA_PD = 1.225 # Sea level standard density (kg/m^3)\

def get_isa_conditions_pd(altitude_m):
    """
    Calculates ISA temperature, pressure, and density at a given altitude for performance diagram.
    Simplified model: only troposphere (h < 11km).
    """
    h_eff = min(altitude_m, 11000.0) # Cap at tropopause for this simple model

    temp_K = T_0_ISA_PD - LAPSE_RATE_ISA_PD * h_eff
    # Pressure calculation based on hydrostatic equation and lapse rate
    if LAPSE_RATE_ISA_PD == 0: # Isothermal layer (not used here for h < 11km) # pragma: no cover
        pressure_Pa = P_0_ISA_PD * math.exp(-G * h_eff / (R_AIR_ISA_PD * T_0_ISA_PD))
    else:
        pressure_Pa = P_0_ISA_PD * (temp_K / T_0_ISA_PD)**(G / (R_AIR_ISA_PD * LAPSE_RATE_ISA_PD))
    
    density_kg_m3 = pressure_Pa / (R_AIR_ISA_PD * temp_K) if temp_K > 0 else 0
    sigma = density_kg_m3 / RHO_0_ISA_PD if RHO_0_ISA_PD > 0 else 0
    delta = pressure_Pa / P_0_ISA_PD if P_0_ISA_PD > 0 else 0
    theta = temp_K / T_0_ISA_PD if T_0_ISA_PD > 0 else 0
    return temp_K, pressure_Pa, density_kg_m3, sigma, delta, theta

# --- Aerodynamics for Performance Diagram (PDF2) ---
def get_aircraft_config_aerodynamics_pd(aircraft_type_pd, config_name="clean", aspect_ratio=9.0):
    """
    Returns C_D0, Oswald efficiency 'e', and C_Lmax for a given configuration for Perf. Diagram.
    Sources: PDF2 Pages 9 (C_Lmax table), 11 (corrections), 12 (example table).
    """
    # Base clean values from PDF2 Page 12 for Business uav example (used as baseline)
    # These are C_D0 and e for the *basic clean airframe*. Flaps/gear are additive.
    base_C_D0_clean_uav = 0.0145
    base_e_clean_uav = 0.85
    
    # C_Lmax values from PDF2 Page 9 (Typical values for Business uav)
    # For stall constraints, we use specific example values if given, or typical ones.
    C_Lmax_clean_typical_uav_min, C_Lmax_clean_typical_uav_max = 1.4, 1.8
    C_Lmax_TO_typical_uav_min, C_Lmax_TO_typical_uav_max = 1.6, 2.2
    C_Lmax_L_typical_uav_min, C_Lmax_L_typical_uav_max = 1.6, 2.6

    # Default to example values from PDF2 P12 for "uav"
    C_D0, e_val, C_Lmax = base_C_D0_clean_uav, base_e_clean_uav, C_Lmax_clean_typical_uav_max # Default

    if "uav" in aircraft_type_pd:
        # Values from PDF2 Page 12 for "uav" example table:
        if config_name == "clean_config_P12": # Explicitly the "Clean*" from table
            C_D0, e_val, C_Lmax = 0.0145, 0.85, 0.8 # Note: C_Lmax here is low, plots use higher
        elif config_name == "stall_clean_P21": # For reproducing PDF2 Page 21 stall lines
            C_D0, e_val, C_Lmax = base_C_D0_clean_uav, base_e_clean_uav, 1.8
        elif config_name == "stall_landing_P21": # For reproducing PDF2 Page 21 stall lines
            C_D0, e_val, C_Lmax = base_C_D0_clean_uav, base_e_clean_uav, 2.6 # Using example C_Lmax for this specific config for stall constraint

        elif config_name == "take_off_gear_up_P12": # PDF2 P12 "Take-off, gear up"
            C_D0, e_val, C_Lmax = 0.0270, 0.90, 1.9
        elif config_name == "take_off_gear_down_P12": # PDF2 P12 "Take-off, gear down"
            C_D0, e_val, C_Lmax = 0.0420, 0.90, 1.9
        elif config_name == "landing_gear_down_P12": # PDF2 P12 "Landing, gear down"
            C_D0, e_val, C_Lmax = 0.0750, 0.95, 2.4
        
        # General approach using corrections from PDF2 Page 11 (if base is truly clean)
        elif config_name == "generic_take_off_flaps":
            C_D0 = base_C_D0_clean_uav + 0.015 # Avg of 0.01-0.02
            e_val = base_e_clean_uav + 0.05
            C_Lmax = C_Lmax_TO_typical_uav_max # e.g., 2.2
        elif config_name == "generic_landing_flaps_gear_down":
            C_D0 = base_C_D0_clean_uav + 0.065 + 0.020 # Avg Landing flaps + Avg Undercarriage
            e_val = base_e_clean_uav + 0.10 # Landing flaps effect on e
            C_Lmax = C_Lmax_L_typical_uav_max # e.g., 2.6
        else: # Default to base clean if specific config not matched for detailed table
             C_D0, e_val, C_Lmax = base_C_D0_clean_uav, base_e_clean_uav, C_Lmax_clean_typical_uav_max


    if C_D0 is None: # pragma: no cover
        raise ValueError(f"Perf. Diagram Aero params for {aircraft_type_pd} config '{config_name}' not defined.")
    return C_D0, e_val, C_Lmax, aspect_ratio


def get_C_L_at_CL32_CD_max_pd(C_D0, A, e): # For best climb rate [cite: 109]
    return math.sqrt(3 * C_D0 * math.pi * A * e) if (C_D0 * A * e) >= 0 else 0

def get_CD_at_CL_pd(C_L, C_D0, A, e): # [cite: 18]
    return C_D0 + C_L**2 / (math.pi * A * e) if (math.pi * A * e) > 0 else float('inf')


# --- Performance Constraint Functions for T/W-W/S Diagram (from previous combined code) ---

def constraint_stall_speed_pd(wing_loading_range_Npm2, rho_kg_m3, V_s_max_ms, C_Lmax): # [cite: 30]
    if C_Lmax <= 0 or rho_kg_m3 <=0 or V_s_max_ms < 0: return None
    W_S_max_Npm2 = 0.5 * rho_kg_m3 * V_s_max_ms**2 * C_Lmax
    return W_S_max_Npm2

def interpolate_TOP_pd(S_TO_ft, ac_category="uav_2_engine"): # [cite: 44] (chart interpretation)
    chart_S_TO_ft = np.array([2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]) # Extended range
    if ac_category == "uav_2_engine": # "uav OVER 50ft" (2 engines)
        chart_TOP_psf = np.array([60, 100, 135, 170, 200, 230, 260, 290, 320])
    elif ac_category == "propeller_single_double": # pragma: no cover
        chart_TOP_psf = np.array([80, 130, 180, 230, 280, 330, 380, 430, 480])
    else: # Default to uav #pragma: no cover
        chart_TOP_psf = np.array([60, 100, 135, 170, 200, 230, 260, 290, 320])
    TOP_psf = np.interp(S_TO_ft, chart_S_TO_ft, chart_TOP_psf, left=chart_TOP_psf[0], right=chart_TOP_psf[-1])
    return psf_to_Npm2(TOP_psf)


def constraint_take_off_distance_uav_pd(wing_loading_range_Npm2, S_TO_req_m, C_Lmax_TO, sigma_TO=1.0, ac_category_TOP_chart="uav_2_engine"): # [cite: 51, 52]
    if C_Lmax_TO <= 0 or sigma_TO <=0 : return np.full_like(wing_loading_range_Npm2, np.nan)
    S_TO_req_ft = m_to_ft(S_TO_req_m)
    TOP_uav_Npm2 = interpolate_TOP_pd(S_TO_req_ft, ac_category_TOP_chart)
    if TOP_uav_Npm2 <= 0: return np.full_like(wing_loading_range_Npm2, np.nan)
    C_L_TO = C_Lmax_TO / (1.1**2) # [cite: 49]
    T_W = wing_loading_range_Npm2 / (TOP_uav_Npm2 * C_L_TO * sigma_TO)
    return T_W

def constraint_landing_distance_pd(wing_loading_range_Npm2, S_L_req_m, C_Lmax_L, W_L_over_W_TO, rho_kg_m3, ac_type="CS25"): # [cite: 77, 86]
    if C_Lmax_L <= 0 or rho_kg_m3 <=0 or W_L_over_W_TO <=0 or S_L_req_m <0: return None
    factor = 0.5847 if "CS25" in ac_type or "uav" in ac_type else 0.5915 # [cite: 76, 86]
    V_s_land_squared = S_L_req_m / factor if factor > 0 else float('inf')
    W_S_L_limit = 0.5 * C_Lmax_L * rho_kg_m3 * V_s_land_squared
    W_S_TO_limit_Npm2 = W_S_L_limit / W_L_over_W_TO if W_L_over_W_TO > 0 else float('inf')
    return W_S_TO_limit_Npm2

def constraint_cruise_speed_uav_pd(wing_loading_range_Npm2, V_cruise_ms, alt_cruise_m,
                                C_D0_clean, e_clean, A_clean,
                                W_cruise_frac_W_TO=0.8, thrust_setting_frac=0.9): # [cite: 100, 101]
    _, _, rho_cruise, sigma_cruise, _, _ = get_isa_conditions_pd(alt_cruise_m)
    if rho_cruise <= 0 : return np.full_like(wing_loading_range_Npm2, np.nan)
    thrust_lapse_corr = (1.0 / sigma_cruise)**0.75 if sigma_cruise > 0 else float('inf') # [cite: 100]
    q_cruise = 0.5 * rho_cruise * V_cruise_ms**2
    if q_cruise <= 0: return np.full_like(wing_loading_range_Npm2, np.nan)
    term1_coeff = C_D0_clean * q_cruise
    term2_den_factor = math.pi * A_clean * e_clean * q_cruise
    if term2_den_factor <= 0: return np.full_like(wing_loading_range_Npm2, np.nan)

    T_W_TO_list = []
    for W_S_TO in wing_loading_range_Npm2:
        if W_S_TO <= 0: T_W_TO_list.append(np.nan); continue
        # (W/S) in formula is current (W/S)_cruise = (W/S)_TO * W_cruise_frac
        # So the T/W formula terms are (D_0/ (W/S)_cruise) and ( (W/S)_cruise / (pi A e q))
        # T/W_cruise = (C_D0 q / (W/S)_cruise) + ( (W/S)_cruise / (pi A e q) )
        # T/W_cruise = (C_D0 q / (W/S_TO W_cruise_frac)) + ( (W/S_TO W_cruise_frac) / (pi A e q) )
        # T_TO/W_TO = (1/thrust_setting) * thrust_lapse_corr * (T_cruise/W_cruise) * W_cruise_frac
        # T_cruise/W_cruise = (C_D0 q / (W_S_TO W_cruise_frac)) + (W_S_TO W_cruise_frac / (pi A e q))
        # The formula on slide 56 is T/W. If T is current thrust and W is current weight.
        # T_TO/W_TO = (W_cruise_frac / thrust_setting_frac) * thrust_lapse_corr * [ C_D0*q/(W_S_TO*W_cruise_frac) + (W_S_TO*W_cruise_frac)/(pi*A*e*q) ]
        # This simplifies to: T_TO/W_TO = (1/thrust_setting_frac)*thrust_lapse_corr * [C_D0*q/W_S_TO + (W_S_TO * W_cruise_frac^2)/(pi*A*e*q)] as per previous logic from PDF2 P57 analysis
        
        term1 = term1_coeff / W_S_TO
        term2 = (W_S_TO * W_cruise_frac_W_TO**2) / term2_den_factor
        T_W_at_alt_for_Wcruise = term1 + term2 # This is T_cruise / W_TO
        
        # The equation on P56/57 seems to be directly giving T_TO/W_TO on LHS if W/S on RHS is (W/S)_TO
        # Let's re-verify (T_TO/W) = (rho_0/rho)^0.75 * [ (CD0 * q) / (W/S)_TO_at_current_W + ( (W/S)_TO_at_current_W * W_actual^2/W_TO^2 ) / (pi A e q) ]
        # The term W_S_TO on page 57 example's RHS is (0.8W/S), where W/S is W_TO/S. So it's 0.8 * (W_TO/S).
        # This implies (W/S) in the formula is (actual_weight/S).
        # (T_TO/W_TO) = (1/ThrustSetting) * (rho0/rho)^0.75 * [ (CD0 * q / (W_TO/S * Wfrac)) + ( (W_TO/S * Wfrac) / (pi A e q) ) ] * Wfrac
        # T_TO/W_TO = (1/TS) * TLcorr * [ (CD0*q / ( (W/S)_TO *Wfrac)) + ( (W/S)_TO * Wfrac / (pi*A*e*q) ) ] * Wfrac

        # The expression on slide 57 is: T_TO/W = (0.8/0.9) * TL_corr * [CD0*q / (0.8 W/S) + (0.8 W/S) / (pi A e q) ]
        # Where W is W_TO. So T_TO/W_TO = (W_cruise_frac / thrust_setting_frac) * TL_corr * [ CD0*q / ((W/S)_TO * W_cruise_frac) + ((W/S)_TO * W_cruise_frac) / (pi A e q) ]
        # T_TO/W_TO = (1/thrust_setting_frac) * TL_corr * [ CD0*q / (W/S)_TO + ((W/S)_TO * W_cruise_frac^2) / (pi A e q) ] (This matches what was implemented)

        T_W_TO = (1.0 / thrust_setting_frac) * thrust_lapse_corr * (term1 + term2)
        T_W_TO_list.append(T_W_TO)
    return np.array(T_W_TO_list)


def constraint_climb_rate_uav_pd(wing_loading_range_Npm2, roc_ms, alt_climb_m,
                              C_D0_climb, e_climb, A_climb,
                              thrust_setting_frac=1.0, W_climb_frac_W_TO=1.0): # [cite: 118, 120]
    _, _, rho_climb, sigma_climb, _, _ = get_isa_conditions_pd(alt_climb_m)
    if rho_climb <=0: return np.full_like(wing_loading_range_Npm2, np.nan)
    C_L_opt_climb = get_C_L_at_CL32_CD_max_pd(C_D0_climb, A_climb, e_climb) # [cite: 109]
    C_D_opt_climb = get_CD_at_CL_pd(C_L_opt_climb, C_D0_climb, A_climb, e_climb) # Actually 4*CD0 [cite: 109]
    if C_L_opt_climb <= 0: return np.full_like(wing_loading_range_Npm2, np.nan)
    D_L_opt_climb = C_D_opt_climb / C_L_opt_climb if C_L_opt_climb > 0 else float('inf')
    thrust_lapse_corr = (1.0 / sigma_climb)**0.75 if sigma_climb > 0 else float('inf')

    T_W_TO_list = []
    for W_S_TO in wing_loading_range_Npm2:
        if W_S_TO <= 0: T_W_TO_list.append(np.nan); continue
        W_S_climb = W_S_TO * W_climb_frac_W_TO
        V_climb_num = W_S_climb * 2
        V_climb_den = rho_climb * C_L_opt_climb
        if V_climb_num < 0 or V_climb_den <= 0: T_W_TO_list.append(np.nan); continue
        V_climb = math.sqrt(V_climb_num / V_climb_den)
        if V_climb <=0: T_W_TO_list.append(np.nan); continue
        T_W_at_alt = (roc_ms / V_climb) + D_L_opt_climb # This is T_climb / W_climb [cite: 120]
        T_W_TO = (1.0 / thrust_setting_frac) * thrust_lapse_corr * T_W_at_alt * W_climb_frac_W_TO
        T_W_TO_list.append(T_W_TO)
    return np.array(T_W_TO_list)

def constraint_climb_gradient_uav_pd(wing_loading_range_Npm2, grad_req, alt_grad_m,
                                  C_D0_grad, e_grad, A_grad,
                                  is_OEI=False, num_engines=2, delta_CD0_OEI=0.005,
                                  thrust_setting_frac=1.0, W_grad_frac_W_TO=1.0): # [cite: 136, 138, 143]
    _, _, rho_grad, sigma_grad, _, _ = get_isa_conditions_pd(alt_grad_m)
    C_D0_eff = C_D0_grad + delta_CD0_OEI if is_OEI else C_D0_grad
    if C_D0_eff <=0 or (math.pi * A_grad * e_grad) <=0: return np.full_like(wing_loading_range_Npm2, float('inf'))
    D_L_min = 2 * math.sqrt(C_D0_eff / (math.pi * A_grad * e_grad)) # [cite: 138]
    T_W_at_alt_for_Wgrad = grad_req + D_L_min # This is T_actual / W_actual [cite: 136]
    factor_OEI = num_engines / (num_engines - 1.0) if is_OEI and num_engines > 1 else 1.0 # [cite: 143]
    thrust_lapse_corr = (1.0 / sigma_grad)**0.75 if sigma_grad > 0 else float('inf')
    T_W_TO_val = factor_OEI * (1.0 / thrust_setting_frac) * thrust_lapse_corr * T_W_at_alt_for_Wgrad * W_grad_frac_W_TO
    return np.full_like(wing_loading_range_Npm2, T_W_TO_val)


# --- Plotting Function (from previous combined code) ---
def plot_TW_WS_diagram_pd(wing_loading_Npm2, constraints_data_pd, title="T/W vs W/S Diagram", design_point=None): #pragma: no cover
    plt.figure(figsize=(14, 7))
    colors = plt.cm.get_cmap('tab10', len(constraints_data_pd))
    
    for i, constr in enumerate(constraints_data_pd):
        color = colors(i % 10) # Cycle through 10 colors

        # Plot lines for T_W values
        if constr.get('T_W_values', None) is not None:
            # Filter out NaN values for plotting to avoid gaps if possible, or plot as is
            valid_indices = np.isfinite(wing_loading_Npm2) & np.isfinite(constr['T_W_values'])
            if np.any(valid_indices):
                plt.plot(wing_loading_Npm2[valid_indices], constr['T_W_values'][valid_indices], 
                         label=constr['label'], color=color, linestyle=constr.get('style', '-'))


        elif constr.get('W_S_max', None) is not None:
            TW_min_for_plot, TW_max_for_plot = plt.gca().get_ylim() if plt.gca().get_lines() else (0, 0.6)
            if not plt.gca().get_lines(): TW_max_for_plot = 0.6

            plt.vlines(x=constr['W_S_max'], ymin=TW_min_for_plot, ymax=TW_max_for_plot, label=constr['label'], colors=color, linestyles=constr.get('style', '--'))

    if design_point:
        plt.plot(design_point['W_S'], design_point['T_W'], 'ko', markersize=4, label=f"Design Point ({design_point['label']})")
        plt.text(design_point['W_S']*1.02, design_point['T_W']*1.02, f" W/S={design_point['W_S']:.0f}\n T/W={design_point['T_W']:.3f}", fontsize=9)


    plt.xlabel("Wing Loading (W/S) $[N/m^2]$")
    plt.ylabel("Thrust-to-Weight Ratio (T/W)")
    #plt.title(title)
    plt.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize='small')
    plt.grid(True)
    # Sensible auto-limits or user-defined
    y_min = min(c['T_W_values'].min() for c in constraints_data_pd if c.get('T_W_values', None) is not None and np.any(np.isfinite(c['T_W_values']))) if any(c.get('T_W_values', None) is not None for c in constraints_data_pd) else 0
    y_max = max(c['T_W_values'].max() for c in constraints_data_pd if c.get('T_W_values', None) is not None and np.any(np.isfinite(c['T_W_values']))) if any(c.get('T_W_values', None) is not None for c in constraints_data_pd) else 0.6
    
    finite_tw_values = [tw for constr in constraints_data_pd if constr.get('T_W_values') is not None for tw in constr['T_W_values'] if np.isfinite(tw)]
    if finite_tw_values:
        plt.ylim(max(0, min(finite_tw_values) * 0.8), min(0.8, max(finite_tw_values) * 1.2))
    else:
        plt.ylim(0, 0.6)

    plt.ylim(0, 0.6)
    plt.xlim(wing_loading_Npm2[0], 4000)
    plt.tight_layout(w_pad=0.5)
    plt.savefig("Figures/Performance Diagrams/TW_WS_Diagram.pdf")
    print("\nPerformance Diagram saved as TW_WS_Diagram.pdf")


def run_performance_diagram(params: DesignParameters): #pragma: no cover	
    """
    Generates the T/W vs W/S diagram for the UAV based on performance constraints.
    """
    uav_A_perf = params.wing.A_w_target
    num_engines_uav_perf = params.engine.N_engines

    # Aerodynamic parameters (PDF2 P12 "uav" example data or specific configs)
    # Using specific configurations for clarity based on constraint context
    C_D0_s_clean, e_s_clean, C_Lmax_s_clean, _ = get_aircraft_config_aerodynamics_pd("uav", "stall_clean_P21", uav_A_perf)
    _, _, C_Lmax_s_L, _ = get_aircraft_config_aerodynamics_pd("uav", "stall_landing_P21", uav_A_perf) # For stall landing
    
    C_D0_to_cfg, e_to_cfg, C_Lmax_to_cfg_base, _ = get_aircraft_config_aerodynamics_pd("uav", "take_off_gear_up_P12", uav_A_perf) # Base for T/O related constraints
    C_D0_l_cfg, e_l_cfg, C_Lmax_l_cfg_base, _ = get_aircraft_config_aerodynamics_pd("uav", "landing_gear_down_P12", uav_A_perf) # Base for Landing constraints

    C_D0_cruise_cfg, e_cruise_cfg, _, _ = get_aircraft_config_aerodynamics_pd("uav", "clean_config_P12", uav_A_perf) # Clean for cruise/climb rate

    # Performance Requirements
    V_s_clean_req_kts_pd = params.stall_speed_clean  
    V_s_land_req_kts_pd = params.stall_speed_land   
    S_TO_req_m_pd = params.take_off_distance        
    S_L_req_m_pd = params.landing_distance        
    W_L_over_W_TO_uav_pd = 0.88             # [cite: 88]

    cruise_alt_m_pd = params.cruise_altitude                        
    cruise_V_ms_pd = params.cruise_speed                               
    cruise_W_frac_pd = 0.8                                     
    cruise_thrust_setting_pd = params.engine.cruise_thrust_setting          

    climb_rate_req_ms_pd = params.performance.climb_rate
    climb_rate_alt_m_pd = params.performance.climb_rate_alt
    climb_rate_W_frac_pd = 1.0

    climb_grad_AEO_req_pd = params.performance.climb_gradient_AEO
    climb_grad_AEO_alt_m_pd = ft_to_m(params.performance.climb_gradient_AEO_alt)
    C_D0_grad_AEO, e_grad_AEO, _, _ = get_aircraft_config_aerodynamics_pd("uav", "take_off_gear_up_P12", uav_A_perf) # T/O config for this

    climb_grad_OEI_req_pd = params.performance.climb_gradient_OEI
    climb_grad_OEI_alt_m_pd = ft_to_m(params.performance.climb_gradient_OEI_alt)
    delta_CD0_OEI_val_pd = params.performance.delta_CD0_OEI  
    C_D0_grad_OEI, e_grad_OEI, _, _ = get_aircraft_config_aerodynamics_pd("uav", "take_off_gear_up_P12", uav_A_perf) # T/O config for OEI

    W_S_range_Npm2_pd = np.linspace(1500, 6000, 200)
    constraints_list_pd = []
    _, _, rho_SL_pd, _, _, _ = get_isa_conditions_pd(0)

    # 1. Stall Speed
    ws_stall_cl = constraint_stall_speed_pd(W_S_range_Npm2_pd, rho_SL_pd, kts_to_ms(V_s_clean_req_kts_pd), C_Lmax_s_clean)
    constraints_list_pd.append({'label': f'Stall Speed $(V_s)_{{TO}}$ (Clean)', 'W_S_max': ws_stall_cl, 'style': '-.'})
    
    ws_stall_L_at_landing = constraint_stall_speed_pd(W_S_range_Npm2_pd, rho_SL_pd, kts_to_ms(V_s_land_req_kts_pd), C_Lmax_s_L)
    ws_stall_L_at_TO = ws_stall_L_at_landing / W_L_over_W_TO_uav_pd if ws_stall_L_at_landing else None
    constraints_list_pd.append({'label': f'Stall Speed $(V_s)_L$ (Landing)', 'W_S_max': ws_stall_L_at_TO, 'style': ':'})

    # 2. Take-Off
    for clmax_to in [1.6, 1.9, 2.2]: # PDF2 P27 values
        tw_to = constraint_take_off_distance_uav_pd(W_S_range_Npm2_pd, S_TO_req_m_pd, clmax_to, sigma_TO=1.0)
        constraints_list_pd.append({'label': f'Take-Off Distance $S_{{TO}}$ @ $(C_L)_{{max}} = {clmax_to}$', 'T_W_values': tw_to, 'style': '-'})

    # 3. Landing
    ws_land_18 = None
    for clmax_l in [1.8, 2.1, C_Lmax_l_cfg_base]: # C_Lmax_l_cfg_base is 2.4 from P12 example
        ws_land = constraint_landing_distance_pd(W_S_range_Npm2_pd, S_L_req_m_pd, clmax_l, W_L_over_W_TO_uav_pd, rho_SL_pd, "CS25")
        constraints_list_pd.append({'label': f'Landing Distance $S_L$ @ $(C_L)_{{max}} = {clmax_l}$', 'W_S_max': ws_land, 'style': '--'})
        if clmax_l == 1.8:
            ws_land_18 = ws_land

    # 4. Cruise Speed
    tw_cruise = constraint_cruise_speed_uav_pd(W_S_range_Npm2_pd, cruise_V_ms_pd, cruise_alt_m_pd, C_D0_cruise_cfg, e_cruise_cfg, uav_A_perf, cruise_W_frac_pd, cruise_thrust_setting_pd)
    constraints_list_pd.append({'label': f'Cruise Speed $V_c$', 'T_W_values': tw_cruise, 'style': '-'})

    # 5. Climb Rate AEO (Clean config assumed for best RoC speed condition)
    tw_roc = constraint_climb_rate_uav_pd(W_S_range_Npm2_pd, climb_rate_req_ms_pd, climb_rate_alt_m_pd, C_D0_cruise_cfg, e_cruise_cfg, uav_A_perf, W_climb_frac_W_TO=climb_rate_W_frac_pd)
    constraints_list_pd.append({'label': f'Rate of Climb c (AEO)', 'T_W_values': tw_roc, 'style': '-'})

    # --- Find intersection of rate of climb curve and landing distance (clmax=1.8) ---
    if ws_land_18 is not None:
        idx_land = np.argmin(np.abs(W_S_range_Npm2_pd - ws_land_18))
        ws_intersect = W_S_range_Npm2_pd[idx_land]
        tw_intersect = tw_roc[idx_land]
        ws_intersect_rounded = int(round(ws_intersect, -2))
        tw_intersect_rounded = round(tw_intersect, 2)
        design_point_example = {'W_S': ws_intersect, 'T_W': tw_intersect, 'label': f'Intersection ({ws_intersect_rounded}, {tw_intersect_rounded})'}
    else:
        design_point_example = None

    # 6. Climb Gradient AEO (T/O config, using C_D0_grad_AEO, e_grad_AEO)
    tw_grad_aeo = constraint_climb_gradient_uav_pd(W_S_range_Npm2_pd, climb_grad_AEO_req_pd, climb_grad_AEO_alt_m_pd, C_D0_grad_AEO, e_grad_AEO, uav_A_perf, is_OEI=False, num_engines=num_engines_uav_perf)
    constraints_list_pd.append({'label': f'Climb Gradient c/V (AEO)', 'T_W_values': tw_grad_aeo, 'style': '-'})

    # 7. Climb Gradient OEI (T/O config, C_D0_grad_OEI is C_D0_grad_AEO + delta_CD0_OEI_val)
    tw_grad_oei = constraint_climb_gradient_uav_pd(W_S_range_Npm2_pd, climb_grad_OEI_req_pd, climb_grad_OEI_alt_m_pd, C_D0_grad_OEI, e_grad_OEI, uav_A_perf, is_OEI=True, num_engines=num_engines_uav_perf, delta_CD0_OEI=delta_CD0_OEI_val_pd)
    constraints_list_pd.append({'label': f'Climb Gradient c/V (OEI)', 'T_W_values': tw_grad_oei, 'style': '--'})

    plot_TW_WS_diagram_pd(W_S_range_Npm2_pd, constraints_list_pd, title=f"T/W vs W/S Diagram - Business uav (A={uav_A_perf})", design_point=design_point_example)

    return {"T_W": float(tw_intersect), "W_S": float(ws_intersect)}

if __name__ == "__main__": #pragma: no cover

    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    results = run_performance_diagram(params)
    print(results)