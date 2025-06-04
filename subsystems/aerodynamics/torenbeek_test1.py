import numpy as np
import matplotlib.pyplot as plt

# --- Constants ---
H_g = 4350  # km, Fuel specific energy (H/g) for jet fuel (kerosene)
g = 9.80665 # m/s^2, standard gravity

# --- Helper Functions ---
def dynamic_pressure(rho, V):
    """Calculates dynamic pressure."""
    return 0.5 * rho * V**2

def dynamic_pressure_mach(gamma, p, M):
    """Calculates dynamic pressure from Mach number and static pressure."""
    return 0.5 * gamma * p * M**2

# --- Section 10.3: Design Sensitivity Information (Recap for context) ---
# These are foundational for understanding WPF and MTOW calculations.

def calculate_C_Dp_hat_subsonic(C_f_eq_fuselage, S_wet_fuselage,
                                C_f_eq_vtail, S_vtail,
                                C_f_eq_nacelles, S_nacelles, # Per engine
                                N_eng,
                                C_f_eq_wing, S_wet_wing, # Exposed wing
                                C_f_eq_htail, S_htail, # Exposed htail
                                S_w_ref):
    """
    Estimates the fixed and variable parts of parasite drag area for subsonic aircraft.
    This is a conceptual representation based on Eq 10.3 and surrounding text.
    More detailed component buildup is usually needed (e.g., from Chapter 4 & 8).

    Returns:
        C_Dp_S_fix (m^2): Fixed parasite drag area (fuselage, vtail, nacelles).
        C_Dp_coeff_var (dimensionless): Coefficient for variable parasite drag (wing, htail)
                                       such that (C_Dp_S)_var = C_Dp_coeff_var * S_w_ref
    """
    # Fixed parasite drag area components
    C_Dp_S_fus = C_f_eq_fuselage * S_wet_fuselage
    C_Dp_S_vtail = C_f_eq_vtail * S_vtail
    C_Dp_S_nac = C_f_eq_nacelles * S_nacelles * N_eng
    C_Dp_S_fix = C_Dp_S_fus + C_Dp_S_vtail + C_Dp_S_nac
    
    # For actual use, one would use methods from Chapter 4 and 8 to get:
    # (CDp S)_fix from Eq 8.18 (modified for subsonic)
    # C_Dp_hat_sub (variable part coefficient) from Eq 8.17 (modified for subsonic)
    # print("Note: calculate_C_Dp_hat_subsonic is conceptual. Use detailed drag buildup.")
    return C_Dp_S_fix, 0.008 # Placeholder for C_Dp_coeff_var

def calculate_wing_plus_htail_weight_fraction_subsonic(Lambda_1, Lambda_2, A_w, C_L_hat):
    """
    Calculates wing and horizontal tail weight fraction (mu_w+h) for subsonic aircraft.
    Based on Eq. 10.11.
    Args:
        Lambda_1 (float): Wing weight parameter (Eq. 10.12).
        Lambda_2 (float): Wing weight parameter (Eq. 10.13).
        A_w (float): Wing aspect ratio.
        C_L_hat (float): Design lift coefficient.
    Returns:
        float: Wing and horizontal tail weight fraction (mu_w+h).
    """
    if C_L_hat <= 0: return np.inf # Avoid division by zero or non-physical C_L
    if A_w <=0: return np.inf
    # Ensure A_w/C_L_hat is positive for sqrt
    val_sqrt = A_w / C_L_hat
    if val_sqrt <= 0: return np.inf
        
    term1 = Lambda_1 * A_w / np.sqrt(val_sqrt)
    term2 = Lambda_2 / C_L_hat
    return term1 + term2

def calculate_propulsion_function(R_eq, eta_o_cruise, mu_T, tau_cruise, delta_cruise):
    """
    Calculates the propulsion function F_prop.
    Based on Eq. 8.32 (adapted for general use).
    Args:
        R_eq (float): Equivalent range (km) (Eq. 8.29).
        eta_o_cruise (float): Overall engine efficiency in cruise.
        mu_T (float): Power plant weight per unit take-off thrust.
        tau_cruise (float): Corrected thrust lapse rate in cruise (T_cruise / (delta_cruise * T_TO)).
        delta_cruise (float): Relative ambient pressure at cruise altitude.
    Returns:
        float: Propulsion function F_prop.
    """
    if eta_o_cruise <= 0 or tau_cruise <= 0 or delta_cruise <= 0: return np.inf
    return (R_eq / (eta_o_cruise * H_g)) + (mu_T / (tau_cruise * delta_cruise))

