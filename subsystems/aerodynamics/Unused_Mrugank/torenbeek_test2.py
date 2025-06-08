# torenbeek_test2.py -> be careful, torenbeek_test1.py is leading
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, fsolve

# --- Constants ---
H_g = 4350  # km, Fuel specific energy (H/g) for jet fuel (kerosene)
g = 9.80665 # m/s^2, standard gravity
gamma_air = 1.4 # Ratio of specific heats for air
p_sl = 101325 # Pa, sea level pressure ISA
rho_sl = 1.225 # kg/m^3, sea level density ISA

# --- Helper Functions ---
def dynamic_pressure_mach(p_static, M, gamma=gamma_air):
    """Calculates dynamic pressure from Mach number and static pressure."""
    return 0.5 * gamma * p_static * M**2

def get_isa_delta_theta(altitude_m):
    """ Returns relative pressure (delta) and relative temperature (theta) at a given altitude """
    if altitude_m <= 11000: # Troposphere
        T_K = 288.15 - 0.0065 * altitude_m
        theta = T_K / 288.15
        delta = (T_K / 288.15)**(g / (0.0065 * 287.05))
    elif altitude_m <= 20000: # Lower Stratosphere
        T_K = 216.65
        theta = T_K / 288.15
        delta = 0.22336 * np.exp(-g * (altitude_m - 11000) / (287.05 * 216.65))
    else: # Above 20km, approximation
        T_K = 216.65 
        theta = T_K / 288.15
        delta = 0.22336 * np.exp(-g * (altitude_m - 11000) / (287.05 * 216.65))
        # This is a simplification for higher altitudes if needed, model is valid up to 20km strictly
    return delta, theta
    
# --- Parameter Calculation Functions (Lambda1, Lambda2, Lambda3, F_prop) ---
def calculate_Lambda_1_subsonic(r_h, W_MZF_frac, W_MTO, q_hat, b_ref_wing, n_ult, eta_cp_wing, t_c_w, cos_Lambda_w_sq):
    """ Eq 10.12 - Lambda_1 for subsonic wing weight """
    if q_hat <=0 or t_c_w <=0 or cos_Lambda_w_sq <=0 : return np.inf
    return 0.0013 * (1 + r_h) * np.sqrt(W_MZF_frac * W_MTO / q_hat) / b_ref_wing * n_ult * eta_cp_wing / (t_c_w * cos_Lambda_w_sq)

def calculate_phi_2(r_h, Sigma_S_wing, q_hat):
    """ Eq 10.13 - phi_2 for wing secondary structure weight """
    if q_hat <=0 : return np.inf
    return (1 + r_h) * Sigma_S_wing / q_hat

def calculate_phi_3_transonic(r_h, W_MZF_frac, W_MTO, q_hat, b_ref_wing, n_ult, eta_cp_wing):
    """ Eq 10.35 - phi_3 for transonic wing weight (part of Lambda_1 independent of t/c and sweep) """
    if q_hat <=0: return np.inf
    return 0.0013 * (1 + r_h) * eta_cp_wing * n_ult * np.sqrt(W_MZF_frac * W_MTO / q_hat) / b_ref_wing

def calculate_propulsion_function(R_eq, eta_o_cruise, mu_T, tau_cruise, delta_cruise):
    """ Eq 8.32 - Propulsion function F_prop """
    if eta_o_cruise <= 0 or tau_cruise <= 0 or delta_cruise <= 0: return np.inf
    return (R_eq / (eta_o_cruise * H_g)) + (mu_T / (tau_cruise * delta_cruise))

# --- Core Calculation Functions from Previous Response (Sections 10.3, 10.6) ---
# calculate_wing_plus_htail_weight_fraction_subsonic, calculate_WPF_subsonic, calculate_MTOW_subsonic
# calculate_mu_w_plus_h_transonic, calculate_C_Dp_hat_wing_transonic
# calculate_tc_cos2_lambda_limit, get_tc_from_tc_cos2_lambda
# calculate_WPF_transonic, calculate_L_D_wing_plus_htail_transonic
# calculate_optimal_Aw_transonic_given_CL_Lambda

# (Keeping previous functions here, assuming they are correct as per prior context)
def calculate_wing_plus_htail_weight_fraction_subsonic(Lambda_1, phi_2, A_w, C_L_hat):
    if C_L_hat <= 0: return np.inf 
    if A_w <=0: return np.inf
    val_sqrt = A_w / C_L_hat
    if val_sqrt <= 0: return np.inf
    term1 = Lambda_1 * A_w / np.sqrt(val_sqrt)
    term2 = phi_2 / C_L_hat
    return term1 + term2

def calculate_mu_w_plus_h_transonic(phi_3, t_c_w, Lambda_w_rad, A_w, C_L_hat, phi_2):
    if C_L_hat <= 0 or t_c_w <= 0 or np.cos(Lambda_w_rad) == 0 or A_w <=0: return np.inf
    val_sqrt = A_w / C_L_hat
    if val_sqrt <=0: return np.inf
    term1_num = phi_3 * A_w * np.sqrt(val_sqrt)
    term1_den = t_c_w * (np.cos(Lambda_w_rad))**2
    term1 = term1_num / term1_den if term1_den > 0.0001 else np.inf 
    term2 = phi_2 / C_L_hat
    return term1 + term2

