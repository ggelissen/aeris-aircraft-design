# Wing_Planform_Adv_AC_Design_torenbeek.py

import numpy as np
import math
import matplotlib.pyplot as plt
import sys
import os

# Allow imports from parent directory to access design_variables
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters

# --- Constants ---
H_g = 4350  # km, Fuel specific energy (H/g) for jet fuel (kerosene)
g = 9.80665 # m/s^2, standard gravity

# --- Calculation Functions from Torenbeek ---

def calculate_propulsion_function(R_eq, eta_o_cruise, mu_T, tau_cruise, delta_cruise):
    """Calculates the propulsion function F_prop. Based on Eq. 10.9."""
    if eta_o_cruise <= 0 or tau_cruise <= 0 or delta_cruise <= 0: return np.inf
    fuel_term = R_eq / (eta_o_cruise * H_g)
    engine_weight_term = mu_T / (tau_cruise * delta_cruise)
    return fuel_term + engine_weight_term

def calculate_WPF_transonic(phi_3, phi_2, F_prop, C_L_hat, A_w, Lambda_w_rad, e_hat, M_dd, M_kappa, C_f, C_Dc, return_tc=False):
    """Calculates the Wing Penalty Function (WPF) for transonic aircraft. Based on Eq. 10.43."""
    if C_L_hat <= 1e-6 or A_w <= 0 or e_hat <= 0:
        return (np.inf, np.inf) if return_tc else np.inf

    # Step 1: Determine max allowed thickness from M_dd constraint (Eq. 10.49)
    cos_Lambda_w = np.cos(Lambda_w_rad)
    if C_L_hat < 0: return (np.inf, np.inf) if return_tc else np.inf
    tc_cos2_val = (cos_Lambda_w**3) * (M_kappa - M_dd * cos_Lambda_w) - 0.115 * C_L_hat**1.5
    tc_cos2_val = max(0, tc_cos2_val)

    # Step 2: Get the t/c ratio
    if cos_Lambda_w**2 < 1e-6: return (np.inf, np.inf) if return_tc else np.inf
    t_c_w = tc_cos2_val / (cos_Lambda_w**2)
    if t_c_w <= 0.05: return (np.inf, t_c_w) if return_tc else np.inf

    # Step 3: Calculate wing & tail structure weight fraction, mu_w+h (Eq. 10.34)
    mu_w_plus_h = (phi_3 * A_w * np.sqrt(A_w / C_L_hat)) / (t_c_w * cos_Lambda_w**2) + (phi_2 / C_L_hat)

    # Step 4: Calculate wing & tail profile drag coefficient, C_Dp_hat (Eq. 10.39)
    C_Dp_hat_var = 2 * (1 + 3.0 * t_c_w * cos_Lambda_w**2) * C_f * 1.25

    # Step 5: Combine into the final WPF (Eq. 10.43)
    drag_term = F_prop * ((C_Dp_hat_var + C_Dc) / C_L_hat + C_L_hat / (np.pi * A_w * e_hat))
    wpf = mu_w_plus_h + drag_term

    return (wpf, t_c_w) if return_tc else wpf

def calculate_MTOW(W_pay, W_fix_other, F_prop, q_hat, C_Dp_S_fix, mu_resf, mu_lg, F_wp):
    """Calculates Maximum Take-Off Weight (MTOW). Based on Eq. 10.15."""
    denominator = 1 - (mu_resf + mu_lg + F_wp)
    if denominator <= 0: return float('inf')
    numerator = W_pay + W_fix_other + F_prop * q_hat * C_Dp_S_fix
    return numerator / denominator

# --- Module-Specific Functions ---

