import os
import sys
import math
import matplotlib.pyplot as plt

G  = 9.80665  # Acceleration due to gravity (m/s^2)
# Add parent directory to path to allow imports from 'class1', 'class2', etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from design_variables import DesignParameters
from utils.unit_conversions import *

# Import all the necessary Class II functions
from class2.component_weights import class_II_weight_estimation
from class2.improved_drag import run_improved_drag_estimations
from class2.prelim_sizing_tail import run_preliminary_sizing_tail
from class2.prelim_sizing_undercarriage import perform_undercarriage_positioning
from Wing_Planform_Adv_AC_Design_Delta_torenbeek_classII import perform_wing_optimization
from class1.initial_weight_estimations import run_initial_weight_estimations

def perform_class_II_analysis(params: DesignParameters) -> dict:
    """
    Performs the complete Class II analysis sequence.
    This function acts as the high-level orchestrator for the detailed design phase,
    calling each major analysis module in the correct order.
    
    The execution sequence is:
    1. Detailed Wing Optimization (Torenbeek method) to get refined wing geometry.
    2. Detailed sizing of other components (tail, undercarriage) using this geometry.
    3. Detailed drag estimation based on the complete, refined airframe.
    4. Final iterative weight estimation using detailed component weight formulas.
    
    Parameters:
        params (DesignParameters): An instance of DesignParameters containing the latest
                                   design variables, typically from a Class I analysis pass.
    
    Returns:
        dict: A dictionary containing the combined results from all Class II analyses.
    """
    print("\n" + "="*60)
    print("      PERFORMING FULL CLASS II ANALYSIS SEQUENCE")
    print("="*60)
    
    # --- Step 1: Detailed Wing Optimization (Torenbeek) ---
    print("\n--- Running Wing Optimization (Torenbeek) ---")
    wing_opt_results = perform_wing_optimization(params)
    if not wing_opt_results:
        print("\n!!! Wing optimization failed to find a solution. Class II analysis aborted. !!!")
        return {"error": "Wing optimization failed"}
        
    # --- Step 2: Update Parameters with Wing Results ---
    print("\n--- Updating parameters with optimized wing geometry ---")
    params.wing.S_w = wing_opt_results.get('S_w_m2', params.wing.S_w)
    params.wing.b_w = wing_opt_results.get('b_w_m', params.wing.b_w)
    params.wing.A_w_actual = wing_opt_results.get('A_w', params.wing.A_w_target)
    params.wing.t_c_w_max = wing_opt_results.get('t_c_ratio', params.wing.t_c_w_max)
    # The MTOW from Torenbeek optimization becomes the new best guess for the next step
    initial_W_TO_guess = wing_opt_results.get('MTOW_N', params.weight.W_TO)
    print(f"  - Wing geometry updated. Using W_TO guess for final weight loop: {initial_W_TO_guess:.2f} N")

    # --- Step 3: Detailed Sizing of Other Components ---
    print("\n--- Running detailed sizing for other components ---")
    tail_results = run_preliminary_sizing_tail(params)
    # Update params with tail results for subsequent calculations
    params.empennage.S_t = tail_results.get('S_t', params.empennage.S_t)
    params.empennage.S_h = tail_results.get('S_h', params.empennage.S_h)
    params.empennage.S_v = tail_results.get('S_v', params.empennage.S_v)
    params.empennage.vtail_dihedral = tail_results.get('dihedral_rad (gamma)', params.empennage.vtail_dihedral)

    undercarriage_results = perform_undercarriage_positioning(params)
    
    # --- Step 4: Detailed Drag Estimation ---
    print("\n--- Running improved drag estimation ---")
    drag_results = run_improved_drag_estimations(params)
    params.wing.C_D0 = drag_results.get('C_D0', params.wing.C_D0)
    
    # --- Step 5: Final Converged Weight Estimation ---
    # This is the detailed weight buildup loop using the final, refined geometry.
    print("\n--- Running final Class II weight convergence loop ---")
    weight_results = class_II_weight_estimation(
        params=params,
        initial_W_TO_N_guess=initial_W_TO_guess
    )

    # --- Step 6: Combine All Results ---
    final_results = (
        wing_opt_results |
        tail_results |
        undercarriage_results |
        drag_results |
        weight_results
    )
    
    print("\n" + "="*60)
    print("      CLASS II ANALYSIS SEQUENCE COMPLETE")
    print("="*60)
    
    return final_results


if __name__ == '__main__':
    # This block allows for standalone testing of the full Class II sequence
    
    params = DesignParameters()
    # Ensure the path to the config file is correct, assuming it's in the parent directory
    config_path = os.path.join(os.path.dirname(__file__), '..', 'design_config.yaml')
    params.load_from_yaml(config_path)

    # --- Simulate Initial State from Class I ---
    print("--- Simulating inputs from Class I for standalone Class II test ---")
    class_I_weights = run_initial_weight_estimations(params)
    params.weight.W_TO = class_I_weights['W_TO']
    params.weight.M_ff = class_I_weights['M_ff']
    params.weight.W_PL = class_I_weights['W_PL']
    params.weight.W_crew = class_I_weights['W_crew']
    params.weight.W_OE = class_I_weights['W_OE']
    
    # Class I wing sizing is needed for some Class II inputs
    from class1.preliminary_sizing.prelim_sizing_wing import run_preliminary_sizing_wing
    class_I_wing = run_preliminary_sizing_wing(params)
    params.wing.root_chord = class_I_wing.get('root_chord', params.wing.root_chord)
    params.wing.mac = class_I_wing.get('mac', params.wing.mac)
    params.wing.Lambda_05_w = class_I_wing.get('Lambda_05c_w', params.wing.Lambda_05_w)


    print(f"Using initial W_TO: {params.weight.W_TO:.2f} N for Class II analysis.")

    # Run the full Class II analysis sequence
    class_II_results = perform_class_II_analysis(params)
    
    # --- Display Final Results ---
    print("\n--- FINAL CLASS II ANALYSIS RESULTS (Standalone Test) ---")
    if "error" not in class_II_results:
        converged = class_II_results.get('converged', False)
        print(f"Weight Convergence Status: {'Converged' if converged else 'Not Converged'}")
        
        # Key performance and geometry parameters
        final_mtow_n = class_II_results.get('W_TO', 0)
        final_oew_n = class_II_results.get('W_OE', 0)
        final_wing_area = class_II_results.get('S_w_m2', 0)
        final_aspect_ratio = class_II_results.get('A_w', 0)
        final_cd0 = class_II_results.get('C_D0', 0)

        print(f"Final MTOW: {final_mtow_n/G:.2f} kg ({final_mtow_n:.2f} N)")
        print(f"Final OEW: {final_oew_n/G:.2f} kg ({final_oew_n:.2f} N)")
        print(f"Final Wing Area: {final_wing_area:.2f} m^2")
        print(f"Final Aspect Ratio: {final_aspect_ratio:.2f}")
        print(f"Final CD0: {final_cd0:.4f}")
    else:
        print(f"Analysis failed with error: {class_II_results['error']}")
