import math
import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
#from design_variables import DesignParameters

# --- Constants ---
G = 9.80665  # Acceleration due to gravity (m/s^2)

def calculate_cruise_dynamic_pressure_lbf_ft2(params) -> float:
    """
    Calculate cruise dynamic pressure in lbf/ft² using cruise conditions.
    
    Parameters:
    params (DesignParameters): Design parameters object
    
    Returns:
    float: Dynamic pressure in lbf/ft²
    """
    # Calculate dynamic pressure in SI units (Pa)
    q_cruise_Pa = 0.5 * params.cruise_density * params.cruise_speed**2
    
    # Convert to imperial units (lbf/ft²)
    q_cruise_lbf_ft2 = Pa_to_lbf_ft2(q_cruise_Pa)
    
    return q_cruise_lbf_ft2

def wing_weight_N(params): # Torenbeek light transport aircraft method
    """
    Calculates wing weight based on the Torenbeek method for light transport aircraft.
    Source: Torenbeek, "Advanced Aircraft Design", Appendix C.
    NOTE: This formula is empirical and requires imperial units (lbf, ft).
    """
    #print("  - Calculating Wing Weight (Torenbeek)...") # Removed so that it doesnt print in iterations.
    #print(f"W_TO: {params.weight.W_TO}, b_w_ft: {params.wing.b_w}, Lambda_05_w: {np.rad2deg(params.wing.Lambda_05_w)}, ")
    W_TO_lb = N_to_lbf(params.weight.W_TO)
    b_w_ft = m_to_ft(params.wing.b_w)
    S_w_ft2 = m2_to_ft2(params.wing.S_w)
    
    # Ultimate load factor
    N_z = params.max_load_factor * 1.5  # Ultimate load factor is typically 1.5 times the maximum load factor
    if params.wing.root_chord is None or params.wing.t_c_w_r is None:
        print("    - WARNING: Wing root chord or t/c ratio not defined. Cannot calculate wing weight.")
        return 0
    # Correctly calculates root thickness in feet
    t_r_ft = m_to_ft(params.wing.root_chord * params.wing.t_c_w_r) # This is a parameter on design_parameters, but goot to calculate it here for clarity.
    
    if any(v is None for v in [W_TO_lb, b_w_ft, params.wing.Lambda_05_w, params.max_load_factor, S_w_ft2, t_r_ft]):
        print("    - WARNING: Missing parameters for wing weight calculation. Returning 0.")
        return 0

    #print(f"Using parameters for wing weight calculation: W_TO_lb: {params.weight.W_TO}, b_w_ft: {params.wing.b_w}, Lambda_05_w: {np.rad2deg(params.wing.Lambda_05_w)}, "
          #f"max_load_factor: {params.max_load_factor}, S_w_ft2: {params.wing.S_w}, t_r_ft: {t_r_ft}, N_z: {N_z}, lambda_w: {params.wing.lambda_w}")
    
    # CORRECTED FORMULA: All weight/force terms now use W_TO_lb
    W_wing_lb = 0.00125 * W_TO_lb * (b_w_ft / math.cos(params.wing.Lambda_05_w))**0.75 * \
                (1 + (6.3 * math.cos(params.wing.Lambda_05_w) / b_w_ft)**0.5) * \
                N_z**0.55 * \
                (S_w_ft2 * b_w_ft / (t_r_ft * W_TO_lb * math.cos(params.wing.Lambda_05_w)))**0.3
    
    return lbf_to_N(W_wing_lb)

def wing_weight_N_z(params): # Torenbeek not so light transport aircraft method
    """
    Calculates wing weight based on the Torenbeek method for light transport aircraft.
    Source: Torenbeek, "Advanced Aircraft Design", Appendix C. NO!?
    NOTE: This formula is empirical and requires imperial units (lbf, ft).
    """
    #print("  - Calculating Wing Weight (Torenbeek)...") # Removed so that it doesnt print in iterations.
    W_ZFW_lb = N_to_lbf(params.weight.W_TO - params.weight.W_F)
    b_w_ft = m_to_ft(params.wing.b_w)
    S_w_ft2 = m2_to_ft2(params.wing.S_w)
    
    # Ultimate load factor
    N_z = params.max_load_factor * 1.5  # Ultimate load factor is typically 1.5 times the maximum load factor
    if params.wing.root_chord is None or params.wing.t_c_w_r is None:
        print("    - WARNING: Wing root chord or t/c ratio not defined. Cannot calculate wing weight.")
        return 0
    # Correctly calculates root thickness in feet
    t_r_ft = m_to_ft(params.wing.root_chord * params.wing.t_c_w_r) # This is a parameter on design_parameters, but goot to calculate it here for clarity.
    
    if any(v is None for v in [W_ZFW_lb, b_w_ft, params.wing.Lambda_05_w, params.max_load_factor, S_w_ft2, t_r_ft]):
        print("    - WARNING: Missing parameters for wing weight calculation. Returning 0.")
        return 0

    # CORRECTED FORMULA: All weight/force terms now use W_TO_lb
    W_wing_lb = 0.0017 * W_ZFW_lb * (b_w_ft / math.cos(params.wing.Lambda_05_w))**0.75 * \
                (1 + (6.3 * math.cos(params.wing.Lambda_05_w) / b_w_ft)**0.5) * \
                N_z**0.55 * \
                (S_w_ft2 * b_w_ft / (t_r_ft * W_ZFW_lb * math.cos(params.wing.Lambda_05_w)))**0.3
    
    return lbf_to_N(W_wing_lb)

