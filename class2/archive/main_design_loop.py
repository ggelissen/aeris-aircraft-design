# master_design_process.py

import os
import sys
import matplotlib.pyplot as plt

# --- Add project directories to Python's path to allow imports ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# /project_root
#   - master_design_process.py
#   - design_variables.py
#   - /class1
#     - main_class_I.py
#     - ...
#   - /class2
#     - main_class_II.py
#     - Wing_Planform_Adv_AC_Design_Delta_torenbeek.py
#     - ...

# --- Import all design modules ---
from config.design_variables import DesignParameters
from class1.main_class_I import perform_class_I_analysis
from class2.main_class_II import class_II_weight_estimation, calculate_cg_longitudinal
from class2.prelim_sizing_tail import run_preliminary_sizing_tail
from class2.prelim_sizing_undercarriage import perform_undercarriage_positioning
from class2.improved_drag import run_improved_drag_estimations
from Wing_Planform_Adv_AC_Design_Delta_torenbeek_classII import perform_wing_optimization

g = 9.80665  # m/s^2

def run_full_design_iteration(params: DesignParameters) -> DesignParameters:
    """
    This function represents one full pass through the Class II design loop, as in Gabriel's diagram.
    """
    print("\n" + "="*50)
    print(f"      RUNNING CLASS II DESIGN ITERATION (Based on MTOW = {params.weight.W_TO/g:.2f} kg)")
    print("="*50)

    # --- 1. Wing Sizing (Torenbeek Optimization Module) ---
    print("\n[STEP 1] Running Advanced Wing Planform Optimization...")
    optimal_wing_design = perform_wing_optimization(params)
    if not optimal_wing_design:
        print("ERROR: Wing optimization failed. Aborting iteration.")
        # Return current params without updating, and signal non-convergence
        return params, False

    # Update the main params object with the new, optimized wing design
    params.wing.A_w = optimal_wing_design["A_w"]
    params.wing.S_w = optimal_wing_design["S_w_m2"]
    params.wing.b_w = optimal_wing_design["b_w_m"]
    params.wing.Lambda_w_deg = optimal_wing_design["Lambda_w_deg"]
    params.wing.t_c_w_avg = optimal_wing_design["t_c_ratio"] # Using a single avg value for now
    params.wing.t_c_w_r = optimal_wing_design["t_c_ratio"]   # Simplification
    params.wing.t_c_w_t = optimal_wing_design["t_c_ratio"]   # Simplification
    params.wing.mac = optimal_wing_design["S_w_m2"] / optimal_wing_design["b_w_m"] # Approximation
    print(f"Wing Opt. Complete. New A_w: {params.wing.A_w:.2f}, S_w: {params.wing.S_w:.2f} m^2")

    # --- 2. Empennage (Tail) Sizing ---
    print("\n[STEP 2] Sizing Empennage...")
    tail_results = run_preliminary_sizing_tail(params)
    params.empennage.S_t = tail_results["S_t"]
    #params.empennage.vtail_dihedral = tail_results["dihedral_rad"]
    print(f"Tail Sizing Complete. New Tail Area: {params.empennage.S_t:.2f} m^2")

    # --- 3. Drag Refinement (Class II) ---
    print("\n[STEP 3] Running Improved Drag Estimation...")
    drag_results = run_improved_drag_estimations(params)
    # Storing the total CD0 in a parameter that can be used by other modules
    params.performance.CD0 = drag_results['CD0']
    print(f"Drag Estimation Complete. New CD0: {params.performance.CD0:.4f}")

    # --- 4. Class II Weight Convergence ---
    print("\n[STEP 4] Running Class II Weight Convergence Loop...")
    # This is the inner loop from your main_class_II.py
    final_W_TO, converged, _, W_empty_final_N = class_II_weight_estimation(
        params=params,
        initial_W_TO_N_guess=params.weight.W_TO
    )

    # --- 5. Update Master Parameters with Converged Weight ---
    params.weight.W_TO = final_W_TO
    params.weight.W_E = W_empty_final_N # Store the final empty weight
    print("Class II Weight Loop Finished.")

    return params, converged

if __name__ == "__main__":
    # Step 0: Initial Setup
    design_params = DesignParameters()
    design_params.load_from_yaml('design_config.yaml')
    print("--- Initial Parameters Loaded ---")
    print(f"Initial MTOW Guess: {design_params.weight.W_TO / g:.2f} kg")

    # Step 1: Run Class I Analysis for a solid starting point
    print("\n--- Running Class I Analysis ---")
    class_I_weights = perform_class_I_analysis(design_params)
    # Update the params object with the key results from Class I
    design_params.weight.W_TO = class_I_weights['W_TO']
    design_params.weight.M_ff = class_I_weights['M_ff']
    design_params.weight.W_PL = class_I_weights['W_PL']
    design_params.weight.W_crew = class_I_weights['W_crew']
    design_params.weight.W_OE = class_I_weights['W_OE']
    print(f"Class I Analysis Complete. Updated MTOW: {design_params.weight.W_TO / g:.2f} kg")

    # Step 2: The Main Iterative Loop (Class II)
    max_iterations = 5
    for i in range(max_iterations):
        previous_MTOW = design_params.weight.W_TO
        
        # This function call represents one full cycle of the design spiral
        design_params, converged_inner = run_full_design_iteration(design_params)

        # Check for convergence of the outer loop
        relative_diff = abs(design_params.weight.W_TO - previous_MTOW) / previous_MTOW
        print("\n" + "*"*60)
        print(f"      END OF OUTER LOOP ITERATION {i+1}")
        print(f"      New MTOW: {design_params.weight.W_TO / g:.2f} kg")
        print(f"      Change from previous iteration: {relative_diff:.4%}")
        print("*"*60)

        if relative_diff < 0.01: # 1% convergence tolerance
            print(f"\nOUTER DESIGN LOOP CONVERGED in {i+1} iterations!")
            break
    else:
        print(f"\nOUTER DESIGN LOOP did not converge after {max_iterations} iterations.")

    # Step 3: Final Analysis (Post-Convergence)
    print("\n--- Running Final Sizing and Analysis on Converged Design ---")
    # 1. Undercarriage Positioning
    uc_results = perform_undercarriage_positioning(design_params)
    print("\nUndercarriage Positioning Results:")
    for key, val in uc_results.items():
        print(f"  {key}: {val:.3f}")
        
    # 2. CG Analysis
    cg_results = calculate_cg_longitudinal(design_params, design_params.weight.W_E)
    print("\nFinal Center of Gravity Range:")
    for key, val in cg_results.items():
        print(f"  {key}: {val:.3f} m from nose")