def calculate_WPF_subsonic(Lambda_1, Lambda_2, F_prop,
                           C_Dp_hat_var, # Variable part of parasite drag coeff related to S_w
                           C_L_hat, A_w, e_hat):
    """
    Calculates the Wing Penalty Function (WPF) for subsonic aircraft.
    Based on Eq. 10.14, assuming (CDpS)_fix drag is handled in MTOW calc.
    This WPF focuses on wing-related drag and weight contributions.
    Args:
        Lambda_1, Lambda_2: Wing weight parameters.
        F_prop: Propulsion function.
        C_Dp_hat_var: Parasite drag coefficient of wing+htail (referred to S_w).
        C_L_hat: Design lift coefficient.
        A_w: Wing aspect ratio.
        e_hat: Oswald efficiency factor (modified).
    Returns:
        float: Wing Penalty Function (F_wp).
    """
    if C_L_hat <= 0 or A_w <= 0 or e_hat <= 0: return np.inf
    
    mu_w_plus_h = calculate_wing_plus_htail_weight_fraction_subsonic(Lambda_1, Lambda_2, A_w, C_L_hat)
    if mu_w_plus_h == np.inf: return np.inf
        
    drag_term_parasite = C_Dp_hat_var / C_L_hat
    drag_term_induced = C_L_hat / (np.pi * A_w * e_hat)
    
    F_wp = mu_w_plus_h + F_prop * (drag_term_parasite + drag_term_induced)
    return F_wp

def calculate_MTOW_subsonic(W_pay, W_fix_other, F_prop, q_hat_cruise, C_Dp_S_fix,
                            mu_resf, mu_lg, F_wp):
    """
    Calculates Maximum Take-Off Weight (MTOW) for subsonic aircraft.
    Based on Eq. 10.15.
    Args:
        W_pay (float): Payload weight.
        W_fix_other (float): Other fixed weights (fuselage structure, systems, etc., excluding W_pay).
        F_prop (float): Propulsion function.
        q_hat_cruise (float): Dynamic pressure at design cruise.
        C_Dp_S_fix (float): Fixed parasite drag area (fuselage, nacelles, vtail).
        mu_resf (float): Reserve fuel fraction (W_resf / W_MTO).
        mu_lg (float): Landing gear weight fraction (W_lg / W_MTO).
        F_wp (float): Wing Penalty Function (from calculate_WPF_subsonic).
    Returns:
        float: Maximum Take-Off Weight (W_MTO).
    """
    if q_hat_cruise <0 : return np.inf
    numerator = W_pay + W_fix_other + F_prop * q_hat_cruise * C_Dp_S_fix
    denominator = 1 - (mu_resf + mu_lg + F_wp)
    if denominator <= 0:
        return np.inf # Indicates an unfeasible design
    return numerator / denominator

# --- Section 10.5: Constrained Optima ---

def check_TOFL_constraint_satisfied(W_MTO, b_w, L_TOFL_req,
                                    rho_TO, E_takeoff, k_T_takeoff, h_TO, N_eng, C0_takeoff,
                                    T_V2_over_W_TO_available):
    """
    Checks if the Take-Off Field Length (TOFL) constraint is satisfied.
    Placeholder for a detailed TOFL calculation from Chapter 9.
    Returns:
        bool: True if TOFL constraint is met, False otherwise.
        float: Calculated required T_V2 / W_TO for the given L_TOFL (conceptual).
    """
    if b_w <=0 or L_TOFL_req <=0 or rho_TO <=0 or E_takeoff <=0 : return False, np.inf
    term1_sqrt_factor = (W_MTO / b_w**2) / (L_TOFL_req * rho_TO * g * np.pi * E_takeoff)
    if term1_sqrt_factor < 0: term1_sqrt_factor = 0 

    factor_N_eng = N_eng / (0.89 * N_eng - 1) if (0.89 * N_eng - 1) > 0.001 else N_eng 

    required_T_V2_W_TO = 0.78 * factor_N_eng * np.sqrt(term1_sqrt_factor) + \
                           (42 / L_TOFL_req) * factor_N_eng
                           
    return T_V2_over_W_TO_available >= required_T_V2_W_TO, required_T_V2_W_TO


