import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

# --- Constants ---
G0 = 9.80665  # Standard gravity (m/s^2)
R_AIR = 287.058  # Specific gas constant for dry air (J/(kg·K))
GAMMA_AIR = 1.4  # Ratio of specific heats for air
T0_ISA = 288.15  # Sea level standard temperature (K)
P0_ISA = 101325.0  # Sea level standard pressure (Pa)
RHO0_ISA = P0_ISA / (R_AIR * T0_ISA) # Sea level standard density (kg/m^3)
LAPSE_RATE_ISA = 0.0065  # Temperature lapse rate in troposphere (K/m)
TROPOPAUSE_ALT_M = 11000.0  # Altitude of tropopause (m)
T_TROPOPAUSE = T0_ISA - LAPSE_RATE_ISA * TROPOPAUSE_ALT_M

# Sutherland's Law constants for viscosity
C1_SUTHERLAND = 1.458e-6  # kg / (m·s·K^0.5)
S_SUTHERLAND = 110.4     # K

# --- Helper Functions ---
def get_atmospheric_properties(altitude_m):
    """
    Calculates atmospheric properties (temperature, pressure, density, speed of sound, viscosity)
    at a given altitude based on a simplified ISA model.
    """
    properties = {}
    if altitude_m <= TROPOPAUSE_ALT_M:
        properties['temperature_K'] = T0_ISA - LAPSE_RATE_ISA * altitude_m
        properties['pressure_Pa'] = P0_ISA * (properties['temperature_K'] / T0_ISA)**(G0 / (LAPSE_RATE_ISA * R_AIR))
    else: # Stratosphere (isothermal layer in simplified ISA)
        properties['temperature_K'] = T_TROPOPAUSE
        pressure_tropopause = P0_ISA * (T_TROPOPAUSE / T0_ISA)**(G0 / (LAPSE_RATE_ISA * R_AIR))
        properties['pressure_Pa'] = pressure_tropopause * math.exp(-G0 * (altitude_m - TROPOPAUSE_ALT_M) / (R_AIR * T_TROPOPAUSE))

    properties['density_kg_m3'] = properties['pressure_Pa'] / (R_AIR * properties['temperature_K'])
    properties['speed_of_sound_m_s'] = math.sqrt(GAMMA_AIR * R_AIR * properties['temperature_K'])
    
    # Dynamic viscosity using Sutherland's Law
    T = properties['temperature_K']
    properties['viscosity_Pa_s'] = C1_SUTHERLAND * (T**1.5) / (T + S_SUTHERLAND) # kg/(m·s) or Pa·s
    
    return properties

# --- Main Calculation Functions ---

def calculate_initial_planform_params(M_cruise, M_star, S_m2, A):
    """
    Calculates initial wing planform parameters, including dihedral.
    Formulas are based on Section 2.4 of A05_WP2.pdf.
    M_star is a technology factor for supercritical airfoils (e.g., 0.935).

    Args:
        M_cruise (float): Cruise Mach number.
        M_star (float): Technology factor for supercritical airfoils.
        S_m2 (float): Wing surface area in square meters.
        A (float): Aspect ratio.

    Returns:
        dict: A dictionary containing the calculated planform parameters.
              Returns None if an invalid calculation occurs (e.g., math domain error).
    """
    params = {}
    params['M_cruise'] = M_cruise
    params['M_star'] = M_star 
    params['S_ref_m2'] = S_m2 
    params['AR'] = A       

    # 1. Quarter-chord Sweep Angle (Lambda_c4) (A05_WP2.pdf, Eq. 2.1)
    denominator_lambda_c4 = M_cruise + 0.03 # TODO, might use 0.015, as per Vargas and Vos. 
    if denominator_lambda_c4 == 0:
        print("Error: Denominator for Lambda_c4 calculation is zero.")
        return None
    
    cos_Lambda_c4_val = 0.75 * M_star / denominator_lambda_c4 # TODO, formula is for half-chord sweep, not quarter-chord
    if not (-1 <= cos_Lambda_c4_val <= 1):
        print(f"Error: Invalid value for acos for Lambda_c4: {cos_Lambda_c4_val}. Check M_cruise and M_star inputs.")
        return None
    Lambda_c4_rad = math.acos(cos_Lambda_c4_val)
    params['Lambda_c4_deg'] = math.degrees(Lambda_c4_rad)
    params['Lambda_c4_rad'] = Lambda_c4_rad

    # 2. Wing Span (b) (A05_WP2.pdf, Eq. 2.2)
    if S_m2 < 0 or A < 0:
        print("Error: Wing surface area (S) and Aspect ratio (A) must be non-negative.")
        return None
    b_m = math.sqrt(S_m2 * A)
    params['b_m'] = b_m

    # 3. Taper Ratio (lambda_taper) (A05_WP2.pdf, Eq. 2.3)
    lambda_taper = 0.2 * (2 - params['Lambda_c4_deg'] * math.pi / 180.0) # Lambda_c4_deg used here
    params['lambda_taper'] = lambda_taper

    # 4. Root Chord (Cr_m) (A05_WP2.pdf, Eq. 2.4)
    denominator_cr = (1 + lambda_taper) * b_m
    if denominator_cr == 0: 
        print("Error: Denominator for Cr calculation is zero.")
        return None
    Cr_m = (2 * S_m2) / denominator_cr
    params['Cr_m'] = Cr_m

    # 5. Tip Chord (Ct_m) (A05_WP2.pdf, Eq. 2.5)
    Ct_m = lambda_taper * Cr_m
    params['Ct_m'] = Ct_m

    # 6. Leading Edge Sweep Angle (Lambda_LE) (A05_WP2.pdf, Eq. 2.6)
    if b_m == 0:
        print("Error: Wing span (b) is zero, cannot calculate LE sweep.")
        return None
    tan_Lambda_LE = math.tan(Lambda_c4_rad) + (Cr_m / (2 * b_m)) * (1 - lambda_taper)
    Lambda_LE_rad = math.atan(tan_Lambda_LE)
    params['Lambda_LE_deg'] = math.degrees(Lambda_LE_rad)
    params['Lambda_LE_rad'] = Lambda_LE_rad

    # 7. Mean Aerodynamic Chord (MAC_m) (A05_WP2.pdf, Eq. 2.7)
    denominator_cmac = (1 + lambda_taper)
    if denominator_cmac == 0:
        print("Error: Denominator for MAC calculation is zero.")
        return None
    MAC_m = (2.0/3.0) * Cr_m * ((1 + lambda_taper + lambda_taper**2) / denominator_cmac)
    params['MAC_m'] = MAC_m 

    # 8. Y-position of MAC (y_MAC_m) - Spanwise location from centerline (A05_WP2.pdf, Eq. 2.8)
    y_MAC_m = (b_m / 6.0) * ((1 + 2 * lambda_taper) / denominator_cmac) 
    params['y_MAC_m'] = y_MAC_m

    # 9. X-position of Leading Edge of MAC (x_LEMAC_m) - Chordwise location from root LE line (A05_WP2.pdf, Eq. 2.9)
    x_LEMAC_m = y_MAC_m * math.tan(Lambda_LE_rad)
    params['x_LEMAC_m'] = x_LEMAC_m
    
    # Average Chord (Summary Doc, p.9, Eq. 1.10 - consistent with A05_WP2.pdf values)
    params['C_avg_m'] = (Cr_m + Ct_m) / 2.0

    # Mid-chord sweep (Summary Doc, p.9, Eq. 1.16 - used for CLalpha calculation)
    tan_Lambda_05c = math.tan(Lambda_LE_rad) - (4/A) * (0.5 * (1-lambda_taper)/(1+lambda_taper))
    Lambda_05c_rad = math.atan(tan_Lambda_05c)
    params['Lambda_05c_deg'] = math.degrees(Lambda_05c_rad)
    params['Lambda_05c_rad'] = Lambda_05c_rad
    
    # 10. Dihedral Angle (Gamma_deg) (A05_WP2.pdf, Eq. 2.10)
    Gamma_deg = 5 - (params['Lambda_c4_deg'] / 10.0) # Lambda_c4_deg used here
    params['Gamma_deg'] = Gamma_deg

        # 4. Tip stall check (Summary Doc, p.11, Eq. 1.18)
    if params['AR'] > 17.7 * (2 - params['lambda_taper']) * math.exp(-0.043 * Lambda_c4_rad):
         print("Warning: Low Aspect Ratio or high taper ratio. Tip stall may occur.")

    
    return params

