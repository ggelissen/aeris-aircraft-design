import math
import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters

# --- Constants ---
G = 9.80665  # Acceleration due to gravity (m/s^2)

def wing_weight_N(params: DesignParameters):
    """
    Calculates wing weight based on the Torenbeek method for light transport aircraft.
    Source: Torenbeek, "Advanced Aircraft Design", Appendix C.
    NOTE: This formula is empirical and requires imperial units (lbf, ft).
    """
    #print("  - Calculating Wing Weight (Torenbeek)...") # Removed so that it doesnt print in iterations.
    W_TO_lb = N_to_lbf(params.weight.W_TO)
    b_w_ft = m_to_ft(params.wing.b_w)
    S_w_ft2 = m2_to_ft2(params.wing.S_w)
    
    if params.wing.root_chord is None or params.wing.t_c_w_r is None:
        print("    - WARNING: Wing root chord or t/c ratio not defined. Cannot calculate wing weight.")
        return 0
    # Correctly calculates root thickness in feet
    t_r_ft = m_to_ft(params.wing.root_chord * params.wing.t_c_w_r) # This is a parameter on design_parameters, but goot to calculate it here for clarity.
    
    if any(v is None for v in [W_TO_lb, b_w_ft, params.wing.Lambda_05_w, params.max_load_factor, S_w_ft2, t_r_ft]):
        print("    - WARNING: Missing parameters for wing weight calculation. Returning 0.")
        return 0

    # CORRECTED FORMULA: All weight/force terms now use W_TO_lb
    W_wing_lb = 0.00125 * W_TO_lb * (b_w_ft / math.cos(params.wing.Lambda_05_w))**0.75 * \
                (1 + (6.3 * math.cos(params.wing.Lambda_05_w) / b_w_ft)**0.5) * \
                params.max_load_factor**0.55 * \
                (S_w_ft2 * b_w_ft / (t_r_ft * W_TO_lb * math.cos(params.wing.Lambda_05_w)))**0.3
    
    return lbf_to_N(W_wing_lb)

def fuselage_weight_N(params: DesignParameters):
    """
    Calculates fuselage weight using the Gundlach statistical method.
    Source: Gundlach, "Designing Unmanned Aircraft Systems", Eq. 6.40.
    """
    print("  - Calculating Fuselage Weight (Gundlach Eq. 6.40)...")
    F_MG = 1.07    # Main gear on fuselage
    F_NG = 1.04    # Nose gear on fuselage
    F_press = 1.0  # Unpressurized
    F_VT = 1.0     # V-tail weight is calculated separately
    F_matl = 1.0   # Carbon fiber/metal

    L_struct_ft = m_to_ft(params.fuselage.l_f)
    W_carried_lbf = N_to_lbf(params.weight.W_PL)
    N_Z = params.max_load_factor
    V_EqMax_kts = params.max_eq_velocity

    # CORRECTED FORMULA: Reverting to the normalized velocity term as it is
    # required to get a sensible result from this empirical formula.
    W_fus_lb = (
        0.5257 * F_MG * F_NG * F_press * F_VT * F_matl
        * (L_struct_ft ** 0.3796)
        * ((W_carried_lbf * N_Z) ** 0.4863)
        * (V_EqMax_kts / 100.0)**2 # TODO, do not understand why this is divided by 100, but impossible to get a sensible result without it.
    )
    return lbf_to_N(W_fus_lb)

def landing_gear_weight_N(params: DesignParameters):
    """
    Calculates landing gear weight as a statistical fraction of MTOW.
    Source: Gundlach, p. 222. 4% is a standard starting point for conventional gear.
    """
    print("  - Calculating Landing Gear Weight (Statistical)...")
    F_lg = 0.04
    W_lg_lb = F_lg * N_to_lbf(params.weight.W_TO)
    return lbf_to_N(W_lg_lb)

def empennage_weight_N(params: DesignParameters):
    """
    Calculates V-tail empennage weight based on your teammate's original script.
    Source: Gundlach, Eq. 6.37-6.39 provide weight-per-area factors.
    The formula resolves projected area weights back to the true panel weight.
    """
    print("  - Calculating Empennage Weight (Original Method)...")
    WA_emp = 0.8
    W_HT_proj_lb = WA_emp * m2_to_ft2(params.empennage.S_h)
    W_VT_proj_lb = WA_emp * m2_to_ft2(params.empennage.S_v)
    
    W_emp_lb = W_HT_proj_lb * math.cos(params.empennage.vtail_dihedral)**2 + \
               W_VT_proj_lb * math.sin(params.empennage.vtail_dihedral)**2
               
    return lbf_to_N(W_emp_lb)

def propulsion_weight_N(params: DesignParameters):
    """
    Calculates propulsion system weight including engine, nacelle, and fuel system.
    """
    print("  - Calculating Propulsion Weight...")
    F_nac = 0.055
    F_fs = 0.692
    E1 = 0.67

    if any(v is None for v in [params.engine.engine_max_thrust, params.weight.W_F, params.engine.engine_weight]):
        print("    - WARNING: Missing parameters for propulsion weight calculation. Returning 0.")
        return 0
        
    T_max_lbf = N_to_lbf(params.engine.engine_max_thrust)
    W_nacelle_lb = F_nac * T_max_lbf
    W_fuel_system_lb = F_fs * N_to_lbf(params.weight.W_F)**E1
    W_propulsion_lb = W_nacelle_lb + N_to_lbf(params.engine.engine_weight) + W_fuel_system_lb
    
    return lbf_to_N(W_propulsion_lb)