def calculate_tank_volume(eta_tank, t_c_w_avg, S_w, A_w):
    """
    Calculates available wing tank volume. Based on Eq. 10.30.
    """
    if A_w <= 0 or S_w <=0 or t_c_w_avg <=0 : return 0
    return 0.90 * eta_tank * t_c_w_avg * S_w**1.5 * A_w**-0.5

def calculate_max_fuel_weight_volume(R_m_eq, eta_o_cruise, C_Dp_hat, C_L_hat, A_w, e_hat, W_MTO, C_resf_frac, rho_fuel):
    """
    Calculates the volume of maximum fuel required (mission for R_m + reserves).
    Based on Eq. 10.31 for fuel weight, then converted to volume.
    """
    if C_L_hat <= 0 or A_w <= 0 or e_hat <= 0 or rho_fuel <=0 or eta_o_cruise <=0: return np.inf
    C_D_hat_at_C_L_hat = C_Dp_hat + C_L_hat**2 / (np.pi * A_w * e_hat)
    W_f_max_weight = W_MTO * ( (R_m_eq / (eta_o_cruise * H_g)) * (C_D_hat_at_C_L_hat / C_L_hat) + C_resf_frac )
    if W_f_max_weight < 0: return np.inf # Avoid issues if C_L_hat is very small
    return W_f_max_weight / (rho_fuel * g) 

def check_tank_volume_constraint(eta_tank, t_c_w_avg, S_w, A_w,
                                 R_m_eq, eta_o_cruise, C_Dp_hat, C_L_hat, e_hat, W_MTO, C_resf_frac, rho_fuel):
    """
    Checks if the tank volume constraint is met.
    """
    V_tank_avail = calculate_tank_volume(eta_tank, t_c_w_avg, S_w, A_w)
    V_fuel_req = calculate_max_fuel_weight_volume(R_m_eq, eta_o_cruise, C_Dp_hat, C_L_hat, A_w, e_hat, W_MTO, C_resf_frac, rho_fuel)
    return V_tank_avail >= V_fuel_req, V_tank_avail, V_fuel_req

# --- Section 10.6: Transonic Aircraft Wing ---

def calculate_mu_w_plus_h_transonic(Lambda_3, t_c_w, Lambda_w_rad, A_w, C_L_hat, Lambda_2):
    """
    Calculates wing and horizontal tail weight fraction for transonic aircraft. Eq. 10.34.
    """
    if C_L_hat <= 0 or t_c_w <= 0 or np.cos(Lambda_w_rad) == 0 or A_w <=0: return np.inf
    val_sqrt = A_w / C_L_hat
    if val_sqrt <=0: return np.inf
    term1_num = Lambda_3 * A_w * np.sqrt(val_sqrt)
    term1_den = t_c_w * (np.cos(Lambda_w_rad))**2
    term1 = term1_num / term1_den if term1_den > 0.0001 else np.inf # Avoid division by zero
    term2 = Lambda_2 / C_L_hat
    return term1 + term2

def calculate_C_Dp_hat_wing_transonic(t_c_w, Lambda_w_rad, C_f, r_prime=3.0, d_w_h=1.25):
    """
    Calculates profile drag coefficient C_Dp_hat for transonic wing (and htail). Eq. 10.39.
    """
    if t_c_w <0 or C_f <0: return np.inf
    cos_Lambda_w = np.cos(Lambda_w_rad)
    C_Dp_hat_wing_only = 2 * (1 + r_prime * t_c_w * cos_Lambda_w**2) * C_f
    return d_w_h * C_Dp_hat_wing_only

def calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa=0.935):
    """
    Calculates the limiting (t/c)_w * (cos Lambda_w)^2 based on M_dd constraint. Eq. 10.49.
    """
    cos_Lambda_w = np.cos(Lambda_w_rad)
    # Ensure C_L_hat is not negative for C_L_hat**1.5
    if C_L_hat < 0: C_L_hat_pow = - ((-C_L_hat)**1.5) # Or handle error
    else: C_L_hat_pow = C_L_hat**1.5

    val = (cos_Lambda_w**3) * (M_kappa - M_dd * cos_Lambda_w) - 0.115 * C_L_hat_pow
    return max(0, val) # Thickness term cannot be negative