def wing_weight_N_z(params): # Raymer Cargo Aircraft Method, Page 402, Eq 15.25
    """
    Calculates wing weight based on the updated empirical formula.
    Formula: W_wing = 0.0051(W_dg*N_z)^0.557 * S_w^0.649 * A^0.5 * (t/c)_root^-0.4 * (1 + λ)^0.1 * (cosΛ)^-1.0 * S_csw^0.1
    
    Where:
    - W_dg = design gross weight (lb)
    - N_z = ultimate load factor
    - S_w = wing area (ft²)
    - A = aspect ratio
    - (t/c)_root = thickness-to-chord ratio at root
    - λ = taper ratio
    - Λ = quarter-chord sweep angle (rad)
    - S_csw = control surface area (ft²)
    
    NOTE: This formula is empirical and requires imperial units (lbf, ft).
    """
        #print("  - Calculating Wing Weight (Updated Formula)...")
    
    # Convert to imperial units
    W_TO_lb = N_to_lbf(params.weight.W_TO)
    S_w_ft2 = m2_to_ft2(params.wing.S_w)

    # Get Aspect Ratio
    A_w = params.wing.A_w_target # Ok to use target, its updated from the wing planform optimization
    #print(f"Aspect Ratio (A_w): {A_w}")
    lambda_w = params.wing.lambda_w # Taper ratio
    Lambda_qc = params.wing.Lambda_025c_w

    # Ultimate load factor
    N_z = params.max_load_factor * 1.5
    # Get control surface area and convert to ft²
    S_csw_ft2 = m2_to_ft2(params.control_surface.S_a)
    W_wing_lb = (0.0051 * 
                (W_TO_lb * N_z)**0.557 * 
                S_w_ft2**0.649 * 
                A_w**0.5 * 
                (params.wing.t_c_w_r)**(-0.4) * 
                (1 + lambda_w)**0.1 * 
                (math.cos(Lambda_qc))**(-1.0) * 
                S_csw_ft2**0.1)

    return lbf_to_N(W_wing_lb)

def wing_weight_N_z(params): # General Aviation weights
    """
    Calculates wing weight based on the updated empirical formula (Equation 15.46), Page 402 Raymer.
    Formula: W_wing = 0.036 * S_w^0.758 * W_fw^0.0415 * (A/cos²Λ)^0.6 * q^0.006 * λ^0.04 * (100*t/c/cosΛ)^-0.3 * (N_z*W_dg)^0.49
    
    Where:
    - S_w = wing area (ft²)
    - W_fw = fuel weight (lb)
    - A = aspect ratio
    - Λ = quarter-chord sweep angle (rad)
    - q = dynamic pressure at cruise (lbf/ft²)
    - N_u = ultimate load factor (assumed same as N_z)
    - t/c = thickness-to-chord ratio at root
    - N_z = load factor
    - W_dg = design gross weight (lb)
    
    NOTE: This formula is empirical and requires imperial units (lbf, ft).
    """
    #print("  - Calculating Wing Weight (Updated Formula 15.46)...")
    
    # Convert to imperial units
    W_TO_lb = N_to_lbf(params.weight.W_TO)
    W_fuel_lb = N_to_lbf(params.weight.W_F)
    S_w_ft2 = m2_to_ft2(params.wing.S_w)
    
    # Calculate dynamic pressure at cruise in lbf/ft²
    q_cruise_lbf_ft2 = calculate_cruise_dynamic_pressure_lbf_ft2(params)

    # Get aspect ratio (prefer target, fall back to actual)
    A_w = params.wing.A_w_target
    
    # Get quarter-chord sweep angle
    Lambda_qc = params.wing.Lambda_025c_w
    
    # Get taper ratio
    lambda_w = params.wing.lambda_w  # Taper ratio
    # Calculate wing weight using the updated formula (Equation 15.46)
    cos_Lambda = math.cos(Lambda_qc)
    
    N_z = params.max_load_factor * 1.5  # Ultimate load factor, assumed same as N_z
    # Calculate each term
    term1 = S_w_ft2**0.758
    term2 = W_fuel_lb**0.0035
    term3 = (A_w / (cos_Lambda**2))**0.6
    term4 = q_cruise_lbf_ft2**0.006
    term5 = lambda_w**0.04  
    term6 = (100 * params.wing.t_c_w_r / cos_Lambda)**(-0.3)
    term7 = (N_z * W_TO_lb)**0.49
    
    W_wing_lb = 0.036 * term1 * term2 * term3 * term4 * term5 * term6 * term7
    
    # Convert back to Newtons
    return lbf_to_N(W_wing_lb)
    