def calculate_C_Dp_hat_wing_transonic(t_c_w, Lambda_w_rad, C_f, r_prime=3.0, d_w_h=1.25):
    if t_c_w <0 or C_f <0: return np.inf
    cos_Lambda_w = np.cos(Lambda_w_rad)
    C_Dp_hat_wing_only = 2 * (1 + r_prime * t_c_w * cos_Lambda_w**2) * C_f
    return d_w_h * C_Dp_hat_wing_only

def calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa=0.935):
    cos_Lambda_w = np.cos(Lambda_w_rad)
    if C_L_hat < 0: C_L_hat_pow = - ((-C_L_hat)**1.5) 
    else: C_L_hat_pow = C_L_hat**1.5
    val = (cos_Lambda_w**3) * (M_kappa - M_dd * cos_Lambda_w) - 0.115 * C_L_hat_pow
    return max(0, val) 

def get_tc_from_tc_cos2_lambda(tc_cos2_lambda_val, Lambda_w_rad):
    cos_Lambda_w = np.cos(Lambda_w_rad)
    if abs(cos_Lambda_w) < 0.001: return np.inf 
    return tc_cos2_lambda_val / (cos_Lambda_w**2)

def calculate_WPF_transonic(phi_3, phi_2, F_prop,
                            C_L_hat, A_w, Lambda_w_rad, e_hat,
                            M_dd, M_kappa=0.935, 
                            C_f=0.003, r_prime=3.0, d_w_h=1.25,
                            C_Dc=0.0005, return_tc=False): # Added return_tc
    if C_L_hat <= 0 or A_w <= 0 or e_hat <=0 or F_prop <0 : 
        return np.inf if not return_tc else (np.inf, np.inf)

    tc_cos2_lambda_val = calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa)
    t_c_w = get_tc_from_tc_cos2_lambda(tc_cos2_lambda_val, Lambda_w_rad)
    
    if t_c_w <= 0.01 or t_c_w == np.inf : 
        return np.inf if not return_tc else (np.inf, t_c_w)

    mu_w_plus_h = calculate_mu_w_plus_h_transonic(phi_3, t_c_w, Lambda_w_rad, A_w, C_L_hat, phi_2)
    if mu_w_plus_h == np.inf: return np.inf if not return_tc else (np.inf, t_c_w)

    C_Dp_hat_var = calculate_C_Dp_hat_wing_transonic(t_c_w, Lambda_w_rad, C_f, r_prime, d_w_h)
    if C_Dp_hat_var == np.inf: return np.inf if not return_tc else (np.inf, t_c_w)
        
    drag_term_parasite_profile = C_Dp_hat_var / C_L_hat
    drag_term_compressibility = C_Dc / C_L_hat 
    drag_term_induced = C_L_hat / (np.pi * A_w * e_hat)
    
    total_drag_coeff_over_CL = drag_term_parasite_profile + drag_term_compressibility + drag_term_induced
    
    F_wp = mu_w_plus_h + F_prop * total_drag_coeff_over_CL
    return F_wp if not return_tc else (F_wp, t_c_w)

def calculate_L_D_wing_plus_htail_transonic(C_L_hat, A_w, Lambda_w_rad, e_hat,
                                           M_dd, M_kappa=0.935,
                                           C_f=0.003, r_prime=3.0, d_w_h=1.25,
                                           C_Dc=0.0005):
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
                                                    F_prop, phi_3, e_hat,
                                                    M_dd, M_kappa=0.935):
    if C_L_hat <= 0 or F_prop <0 or phi_3 <=0 or e_hat <=0: return np.inf

    tc_cos2_lambda_val = calculate_tc_cos2_lambda_limit(M_dd, Lambda_w_rad, C_L_hat, M_kappa)
    if tc_cos2_lambda_val <= 0: return np.inf

    numerator = (2/3) * F_prop * C_L_hat * tc_cos2_lambda_val
    denominator = phi_3 * np.pi * e_hat
    if abs(denominator) < 1e-9: return np.inf 
    
    base_val = numerator / denominator
    if base_val < 0: return np.inf

    optimal_A_w = base_val**0.4
    return optimal_A_w
    
# --- Optimization Setup (Conceptual) ---
def objective_WPF_opt(variables, params):
    """ Objective function for scipy.optimize.minimize """
    C_L_hat, A_w, Lambda_w_rad = variables
    phi_3, phi_2, F_prop, e_hat, M_dd, M_kappa, C_f, r_prime, d_w_h, C_Dc = params
    
    wpf = calculate_WPF_transonic(phi_3, phi_2, F_prop,
                                  C_L_hat, A_w, Lambda_w_rad, e_hat,
                                  M_dd, M_kappa, C_f, r_prime, d_w_h, C_Dc)
    return wpf

def perform_optimization_WPF_transonic(params, initial_guess, bounds):
    """
    Conceptual demonstration of optimizing WPF using scipy.minimize.
    Requires specific bounds and potentially constraint handling for a real case.
    """
    print("\n--- Conceptual Optimization Run ---")
    print(f"Initial guess (C_L_hat, A_w, Lambda_w_rad): {initial_guess}")
    print(f"Parameters (phi_3, etc.): {params}")
    
    result = minimize(objective_WPF_opt, initial_guess, args=(params,), method='SLSQP', bounds=bounds) # L-BFGS-B for bounds only
    
    if result.success:
        opt_CL, opt_Aw, opt_Lw_rad = result.x
        opt_WPF, opt_tc = calculate_WPF_transonic(*params[0:2], params[2], opt_CL, opt_Aw, opt_Lw_rad, *params[3:], return_tc=True)
        
        print("Optimization Successful:")
        print(f"  Optimized C_L_hat: {opt_CL:.3f}")
        print(f"  Optimized A_w: {opt_Aw:.2f}")
        print(f"  Optimized Lambda_w: {np.rad2deg(opt_Lw_rad):.2f} deg")
        print(f"  Resulting (t/c)_w: {opt_tc:.4f}")
        print(f"  Minimum WPF: {opt_WPF:.4f}")
        return result.x, opt_WPF, opt_tc
    else:
        print("Optimization Failed:", result.message)
        return None, None, None