def get_tc_from_tc_cos2_lambda(tc_cos2_lambda_val, Lambda_w_rad):
    """ Utility to get t/c from the tc_cos2_lambda_val """
    cos_Lambda_w = np.cos(Lambda_w_rad)
    if abs(cos_Lambda_w) < 0.001: return np.inf # Avoid division by zero for near 90 deg sweep
    return tc_cos2_lambda_val / (cos_Lambda_w**2)

def calculate_WPF_transonic(Lambda_3, Lambda_2, F_prop,
                            C_L_hat, A_w, Lambda_w_rad, e_hat,
                            M_dd, M_kappa=0.935, 
                            C_f=0.003, r_prime=3.0, d_w_h=1.25,
                            C_Dc=0.0005):
    """
    Calculates the Wing Penalty Function (WPF) for transonic aircraft. Eq. 10.43.
    """
    if C_L_hat <= 0 or A_w <= 0 or e_hat <=0 or F_prop <0 : return np.inf

    tc_cos2_lambda_val = calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa)
    t_c_w = get_tc_from_tc_cos2_lambda(tc_cos2_lambda_val, Lambda_w_rad)
    
    if t_c_w <= 0.01 or t_c_w == np.inf : 
        return np.inf

    mu_w_plus_h = calculate_mu_w_plus_h_transonic(Lambda_3, t_c_w, Lambda_w_rad, A_w, C_L_hat, Lambda_2)
    if mu_w_plus_h == np.inf: return np.inf

    C_Dp_hat_var = calculate_C_Dp_hat_wing_transonic(t_c_w, Lambda_w_rad, C_f, r_prime, d_w_h)
    if C_Dp_hat_var == np.inf: return np.inf
        
    drag_term_parasite_profile = C_Dp_hat_var / C_L_hat
    drag_term_compressibility = C_Dc / C_L_hat 
    drag_term_induced = C_L_hat / (np.pi * A_w * e_hat)
    
    total_drag_coeff_over_CL = drag_term_parasite_profile + drag_term_compressibility + drag_term_induced
    
    F_wp = mu_w_plus_h + F_prop * total_drag_coeff_over_CL
    return F_wp

def calculate_L_D_wing_plus_htail_transonic(C_L_hat, A_w, Lambda_w_rad, e_hat,
                                           M_dd, M_kappa=0.935,
                                           C_f=0.003, r_prime=3.0, d_w_h=1.25,
                                           C_Dc=0.0005):
    """
    Calculates L/D for wing + htail for transonic aircraft, considering M_dd constraint.
    """
    if C_L_hat <= 0 or A_w <= 0 or e_hat <=0: return 0

    tc_cos2_lambda_val = calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa)
    t_c_w = get_tc_from_tc_cos2_lambda(tc_cos2_lambda_val, Lambda_w_rad)

    if t_c_w <= 0.01 or t_c_w == np.inf: return 0

    C_Dp_hat_var = calculate_C_Dp_hat_wing_transonic(t_c_w, Lambda_w_rad, C_f, r_prime, d_w_h)
    if C_Dp_hat_var == np.inf: return 0
        
    C_D_total_wing_htail = C_Dp_hat_var + C_Dc + C_L_hat**2 / (np.pi * A_w * e_hat)
    
    if C_D_total_wing_htail <= 0: return np.inf
    return C_L_hat / C_D_total_wing_htail

def calculate_optimal_Aw_transonic_given_CL_Lambda(C_L_hat, Lambda_w_rad,
                                                    F_prop, Lambda_3, e_hat,
                                                    M_dd, M_kappa=0.935):
    """
    Calculates optimal A_w for given C_L_hat, Lambda_w_rad (transonic). Eq. 10.52 (re-derived).
    """
    if C_L_hat <= 0 or F_prop <0 or Lambda_3 <=0 or e_hat <=0: return np.inf

    tc_cos2_lambda_val = calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa)
    if tc_cos2_lambda_val <= 0: return np.inf

    numerator = (2/3) * F_prop * C_L_hat * tc_cos2_lambda_val
    denominator = Lambda_3 * np.pi * e_hat
    if abs(denominator) < 1e-9: return np.inf # Avoid division by zero
    
    # Ensure base of power is non-negative
    base_val = numerator / denominator
    if base_val < 0: return np.inf

    optimal_A_w = base_val**0.4
    return optimal_A_w