def fixed_equipment_weight_N(params: DesignParameters):
    """
    Calculates fixed equipment weight based on your teammate's original script.
    Source: Gundlach 6.3.3
    """
    print("  - Calculating Fixed Equipment Weight (Original Method)...")
    W_autopilot = 50.0
    W_AirDataSystem = 1.0
    W_GPS = 0.5
    W_INS = 22.0
    W_processor = 25.0
    W_wiring = 0.35
    W_line_of_sight = 2.0
    W_SATCOM = 85.0
    W_avionics_lb = W_autopilot + W_AirDataSystem + W_GPS + W_INS + W_processor + W_wiring + W_line_of_sight + W_SATCOM

    F_FCS = 0.0002
    W_FCS_lb = F_FCS * m2_to_ft2(params.control_surface.S_a) * (params.max_eq_velocity)**2
    
    W_fixed_equipment_lb = W_avionics_lb + W_FCS_lb
    return lbf_to_N(W_fixed_equipment_lb)

def get_final_weight_breakdown(params: DesignParameters) -> dict:
    """
    Calculates the final weight of each component based on the converged design
    and returns a dictionary with the breakdown.
    """
    print("\n--- Generating Final Weight Breakdown ---")
    
    weights = {
        "W_wing": wing_weight_N(params),
        "W_fuselage": fuselage_weight_N(params),
        "W_landing_gear": landing_gear_weight_N(params),
        "W_empennage": empennage_weight_N(params),
        "W_propulsion": propulsion_weight_N(params),
        "W_fixed_equipment": fixed_equipment_weight_N(params),
    }

    W_E_calc = sum(weights.values())
    W_OE_calc = W_E_calc + params.weight.W_crew # Operating Empty Weight includes crew weight, but it's 0 as it's a UAS
    weights["W_E_calculated"] = W_E_calc
    weights["W_OE_calculated"] = W_OE_calc
    
    print(f"\n  Calculated Empty Weight (W_E): {W_E_calc:.2f} N")
    print(f"  Calculated Op. Empty Weight (W_OE): {W_OE_calc:.2f} N")
    
    return weights

# # ==============================================================================
# # CLASS II WEIGHT ESTIMATION LOOP (MOVED FROM main_class_II.py)
# # ==============================================================================
# def class_II_weight_estimation(params: DesignParameters,
#                                initial_W_TO_N_guess: float,
#                                max_iterations: int = 100,
#                                tolerance: float = 0.005) -> dict:
#     """
#     Iteratively calculates the MTOW based on detailed component weight estimations (Class II).
#     This loop continues until the calculated MTOW converges.

#     Parameters:
#         params (DesignParameters): The main design parameters object.
#         initial_W_TO_N_guess (float): An initial guess for the MTOW in Newtons.
#         max_iterations (int): The maximum number of iterations to perform.
#         tolerance (float): The convergence tolerance for the relative difference in MTOW.

#     Returns:
#         dict: A dictionary containing the final converged weights and convergence status.
#     """
#     if initial_W_TO_N_guess is None:
#         print("Error: Initial W_TO guess is None. Aborting weight estimation.")
#         return {"W_TO": 0, "converged": False}

#     W_TO_N_current = initial_W_TO_N_guess
#     params.weight.W_TO = W_TO_N_current
#     print(f"Starting Class II Weight Estimation with initial WTO: {W_TO_N_current:.2f} N")

#     for i in range(max_iterations):
#         print(f"\nWeight Iteration {i+1}:")
#         # Recalculate empty weight based on the current W_TO_N_current
#         W_empty_N_calculated = (
#             wing_weight_N(params) +
#             landing_gear_weight_N(params) +
#             empennage_weight_N(params) +
#             propulsion_weight_N(params) +
#             fixed_equipment_weight_N(params) +
#             fuselage_weight_N(params)
#         )

#         W_OE_N = W_empty_N_calculated + params.weight.W_crew
        
#         if params.weight.M_ff is None or params.weight.M_ff <= 0 or params.weight.M_ff >= 1:
#             print("Error: Invalid M_ff value for weight calculation. Aborting.")
#             return {"W_TO": W_TO_N_current, "converged": False}
        
#         W_TO_N_new = (W_OE_N + params.weight.W_PL) / params.weight.M_ff

#         relative_difference = abs(W_TO_N_new - W_TO_N_current) / W_TO_N_current
#         print(f"  - Iteration {i+1} Summary: W_TO_current = {W_TO_N_current:.2f} N, W_empty_calc = {W_empty_N_calculated:.2f} N, W_OE_calc = {W_OE_N:.2f}, W_TO_new = {W_TO_N_new:.2f} N, Rel_Diff = {relative_difference:.6f}")
        
#         if relative_difference < tolerance:
#             print(f"\nClass II WTO converged in {i+1} iterations.")
#             params.weight.W_TO = W_TO_N_new
#             return {
#                 "W_TO": W_TO_N_new,
#                 "W_E": W_empty_N_calculated,
#                 "W_OE": W_OE_N,
#                 "W_F": W_TO_N_new * (1 - params.weight.M_ff),
#                 "converged": True,
#                 "iterations": i + 1
#             }
        
#         W_TO_N_current = W_TO_N_new
#         params.weight.W_TO = W_TO_N_current

#     print(f"Class II WTO did not converge after {max_iterations} iterations.")
#     params.weight.W_TO = W_TO_N_current
#     return {
#         "W_TO": W_TO_N_current,
#         "W_E": W_empty_N_calculated,
#         "W_OE": W_OE_N,
#         "W_F": W_TO_N_current * (1 - params.weight.M_ff),
#         "converged": False,
#         "iterations": max_iterations
#     }