# --- Plotting Functions from previous response (plot_figure_10_10, _11, _12) ---
# (Assumed to be here)
def plot_figure_10_10(C_L_hat_fixed=0.55, M_kappa_fixed=0.935):
    Lambda_w_deg_range = np.linspace(0, 50, 100)
    Lambda_w_rad_range = np.deg2rad(Lambda_w_deg_range)
    M_dd_values = [0.70, 0.75, 0.80, 0.85, 0.90]
    plt.figure(figsize=(8, 6))
    for M_dd in M_dd_values:
        tc_cos2_lambda_results = [calculate_tc_cos2_lambda_limit(M_dd, lw_rad, C_L_hat_fixed, M_kappa_fixed)
                                  for lw_rad in Lambda_w_rad_range]
        plt.plot(Lambda_w_deg_range, tc_cos2_lambda_results, label=f'$M_{{dd}}={M_dd:.2f}$')
    plt.xlabel('Wing Sweep $\Lambda_w$ (degrees)'); plt.ylabel('$(t/c)_w \cos^2 \Lambda_w$')
    plt.title(f'Fig 10.10 Approx: $(t/c)_w \cos^2 \Lambda_w$ vs. Sweep ($C_{{L,hat}}={C_L_hat_fixed}$)')
    plt.legend(); plt.grid(True); plt.ylim(0, 0.16); plt.show()