def calculate_torenbeek_inputs_from_params(params: DesignParameters) -> dict:
    """Calculates the primary input parameters for the Torenbeek optimization from the DesignParameters object."""
    # --- Mission and Weight ---
    R_eq_km = params.range / 1000 * 1.05  # Equivalent Range (km) with 5% margin
    W_pay_N = params.weight.W_PL
    W_MZF_N = params.weight.W_OE + params.weight.W_PL
    mu_resf = params.weight.M_tfo
    mu_lg = 0.04  # Placeholder for landing gear weight fraction TODO, might be able to get from preliminary sizing undercarriage

    # Estimate fixed other weight (fuselage, systems) as a fraction of OEW
    W_fix_other_N = params.weight.W_OE * 0.4 # TODO, major assumption

    # --- Propulsion ---
    eta_o = 0.31 # Placeholder, could be derived from TSFC TODO, check with Arthur
    # Power plant weight per unit take-off thrust
    mu_T = params.engine.engine_weight / params.engine.T_TO if params.engine.T_TO > 0 else 0.172
    print(f"Propulsion weight fraction (mu_T): {mu_T:.4f}")
    tau_cruise = 0.85 # Placeholder for thrust lapse
    
    # --- Performance ---
    q_hat_Pa = 0.5 * params.cruise_density * params.cruise_speed**2
    print(f"Dynamic pressure at cruise (q_hat): {q_hat_Pa:.2f} Pa")
    C_Dp_S_fix_m2 = 0.25  # Placeholder for fixed parasite drag area TODO, check with detailed drag buildup

    # --- Wing Weight Parameters ---
    n_ult = params.max_load_factor * 1.5
    n_ult = 3.75 # TODO, placeholder, should be derived from design parameters
    # Eq. 10.35 for phi_3
    phi_3 = (0.0013 * (1 + 0.15) * 1.0 * n_ult / 100) * math.sqrt(W_MZF_N / q_hat_Pa)
    # Eq. 10.13 for phi_2
    phi_2 = 0.025 # Using Torenbeek's typical value for now

    # --- Technology Levels ---
    M_des = params.cruise_mach
    M_dd = M_des + 0.015 # Vargas and Vos, or 0.03 from Eq. 10.41 context Torembeek
    M_kappa = params.wing.Mach_cross  # 0.935, for supercritical airfoil
    e_hat = 0.90
    C_Dc = 0.0008 # Eq. 10.42 context
    C_f = 0.00225

    # --- Calculate F_prop ---
    # Simplified delta_cruise for high altitude
    delta_cruise = params.cruise_density / 1.225 # TODO, was a magic number in the original code, check with Mrugank's functions
    delta_cruise = 0.246
    F_prop = calculate_propulsion_function(R_eq_km, eta_o, mu_T, tau_cruise, delta_cruise)  # Eq. 10.9, or another, 8.32 maybe?

    inputs = {
        "F_prop": F_prop, "phi_3": phi_3, "phi_2": phi_2, "W_pay_N": W_pay_N,
        "W_fix_other_N": W_fix_other_N, "C_Dp_S_fix_m2": C_Dp_S_fix_m2,
        "q_hat_Pa": q_hat_Pa, "mu_resf": mu_resf, "mu_lg": mu_lg, "M_dd": M_dd,
        "M_kappa": M_kappa, "e_hat": e_hat, "C_Dc": C_Dc, "C_f": C_f
    }
    return inputs

def optimize_wing_planform(inputs):
    """Performs the wing optimization by iterating through a grid of design variables."""
    print("--- Starting Wing Planform Optimization (Grid Search) ---")
    Lambda_w_deg_range = np.linspace(20, 40, 50)
    A_w_range = np.linspace(7, 15, 50)
    C_L_hat_range = np.linspace(0.3, 0.8, 21)
    min_mtow = float('inf')
    optimal_params = {}

    for Lambda_w_deg in Lambda_w_deg_range:
        Lambda_w_rad = np.deg2rad(Lambda_w_deg)
        for A_w in A_w_range:
            for C_L_hat in C_L_hat_range:
                wpf, t_c = calculate_WPF_transonic(
                    inputs["phi_3"], inputs["phi_2"], inputs["F_prop"], C_L_hat,
                    A_w, Lambda_w_rad, inputs["e_hat"], inputs["M_dd"],
                    inputs["M_kappa"], inputs["C_f"], inputs["C_Dc"], return_tc=True
                )
                if wpf == float('inf'): continue

                mtow = calculate_MTOW(
                    inputs["W_pay_N"], inputs["W_fix_other_N"], inputs["F_prop"],
                    inputs["q_hat_Pa"], inputs["C_Dp_S_fix_m2"],
                    inputs["mu_resf"], inputs["mu_lg"], wpf
                )
                if mtow < min_mtow:
                    min_mtow = mtow
                    optimal_params = {
                        "MTOW_N": min_mtow, "C_L_hat": C_L_hat, "A_w": A_w,
                        "Lambda_w_deg": Lambda_w_deg,
                        "t_c_ratio": t_c,
                        "S_w_m2": min_mtow / (inputs["q_hat_Pa"] * C_L_hat),
                        "b_w_m": np.sqrt(A_w * (min_mtow / (inputs["q_hat_Pa"] * C_L_hat)))
                    }
    print("--- Optimization Complete ---")
    return optimal_params