def calculate_airfoil_and_cruise_params(planform_params, W_estim_N, alt_cruise_m, 
                                        tc_root, tc_tip, selected_airfoil_family_data):
    """
    Step 2: Airfoil Selection and Definition
    Calculates cruise dynamic pressure, target lift coefficients, and defines airfoil properties.
    """
    cruise_params = {}
    M_cruise = planform_params['M_cruise']
    S_ref_m2 = planform_params['S_ref_m2']
    Lambda_c4_rad = planform_params['Lambda_c4_rad']

    # 1. Atmospheric Properties at Cruise
    atm_props = get_atmospheric_properties(alt_cruise_m)
    cruise_params.update(atm_props) 

    # 2. Dynamic Pressure (q_cruise)
    V_cruise = M_cruise * atm_props['speed_of_sound_m_s']
    q_cruise = 0.5 * atm_props['density_kg_m3'] * V_cruise**2
    cruise_params['V_cruise_m_s'] = V_cruise
    cruise_params['q_cruise_Pa'] = q_cruise

    # 3. Target Wing Design Lift Coefficient (C_L_des) (Summary Doc, p.11)
    wing_loading_Pa = W_estim_N / S_ref_m2
    cruise_params['wing_loading_Pa'] = wing_loading_Pa
    C_L_des = 1.1 * wing_loading_Pa / q_cruise 
    cruise_params['C_L_des'] = C_L_des

    # 4. Target Airfoil Design Lift Coefficient (C_l_des) (Summary Doc, p.12)
    cos_Lambda_c4_sq = math.cos(Lambda_c4_rad)**2
    if cos_Lambda_c4_sq == 0:
        print("Error: cos^2(Lambda_c4) is zero in C_l_des calculation.")
        C_l_des = float('inf')
    else:
        C_l_des = C_L_des / cos_Lambda_c4_sq
    cruise_params['C_l_des'] = C_l_des

    # 5. Airfoil Selection & Properties
    cruise_params['selected_airfoil_family'] = selected_airfoil_family_data['name']
    cruise_params['Cl_max_airfoil_estim'] = selected_airfoil_family_data['Cl_max']
    cruise_params['Cm0_airfoil_estim'] = selected_airfoil_family_data['Cm0']
    cruise_params['ka_airfoil_tech_factor'] = selected_airfoil_family_data['ka']
    cruise_params['xc_max_thick_airfoil'] = selected_airfoil_family_data['xc_max_thick']

    # 6. Define Thickness-to-Chord Ratio (t/c)
    cruise_params['tc_root'] = tc_root
    cruise_params['tc_tip'] = tc_tip
    y_mac_norm = planform_params['y_MAC_m'] / (planform_params['b_m'] / 2.0) if planform_params['b_m'] !=0 else 0
    tc_mac = tc_root * (1 - y_mac_norm) + tc_tip * y_mac_norm
    cruise_params['tc_MAC'] = tc_mac
    cruise_params['tc_avg'] = tc_mac 

    return cruise_params