def fuselage_weight_N(params):
    """
    Calculates fuselage weight using the Gundlach statistical method.
    Source: Gundlach, "Designing Unmanned Aircraft Systems", Eq. 6.40.
    """
    #print("  - Calculating Fuselage Weight (Gundlach Eq. 6.40)...")
    F_MG = 1.07    # Main gear on fuselage
    F_NG = 1.04    # Nose gear on fuselage
    F_press = 1.0  # Unpressurized
    F_VT = 1.0     # V-tail weight is calculated separately
    F_matl = 1.0   # Carbon fiber/metal

    L_struct_ft = m_to_ft(params.fuselage.l_f)
    W_carried_lbf = N_to_lbf(params.weight.W_PL + landing_gear_weight_N(params) + fixed_equipment_weight_N(params) + propulsion_weight_N(params))
    N_Z = params.max_load_factor * 1.5  # Ultimate load factor is typically 1.5 times the maximum load factor
    V_EqMax_kts = params.max_eq_velocity
    V_cruise_kts = ms_to_kts(params.cruise_speed)
    V_dive_kts = 1.05 * V_cruise_kts  # Dive speed is 1.25 times cruise speed -> Would be supersonic, change to 1.0
    V_dive_Eq_kts = true_to_equivalent_air_speed(V_dive_kts, params.cruise_density, 1.225)
    # CORRECTED FORMULA: As per Elise's findings, EQ on book was incorrect.
    W_fus_lb = (
        0.5257 * F_MG * F_NG * F_press * F_VT * F_matl
        * (L_struct_ft ** 0.3796)
        * ((W_carried_lbf * N_Z) ** 0.4863)
        * (0.8 * V_dive_Eq_kts / 100.0)**2 # Equation 6.40 on Gundlach is incorrect! Elise found the corrected and it's like this.
    )
    #print(f"V_dive_Eq_kts: {V_dive_Eq_kts}, V_EqMax_kts: {V_EqMax_kts}, V_dive_kts: {V_dive_kts}")
    return lbf_to_N(W_fus_lb)

def landing_gear_weight_N(params):
    """
    Calculates landing gear weight as a statistical fraction of MTOW.
    Source: Gundlach, p. 222. 4% is a standard starting point for conventional gear.
    """
    #print("  - Calculating Landing Gear Weight (Statistical)...")
    F_lg = 0.04
    W_lg_lb = F_lg * N_to_lbf(params.weight.W_TO)
    return lbf_to_N(W_lg_lb)

def empennage_weight_N(params):
    """
    Calculates V-tail empennage weight based on your teammate's original script.
    Source: Gundlach, Eq. 6.37-6.39 provide weight-per-area factors.
    The formula resolves projected area weights back to the true panel weight.
    """
    #print("  - Calculating Empennage Weight (Original Method)...")
    WA_emp = 3  # Weight per area factor for empennage (lb/ft²)
    W_HT_proj_lb = WA_emp * m2_to_ft2(params.empennage.S_h)
    W_VT_proj_lb = WA_emp * m2_to_ft2(params.empennage.S_v)
    
    W_emp_lb = W_HT_proj_lb * math.cos(params.empennage.vtail_dihedral)**2 + \
               W_VT_proj_lb * math.sin(params.empennage.vtail_dihedral)**2
               
    return lbf_to_N(W_emp_lb)

def empennage_weight_N_z(params):
    # Use minimum gauge method for UAV
    F_Emp = 1.3
    F_Cont = 1.2
    S_Emp_ft2 = m2_to_ft2(params.empennage.S_t)  # Total tail area
    t_Min_in = 0.04  # Minimum gauge thickness (inches) for UAV
    rho_Matl_lb_ft3 = 169  # Aluminum density (lb/ft³)
    
    W_emp_lb = (1/6) * F_Emp * F_Cont * S_Emp_ft2 * t_Min_in * rho_Matl_lb_ft3
    
    return lbf_to_N(W_emp_lb)

def propulsion_weight_N(params):
    """
    Calculates propulsion system weight including engine, nacelle, and fuel system.
    """
    #print("  - Calculating Propulsion Weight...")
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

def fixed_equipment_weight_N(params):
    """
    Calculates fixed equipment weight based on your teammate's original script.
    Source: Gundlach 6.3.3
    """
    #print("  - Calculating Fixed Equipment Weight (Original Method)...")
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

def get_final_weight_breakdown(params) -> dict:
    """
    Calculates the final weight of each component based on the converged design
    and returns a dictionary with the breakdown.
    """
    #print("\n--- Generating Final Weight Breakdown ---")
    
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