def plot_figure_10_11(A_w_fixed=9.0, M_dd_fixed=0.825, M_kappa_fixed=0.935, params=None):
    if params is None: raise ValueError("Params must be provided for plot_figure_10_11")
    phi_3_val, phi_2_val, F_prop_val, e_hat_fixed, _, _, C_f_fixed, r_prime_fixed, d_w_h_fixed, C_Dc_fixed = params

    Lambda_w_deg_range = np.linspace(0, 50, 50)
    Lambda_w_rad_range = np.deg2rad(Lambda_w_deg_range)
    C_L_hat_values = [0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8]
    fig, ax1 = plt.subplots(figsize=(10, 7))
    colors = plt.cm.viridis(np.linspace(0, 1, len(C_L_hat_values)))
    for idx, C_L_hat in enumerate(C_L_hat_values):
        wpf_results = [calculate_WPF_transonic(phi_3_val, phi_2_val, F_prop_val, C_L_hat, A_w_fixed,
                                               lw_rad, e_hat_fixed, M_dd_fixed, M_kappa_fixed, C_f_fixed,
                                               r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
                       for lw_rad in Lambda_w_rad_range]
        ax1.plot(Lambda_w_deg_range, wpf_results, label=f'WPF $C_{{L,hat}}={C_L_hat:.2f}$', color=colors[idx])
    ax1.set_xlabel('Wing Sweep $\Lambda_w$ (degrees)'); ax1.set_ylabel('Wing Penalty Function (WPF)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue'); ax1.set_ylim(0.32, 0.42); ax1.grid(True, linestyle=':', alpha=0.7)
    ax2 = ax1.twinx()
    for idx, C_L_hat in enumerate(C_L_hat_values):
        ld_results = [calculate_L_D_wing_plus_htail_transonic(C_L_hat, A_w_fixed, lw_rad, e_hat_fixed, M_dd_fixed,
                                                            M_kappa_fixed, C_f_fixed, r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
                      for lw_rad in Lambda_w_rad_range]
        ax2.plot(Lambda_w_deg_range, ld_results, linestyle='--', label=f'L/D $C_{{L,hat}}={C_L_hat:.2f}$', color=colors[idx])
    ax2.set_ylabel('$(L/D)_{w+h}$', color='green'); ax2.tick_params(axis='y', labelcolor='green'); ax2.set_ylim(20, 30)
    L_W_DEG, C_L_H_mesh = np.meshgrid(Lambda_w_deg_range, np.array(C_L_hat_values))
    T_C_W_grid = np.array([[get_tc_from_tc_cos2_lambda(calculate_tc_cos2_lambda_limit(M_dd_fixed, np.deg2rad(lw_deg), clh, M_kappa_fixed), np.deg2rad(lw_deg))
                           for lw_deg in Lambda_w_deg_range] for clh in C_L_hat_values])
    contour_tc = ax1.contour(L_W_DEG, C_L_H_mesh, T_C_W_grid, levels=[0.08, 0.10, 0.12, 0.14, 0.16], colors='grey', linestyles='-.')
    ax1.clabel(contour_tc, inline=True, fontsize=8, fmt='t/c=%.2f')
    fig.tight_layout(); plt.title(f'Fig 10.11 Approx: WPF & L/D vs. Sweep ($A_w={A_w_fixed}, M_{{dd}}={M_dd_fixed}$)')
    lines_ax1, labels_ax1 = ax1.get_legend_handles_labels()
    # ax2.legend(lines_ax1, labels_ax1, loc='upper right', fontsize='small') # Avoid duplicate legends
    plt.show()

def plot_figure_10_12(Lambda_w_deg_fixed=30.0, M_dd_fixed=0.825, params=None, q_hat_cruise_eg=30000):
    if params is None: raise ValueError("Params must be provided for plot_figure_10_12")
    phi_3_val, phi_2_val, F_prop_val, e_hat_fixed, M_kappa_fixed, _, C_f_fixed, r_prime_fixed, d_w_h_fixed, C_Dc_fixed = params
    
    C_L_hat_range = np.linspace(0.3, 0.9, 30)
    A_w_range = np.linspace(4, 16, 30)
    Lambda_w_rad_fixed = np.deg2rad(Lambda_w_deg_fixed)
    CLH_mesh, AW_mesh = np.meshgrid(C_L_hat_range, A_w_range)
    WPF_grid = np.array([[calculate_WPF_transonic(phi_3_val, phi_2_val, F_prop_val, clh, aw,
                                                 Lambda_w_rad_fixed, e_hat_fixed, M_dd_fixed, M_kappa_fixed, C_f_fixed,
                                                 r_prime_fixed, d_w_h_fixed, C_Dc_fixed)
                         for clh in C_L_hat_range] for aw in A_w_range]) # Corrected loop order for meshgrid
    plt.figure(figsize=(10, 7))
    contour_wpf = plt.contour(CLH_mesh, AW_mesh, WPF_grid, levels=np.arange(0.33, 0.41, 0.005), cmap='viridis')
    plt.clabel(contour_wpf, inline=True, fontsize=8, fmt='%.3f')
    opt_A_w_line = [calculate_optimal_Aw_transonic_given_CL_Lambda(cl, Lambda_w_rad_fixed, F_prop_val, phi_3_val, e_hat_fixed, M_dd_fixed, M_kappa_fixed) for cl in C_L_hat_range]
    plt.plot(C_L_hat_range, opt_A_w_line, 'k--', label='Opt $A_w$ (dFwp/dAw=0)')
    
    # Illustrative Constraints
    span_load_const_val_Pa = 5500 # N/m^2; W_MTO/b_w^2
    # W_MTO / b_w^2 = (q_hat * C_L_hat * S_w) / (A_w * S_w) = q_hat * C_L_hat / A_w
    A_w_span_load = (q_hat_cruise_eg / span_load_const_val_Pa) * C_L_hat_range
    plt.plot(C_L_hat_range, A_w_span_load, 'r:', label=f'Span Load Limit ({span_load_const_val_Pa:.0f} N/m$^2$)')
    plt.axvline(x=0.8, color='m', linestyle='-.', label='Buffet Limit ($C_L \leq 0.8$)')
    plt.axhline(y=10, color='c', linestyle=':', label='Pitch-up Limit ($A_w \leq 10$)')
    
    plt.xlabel('Design Lift Coefficient $C_{L,hat}$'); plt.ylabel('Aspect Ratio $A_w$')
    plt.title(f'Fig 10.12 Approx: WPF Contours ($\Lambda_w={Lambda_w_deg_fixed}^\circ, M_{{dd}}={M_dd_fixed}$)')
    plt.legend(fontsize='small'); plt.grid(True, linestyle=':', alpha=0.7); plt.ylim(min(A_w_range), max(A_w_range)); plt.xlim(min(C_L_hat_range), max(C_L_hat_range))
    plt.colorbar(contour_wpf, label='WPF'); plt.show()

# --- Functions for Figure 10.13 ---
def calculate_WPF_transonic_fixed_tc(phi_3_fixed_tc_Lambda, phi_2, F_prop,
                                     C_L_hat, A_w, e_hat,
                                     C_Dp_hat_fixed_tc_Lambda, C_Dc=0.0005):
    """ WPF for fixed t/c and Lambda_w (profile & weight terms become simpler). """
    if C_L_hat <= 0 or A_w <= 0 or e_hat <= 0: return np.inf
    # Weight term: K_wt1 * A_w^1.5 * C_L_hat^-0.5 + K_wt2 * C_L_hat^-1
    # K_wt1 = phi_3 / ( (t/c)_w * cos^2(Lambda_w) )
    # K_wt2 = phi_2
    mu_w_plus_h = phi_3_fixed_tc_Lambda * A_w * np.sqrt(A_w/C_L_hat) + phi_2 / C_L_hat
    
    # Drag term: F_prop * ( (C_Dp_profile_fixed + C_Dc)/C_L_hat + C_L_hat/(pi*A_w*e_hat) )
    drag_contrib = F_prop * ( (C_Dp_hat_fixed_tc_Lambda + C_Dc)/C_L_hat + C_L_hat / (np.pi * A_w * e_hat) )
    return mu_w_plus_h + drag_contrib

def plot_figure_10_13(params_const_Mdd, params_fixed_tc, # Provide all necessary parameters
                        M_dd_fixed=0.825, Lambda_w_deg_fixed_for_tc_calc=30, C_L_hat_for_tc_calc=0.55, t_c_w_fixed_val=None):
    """ Plots conceptual comparison for Figure 10.13. """
    C_L_hat_range = np.linspace(0.3, 0.9, 30)
    A_w_range = np.linspace(4, 16, 30)
    CLH_mesh, AW_mesh = np.meshgrid(C_L_hat_range, A_w_range)
    Lambda_w_rad_fixed_for_tc_calc = np.deg2rad(Lambda_w_deg_fixed_for_tc_calc)

    # --- Constant M_dd case ---
    L3_mdd, L2_mdd, Fp_mdd, eh_mdd, Mk_mdd, _, Cf_mdd, rp_mdd, dwh_mdd, Cdc_mdd = params_const_Mdd
    opt_Aw_const_Mdd = [calculate_optimal_Aw_transonic_given_CL_Lambda(
        cl, Lambda_w_rad_fixed_for_tc_calc, Fp_mdd, L3_mdd, eh_mdd, M_dd_fixed, Mk_mdd) for cl in C_L_hat_range]
    # For opt_CL_const_Mdd, we'd numerically minimize WPF_transonic for fixed A_w
    opt_CL_const_Mdd = []
    for aw_val in A_w_range:
        obj_func = lambda cl: calculate_WPF_transonic(L3_mdd, L2_mdd, Fp_mdd, cl, aw_val, Lambda_w_rad_fixed_for_tc_calc, eh_mdd, M_dd_fixed, Mk_mdd, Cf_mdd, rp_mdd, dwh_mdd, Cdc_mdd)
        res = minimize(obj_func, x0=0.55, bounds=[(0.2, 1.0)])
        if res.success: opt_CL_const_Mdd.append(res.x[0])
        else: opt_CL_const_Mdd.append(np.nan)

    plt.figure(figsize=(8,6))
    plt.plot(C_L_hat_range, opt_Aw_const_Mdd, 'b-', label='Opt $A_w$ (const $M_{dd}$)')
    plt.plot(opt_CL_const_Mdd, A_w_range, 'b--', label='Opt $C_L$ (const $M_{dd}$)')

    # --- Constant t/c case ---
    if t_c_w_fixed_val is None: # Derive a t_c from the M_dd case for comparison
        tc_cos2 = calculate_tc_cos2_lambda_limit(M_dd_fixed, Lambda_w_rad_fixed_for_tc_calc, C_L_hat_for_tc_calc, Mk_mdd)
        t_c_w_fixed_val = get_tc_from_tc_cos2_lambda(tc_cos2, Lambda_w_rad_fixed_for_tc_calc)
    print(f"Using fixed t/c = {t_c_w_fixed_val:.4f} for comparison plot.")

    L3_ftc, L2_ftc, Fp_ftc, eh_ftc, Cf_ftc, rp_ftc, dwh_ftc, Cdc_ftc = params_fixed_tc
    # Pre-calculate terms for fixed t/c, fixed Lambda_w
    phi_3_eff_fixed_tc = L3_ftc / (t_c_w_fixed_val * np.cos(Lambda_w_rad_fixed_for_tc_calc)**2)
    C_Dp_fixed_tc = calculate_C_Dp_hat_wing_transonic(t_c_w_fixed_val, Lambda_w_rad_fixed_for_tc_calc, Cf_ftc, rp_ftc, dwh_ftc)

    opt_CL_const_tc = []
    for aw_val in A_w_range:
        obj_func_tc = lambda cl: calculate_WPF_transonic_fixed_tc(phi_3_eff_fixed_tc, L2_ftc, Fp_ftc, cl, aw_val, eh_ftc, C_Dp_fixed_tc, Cdc_ftc)
        res = minimize(obj_func_tc, x0=0.55, bounds=[(0.2,1.0)])
        if res.success: opt_CL_const_tc.append(res.x[0])
        else: opt_CL_const_tc.append(np.nan)
    
    # Optimal Aw for fixed t/c (re-deriving form similar to Eq 10.18 for the more complex WPF)
    # Fwp_fixed_tc ~ K1*Aw^1.5*CL^-0.5 + K2*CL^-1 + K3*CL*Aw^-1
    # dFwp/dAw = 1.5*K1*Aw^0.5*CL^-0.5 - K3*CL*Aw^-2 = 0 => 1.5*K1*Aw^2.5 = K3*CL^1.5 => Aw_opt = (K3*CL^1.5 / (1.5*K1) )^0.4
    opt_Aw_const_tc = []
    for cl_val in C_L_hat_range:
        K1 = phi_3_eff_fixed_tc
        K3_term = Fp_ftc / (np.pi * eh_ftc)
        if K1 <= 0: opt_Aw_const_tc.append(np.nan); continue
        base = (K3_term * cl_val**1.5) / (1.5 * K1)
        if base < 0: opt_Aw_const_tc.append(np.nan); continue
        opt_Aw_const_tc.append(base**0.4)

    plt.plot(C_L_hat_range, opt_Aw_const_tc, 'g-', label=f'Opt $A_w$ (fixed $t/c={t_c_w_fixed_val:.3f}$)')
    plt.plot(opt_CL_const_tc, A_w_range, 'g--', label=f'Opt $C_L$ (fixed $t/c={t_c_w_fixed_val:.3f}$)')

    plt.xlabel('$C_{L,hat}$'); plt.ylabel('$A_w$')
    plt.title('Fig 10.13 Conceptual: Optima Comparison')
    plt.legend(fontsize='small'); plt.grid(True); plt.ylim(4,16); plt.xlim(0.3,0.9); plt.show()

def plot_figure_10_14_illustrative(M_cruise_example=0.81):
    """ Illustrative plot for Figure 10.14 Buffet Boundary. """
    mach_range = np.linspace(0.6, 0.9, 50)
    # Example buffet onset C_L (decreases with Mach)
    C_L_buffet = 0.9 - 0.7 * (mach_range - 0.6) / 0.3 + 0.1 * np.sin(10*(mach_range-0.6)) # صنع نموذجا تمثيليا
    
    # Example cruise path for constant W/delta (C_L ~ 1/M^2)
    # Assume C_L = 0.5 at M = 0.8, so C_L * M^2 = 0.5 * 0.8^2 = 0.32
    C_L_cruise_path = 0.32 / mach_range**2
    
    plt.figure(figsize=(8,6))
    plt.plot(mach_range, C_L_buffet, 'r-', label='Buffet Onset Boundary (Illustrative)')
    plt.plot(mach_range, C_L_cruise_path, 'b--', label='Cruise Path ($W/\delta$=const, Illustrative)')
    
    # Mark buffet margin at a cruise Mach number
    if M_cruise_example in mach_range:
        cl_buffet_at_Mcruise = np.interp(M_cruise_example, mach_range, C_L_buffet)
        cl_cruise_at_Mcruise = np.interp(M_cruise_example, mach_range, C_L_cruise_path)
        plt.vlines(M_cruise_example, cl_cruise_at_Mcruise, cl_buffet_at_Mcruise, colors='k', linestyles='dotted', label=f'Buffet Margin at M={M_cruise_example}')
        plt.scatter([M_cruise_example, M_cruise_example], [cl_cruise_at_Mcruise, cl_buffet_at_Mcruise], color='k')

    plt.xlabel('Mach Number'); plt.ylabel('$C_L$')
    plt.title('Fig 10.14 Illustrative: Buffet Boundary & Cruise Path')
    plt.legend(); plt.grid(True); plt.ylim(0, 1.0); plt.xlim(0.6, 0.9); plt.show()

def calculate_n_gust(K_g, rho_sl_val, U_DE, V_EAS, S_w, W_G, dCL_dalpha):
    """ Calculates gust load factor increment (Eq 10.53 part). """
    if W_G <=0: return np.inf
    return K_g * 0.5 * rho_sl_val * U_DE * V_EAS * S_w * dCL_dalpha / W_G

def calculate_K_g(mu_g):
    """ Calculates gust alleviation factor K_g (Eq 11.8). """
    if (5.3 + mu_g) == 0: return 0 # Avoid division by zero
    return 0.88 * mu_g / (5.3 + mu_g)

def calculate_mu_g(W_G, b_w, rho_val, S_w, dCL_dalpha):
    """ Calculates mass parameter mu_g (Eq 11.8). """
    if rho_val <=0 or S_w <=0 or dCL_dalpha <=0 : return np.inf
    return 2 * W_G / (rho_val * g * S_w * b_w * dCL_dalpha) # Using b instead of S^2_w

def plot_figure_10_15_illustrative(params, M_dd_fixed=0.825, Lambda_w_deg_fixed=30.0,
                                     n_man_limit=2.5, CLmax_landing_limit=2.8,
                                     # Params for n_gust
                                     U_DE_ms=15.24, V_EAS_ms=180, dCL_dalpha_rad=5.0, W_MTO_ref_N=1e6,
                                     rho_cruise_val = 0.4 # kg/m3 approx at 9km
                                     ):
    """ Illustrative plot for Figure 10.15 Constraint Refinement. """
    # Using Wing Loading W_MTO/S_w as x-axis
    wing_loading_range_Pa = np.linspace(3000, 9000, 50) # N/m^2
    Lambda_w_rad = np.deg2rad(Lambda_w_deg_fixed)
    
    # Fixed A_w for simplicity in this illustration
    A_w_fixed_plot = 9.0
    S_w_range = W_MTO_ref_N / wing_loading_range_Pa
    C_L_hat_range = wing_loading_range_Pa / params['q_hat_cruise'] # q_hat needs to be in params

    wpf_values_case_a = []
    wpf_values_case_b = []

    for i, wl_Pa in enumerate(wing_loading_range_Pa):
        CLh = C_L_hat_range[i]
        Sw = S_w_range[i]
        b_w = np.sqrt(A_w_fixed_plot * Sw)

        # Case A: n_ult fixed based on n_man_limit, CLmax fixed
        n_ult_case_a = 1.5 * n_man_limit
        current_phi_3 = calculate_phi_3_transonic(params['r_h'], params['W_MZF_frac'], W_MTO_ref_N, params['q_hat_cruise'], params['b_ref_wing'], n_ult_case_a, params['eta_cp_wing'])
        wpf_a = calculate_WPF_transonic(current_phi_3, params['phi_2'], params['F_prop'], CLh, A_w_fixed_plot, Lambda_w_rad, params['e_hat'], M_dd_fixed, params['M_kappa'], params['C_f'], params['r_prime'], params['d_w_h'], params['C_Dc'])
        wpf_values_case_a.append(wpf_a)

        # Case B: n_ult varies (gust vs maneuver), CLmax varies (conceptual)
        mu_g_val = calculate_mu_g(W_MTO_ref_N, b_w, rho_cruise_val, Sw, dCL_dalpha_rad) # rho at cruise for V_EAS
        K_g_val = calculate_K_g(mu_g_val)
        n_gust_increment = calculate_n_gust(K_g_val, rho_sl, U_DE_ms, V_EAS_ms, Sw, W_MTO_ref_N, dCL_dalpha_rad)
        n_gust_val = 1 + n_gust_increment
        n_eff_for_ult = max(n_man_limit, n_gust_val)
        n_ult_case_b = 1.5 * n_eff_for_ult
        
        current_phi_3_b = calculate_phi_3_transonic(params['r_h'], params['W_MZF_frac'], W_MTO_ref_N, params['q_hat_cruise'], params['b_ref_wing'], n_ult_case_b, params['eta_cp_wing'])
        wpf_b = calculate_WPF_transonic(current_phi_3_b, params['phi_2'], params['F_prop'], CLh, A_w_fixed_plot, Lambda_w_rad, params['e_hat'], M_dd_fixed, params['M_kappa'], params['C_f'], params['r_prime'], params['d_w_h'], params['C_Dc'])
        wpf_values_case_b.append(wpf_b)

    plt.figure(figsize=(10,6))
    plt.plot(wing_loading_range_Pa / 1000, wpf_values_case_a, label='WPF (Case A: $n_{ult}, C_{Lmax}$ fixed constraints)')
    plt.plot(wing_loading_range_Pa / 1000, wpf_values_case_b, '--', label='WPF (Case B: $n_{ult}$ varies, conceptual $C_{Lmax}$ effect)')

    # Illustrate a constraint line (e.g., landing speed related to CLmax_landing_limit)
    # V_app_limit_ms = 70 # m/s example
    # wing_loading_land_limit_Pa = 0.5 * rho_sl * V_app_limit_ms**2 * CLmax_landing_limit / (1.3**2) # W/S <= ...
    # MLW_MTOW_ratio = 0.85 # Assume MLW = 0.85 MTOW
    # wing_loading_takeoff_limit_Pa = wing_loading_land_limit_Pa / MLW_MTOW_ratio
    # plt.axvline(x=wing_loading_takeoff_limit_Pa/1000, color='r', linestyle=':', label=f'$C_{{Lmax}}={CLmax_landing_limit}$ limit')

    # Find and mark optima conceptually
    min_wpf_a_idx = np.argmin(wpf_values_case_a)
    plt.scatter(wing_loading_range_Pa[min_wpf_a_idx]/1000, wpf_values_case_a[min_wpf_a_idx], color='blue', s=100, label='Optimum (Case A)', zorder=5)
    
    min_wpf_b_idx = np.argmin(wpf_values_case_b) # This will be shifted if n_ult variation is significant
    plt.scatter(wing_loading_range_Pa[min_wpf_b_idx]/1000, wpf_values_case_b[min_wpf_b_idx], color='green', s=100, marker='x', label='Optimum (Case B)', zorder=5)

    plt.xlabel('Wing Loading $W_{MTO}/S_w$ (kN/m$^2$)')
    plt.ylabel('Wing Penalty Function (WPF)')
    plt.title('Fig 10.15 Illustrative: Constraint Refinement Effect on WPF')
    plt.legend(fontsize='small'); plt.grid(True); plt.ylim(min(np.nanmin(wpf_values_case_a), np.nanmin(wpf_values_case_b))*0.95, max(np.nanmax(wpf_values_case_a),np.nanmax(wpf_values_case_b))*1.05)
    plt.show()


# --- Example Usage ---
if __name__ == '__main__':
    print("--- Aircraft Design Formulas & Plots (Chapter 10) ---")

    # Define a dictionary of baseline parameters for the transonic aircraft example
    # These would be specific to "your design"
    baseline_params = {
        'W_MTO_N': 1100e3 * g,  # Example MTOW from Fig 8.1 baseline in Newtons
        'W_MZF_frac': 0.75,     # Assumed (MTOW - Max Fuel) / MTOW or (OEW+Payload)/MTOW
        'r_h': 0.1,             # horizontal tail weight fraction of wing weight
        'eta_cp_wing': 0.4,     # spanwise center of pressure
        'b_ref_wing': 50.0,     # m, reference span for wing weight formula
        'n_ult_design': 3.75,   # Ultimate load factor (1.5 * 2.5)
        'Sigma_S_wing': 210.0,  # N/m^2, specific secondary structure weight (Eq 8.1)
        'M_cruise': 0.81,       # Design cruise Mach
        'alt_cruise_m': 10668,  # 35,000 ft in meters
        'R_eq_km': 7000,        # Equivalent mission range km
        'eta_o_cruise': 0.35,   # Overall engine efficiency
        'mu_T': 0.25,           # Powerplant weight / T_TO
        'tau_cruise': 0.8,      # Cruise thrust lapse T_cruise / (delta * T_TO)
        'e_hat': 0.90,          # Oswald efficiency factor (modified for design)
        'M_dd_target': 0.825,   # Target drag divergence Mach
        'M_kappa': 0.935,       # Korn's equation technology factor
        'C_f_skin': 0.0028,     # Skin friction coefficient
        'r_prime_tc': 3.0,      # Form factor for t/c drag
        'd_w_h_drag': 1.25,     # Htail drag factor
        'C_Dc_comp': 0.0008,    # Base compressibility drag (8 counts)
    }
    
    # Calculate derived parameters
    delta_cruise_val, theta_cruise_val = get_isa_delta_theta(baseline_params['alt_cruise_m'])
    p_cruise_val = delta_cruise_val * p_sl
    baseline_params['q_hat_cruise'] = dynamic_pressure_mach(p_cruise_val, baseline_params['M_cruise'])
    
    phi_3_calc = calculate_phi_3_transonic(baseline_params['r_h'], baseline_params['W_MZF_frac'], baseline_params['W_MTO_N'],
                                                 baseline_params['q_hat_cruise'], baseline_params['b_ref_wing'],
                                                 baseline_params['n_ult_design'], baseline_params['eta_cp_wing'])
    phi_2_calc = calculate_phi_2(baseline_params['r_h'], baseline_params['Sigma_S_wing'], baseline_params['q_hat_cruise'])
    F_prop_calc = calculate_propulsion_function(baseline_params['R_eq_km'], baseline_params['eta_o_cruise'],
                                                baseline_params['mu_T'], baseline_params['tau_cruise'], delta_cruise_val)

    print(f"Calculated q_hat_cruise: {baseline_params['q_hat_cruise']:.0f} Pa")
    print(f"Calculated phi_3: {phi_3_calc:.6f}")
    print(f"Calculated phi_2: {phi_2_calc:.6f}")
    print(f"Calculated F_prop: {F_prop_calc:.3f}")

    # Parameters for WPF optimizer and plots (order matters for objective_WPF_opt)
    opt_plot_params = [phi_3_calc, phi_2_calc, F_prop_calc, baseline_params['e_hat'], 
                       baseline_params['M_kappa'], baseline_params['C_f_skin'], 
                       baseline_params['r_prime_tc'], baseline_params['d_w_h_drag'], baseline_params['C_Dc_comp']]
    
    # --- Perform Conceptual Optimization ---
    # Variables: [C_L_hat, A_w, Lambda_w_rad]
    initial_guess_opt = [0.55, 9.0, np.deg2rad(30.0)] 
    bounds_opt = [(0.2, 0.9), (5, 15), (np.deg2rad(0), np.deg2rad(45))] # Example bounds
    
    # This is conceptual; a full MDO setup would have more constraints.
    # perform_optimization_WPF_transonic(opt_plot_params_for_objective, initial_guess_opt, bounds_opt)
    # Note: scipy.optimize.minimize may require careful setup of constraints for M_dd

    # --- Plotting Figures ---
    plot_figure_10_10(C_L_hat_fixed=0.55, M_kappa_fixed=baseline_params['M_kappa'])
    
    # For plot_figure_10_11, params are:
    # phi_3, phi_2, F_prop, e_hat, M_dd, M_kappa, C_f, r_prime, d_w_h, C_Dc
    params_10_11 = [phi_3_calc, phi_2_calc, F_prop_calc, 
                    baseline_params['e_hat'], baseline_params['M_dd_target'], baseline_params['M_kappa'],
                    baseline_params['C_f_skin'], baseline_params['r_prime_tc'], 
                    baseline_params['d_w_h_drag'], baseline_params['C_Dc_comp']]
    plot_figure_10_11(A_w_fixed=9.0, M_dd_fixed=baseline_params['M_dd_target'], params=params_10_11)

    plot_figure_10_12(Lambda_w_deg_fixed=30.0, M_dd_fixed=baseline_params['M_dd_target'], params=params_10_11, q_hat_cruise_eg=baseline_params['q_hat_cruise'])
    
    # For plot_figure_10_13
    # params_const_Mdd is params_10_11
    # params_fixed_tc needs: L3_eff, L2, Fp, eh, Cf, rp, dwh, Cdc_ftc
    # L3_eff = phi_3 / ( (t/c)_w_fixed * cos^2(Lambda_w_fixed) )
    # C_Dp_fixed_tc = calculate_C_Dp_hat_wing_transonic(t_c_w_fixed, Lambda_w_rad_fixed, Cf, rp, dwh)
    # This requires selecting a fixed t/c and Lambda_w for the "fixed_tc" case.
    # Let's derive t_c for C_L=0.55, Lambda=30deg, Mdd=0.825
    tc_cos2_ref = calculate_tc_cos2_lambda_limit(baseline_params['M_dd_target'], np.deg2rad(30), 0.55, baseline_params['M_kappa'])
    t_c_w_ref_for_plot13 = get_tc_from_tc_cos2_lambda(tc_cos2_ref, np.deg2rad(30))

    phi_3_eff_fixed_tc_val = phi_3_calc / (t_c_w_ref_for_plot13 * np.cos(np.deg2rad(30))**2) if (t_c_w_ref_for_plot13 * np.cos(np.deg2rad(30))**2) > 0 else np.inf
    C_Dp_fixed_tc_val = calculate_C_Dp_hat_wing_transonic(t_c_w_ref_for_plot13, np.deg2rad(30), baseline_params['C_f_skin'], baseline_params['r_prime_tc'], baseline_params['d_w_h_drag'])
    
    params_for_10_13_fixed_tc = [phi_3_eff_fixed_tc_val, phi_2_calc, F_prop_calc, 
                                 baseline_params['e_hat'], baseline_params['C_f_skin'], 
                                 baseline_params['r_prime_tc'], baseline_params['d_w_h_drag'], baseline_params['C_Dc_comp']]
    
    plot_figure_10_13(params_const_Mdd=params_10_11, params_fixed_tc=params_for_10_13_fixed_tc,
                        M_dd_fixed=baseline_params['M_dd_target'],
                        Lambda_w_deg_fixed_for_tc_calc=30, C_L_hat_for_tc_calc=0.55,
                        t_c_w_fixed_val=t_c_w_ref_for_plot13)

    plot_figure_10_14_illustrative(M_cruise_example=baseline_params['M_cruise'])
    plot_figure_10_15_illustrative(params=baseline_params, M_dd_fixed=baseline_params['M_dd_target'])
