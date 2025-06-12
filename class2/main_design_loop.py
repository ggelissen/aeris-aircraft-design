# main_design_loop.py

import os
import sys
import matplotlib.pyplot as plt

# --- Add project directory to path to allow imports ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import all your design modules ---
from design_variables import DesignParameters
from class1.main_class_I import perform_class_I_analysis
from class2.main_class_II import class_II_weight_estimation, calculate_cg_longitudinal
from class2.prelim_sizing_tail import perform_tail_sizing # Assuming this function exists
from class2.prelim_sizing_undercarriage import perform_undercarriage_positioning
from class2.improved_drag import run_improved_drag_estimations

# This is our advanced wing optimization script
from class2.Wing_Planform_Adv_AC_Design_torenbeek_class_II import calculate_torenbeek_inputs_from_params, optimize_wing_planform

g = 9.80665  # Standard gravity in m/s^2 # Might want to import this from a constants module instead, for consistency
def run_full_design_iteration(params: DesignParameters) -> DesignParameters:
    """
    This function represents one full pass through the outer design loop
    (the green arrow in your diagram).
    """
    print("\n" + "="*50)
    print("      RUNNING NEW FULL DESIGN ITERATION")
    print("="*50)

    # --- 1. Wing Sizing (Our Advanced Module) ---
    # Use current params to get inputs for Torenbeek optimization
    print("\n[STEP 1] Running Advanced Wing Planform Optimization...")
    torenbeek_inputs = calculate_torenbeek_inputs_from_params(params) # We'll need to adapt this function
    optimal_wing_design = optimize_wing_planform(torenbeek_inputs)
    # Update the main params object with the new, optimized wing design
    params.wing.A_w = optimal_wing_design["A_w"]
    params.wing.S_w = optimal_wing_design["S_w_m2"]
    params.wing.b_w = optimal_wing_design["b_w_m"]
    params.wing.Lambda_w_deg = optimal_wing_design["Lambda_w_deg"]
    params.wing.t_c_w_avg = optimal_wing_design["t_c_ratio"]
    print("Wing Optimization Complete. New Aspect Ratio: {:.2f}, New Wing Area: {:.2f} m^2".format(params.wing.A_w, params.wing.S_w))

    # --- 2. Empennage (Tail) Sizing ---
    print("\n[STEP 2] Sizing Empennage...")
    # This function would use the new wing params (S_w, b_w) to size the tail
    tail_params = perform_tail_sizing(params)
    params.empennage.S_h = tail_params["S_h"]
    params.empennage.S_v = tail_params["S_v"]
    print("Tail Sizing Complete.")

    # --- 3. Drag Refinement (Class II) ---
    print("\n[STEP 3] Running Improved Drag Estimation...")
    # This function uses the new wing and tail geometry for a detailed drag buildup
    drag_results = run_improved_drag_estimations(params)
    params.performance.CD0 = drag_results['CD0']
    print(f"Drag Estimation Complete. New CD0: {params.performance.CD0:.4f}")

    # --- 4. Class II Weight Convergence ---
    # This is the inner loop from your main_class_II.py
    print("\n[STEP 4] Running Class II Weight Convergence Loop...")
    final_W_TO, converged, _, W_empty_final_N = class_II_weight_estimation(
        params=params,
        initial_W_TO_N_guess=params.weight.W_TO # Use the latest MTOW as the guess
    )

    # --- 5. Update Master Parameters with Converged Weight ---
    params.weight.W_TO = final_W_TO
    params.weight.W_E = W_empty_final_N
    print("Class II Weight Loop Finished.")

    return params, converged


if __name__ == "__main__":
    # --- Step 0: Initial Setup ---
    # Initialize parameters from your config file
    design_params = DesignParameters()
    design_params.load_from_yaml('design_config.yaml')
    print("--- Initial Parameters Loaded ---")
    print(f"Initial MTOW Guess: {design_params.weight.W_TO / g:.2f} kg")

    # --- Optional: Run Class I Analysis for a better starting point ---
    # print("\n--- Running Class I Analysis ---")
    # class_I_results = perform_class_I_analysis(design_params)
    # design_params.weight.W_TO = class_I_results['W_TO']
    # design_params.weight.W_S = class_I_results['W_S']
    # design_params.weight.T_W = class_I_results['T_W']
    # print(f"Class I Analysis Complete. Updated MTOW: {design_params.weight.W_TO / g:.2f} kg")

    # --- The Main Iterative Loop (Class II) ---
    max_iterations = 5
    for i in range(max_iterations):
        previous_W_TO = design_params.weight.W_TO
        
        # This function call represents one full cycle of the design spiral
        design_params, converged_inner = run_full_design_iteration(design_params)

        # Check for convergence of the outer loop
        relative_diff = abs(design_params.weight.W_TO - previous_W_TO) / design_params.weight.W_TO
        print("\n" + "*"*60)
        print(f"      END OF OUTER LOOP ITERATION {i+1}")
        print(f"      New MTOW: {design_params.weight.W_TO / g:.2f} kg")
        print(f"      Change from previous iteration: {relative_diff:.4%}")
        print("*"*60)

        if relative_diff < 0.01: # e.g., 1% convergence tolerance
            print(f"\nOUTER DESIGN LOOP CONVERGED in {i+1} iterations!")
            break
    else:
        print(f"\nOUTER DESIGN LOOP did not converge after {max_iterations} iterations.")

    # --- Final Analysis (Post-Convergence) ---
    print("\n--- Running Final Sizing and Analysis on Converged Design ---")
    # 1. Undercarriage Positioning
    perform_undercarriage_positioning(design_params)
    # 2. CG Analysis
    calculate_cg_longitudinal(design_params, design_params.weight.W_E)