def plot_WPF_contours(inputs, optimal_design):
    """Plots the WPF contours similar to Figure 10.12."""
    print("--- Generating WPF Contour Plot (Fig 10.12) ---")
    Lambda_w_deg_fixed = optimal_design["Lambda_w_deg"]
    Lambda_w_rad_fixed = np.deg2rad(Lambda_w_deg_fixed)
    A_w_range = np.linspace(4, 16, 50)
    C_L_hat_range = np.linspace(0.2, 0.9, 50)
    CLH_mesh, AW_mesh = np.meshgrid(C_L_hat_range, A_w_range)
    WPF_grid = np.zeros_like(CLH_mesh)

    for i in range(len(A_w_range)):
        for j in range(len(C_L_hat_range)):
            A_w = AW_mesh[i, j]
            C_L_hat = CLH_mesh[i, j]
            WPF_grid[i, j] = calculate_WPF_transonic(
                inputs["phi_3"], inputs["phi_2"], inputs["F_prop"],
                C_L_hat, A_w, Lambda_w_rad_fixed, inputs["e_hat"],
                inputs["M_dd"], inputs["M_kappa"], inputs["C_f"], inputs["C_Dc"]
            )
    
    plt.figure(figsize=(10, 8))
    # Filter out infinite values for cleaner plotting
    WPF_grid[WPF_grid == np.inf] = np.nan 
    contour_levels = np.nanpercentile(WPF_grid, np.linspace(1, 50, 20))
    contour_wpf = plt.contour(CLH_mesh, AW_mesh, WPF_grid, levels=contour_levels, cmap='viridis')
    plt.clabel(contour_wpf, inline=True, fontsize=8, fmt='%.3f')
    # Plot the optimal point
    plt.plot(optimal_design["C_L_hat"], optimal_design["A_w"], 'r*', markersize=15, label=f'Optimum (MTOW = {optimal_design["MTOW_N"]/g:.0f} kg)')
    
    # Using the existing, correct logic for plotting constraints
    lambda_w_taper = 0.2703
    root_chord_approx = optimal_design["S_w_m2"]*2 / ((1+lambda_w_taper)*optimal_design["b_w_m"])
    tan_Lambda_LE = np.tan(Lambda_w_rad_fixed) - 0.5 * root_chord_approx * (1 - lambda_w_taper) / (optimal_design["b_w_m"]/2)
    tan_Lambda_c4 = tan_Lambda_LE + 0.25 * root_chord_approx * (1 - lambda_w_taper) / (optimal_design["b_w_m"]/2)
    Lambda_w_deg_c4 = np.rad2deg(np.arctan(tan_Lambda_c4))
    A_max = 17.7 * (2 - lambda_w_taper) * np.exp(-0.043 * Lambda_w_deg_c4)
    # Add illustrative constraints (as seen in Fig 10.12)
    plt.axhline(y=A_max, color='c', linestyle=':', label=f'Pitch-up Limit ($A_w \\leq {A_max:.2f}$)')
    plt.axvline(x=0.8, color='m', linestyle='-.', label='Buffet Limit (Illustrative)')
    # Take-off distance line (Span Loading Constraint) (Eq. 10.28)
    # W_MTO / b_w^2 = q_hat * C_L_hat / A_w
    # For a fixed TOFL, this span loading is roughly constant. Let's assume 550 N/m^2
    span_load_const_val_Pa = 2000 # Using a lower value for a light UAV
    A_w_span_load = (inputs["q_hat_Pa"] / span_load_const_val_Pa) * C_L_hat_range
    plt.plot(C_L_hat_range, A_w_span_load, 'grey', linestyle='--', label='Take-off Distance Limit')

    plt.xlabel('Design Lift Coefficient (C_L_hat)')
    plt.ylabel('Aspect Ratio (A_w)')
    plt.title(f'WPF Contours for Optimal Sweep Angle (Λ_w = {Lambda_w_deg_fixed:.1f}°)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(A_w_range.min(), A_w_range.max())
    plt.xlim(C_L_hat_range.min(), C_L_hat_range.max())
    plt.colorbar(contour_wpf, label='Wing Penalty Function (WPF)')
    plt.show()


# --- MAIN FUNCTION TO BE CALLED FROM MASTER SCRIPT ---

def perform_wing_optimization(params: DesignParameters) -> dict:
    """
    Main entry point for the wing optimization module.
    Takes the main DesignParameters object and returns the optimal wing design.
    """
    print("\n" + "="*50)
    print("      STARTING WING OPTIMIZATION MODULE")
    print("="*50)
    
    # 1. Calculate Torenbeek-specific inputs from the main params object
    inputs = calculate_torenbeek_inputs_from_params(params)
    
    # 2. Run the optimization loop
    optimal_design = optimize_wing_planform(inputs)
    
    # 3. Visualize the results
    if optimal_design:
        plot_WPF_contours(inputs, optimal_design)
    else:
        print("\nNo feasible wing solution found in the specified design space.")
        
    return optimal_design

# --- Example Usage (for testing this module standalone) ---
if __name__ == '__main__':
    # Create a DesignParameters instance and load initial data
    # This simulates how the master script would use this module
    design_params = DesignParameters()
    design_params.load_from_yaml('design_config.yaml')

    # Run the full wing optimization process
    final_wing_design = perform_wing_optimization(design_params)

    # Print final results
    if final_wing_design:
        print("\n--- FINAL OPTIMAL WING DESIGN ---")
        for key, val in final_wing_design.items():
            print(f"{key:<15}: {val:.4f}" if key != "MTOW_N" else f"MTOW_kg:        {val/g:.2f}")