def estimate_wing_lift_characteristics(planform_params, cruise_params, eta_airfoil_eff=0.95):
    """
    Step 3: Estimate Wing Lift Characteristics
    """
    lift_params = {}
    AR = planform_params['AR']
    Lambda_05c_rad = planform_params['Lambda_05c_rad'] 
    M_cruise = planform_params['M_cruise']
    Cl_max_airfoil_estim = cruise_params['Cl_max_airfoil_estim']
    Lambda_c4_rad = planform_params['Lambda_c4_rad']

    # 1. Prandtl-Glauert Compressibility Factor (beta_PG)
    if M_cruise >= 1.0:
        beta_PG = 0 
    else:
        beta_PG = math.sqrt(1 - M_cruise**2)
    lift_params['beta_PG'] = beta_PG

    # 2. Wing Lift Curve Slope (C_L_alpha per radian) (Summary Doc, p.13, Eq. 2.1)
    if beta_PG == 0 and M_cruise >=1.0: # Supersonic, DATCOM formula not directly applicable
        C_L_alpha_per_rad = (4 / math.sqrt(M_cruise**2 - 1)) * (1 - (1/(2*AR*math.sqrt(M_cruise**2-1)))) # Ackeret theory approx for unswept
        print(f"Warning: Supersonic M_cruise. Using Ackeret-like CLa approx: {C_L_alpha_per_rad:.3f}")
    elif beta_PG == 0 and M_cruise < 1.0: # M_cruise is 1.0
         C_L_alpha_per_rad = 0 # Undefined or needs special handling
         print("Warning: M_cruise is 1.0, C_L_alpha is problematic with this formula.")
    else:
        term_A_beta_eta = (AR * beta_PG / eta_airfoil_eff)**2
        term_tan_sweep = (math.tan(Lambda_05c_rad)**2) / (beta_PG**2) 
        denominator_cla = 2 + math.sqrt(4 + term_A_beta_eta * (1 + term_tan_sweep))
        if denominator_cla == 0:
            C_L_alpha_per_rad = 0
        else:
            C_L_alpha_per_rad = (2 * math.pi * AR) / denominator_cla
    lift_params['C_L_alpha_per_rad'] = C_L_alpha_per_rad
    lift_params['C_L_alpha_per_deg'] = math.degrees(C_L_alpha_per_rad)

    # 3. Clean Wing Maximum Lift Coefficient (C_L_max_clean) (Summary Doc, p.14, Eq. 2.5)
    C_L_max_clean = 0.9 * Cl_max_airfoil_estim * math.cos(Lambda_c4_rad)
    lift_params['C_L_max_clean'] = C_L_max_clean


    return lift_params