# --- Plotting Functions ---
def plot_figure_10_10(C_L_hat_fixed=0.55, M_kappa_fixed=0.935):
    """Plots data similar to Figure 10.10."""
    Lambda_w_deg_range = np.linspace(0, 50, 100)
    Lambda_w_rad_range = np.deg2rad(Lambda_w_deg_range)
    M_dd_values = [0.70, 0.75, 0.80, 0.85, 0.90]

    plt.figure(figsize=(8, 6))
    for M_dd in M_dd_values:
        tc_cos2_lambda_results = [calculate_tc_cos2_lambda_limit(M_dd, lw_rad, C_L_hat_fixed, M_kappa_fixed)
                                  for lw_rad in Lambda_w_rad_range]
        plt.plot(Lambda_w_deg_range, tc_cos2_lambda_results, label=f'$M_{{dd}}={M_dd:.2f}$')

    plt.xlabel('Wing Sweep $\Lambda_w$ (degrees)')
    plt.ylabel('$(t/c)_w \cos^2 \Lambda_w$')
    plt.title(f'Fig 10.10 Approx: $(t/c)_w \cos^2 \Lambda_w$ vs. Sweep (Fixed $C_{{L,hat}}={C_L_hat_fixed}, M_{{\kappa}}={M_kappa_fixed}$)')
    plt.legend()
    plt.grid(True)
    plt.ylim(0, 0.16) # Match figure y-axis
    plt.show()

