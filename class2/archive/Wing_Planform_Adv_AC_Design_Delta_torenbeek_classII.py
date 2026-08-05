import numpy as np
import math
import matplotlib.pyplot as plt
import sys
import os
import delta_method_classII as dm

# Allow imports from parent directory to access design_variables
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.design_variables import DesignParameters
import component_weights as cw
import utils.unit_conversions as uc
import improved_drag as id

# --- Constants ---
H_g = 4350  # km, Fuel specific energy (H/g) for jet fuel (kerosene)
g = 9.80665 # m/s^2, standard gravity

# --- Calculation Functions from Torenbeek ---
def dynamic_pressure_mach(gamma, p, M):
    """Calculates dynamic pressure from Mach number and static pressure."""
    return 0.5 * gamma * p * M**2

def get_isa_delta_theta(altitude_m): # TODO, check if someone else has this function, it is a common one
    """ Returns relative pressure (delta) and relative temperature (theta) at a given altitude. """
    T0 = 288.15; P0 = 101325; R = 287.05; g0 = 9.80665; a = -0.0065
    if altitude_m <= 11000:
        T = T0 + a * altitude_m
        delta = (T / T0)**(-g0 / (a * R))
    else:
        T = 216.65
        P_11k = 22632
        delta = (P_11k/P0) * np.exp(-g0 * (altitude_m - 11000) / (R * T))
    return delta, T/T0

def calculate_eta_o_from_tsfc(tsfc_imperial, velocity_ms, H_fuel_J_kg=42.7e6):
    """Converts TSFC in lb/(h*lbf) to overall efficiency eta_o."""
    # Conversion factor from lb/(h*lbf) to kg/(s*N)
    print(f"Converting TSFC from imperial to SI: {tsfc_imperial} lb/(h*lbf)")
    tsfc_si = uc.lb_hr_lbf_to_kg_Ns(tsfc_imperial)  # Convert TSFC to SI units
    # eta_o = V / (TSFC_si * H_fuel), see 12.2 Torenbeek
    eta_o = velocity_ms / (tsfc_si * H_fuel_J_kg)
    return eta_o

def calculate_propulsion_function(R_eq, eta_o_cruise, mu_T, tau_cruise, delta_cruise):
    if eta_o_cruise <= 0 or tau_cruise <= 0 or delta_cruise <= 0: return np.inf
    fuel_term = R_eq / (eta_o_cruise * H_g)
    engine_weight_term = mu_T / (tau_cruise * delta_cruise)
    return fuel_term + engine_weight_term

def calculate_WPF_transonic(phi_3, phi_2, F_prop, C_L_hat, A_w, Lambda_w_rad, e_hat, target_cruise_mach, C_f, C_Dc, return_tc=False):
    if C_L_hat <= 1e-6 or A_w <= 0 or e_hat <= 0:
        return (np.inf, np.inf) if return_tc else np.inf

    Lambda_w_deg = np.rad2deg(Lambda_w_rad)
    t_c_w = dm.calculate_tc_from_delta_method(target_cruise_mach, A_w, Lambda_w_deg, C_L_hat)

    if t_c_w <= 0.05: return (np.inf, t_c_w) if return_tc else np.inf

    cos_Lambda_w = np.cos(Lambda_w_rad)
    mu_w_plus_h = (phi_3 * A_w * np.sqrt(A_w / C_L_hat)) / (t_c_w * cos_Lambda_w**2) + (phi_2 / C_L_hat)
    C_Dp_hat_var = 2 * (1 + 3.0 * t_c_w * cos_Lambda_w**2) * C_f * 1.25
    drag_term = F_prop * ((C_Dp_hat_var + C_Dc) / C_L_hat + C_L_hat / (np.pi * A_w * e_hat))
    wpf = mu_w_plus_h + drag_term
    return (wpf, t_c_w) if return_tc else wpf

def calculate_MTOW(W_pay, W_fix_other, F_prop, q_hat, C_Dp_S_fix, mu_resf, mu_lg, F_wp):
    numerator = W_pay + W_fix_other + F_prop * q_hat * C_Dp_S_fix
    denominator = 1 - (mu_resf + mu_lg + F_wp)
    if denominator <= 0: return float('inf')
    return numerator / denominator