def estimate_zero_lift_drag(planform_params, cruise_params, W_estim_N, 
                            component_geometries, k_surface_roughness_m):
    """
    Step 4a: Estimate Zero-Lift Drag (CD0)
    Uses component build-up method from Summary Doc, p.25-28.
    """
    drag_params = {}
    S_ref_m2 = planform_params['S_ref_m2']
    M_cruise = planform_params['M_cruise']
    rho_cruise = cruise_params['density_kg_m3']
    V_cruise = cruise_params['V_cruise_m_s']
    mu_cruise = cruise_params['viscosity_Pa_s']
    C_L_des = cruise_params['C_L_des']
    tc_avg_wing = cruise_params['tc_avg'] 
    ka_airfoil = cruise_params['ka_airfoil_tech_factor']
    xc_max_thick_wing = cruise_params['xc_max_thick_airfoil'] 
    Lambda_c4_rad = planform_params['Lambda_c4_rad']

    CD0_sum_components = 0.0

    for comp_name, geom in component_geometries.items():
        l_c = geom['l_char_m']
        S_wet_c = geom['S_wet_m2']
        tc_c = geom.get('tc_avg', tc_avg_wing if comp_name == 'wing' else 0.1) 
        xc_max_thick_c = geom.get('xc_max_thick', xc_max_thick_wing if comp_name == 'wing' else 0.4)
        Lambda_m_rad_c = geom.get('Lambda_max_thick_rad', Lambda_c4_rad if 'wing' in comp_name or 'tail' in comp_name else 0)
        slenderness_f_c = geom.get('slenderness', (l_c / geom['d_char_m']) if 'd_char_m' in geom and geom['d_char_m'] > 0 else 8.0)

        Re_c_smooth = (rho_cruise * V_cruise * l_c) / mu_cruise if mu_cruise > 0 else float('inf')
        if M_cruise < 1.0:
             Re_c_limit_rough = 38.21 * (l_c / k_surface_roughness_m)**1.053 if k_surface_roughness_m > 0 and l_c > 0 else float('inf')
        else: 
             Re_c_limit_rough = 44.62 * (l_c / k_surface_roughness_m)**1.053 * M_cruise**1.16 if k_surface_roughness_m > 0 and l_c > 0 else float('inf')
        Re_c = min(Re_c_smooth, Re_c_limit_rough)
        if Re_c <= 0: Re_c = 1e5 # Avoid math errors with log/sqrt for zero or negative Re

        percent_lam = geom.get('percent_laminar', 0.05) 
        percent_turb = 1.0 - percent_lam
        
        C_f_laminar = 1.328 / math.sqrt(Re_c)
        comp_corr_turb_cf = (1 + 0.144 * M_cruise**2)**0.65
        C_f_turbulent = 0.455 / ((math.log10(Re_c)**2.58) * comp_corr_turb_cf)
        C_fc = (percent_lam * C_f_laminar) + (percent_turb * C_f_turbulent)

        FF_c = 1.0 
        if comp_name in ['wing', 'horizontal_tail', 'vertical_tail']: 
            term1_ff = 1 + (0.6 / xc_max_thick_c if xc_max_thick_c > 0 else 1.0) * tc_c + 100 * tc_c**4
            term2_ff = 1.34 * M_cruise**0.18 * (math.cos(Lambda_m_rad_c)**0.28)
            FF_c = term1_ff * term2_ff
        elif comp_name == 'fuselage': 
            f = slenderness_f_c
            FF_c = 1 + 60/(f**3 if f > 0 else 1e9) + f/400
        elif comp_name == 'nacelle': 
            f = slenderness_f_c
            FF_c = 1 + (0.35/f if f > 0 else 0)
        
        IF_c = geom.get('IF', 1.0)
        CD0_contrib_c = C_fc * FF_c * IF_c * (S_wet_c / S_ref_m2)
        CD0_sum_components += CD0_contrib_c

    C_D_misc_percent = 0.03 
    C_D_misc = C_D_misc_percent * CD0_sum_components 
    CD0_friction_form = CD0_sum_components + C_D_misc
    drag_params['CD0_friction_form'] = CD0_friction_form

    cos_L_c4 = math.cos(Lambda_c4_rad)
    if cos_L_c4 == 0: 
        M_DD = M_cruise - 0.05 
    else:
        # Ensure tc_avg_wing is used for the wing's t/c in M_DD calculation
        M_DD = (ka_airfoil / cos_L_c4) - \
               (tc_avg_wing / (cos_L_c4**2)) - \
               (C_L_des / (10 * cos_L_c4**3))
    drag_params['M_DD_wing'] = M_DD
    
    delta_CD_wave = 0.0
    if M_cruise > M_DD and M_DD > 0: # Added M_DD > 0 check
        # Formula for M_DD < M (Summary Doc, p.28, graph implies this for M > M_DD)
        # The formula is actually delta_CD = 0.002 * [1 + ((M-M_DD)/0.05)]^2.5 according to workflow
        # The Summary doc p.28 has two formulas for M_cr < M < M_DD and M_DD < M.
        # For M_DD < M: delta_CD = 0.002 * [1 + (M-M_DD)/0.05]^2.5 (from visual interpretation of graph trend)
        # Let's stick to the one from the workflow document.
        delta_CD_wave = 0.0020 * (1 + (M_cruise - M_DD) / 0.05)**2.5
    elif M_cruise > (M_DD - 0.05) and M_DD > 0: # M_cr <= M <= M_DD
        # Summary Doc p.28: delta_CD = 0.002 * [1 + 2.5 * (M_DD - M)/0.05]^-1
        # This formula can lead to very high or negative delta_CD if (M_DD - M) is small and positive.
        # Using a simpler ramp or a fixed value if M_cruise is near M_DD might be more stable for a skeleton.
        # For now, let's use the provided formula from Summary Doc if M_cruise > M_DD.
        # If M_cruise is slightly below M_DD, wave drag is starting.
        # A common simplification is to add 0.0020 if M_cruise is at M_DD.
        # The logic here needs to be robust. If M_DD is very close to M_cruise, the (M_cruise - M_DD)/0.05 term can be small.
        pass


    drag_params['delta_CD_wave'] = delta_CD_wave
    CD0_total = CD0_friction_form + delta_CD_wave
    drag_params['CD0_total'] = CD0_total
    
    return drag_params

def estimate_lift_induced_drag_factor(planform_params):
    """
    Step 4b: Estimate Lift-Induced Drag Factor (K)
    """
    induced_drag_params = {}
    AR = planform_params['AR']
    Lambda_LE_rad = planform_params['Lambda_LE_rad']

    # 1. Oswald Efficiency Factor (e) (Sammary ADSEE 2nd year, p.29 - for swept wings)
    e_oswald = 4.61 * (1 - 0.045 * AR**0.68) * (math.cos(Lambda_LE_rad)**0.15) - 3.1
    e_oswald = max(0.6, min(0.95, e_oswald))
    induced_drag_params['e_oswald'] = e_oswald

    # 2. Lift-Induced Drag Factor (K)
    K_drag_induced = 1 / (math.pi * AR * e_oswald) if e_oswald > 0 else float('inf')
    induced_drag_params['K_drag_induced'] = K_drag_induced
    
    return induced_drag_params

def conceptual_hld_sizing(planform_params, cruise_params, lift_params, W_estim_N, 
                          V_stall_target_m_s, hld_selection_data):
    """
    Step 5: (Conceptual) High-Lift Device (HLD) Sizing
    """
    hld_params = {}
    C_L_max_clean = lift_params['C_L_max_clean']
    S_ref_m2 = planform_params['S_ref_m2']
    Lambda_hingeline_rad = planform_params.get('Lambda_c4_rad_HLD', planform_params['Lambda_c4_rad'])

    atm_sl = get_atmospheric_properties(0) 
    rho_sl = atm_sl['density_kg_m3']
    q_stall = 0.5 * rho_sl * V_stall_target_m_s**2
    C_L_max_req = (W_estim_N / S_ref_m2) / q_stall if q_stall > 0 else float('inf')
    hld_params['C_L_max_req'] = C_L_max_req

    delta_C_L_max_HLD = C_L_max_req - C_L_max_clean
    hld_params['delta_C_L_max_HLD'] = delta_C_L_max_HLD

    if delta_C_L_max_HLD > 0:
        hld_params['HLD_needed'] = True
        hld_params['HLD_type_selected'] = hld_selection_data['name']
        delta_Cl_max_airfoil_HLD = hld_selection_data['delta_Cl_max']
        
        c_prime_c_ratio = 1.0 # Default for non-Fowler
        if "fowler" in hld_selection_data['name'].lower():
             c_prime_c_ratio = hld_selection_data.get('c_prime_c_ratio', 1.3) 
             # Table 2.2 Summary Doc: Fowler delta_Clmax = 1.3 * c'/c
             # If hld_selection_data['delta_Cl_max'] IS 1.3, then it's the base factor.
             if hld_selection_data['delta_Cl_max'] == 1.3: # Check if it's the base factor
                delta_Cl_max_airfoil_HLD = hld_selection_data['delta_Cl_max'] * c_prime_c_ratio
             else: # Assume the value provided already includes c'/c effect
                pass # delta_Cl_max_airfoil_HLD is already set
             print(f"Note: Fowler flap selected. Using c'/c = {c_prime_c_ratio:.2f}. Effective delta_Cl_max_airfoil_HLD = {delta_Cl_max_airfoil_HLD:.3f}")
        
        denominator_swf_s = 0.9 * delta_Cl_max_airfoil_HLD * math.cos(Lambda_hingeline_rad)
        if denominator_swf_s == 0:
            Swf_S_ratio = float('inf') 
        else:
            Swf_S_ratio = delta_C_L_max_HLD / denominator_swf_s
        hld_params['Swf_S_ratio'] = Swf_S_ratio
    else:
        hld_params['HLD_needed'] = False
        hld_params['HLD_type_selected'] = "None"
        hld_params['Swf_S_ratio'] = 0.0
        
    return hld_params

