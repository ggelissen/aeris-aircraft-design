import os
import sys
import math

# --- Setup Project Paths ---
# This ensures that all necessary modules can be imported correctly
# assuming this script is run from the project's root directory.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'class2')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...')))

from design_variables import DesignParameters
from utils.unit_conversions import *

# --- Import Functions from Both Versions ---
# It's good practice to alias them to avoid name collisions
import class2.Outdated_scripts.component_weights_old as old_cw
import class2.component_weights as new_cw

def run_comparison():
    """
    Initializes design parameters and runs a side-by-side comparison
    of the old and new component weight calculation functions.
    """
    print("="*60)
    print("      COMPONENT WEIGHT CALCULATION COMPARISON")
    print("="*60)

    # --- Step 1: Initialize a single, consistent set of parameters ---
    params = DesignParameters()
    config_path = 'design_config.yaml'
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Make sure you run this script from the project root.")
        return
        
    params.load_from_yaml(config_path)
    print(f"Loaded configuration from '{config_path}' for comparison.\n")

    # --- Step 2: Simulate Prerequisite Data ---
    # The weight functions need some values that are typically calculated
    # in other modules first. We'll add them to the params object here
    # to ensure the functions can run without errors.
    print("--- Simulating prerequisite parameters for the test ---")
    
    # Class I Weight & Wing Sizing Results
    params.weight.S_w = params.weight.W_TO / params.weight.W_S
    params.wing.S_w = params.weight.S_w
    params.wing.b_w = math.sqrt(params.wing.A_w_target * params.wing.S_w)
    params.wing.root_chord = 1.819 # From design_variables.py default
    params.wing.Lambda_05_w = 0.607 # From design_variables.py default
    params.wing.t_r = params.wing.root_chord * params.wing.t_c_w_r # Calculate root thickness
    print(f"Simulated Wing: S_w={params.wing.S_w:.2f}, b_w={params.wing.b_w:.2f}")

    # Class II Tail Sizing Results
    # We need to run a preliminary tail sizing to get S_h and S_v
    params.empennage.L_h = 0.45 * params.fuselage.l_f
    params.empennage.L_v = 0.45 * params.fuselage.l_f
    S_h_temp = (params.empennage.V_v * params.wing.b_w * params.wing.S_w) / params.empennage.L_v
    S_v_temp = (params.empennage.V_h * params.wing.mac * params.wing.S_w) / params.empennage.L_h
    params.empennage.S_h = S_h_temp
    params.empennage.S_v = S_v_temp
    print(f"Simulated Tail: S_h={params.empennage.S_h:.2f}, S_v={params.empennage.S_v:.2f}")
    
    # A placeholder for total fuel weight, required by propulsion calculations
    params.weight.W_F = params.weight.W_TO * (params.weight.M_ff)
    
    # --- Step 3: Run and Compare Each Component ---
    print("\n" + "-"*60)
    print("Comparing Individual Component Weight Functions...")
    print("-" * 60)

    # Wing Weight
    print("\n1. Wing Weight:")
    w_wing_old = old_cw.wing_weight_N(params)
    w_wing_new = new_cw.wing_weight_N(params)
    print(f"-> OLD: {w_wing_old:.2f} N")
    print(f"-> NEW: {w_wing_new:.2f} N")
    print(f"   Difference: {abs(w_wing_old - w_wing_new):.4f} N")

    # Fuselage Weight
    print("\n2. Fuselage Weight:")
    w_fus_old = old_cw.fuselage_weight_N(params)
    w_fus_new = new_cw.fuselage_weight_N(params)
    print(f"-> OLD: {w_fus_old:.2f} N")
    print(f"-> NEW: {w_fus_new:.2f} N")
    print(f"   Difference: {abs(w_fus_old - w_fus_new):.4f} N")

    # Landing Gear Weight
    print("\n3. Landing Gear Weight:")
    w_lg_old = old_cw.landing_gear_weight_N(params)
    w_lg_new = new_cw.landing_gear_weight_N(params)
    print(f"-> OLD: {w_lg_old:.2f} N")
    print(f"-> NEW: {w_lg_new:.2f} N")
    print(f"   Difference: {abs(w_lg_old - w_lg_new):.4f} N")

    # Empennage Weight
    print("\n4. Empennage Weight:")
    w_emp_old = old_cw.empennage_weight_N(params)
    w_emp_new = new_cw.empennage_weight_N(params)
    print(f"-> OLD: {w_emp_old:.2f} N")
    print(f"-> NEW: {w_emp_new:.2f} N")
    print(f"   Difference: {abs(w_emp_old - w_emp_new):.4f} N")

    # Propulsion Weight
    print("\n5. Propulsion Weight:")
    w_prop_old = old_cw.propulsion_weight_N(params)
    w_prop_new = new_cw.propulsion_weight_N(params)
    print(f"-> OLD: {w_prop_old:.2f} N")
    print(f"-> NEW: {w_prop_new:.2f} N")
    print(f"   Difference: {abs(w_prop_old - w_prop_new):.4f} N")
    
    # Fixed Equipment Weight
    print("\n6. Fixed Equipment Weight:")
    w_fe_old = old_cw.fixed_equipment_weight_N(params)
    w_fe_new = new_cw.fixed_equipment_weight_N(params)
    print(f"-> OLD: {w_fe_old:.2f} N")
    print(f"-> NEW: {w_fe_new:.2f} N")
    print(f"   Difference: {abs(w_fe_old - w_fe_new):.4f} N")
    
    print("\n" + "="*60)
    print("      COMPARISON COMPLETE")
    print("="*60)


if __name__ == "__main__":
    # To run this script, you will need to:
    # 1. Save your original component weights file as `component_weights_old.py`
    #    in the `class2` directory.
    # 2. Save our new, refactored component weights file as `component_weights.py`
    #    in the `class2` directory.
    # 3. Run this script from your project's root folder.
    run_comparison()