def plot_figure_10_11(A_w_fixed=9.0, M_dd_fixed=0.825, M_kappa_fixed=0.935,
                        Lambda_3_val=0.0002, Lambda_2_val=0.025, F_prop_val=6.0, # Example values
                        e_hat_fixed=0.9, C_f_fixed=0.0028, r_prime_fixed=3.0,
                        d_w_h_fixed=1.25, C_Dc_fixed=0.0008):
    """Plots data similar to Figure 10.11."""
    Lambda_w_deg_range = np.linspace(0, 50, 50)
    Lambda_w_rad_range = np.deg2rad(Lambda_w_deg_range)
    C_L_hat_values = [0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8]

    fig, ax1 = plt.subplots(figsize=(10, 7))

    # Plot WPF
    color_idx = 0
    colors = plt.cm.viridis(np.linspace(0, 1, len(C_L_hat_values)))
    for C_L_hat in C_L_hat_values:
        wpf_results = [calculate_WPF_transonic(Lambda_3_val, Lambda_2_val, F_prop_val, C_L_hat, A_w_fixed,
                                               lw_rad, e_hat_fixed, M_dd_fixed, M_kappa_fixed, C_f_fixed,
                                               r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
                       for lw_rad in Lambda_w_rad_range]
        ax1.plot(Lambda_w_deg_range, wpf_results, label=f'WPF $C_{{L,hat}}={C_L_hat:.2f}$', color=colors[color_idx])
        color_idx += 1
    
    ax1.set_xlabel('Wing Sweep $\Lambda_w$ (degrees)')
    ax1.set_ylabel('Wing Penalty Function (WPF)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(0.32, 0.42) # Approximate from figure
    ax1.grid(True, linestyle=':', alpha=0.7)

    # Plot L/D on a second y-axis
    ax2 = ax1.twinx()
    color_idx = 0
    for C_L_hat in C_L_hat_values:
        ld_results = [calculate_L_D_wing_plus_htail_transonic(C_L_hat, A_w_fixed, lw_rad, e_hat_fixed, M_dd_fixed,
                                                            M_kappa_fixed, C_f_fixed, r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
                      for lw_rad in Lambda_w_rad_range]
        ax2.plot(Lambda_w_deg_range, ld_results, linestyle='--', label=f'L/D $C_{{L,hat}}={C_L_hat:.2f}$', color=colors[color_idx])
        color_idx += 1
    ax2.set_ylabel('$(L/D)_{w+h}$', color='green')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.set_ylim(20, 30) # Approximate from figure

    # Plot t/c contours
    # Create a grid for contour plot
    L_W_DEG, C_L_H = np.meshgrid(Lambda_w_deg_range, np.array(C_L_hat_values))
    L_W_RAD = np.deg2rad(L_W_DEG)
    
    T_C_W_grid = np.zeros_like(L_W_DEG)
    for i in range(L_W_DEG.shape[0]): # Iterate over C_L_hat values
        for j in range(L_W_DEG.shape[1]): # Iterate over Lambda_w values
            clh = C_L_H[i,j]
            lwr = L_W_RAD[i,j]
            tc_cos2 = calculate_tc_cos2_lambda_limit(M_dd_fixed, lwr, clh, M_kappa_fixed)
            T_C_W_grid[i,j] = get_tc_from_tc_cos2_lambda(tc_cos2, lwr)

    contour_tc = ax1.contour(L_W_DEG, C_L_H, T_C_W_grid, levels=[0.08, 0.10, 0.12, 0.14, 0.16], colors='grey', linestyles='-.')
    ax1.clabel(contour_tc, inline=True, fontsize=8, fmt='t/c=%.2f')
    
    fig.tight_layout()
    plt.title(f'Fig 10.11 Approx: WPF & L/D vs. Sweep ($A_w={A_w_fixed}, M_{{dd}}={M_dd_fixed}$)')
    # Combine legends or place them carefully
    lines_ax1, labels_ax1 = ax1.get_legend_handles_labels()
    lines_ax2, labels_ax2 = ax2.get_legend_handles_labels()
    ax2.legend(lines_ax1 + lines_ax2, labels_ax1 + labels_ax2, loc='upper right', fontsize='small')
    
    plt.show()

def plot_figure_10_12(Lambda_w_deg_fixed=30.0, M_dd_fixed=0.825, M_kappa_fixed=0.935,
                        Lambda_3_val=0.0002, Lambda_2_val=0.025, F_prop_val=6.0,
                        e_hat_fixed=0.9, C_f_fixed=0.0028, r_prime_fixed=3.0,
                        d_w_h_fixed=1.25, C_Dc_fixed=0.0008,
                        W_MTO_example = 1100e3 * g # Example MTOW for constraints
                        ):
    """Plots data similar to Figure 10.12."""
    C_L_hat_range = np.linspace(0.3, 0.9, 50)
    A_w_range = np.linspace(4, 16, 50)
    Lambda_w_rad_fixed = np.deg2rad(Lambda_w_deg_fixed)

    CLH, AW = np.meshgrid(C_L_hat_range, A_w_range)
    WPF_grid = np.zeros_like(CLH)

    for i in range(CLH.shape[0]):
        for j in range(CLH.shape[1]):
            WPF_grid[i, j] = calculate_WPF_transonic(Lambda_3_val, Lambda_2_val, F_prop_val,
                                                     CLH[i, j], AW[i, j], Lambda_w_rad_fixed, e_hat_fixed,
                                                     M_dd_fixed, M_kappa_fixed, C_f_fixed,
                                                     r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
    
    plt.figure(figsize=(8, 6))
    # WPF contours
    contour_wpf = plt.contour(CLH, AW, WPF_grid, levels=np.arange(0.33, 0.41, 0.005), cmap='viridis')
    plt.clabel(contour_wpf, inline=True, fontsize=8, fmt='%.3f')

    # Optimal A_w for given C_L_hat (Curve II from Fig 10.13 logic)
    opt_A_w_line = [calculate_optimal_Aw_transonic_given_CL_Lambda(cl, Lambda_w_rad_fixed, F_prop_val, Lambda_3_val, e_hat_fixed, M_dd_fixed, M_kappa_fixed) for cl in C_L_hat_range]
    plt.plot(C_L_hat_range, opt_A_w_line, 'k--', label='Opt $A_w$ (dFwp/dAw=0)')

    # Example Constraint Lines (Illustrative)
    # 1. Span Loading Constraint (e.g., C_L_hat / A_w = const, or W_MTO / b_w^2 = const)
    # For W_MTO/b_w^2 = 5500 N/m^2 (example value from Fig 10.7 for subsonic)
    # b_w^2 = A_w * S_w = A_w * W_MTO / (q_hat_cruise * C_L_hat)
    # W_MTO / (A_w * W_MTO / (q_hat_cruise * C_L_hat)) = 5500
    # q_hat_cruise * C_L_hat / A_w = 5500
    # Assume q_hat_cruise for M=0.8, alt=10.5km (delta=0.25, p_sl=101325, gamma=1.4)
    # p_cruise = 0.25 * 101325 = 25331 Pa
    q_hat_cruise_eg = dynamic_pressure_mach(1.4, 0.25 * 101325, 0.81) # M_des from Fig 10.11 baseline
    span_load_const_val = 5500 # N/m^2
    A_w_span_load = (q_hat_cruise_eg / span_load_const_val) * C_L_hat_range
    plt.plot(C_L_hat_range, A_w_span_load, 'r:', label=f'Span Load Limit ({span_load_const_val} N/m$^2$)')
      # 2. Buffet Limit (e.g., C_L_hat <= 0.80, from text for Fig 10.12)
    plt.axhline(y=A_w_range.min(), xmin=C_L_hat_range.min(), xmax=0.8, color='m', linestyle='-.', label='Buffet Limit ($C_L \leq 0.8$)')
    plt.axvline(x=0.8, color='m', linestyle='-.')
    # 3. Pitch-up Limit (e.g., A_w <= 10, from text for Fig 10.12)
    plt.axhline(y=10, color='c', linestyle=':', label='Pitch-up Limit ($A_w \leq 10$)')
    
    plt.xlabel('Design Lift Coefficient $C_{L,hat}$')
    plt.ylabel('Aspect Ratio $A_w$')
    plt.title(f'Fig 10.12 Approx: WPF Contours ($\Lambda_w={Lambda_w_deg_fixed}^\circ, M_{{dd}}={M_dd_fixed}$)')
    plt.legend(fontsize='small')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(min(A_w_range), max(A_w_range))
    plt.xlim(min(C_L_hat_range), max(C_L_hat_range))
    plt.colorbar(contour_wpf, label='WPF')
    plt.show()


# --- Example Usage ---
if __name__ == '__main__':
    print("--- Aircraft Design Formulas (Chapter 10) ---")

    # Example parameters for plotting, trying to align with Fig 10.11/10.12 baseline
    # These are illustrative and may need adjustment for specific aircraft
    Lambda_3_val_trans = 0.0002  # From text example for Fig 8.1, section 10.6.1
    Lambda_2_val_trans = 0.025   # From text example for Fig 8.1, section 10.3.3
    
    # Propulsion function example (needs specific mission/engine data)
    # Example: R_eq=7000km, eta_o=0.35, mu_T=0.25, tau_cruise=0.8, delta_cruise=0.25 (approx 10.5km alt for M=0.8)
    F_prop_val_trans = calculate_propulsion_function(R_eq=7000, eta_o_cruise=0.35, mu_T=0.25, tau_cruise=0.8, delta_cruise=0.25)
    print(f"Example F_prop for transonic: {F_prop_val_trans:.3f}")

    e_hat_trans = 0.90       # Modified Oswald factor
    M_dd_trans = 0.825       # Target drag divergence Mach number
    M_kappa_trans = 0.935    # Aerodynamic technology factor
    C_f_trans = 0.0028       # Skin friction coefficient
    r_prime_trans = 3.0      # Form factor for thickness drag
    d_w_h_trans = 1.25       # Htail profile drag factor
    C_Dc_trans = 0.0008      # Compressibility drag coefficient (8 counts)

    # Plot Figure 10.10
    plot_figure_10_10(C_L_hat_fixed=0.55, M_kappa_fixed=M_kappa_trans)

    # Plot Figure 10.11
    plot_figure_10_11(A_w_fixed=9.0, M_dd_fixed=M_dd_trans, M_kappa_fixed=M_kappa_trans,
                        Lambda_3_val=Lambda_3_val_trans, Lambda_2_val=Lambda_2_val_trans,
                        F_prop_val=F_prop_val_trans, e_hat_fixed=e_hat_trans,
                        C_f_fixed=C_f_trans, r_prime_fixed=r_prime_trans,
                        d_w_h_fixed=d_w_h_trans, C_Dc_fixed=C_Dc_trans)
    
    # Plot Figure 10.12
    plot_figure_10_12(Lambda_w_deg_fixed=30.0, M_dd_fixed=M_dd_trans, M_kappa_fixed=M_kappa_trans,
                        Lambda_3_val=Lambda_3_val_trans, Lambda_2_val=Lambda_2_val_trans,
                        F_prop_val=F_prop_val_trans, e_hat_fixed=e_hat_trans,
                        C_f_fixed=C_f_trans, r_prime_fixed=r_prime_trans,
                        d_w_h_fixed=d_w_h_trans, C_Dc_fixed=C_Dc_trans)