def plot_wing_planform(params):
    if params is None:
        print("Cannot plot: Parameters are None.")
        return

    Cr = params['Cr_m']
    Ct = params['Ct_m']
    b_half = params['b_m'] / 2.0
    Lambda_LE_rad = params['Lambda_LE_rad'] # Already in radians from calc
    Lambda_c4_rad = params['Lambda_c4_rad'] # Already in radians
    x_LEMAC_plot_coord = params['x_LEMAC_m'] 
    y_MAC_plot_coord = params['y_MAC_m']   
    C_MAC = params['MAC_m']

    # Define plot coordinates
    rle_plot = (0, 0) # Root Leading Edge
    rte_plot = (0, Cr) # Root Trailing Edge
    tle_plot_x = b_half
    tle_plot_y = b_half * math.tan(Lambda_LE_rad) # Tip Leading Edge y-offset from root LE x-axis
    tle_plot = (tle_plot_x, tle_plot_y)
    tte_plot_x = b_half
    tte_plot_y = tle_plot_y + Ct # Tip Trailing Edge y-offset
    tte_plot = (tte_plot_x, tte_plot_y)

    wing_x_coords = [rle_plot[0], tle_plot[0], tte_plot[0], rte_plot[0], rle_plot[0]]
    wing_y_coords = [rle_plot[1], tle_plot[1], tte_plot[1], rte_plot[1], rle_plot[1]]

    # Quarter-chord line coordinates
    qc_root_y = Cr / 4.0
    qc_root_plot = (0, qc_root_y)
    qc_tip_plot_x = b_half
    # y-coordinate of tip quarter-chord point relative to root LE x-axis
    qc_tip_plot_y = qc_root_y + b_half * math.tan(Lambda_c4_rad) 
    qc_tip_plot = (qc_tip_plot_x, qc_tip_plot_y)
    
    qc_line_x_coords = [qc_root_plot[0], qc_tip_plot[0]]
    qc_line_y_coords = [qc_root_plot[1], qc_tip_plot[1]]

    fig, ax = plt.subplots(figsize=(10, 7)) # Adjusted figure size
    ax.plot(wing_x_coords, wing_y_coords, 'k-', lw=1.5, label="Wing Outline")
    ax.plot(qc_line_x_coords, qc_line_y_coords, 'b:', lw=1.0, label="Quarter-Chord Line") 

    # Plot MAC
    mac_le_x_coord_plot = y_MAC_plot_coord # Spanwise position
    mac_le_y_coord_plot = x_LEMAC_plot_coord # Chordwise position of MAC LE
    mac_te_y_coord_plot = mac_le_y_coord_plot + C_MAC
    
    ax.plot([mac_le_x_coord_plot, mac_le_x_coord_plot], [mac_le_y_coord_plot, mac_te_y_coord_plot], 'r-', lw=1.5, label=f"MAC ({C_MAC:.2f}m)")
    ax.plot(mac_le_x_coord_plot, mac_le_y_coord_plot, 'ro', ms=5)
    ax.text(mac_le_x_coord_plot + 0.02 * b_half, mac_le_y_coord_plot + C_MAC / 2, f"MAC\n{C_MAC:.2f}m", color='red', ha='left', va='center', fontsize=9)


    # Annotations and Dimensions
    ax.text(0, Cr / 2, f"$C_r$: {Cr:.2f}m", ha='right', va='center', fontsize=9, color='darkblue', transform=ax.transData)
    ax.text(b_half, tle_plot_y + Ct / 2, f"$C_t$: {Ct:.2f}m", ha='left', va='center', fontsize=9, color='darkblue', transform=ax.transData)
    ax.text(b_half / 2, -0.1 * Cr, f"b/2: {b_half:.2f}m", ha='center', va='bottom', fontsize=9, color='darkgreen')
    
    # Sweep Angle Annotations    
    ax.text(0.05 * b_half, 0.05 * Cr, f"$\\Lambda_{{LE}}$: {params['Lambda_LE_deg']:.1f}°", fontsize=9, color='purple')
    ax.text(0.05 * b_half, Cr/4 + 0.05 * Cr, f"$\\Lambda_{{c/4}}$: {params['Lambda_c4_deg']:.1f}°", fontsize=9, color='blue')


    ax.set_title(f"Wing Planform (M={params['M_cruise']}, S={params['S_ref_m2']}$m^2$, A={params['AR']})", fontsize=14)
    ax.set_xlabel("Spanwise distance from root (m)", fontsize=10)
    ax.set_ylabel("Chordwise distance from root LE (m)", fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(True, linestyle=':', alpha=0.7)
    ax.set_aspect('equal', adjustable='box')
    plt.legend(fontsize=9)
    plt.gca().invert_yaxis() 
    plt.tight_layout()
    plt.show()

# --- Main Execution ---
if __name__ == "__main__":
    # Step 1: Inputs for Initial Planform based on A05_WP2.pdf, Section 2.4 and Table 2.1
    input_M_cruise = 0.85
    input_M_star = 0.935 # Technology factor for supercritical airfoils (A05_WP2.pdf, p.5)
    input_S_m2 = 12.   # Wing area in m^2 (A05_WP2.pdf, Table 2.1a)
    input_A = 10.5       # Aspect ratio (A05_WP2.pdf, Table 2.1a)

    print("--- Step 1: Initial Planform Calculation (based on A05_WP2.pdf, Sec 2.4 methodology) ---")
    planform_params = calculate_initial_planform_params(
        input_M_cruise, input_M_star, input_S_m2, input_A
    )
    if not planform_params:
        print("Exiting due to planform calculation error.")
        exit()
    
    # Compare with A05_WP2.pdf, Table 2.1b (page 7)
    print(f"  Cruise Mach (M_cruise): {planform_params['M_cruise']} (Input)")
    print(f"  Wing Surface Area (S_ref): {planform_params['S_ref_m2']:.1f} m^2 (Input)")
    print(f"  Aspect Ratio (AR): {planform_params['AR']:.1f} (Input)")
    print(f"  Quarter-Chord Sweep (Lambda_c/4): {planform_params['Lambda_c4_deg']:.1f} degrees (Report Table 2.1b: 37.0)")
    print(f"  Wing Span (b): {planform_params['b_m']:.1f} m (Report Table 2.1b: 55.0; Text p.5 calc: ~55.2)")
    print(f"  Taper Ratio (lambda): {planform_params['lambda_taper']:.2f} (Report Table 2.1b: 0.27)")
    print(f"  Root Chord (Cr): {planform_params['Cr_m']:.1f} m (Report Table 2.1b: 8.3)")
    print(f"  Tip Chord (Ct): {planform_params['Ct_m']:.1f} m (Report Table 2.1b: 2.2)")
    print(f"  Average Chord (C_avg): {planform_params['C_avg_m']:.1f} m (Report Table 2.1b: 5.3)")
    print(f"  LE Sweep (Lambda_LE): {planform_params['Lambda_LE_deg']:.1f} degrees (Report Table 2.1b: 39.0)")
    print(f"  Mean Aerodynamic Chord (MAC): {planform_params['MAC_m']:.1f} m (Report Table 2.1b: 5.8)")
    print(f"  y_MAC (spanwise MAC location): {planform_params['y_MAC_m']:.1f} m (Report Table 2.1b: 11.2)")
    print(f"  x_LEMAC (chordwise MAC LE location): {planform_params['x_LEMAC_m']:.1f} m (Report Table 2.1b: 9.1)")
    print(f"  Dihedral Angle (Gamma): {planform_params['Gamma_deg']:.1f} degrees (Report Table 2.1b: 1.3)")
    print(f"  Mid-Chord Sweep (Lambda_0.5c): {planform_params['Lambda_05c_deg']:.1f} degrees")
    print("-" * 40)

    # Step 2: Inputs for Airfoil Selection and Cruise Params
    # From A05_WP2.pdf, Table 2 (Summary, p.ii) & Section 3.5 (Table 3.5, p.15)
    # Weight estimation is not in this scope, using report's CL_des directly for verification if possible,
    # or calculating it based on an assumed weight.
    # Report (p.12, Sec 3.3) calculates CL_des = 0.58, leading to Cl_des = 0.66.
    # Let's use a weight that would lead to this CL_des for consistency check.
    # CL_des = 1.1 * (W/S) / q  => W = (CL_des * q * S) / 1.1
    # From A05_WP2.pdf, p.28, cruise q_inf = 0.5 * 0.442 * 257^2 = 14619 Pa (approx)
    # W_estim_N_from_report_CL = (0.58 * 14619 * input_S_m2) / 1.1 # This is for the final design.
    # For now, let's use a placeholder weight as the report's CL_des is for its final design.

    input_W_estim_N = 30787.8 # Placeholder weight in Newtons 
    input_alt_cruise_m = 40000 * 0.3048 # converted to meters
    
    # Airfoil: NASA SC(2)-0714 (A05_WP2.pdf, p.14 selected, p.8 geometry)
    # t/c = 0.14 for this airfoil. We'll use this as tc_avg.
    # For tc_root and tc_tip, we can assume a slight variation around this or use it directly.
    avg_tc_airfoil = 0.14 
    input_tc_root = avg_tc_airfoil * 1.05 # e.g. 0.147
    input_tc_tip  = avg_tc_airfoil * 0.95 # e.g. 0.133
    
    selected_airfoil_data = { # Based on NASA SC(2)-0714
        "name": "NASA SC(2)-0714", 
        "Cl_max": 1.77,  # From A05_WP2.pdf Table 3.3 (XFLR5 M=0.2 data)
        "Cm0": -0.12, # Approx from A05_WP2.pdf Fig 3.10 (Cm0 for NACA SC(2)-0714 is around -0.1 to -0.12)
        "ka": 0.935, # Technology factor for supercritical, consistent with M_star
        "xc_max_thick": 0.40 # Typical for supercritical, or specific if known (0714 has max thick near 40%)
    }

    print("--- Step 2: Airfoil Selection and Cruise Parameters ---")
    cruise_params = calculate_airfoil_and_cruise_params(planform_params, input_W_estim_N,
                                                        input_alt_cruise_m, input_tc_root,
                                                        input_tc_tip, selected_airfoil_data)
    print(f"  Cruise Altitude: {input_alt_cruise_m:.0f} m ({input_alt_cruise_m/0.3048:.0f} ft)")
    print(f"  Cruise Density: {cruise_params['density_kg_m3']:.4f} kg/m^3")
    print(f"  Cruise Speed of Sound: {cruise_params['speed_of_sound_m_s']:.2f} m/s")
    print(f"  Cruise Velocity: {cruise_params['V_cruise_m_s']:.2f} m/s ({cruise_params['V_cruise_m_s']*1.94384:.1f} kts)")
    print(f"  Cruise Dynamic Pressure (q): {cruise_params['q_cruise_Pa']:.2f} Pa")
    print(f"  Target Wing C_L_des: {cruise_params['C_L_des']:.4f} (A05_WP2.pdf Table 2 reports 0.58 for final design)")
    print(f"  Target Airfoil C_l_des: {cruise_params['C_l_des']:.4f} (A05_WP2.pdf p.12 reports 0.66 for initial)")
    print(f"  Selected Airfoil Family: {cruise_params['selected_airfoil_family']}")
    print(f"  Est. Airfoil Cl_max: {cruise_params['Cl_max_airfoil_estim']:.2f}")
    print(f"  Est. Airfoil Cm0: {cruise_params['Cm0_airfoil_estim']:.3f}")
    print(f"  Wing t/c: Root={cruise_params['tc_root']:.3f}, Tip={cruise_params['tc_tip']:.3f}, MAC={cruise_params['tc_MAC']:.3f}")
    print(f"  Airfoil Tech Factor (ka): {cruise_params['ka_airfoil_tech_factor']:.3f}")
    print("-" * 40)

    # Step 3: Estimate Wing Lift Characteristics
    input_eta_airfoil_eff = 0.95 

    print("--- Step 3: Wing Lift Characteristics ---")
    lift_params = estimate_wing_lift_characteristics(planform_params, cruise_params, 
                                                     eta_airfoil_eff=input_eta_airfoil_eff)
    print(f"  Prandtl-Glauert Factor (beta): {lift_params['beta_PG']:.4f}")
    print(f"  Wing C_L_alpha: {lift_params['C_L_alpha_per_rad']:.3f} /rad ({lift_params['C_L_alpha_per_deg']:.3f} /deg)")
    # A05_WP2.pdf Table 3.5 reports CLmax at M=0.2 as 1.7 (initial) or 1.83 (final) from XFLR5
    print(f"  Clean Wing C_L_max_clean (estim.): {lift_params['C_L_max_clean']:.3f}") 
    print("-" * 40)

    # Step 4a: Estimate Zero-Lift Drag (CD0)
    # Using S_ref from planform_params
    # Component geometries need to be scaled according to S_ref = 290 m^2
    # Fuselage: (Raymer, typical transport L/D_fus ~ 8-12). If L_fus ~ 50m, D_fus ~ 5m.
    # S_wet_fus ~ pi * D_fus * L_fus * 0.75 (for pointed ends)
    L_fus_estim = 50.0
    D_fus_estim = 5.0
    s_wet_fus_approx = math.pi * D_fus_estim * L_fus_estim * 0.8 
    # Tails: S_ht ~ 0.2*S_ref, S_vt ~ 0.1*S_ref
    S_ht_approx = 0.20 * planform_params['S_ref_m2']
    S_vt_approx = 0.10 * planform_params['S_ref_m2']
    # MAC_ht ~ 0.4 * MAC_wing, MAC_vt ~ 0.35 * MAC_wing
    MAC_ht_approx = 0.4 * planform_params['MAC_m']
    MAC_vt_approx = 0.35 * planform_params['MAC_m']
    s_wet_ht_approx = S_ht_approx * 1.9
    s_wet_vt_approx = S_vt_approx * 1.9
    
    component_geometries_data = {
        "wing": {"l_char_m": planform_params['MAC_m'], 
                 "S_wet_m2": planform_params['S_ref_m2'] * 1.95, # Typical S_wet/S_ref for wing
                 "tc_avg": cruise_params['tc_avg'], 
                 "xc_max_thick": cruise_params['xc_max_thick_airfoil'],
                 "Lambda_max_thick_rad": planform_params['Lambda_c4_rad'], 
                 "IF": 1.0},
        "fuselage": {"l_char_m": L_fus_estim, "d_char_m": D_fus_estim, 
                     "S_wet_m2": s_wet_fus_approx, 
                     "slenderness": L_fus_estim/D_fus_estim, "IF": 1.02}, # Added small IF for wing junction
        "horizontal_tail": {"l_char_m": MAC_ht_approx, "S_wet_m2": s_wet_ht_approx, 
                            "tc_avg": 0.10, "xc_max_thick": 0.4, 
                            "Lambda_max_thick_rad": planform_params['Lambda_c4_rad'], # Approx
                            "IF": 1.01}, # Slight interference from fuselage
        "vertical_tail": {"l_char_m": MAC_vt_approx, "S_wet_m2": s_wet_vt_approx, 
                          "tc_avg": 0.10, "xc_max_thick": 0.4,
                           "Lambda_max_thick_rad": planform_params['Lambda_c4_rad']*0.8, # Approx less sweep
                           "IF": 1.01},
    }
    input_k_surface_roughness_m = 3e-6 # Smoother paint for commercial

    print("--- Step 4a: Zero-Lift Drag (CD0) ---")
    drag_params_cd0 = estimate_zero_lift_drag(planform_params, cruise_params, input_W_estim_N,
                                           component_geometries_data, input_k_surface_roughness_m)
    print(f"  CD0 (Friction+Form): {drag_params_cd0['CD0_friction_form']:.5f}")
    print(f"  Wing M_DD (estim.): {drag_params_cd0['M_DD_wing']:.3f} (A05_WP2.pdf Table 2 reports 0.865 for final design)")
    print(f"  Delta_CD_wave (estim.): {drag_params_cd0['delta_CD_wave']:.5f}")
    print(f"  Total CD0 (estim. incl. wave): {drag_params_cd0['CD0_total']:.5f} (A05_WP2.pdf Eq 5.6 reports CD0=0.0169 for initial design - this was from Raymer's method, not component buildup)")
    print("-" * 40)

    # Step 4b: Estimate Lift-Induced Drag Factor (K)
    print("--- Step 4b: Lift-Induced Drag Factor (K) ---")
    induced_drag_params_k = estimate_lift_induced_drag_factor(planform_params)
    print(f"  Oswald Efficiency (e): {induced_drag_params_k['e_oswald']:.3f} (A05_WP2.pdf p.28 reports 0.35-0.38 for initial/final)")
    print(f"  Lift-Induced Drag Factor (K): {induced_drag_params_k['K_drag_induced']:.4f}")
    print(f"  Drag Polar: CD = {drag_params_cd0['CD0_total']:.5f} + {induced_drag_params_k['K_drag_induced']:.4f} * CL^2")
    print("-" * 40)

    # Step 5: Conceptual HLD Sizing
    # A05_WP2.pdf Table 2 reports CL_landing = 2.7. Let's target a stall speed for this.
    # V_stall = sqrt(2*W / (rho_sl * S * CL_max_land))
    # Assuming W_land ~ 0.85 * W_takeoff. W_takeoff ~ input_W_estim_N
    W_land_estim_N = 0.85 * input_W_estim_N
    CL_max_land_target_report = 2.7 # From A05_WP2.pdf Table 2
    rho_sl_val = get_atmospheric_properties(0)['density_kg_m3']
    input_V_stall_target_m_s = math.sqrt(2 * W_land_estim_N / (rho_sl_val * planform_params['S_ref_m2'] * CL_max_land_target_report))
    print(f"  Targeting CL_max_land={CL_max_land_target_report} from report, implies V_stall ~ {input_V_stall_target_m_s:.1f} m/s for landing weight.")

    # A05_WP2.pdf p.30 selected Single-slotted Fowler flaps and leading edge flaps (droop nose) for final HLD.
    # Table 5.2 (p.30) gives delta_CLmax_total = 0.91 for this combination.
    # Let's assume this delta_CLmax is what we need to achieve.
    # For conceptual sizing, we can use a combined delta_Cl_max for the HLD system.
    # Or, use the individual components. Summary Doc Table 2.2 for Single Slotted Fowler: 1.3 * c'/c. For Droop Nose: 0.3
    # A05_WP2.pdf (p.21) uses delta_Clmax = 1.82 for single slotted fowler (implies c'/c ~ 1.4) and 0.3 for droop nose.
    
    selected_hld_data = { # Representing the combined effect from A05_WP2.pdf Table 5.2
        "name": "Single Slotted Fowler + Droop Nose (Combined Effect)",
        "delta_Cl_max": 2.12, # This would be the effective 2D delta_cl_max to achieve 0.91 3D delta_CL_max
                              # From A05_WP2.pdf p.21: delta_CLmax_total = 0.94 (option 2 initial)
                              # delta_CLmax_final = 0.91 (Table 5.2)
                              # Let's use the delta_Cl_max that would results in the report's delta_CL_max
                              # delta_CL_max_3D = 0.9 * delta_Cl_max_2D_combined * (S_wf/S)_avg * cos(Lambda_HL)_avg
                              # This is tricky to back-calculate without S_wf/S.
                              # Let's use the delta_Cl_max for a dominant TE device like Single Slotted Fowler
        "delta_Cl_max_TE": 1.82, # from A05_WP2.pdf p.21 for single slotted fowler (assumes c'/c ~1.4)
        "delta_Cl_max_LE": 0.3,  # from A05_WP2.pdf p.21 for droop nose
        # For simplicity in this skeleton, we'll use a single delta_Cl_max value that represents the system.
        # To get delta_CL_max of 0.91 (from report Table 5.2), assuming S_wf/S ~ 0.5 and cos(Lambda_HL)~0.85
        # 0.91 = 0.9 * delta_Cl_max_eff_2D * 0.5 * 0.85 => delta_Cl_max_eff_2D ~ 0.91 / (0.9*0.5*0.85) ~ 2.38
        "delta_Cl_max": 2.38, # Effective 2D delta_Cl_max to achieve target 3D delta_CL_max
        "c_prime_c_ratio": 1.4 # For Fowler part
    }


    print("--- Step 5: Conceptual HLD Sizing ---")
    hld_params = conceptual_hld_sizing(planform_params, cruise_params, lift_params, input_W_estim_N,
                                       input_V_stall_target_m_s, selected_hld_data)
    print(f"  Required C_L_max for V_stall={input_V_stall_target_m_s:.1f} m/s: {hld_params['C_L_max_req']:.3f}")
    print(f"  Delta C_L_max needed from HLDs: {hld_params['delta_C_L_max_HLD']:.3f} (A05_WP2.pdf Table 5.2 reports 0.91)")
    if hld_params['HLD_needed']:
        print(f"  HLD Type Selected: {hld_params['HLD_type_selected']}")
        print(f"  Estimated S_wf/S ratio (effective): {hld_params['Swf_S_ratio']:.3f}")
    else:
        print("  HLDs are not required based on C_L_max_clean and target stall speed.")
    print("-" * 40)
    
    print("Displaying wing planform plot...")
    plot_wing_planform(planform_params)