def calculate_torenbeek_inputs_from_params(params: DesignParameters) -> dict:
    """Calculates the primary input parameters for the Torenbeek optimization from the DesignParameters object."""
    # --- Mission and Weight ---
    R_eq_km = params.range / 1000 * 1.05  # Equivalent Range (km) with 5% margin
    W_pay_N = params.weight.W_PL
    W_MZF_N = params.weight.W_OE + params.weight.W_PL
    mu_resf = params.weight.M_tfo
    # (Requires importing component_weights as cw)
    W_lg_N = cw.landing_gear_weight_N(params)
    mu_lg = W_lg_N / params.weight.W_TO # Turns out to be 0.04, Gundlach's assumption
    # TODO, this reveals that the W_TO needs to be updated in the params object, but the m_lg should remain constant.
    print(f"Landing gear weight fraction (mu_lg): {mu_lg:.4f}")

    # Estimate fixed other weight (fuselage, systems) as a fraction of OEW
    # W_fix_other is the sum of OEW components NOT included in the WPF
    W_fix_other_N = (cw.fuselage_weight_N(params) +
                    cw.fixed_equipment_weight_N(params))

    # --- Propulsion ---
    cruise_speed = params.cruise_mach * math.sqrt(1.4 * 287.15 * params.cruise_temperature)  # Speed at cruise altitude
    eta_o = calculate_eta_o_from_tsfc(params.engine.cruise_tsfc, cruise_speed) # Default was 0.31
    print(f"Overall efficiency (eta_o): {eta_o:.4f}")
    # Power plant weight per unit take-off thrust
    mu_T = params.engine.engine_weight / params.engine.T_TO if params.engine.T_TO > 0 else 0.172
    print(f"Propulsion weight fraction (mu_T): {mu_T:.4f}")
    tau_cruise = 0.85 # Placeholder for thrust lapse TODO check this
    delta_cruise, _ = get_isa_delta_theta(params.cruise_altitude) #  0.246 as default value from Torenbeek? Or Mrugank got it but not sure from where

    # --- Technology Levels ---
    M_des = params.cruise_mach
    M_dd = M_des + 0.015 # Vargas and Vos, or 0.03 from Eq. 10.41 context  # TODO, might want to include as input and use for the delta method
    M_kappa = params.wing.Mach_cross  # 0.935, for supercritical airfoil
    
    # --- Performance ---
    q_hat_Pa = dynamic_pressure_mach(1.4, delta_cruise * 101325, M_des) # Default was 9600 Pa # TODO, check for compressibility effects.
    print(f"Dynamic pressure at cruise (q_hat): {q_hat_Pa:.2f} Pa")
    # This is a conceptual call; you'd need to adapt improved_drag.py to calculate
    # drag for individual components.
    drag_buildup = id.run_improved_drag_estimations(params) # TODO, this estimation function needs to be defined in improved_drag.py
    # Assuming drag_buildup returns a dictionary with component drag areas
    #C_Dp_S_fix_m2 = (drag_buildup['CD0_fuselage'] * params.wing.S_w +
                    #drag_buildup['CD0_empennage'] * params.wing.S_w)
    C_Dp_S_fix_m2 = 0.25
    # --- Wing Weight Parameters ---
    n_ult = params.max_load_factor * 1.5
    n_ult = 3.75 # TODO, placeholder, should be derived from design parameters
    # Eq. 10.35 for phi_3
    phi_3 = (0.0013 * (1 + 0.15) * 1.0 * n_ult / 100) * math.sqrt(W_MZF_N / q_hat_Pa)
    # Eq. 10.13 for phi_2
    phi_2 = 0.025 # Using Torenbeek's typical value for now, more accurate values would require FEM?? 

    # --- Technology Levels ---
    e_hat = 0.90 * 1.15 # Oswald's efficiency factor, typical for modern aircraft, check with others for consistency TODO add winglet correction of 1.15
    C_Dc = 0.0005 # Eq. 10.42 context TODO, ARBITRARY DESIGN TARGET VALUE, NOT DERIVED FROM ANYTHING
    # C_f is the skin friction coefficient, typically around 0.00225 for clean aircraft, torenbeek
    Re_cruise = id.calculate_Reynolds_number(V=cruise_speed, rho=params.cruise_density, l=params.wing.root_chord, mu=1.4436e-5, k=0.152e-5, Mach=params.cruise_mach)
    C_f = id.calculate_skin_friction_coefficient(flow_ratio=(0.35, 0.65), Re=Re_cruise, Mach=params.cruise_mach) # For the wing, using a typical flow ratio for a transonic wing
    # TODO, check that fuselage and empennage skin friction coefficients are not needed here, as they are not included in the WPF?
    print(f"Skin friction coefficient (C_f): {C_f:.4f}")
    # --- Calculate F_prop ---
    # Simplified delta_cruise for high altitude
    print(f"Relative pressure at cruise altitude (delta_cruise): {delta_cruise:.4f}")
    F_prop = calculate_propulsion_function(R_eq_km, eta_o, mu_T, tau_cruise, delta_cruise)  # Eq. 10.9, or another, 8.32 maybe?

    inputs = {
        "F_prop": F_prop, "phi_3": phi_3, "phi_2": phi_2, "W_pay_N": W_pay_N,
        "W_fix_other_N": W_fix_other_N, "C_Dp_S_fix_m2": C_Dp_S_fix_m2,
        "q_hat_Pa": q_hat_Pa, "mu_resf": mu_resf, "mu_lg": mu_lg, 
        "target_cruise_mach": M_des, "e_hat": e_hat, "C_Dc": C_Dc, "C_f": C_f
    }
    return inputs

