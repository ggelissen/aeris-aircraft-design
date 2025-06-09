import numpy as np
import math
import matplotlib.pyplot as plt

# --- Constants ---
H_g = 4350  # km, Fuel specific energy (H/g) for jet fuel (kerosene)
g = 9.80665 # m/s^2, standard gravity

# --- Helper & Torenbeek Calculation Functions ---

def calculate_propulsion_function(R_eq, eta_o_cruise, mu_T, tau_cruise, delta_cruise):
    """Calculates the propulsion function F_prop. Based on Eq. 10.9."""
    if eta_o_cruise <= 0 or tau_cruise <= 0 or delta_cruise <= 0: return np.inf
    fuel_term = R_eq / (eta_o_cruise * H_g)
    engine_weight_term = mu_T / (tau_cruise * delta_cruise)
    return fuel_term + engine_weight_term

def calculate_WPF_transonic(phi_3, phi_2, F_prop, C_L_hat, A_w, Lambda_w_rad, e_hat, M_dd, M_kappa, C_f, C_Dc, return_tc=False):
    """
    Calculates the Wing Penalty Function (WPF) for transonic aircraft. Based on Torenbeek, Ch. 10.
    """
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
    numerator = W_pay + W_fix_other + F_prop * q_hat * C_Dp_S_fix
    denominator = 1 - (mu_resf + mu_lg + F_wp)
    if denominator <= 0: return float('inf')
    return numerator / denominator

# --- New Functions for This Optimization ---

def calculate_torenbeek_inputs():
    """Calculates the primary input parameters for the Torenbeek optimization."""
    # TODO: Replace these placeholders with values from your DesignParameters class.

    # --- Mission and Weight Placeholders ---
    R_eq_km = 6500 * 1.05
    W_pay_N = 5884.0
    W_MZF_N = 17857.3
    mu_resf = 0.05
    mu_lg = 0.04
    # Refined placeholder based on your OEW of ~12000N. Assumes ~40% of OEW is non-wing/engine/tail.
    W_fix_other_N = 12000 * 0.4

    # --- Propulsion Placeholders ---
    eta_o = 0.31
    mu_T = 0.172
    tau_cruise = 0.85
    delta_cruise = 0.246

    # --- Performance Placeholders ---
    q_hat_Pa = 9615.0
    C_Dp_S_fix_m2 = 0.25 # Refined placeholder for a smaller UAV

    # --- Wing Weight Parameter Calculation Placeholders ---
    n_ult = 3.75
    # Eq. 10.35 for phi_3
    phi_3_unscaled = 0.0013 * (1 + 0.15) * 1.0 * n_ult / 100
    phi_3 = phi_3_unscaled * math.sqrt(W_MZF_N / q_hat_Pa)
    phi_2 = 0.025 # Eq. 10.13 context

    # --- Technology Level Placeholders ---
    M_des = 0.95
    M_dd = M_des + 0.015 # Vargas and Vos, or 0.03 from Eq. 10.41 context Torembeek
    M_kappa = 0.935 # Eq. 10.46 context
    e_hat = 0.90
    C_Dc = 0.0008 # Eq. 10.42 context
    C_Do = 0.017
    C_f = 0.00225

    # *** Calculate F_prop internally ***
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
    Lambda_w_deg_range = np.linspace(20, 38, 60)
    A_w_range = np.linspace(6, 20, 60)
    C_L_hat_range = np.linspace(0.2, 0.7, 60)

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

    lambda_w = 0.2703 # Radians value for the wing sweep at half chord?

    tan_Lambda_LE = np.tan(Lambda_w_rad_fixed) + 0.5* 2*1.819 / 9.19 * (1 - lambda_w)
    tan_Lambda_c4 = tan_Lambda_LE - 0.25 * 2 * 1.819 / 9.19 * (1 - lambda_w)
    Lambda_w_rad_c4 = np.arctan(tan_Lambda_c4)
    Lambda_w_deg_c4 = np.rad2deg(Lambda_w_rad_c4)
    # Pitch up limit
    print(f"Lambda_w_rad_c4: {Lambda_w_rad_c4:.4f} rad, Lambda_w_deg_fixed: {Lambda_w_deg_c4:.1f}°")
    A_max = 17.7 * (2 - lambda_w)*np.exp(-0.043*Lambda_w_deg_c4)
    # Add illustrative constraints (as seen in Fig 10.12)
    plt.axhline(y=A_max, color='c', linestyle=':', label=f'Pitch-up Limit ($A_w \leq {A_max}$)')
    plt.axvline(x=0.8, color='m', linestyle='-.', label='Buffet Limit (Illustrative)')
    
    # Take-off distance line (Span Loading Constraint) (Eq. 10.28)
    # W_MTO / b_w^2 = q_hat * C_L_hat / A_w
    # For a fixed TOFL, this span loading is roughly constant. Let's assume 550 N/m^2
    span_load_const_val_Pa = 2000 # Using a lower value for a light UAV
    A_w_span_load = (inputs["q_hat_Pa"] / span_load_const_val_Pa) * C_L_hat_range
    plt.plot(C_L_hat_range, A_w_span_load, 'grey', linestyle='--', label=f'Take-off Distance Limit')

    plt.xlabel('Design Lift Coefficient (C_L_hat)')
    plt.ylabel('Aspect Ratio (A_w)')
    plt.title(f'WPF Contours for Optimal Sweep Angle (Λ_w = {Lambda_w_deg_fixed:.1f}°)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(A_w_range.min(), A_w_range.max())
    plt.xlim(C_L_hat_range.min(), C_L_hat_range.max())
    plt.colorbar(contour_wpf, label='Wing Penalty Function (WPF)')
    plt.show()


# --- Main Execution Block ---
if __name__ == '__main__':
    torenbeek_inputs = calculate_torenbeek_inputs()
    print("\n--- Torenbeek Inputs (from placeholders) ---")
    for key, val in torenbeek_inputs.items():
        print(f"{key:<15}: {val:.4g}")

    optimal_design = optimize_wing_planform(torenbeek_inputs)

    if optimal_design:
        print("\n--- Optimal Wing Planform Found ---")
        for key, val in optimal_design.items():
            # Converting MTOW from N to kg for readability
            if key == "MTOW_N":
                print(f"MTOW_kg:        {val/g:.2f}")
            else:
                print(f"{key:<15}: {val:.4f}")
        
        # 4. Visualize the results
        plot_WPF_contours(torenbeek_inputs, optimal_design)
    else:
        print("\nNo feasible solution found in the specified design space.")