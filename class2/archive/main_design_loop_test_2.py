import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# --- Add project directories to Python's path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.design_variables import DesignParameters
from utils.unit_conversions import *

# --- Import all necessary design modules from their final locations ---
from class1.main_class_I import perform_class_I_analysis
# We will need the component weight functions to calculate inputs for the optimization
from class2.component_weights import get_final_weight_breakdown, fuselage_weight_N, fixed_equipment_weight_N, landing_gear_weight_N
from class2.prelim_sizing_tail import run_preliminary_sizing_tail
from class2.prelim_sizing_undercarriage import perform_undercarriage_positioning
from class2.improved_drag import run_improved_drag_estimations
from Wing_Planform_Adv_AC_Design_Delta_torenbeek_classII import perform_wing_optimization
# Final CG analysis is a post-processing step
from class2.main_class_II import calculate_cg_longitudinal

G = 9.80665  # m/s^2

def main():
    """
    The main execution function for the entire aircraft design process.
    This script follows the two-phase iterative design loop.
    """
    # --- Step 1: Initial Setup ---
    design_params = DesignParameters()
    design_params.load_from_yaml('design_config.yaml')
    print("--- Initial Parameters Loaded ---")
    print(f"Initial MTOW Guess: {design_params.weight.W_TO / G:.2f} kg")
    
    mtow_history = []

    # --- Step 2: Class I Analysis ---
    # Run once to get a solid baseline for MTOW, fuel fraction, W/S, T/W, etc.
    print("\n" + "="*60)
    print("      STEP 1: PERFORMING CLASS I ANALYSIS (INITIAL SIZING)")
    print("="*60)
    class_I_results = perform_class_I_analysis(design_params)
    
    # Update the params object with the key results from Class I
    for key, value in class_I_results.items():
        design_params.update_parameter(f"weight.{key}", value)
    
    design_params.wing.S_w = design_params.weight.W_TO / design_params.weight.W_S
    design_params.wing.b_w = np.sqrt(design_params.wing.A_w_target * design_params.wing.S_w)
    
    print(f"Class I Analysis Complete. Updated MTOW: {design_params.weight.W_TO / G:.2f} kg")
    mtow_history.append(design_params.weight.W_TO)

    # --- Step 3: Main Class II Iterative Loop ---
    print("\n" + "="*60)
    print("      STEP 2: ENTERING MAIN CLASS II ITERATIVE DESIGN LOOP")
    print("="*60)
    max_iterations = 5
    for i in range(max_iterations):
        print("\n" + "*"*60)
        print(f"      OUTER LOOP ITERATION {i+1}")
        print(f"      Starting MTOW for this iteration: {design_params.weight.W_TO / G:.2f} kg")
        print("*"*60)
        
        previous_MTOW = design_params.weight.W_TO

        # The Torenbeek wing optimization is the core of the Class II loop.
        # It takes the latest aircraft parameters, finds the optimal wing,
        # and converges to a new MTOW all in one step.
        optimal_wing_design = perform_wing_optimization(design_params)
        
        if not optimal_wing_design:
            print("ERROR: Wing optimization failed. Aborting design loop.")
            break

        # Update the main params object with the new, converged MTOW and geometry
        design_params.weight.W_TO = optimal_wing_design["MTOW_N"]
        design_params.wing.A_w_actual = optimal_wing_design["A_w"]
        design_params.wing.S_w = optimal_wing_design["S_w_m2"]
        design_params.wing.b_w = optimal_wing_design["b_w_m"]
        design_params.wing.Lambda_w_deg = optimal_wing_design["Lambda_w_deg"]
        
        mtow_history.append(design_params.weight.W_TO)

        # Check for convergence of the outer loop
        relative_diff = abs(design_params.weight.W_TO - previous_MTOW) / previous_MTOW
        print("\n" + "*"*60)
        print(f"      END OF OUTER LOOP ITERATION {i+1}")
        print(f"      New Converged MTOW: {design_params.weight.W_TO / G:.2f} kg")
        print(f"      Change from previous iteration: {relative_diff:.4%}")
        print("*"*60)

        if relative_diff < 0.01: # 1% convergence tolerance
            print(f"\nOUTER DESIGN LOOP CONVERGED in {i+1} iterations!")
            break
    else:
        print(f"\nOUTER DESIGN LOOP did not converge after {max_iterations} iterations.")

    # --- Step 4: Final Analysis and Verification (Post-Convergence) ---
    print("\n" + "="*60)
    print("      STEP 3: PERFORMING FINAL ANALYSIS ON CONVERGED DESIGN")
    print("="*60)
    
    # Now that the design is stable, run the other modules once for final numbers
    print("\n--- Running Final Sizing and Analysis on Converged Design ---")
    tail_results = run_preliminary_sizing_tail(design_params)
    undercarriage_results = perform_undercarriage_positioning(design_params)
    drag_results = run_improved_drag_estimations(design_params)
    weight_breakdown = get_final_weight_breakdown(design_params)
    cg_results = calculate_cg_longitudinal(design_params, weight_breakdown.get("W_E_calculated", 0))

    # --- Step 5: Final Report ---
    print("\n" + "#"*60)
    print("      FINAL CONVERGED AIRCRAFT DESIGN PARAMETERS")
    print("#"*60 + "\n")
    print(f"Final MTOW: {design_params.weight.W_TO/G:.2f} kg ({design_params.weight.W_TO:.2f} N)")
    print(f"Final OEW (from breakdown): {weight_breakdown.get('W_OE_calculated', 0)/G:.2f} kg")
    print(f"Final Wing Area: {design_params.wing.S_w:.2f} m^2")
    print(f"Final Aspect Ratio: {design_params.wing.A_w_actual:.2f}")
    print(f"Final CD0: {drag_results.get('C_D0', 'N/A'):.4f}")
    print("\nFinal Center of Gravity Range:")
    for key, val in cg_results.items():
        print(f"  {key}: {val:.3f} m from nose")

    # --- Plot Convergence History ---
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(mtow_history)), [w/G for w in mtow_history], 'o-', label='MTOW per Iteration')
    plt.xlabel("Iteration Number (0 = Class I Result)")
    plt.ylabel("Maximum Takeoff Weight (kg)")
    plt.title("Master Design Process Convergence History")
    plt.grid(True)
    plt.xticks(range(len(mtow_history)))
    plt.legend()
    # Ensure the plot is saved before finishing
    plt.savefig("convergence_history.png")
    print("\nConvergence history plot saved as 'convergence_history.png'")

if __name__ == "__main__":
    main()