def optimize_wing_planform(inputs):
    """Performs the wing optimization by iterating through a grid of design variables."""
    print("--- Starting Wing Planform Optimization (Grid Search with Delta Method) ---")
    
    # Constrain design space as needed
    Lambda_w_deg_range = np.linspace(30, 42, 40)
    A_w_range = np.linspace(8, 13, 40)
    C_L_hat_range = np.linspace(0.1, 0.7, 80)

    # Define the wing loading constraints in N/m^2 (Pascals)
    MIN_WING_LOADING_Pa = 2000.0
    MAX_WING_LOADING_Pa = 7000.0

    # Initialize variables to track the minimum MTOW and optimal parameters
    min_mtow = float('inf')
    optimal_params = {}
    
    for Lambda_w_deg in Lambda_w_deg_range:
        Lambda_w_rad = np.deg2rad(Lambda_w_deg)
        for A_w in A_w_range:
            for C_L_hat in C_L_hat_range:
                wpf, t_c = calculate_WPF_transonic(
                    inputs["phi_3"], inputs["phi_2"], inputs["F_prop"], C_L_hat,
                    A_w, Lambda_w_rad, inputs["e_hat"], 
                    inputs["target_cruise_mach"],
                    inputs["C_f"], inputs["C_Dc"], return_tc=True
                )
                if wpf == float('inf'):
                    continue

                mtow = calculate_MTOW(
                    inputs["W_pay_N"], inputs["W_fix_other_N"], inputs["F_prop"],
                    inputs["q_hat_Pa"], inputs["C_Dp_S_fix_m2"],
                    inputs["mu_resf"], inputs["mu_lg"], wpf
                )
                if mtow == float('inf'):
                    continue

                # Check the Wing Loading Constraint for the current design point
                wing_area = mtow / (inputs["q_hat_Pa"] * C_L_hat)
                if wing_area < 1e-6: continue # Avoid division by zero
                
                current_wing_loading = mtow / wing_area

                # If the constraint is violated, discard this point and move to the next iteration
                if not (MIN_WING_LOADING_Pa <= current_wing_loading <= MAX_WING_LOADING_Pa):
                    continue

                if mtow < min_mtow:
                    min_mtow = mtow
                    optimal_params = {
                        "MTOW_N": min_mtow,
                        "C_L_hat": C_L_hat,
                        "A_w": A_w,
                        "Lambda_w_deg": Lambda_w_deg,
                        "t_c_ratio": t_c,
                        "S_w_m2": wing_area, # Use the already calculated wing area
                        "b_w_m": np.sqrt(A_w * wing_area),
                        "wing_loading_Pa": current_wing_loading # Also store the final wing loading
                    }
    print("--- Optimization Complete ---")
    return optimal_params

# --- Plotting and Main Execution Block (unchanged) ---
def plot_WPF_contours(inputs, optimal_design):
    """Plots the WPF contours similar to Figure 10.12."""
    print("--- Generating WPF Contour Plot (Fig 10.12) ---")
    
    Lambda_w_deg_fixed = optimal_design["Lambda_w_deg"]
    Lambda_w_rad_fixed = np.deg2rad(Lambda_w_deg_fixed)
    
    A_w_range = np.linspace(4, 15, 50)
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
                inputs["target_cruise_mach"], inputs["C_f"], inputs["C_Dc"]
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

# --- Main Execution Block ---
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