"""
Master Design Process - Two-Phase Iterative Aircraft Design

This script implements the complete iterative design process with:
1. Class I Analysis (initial estimates)
2. Wing Planform Optimization (fuel burn minimization)  
3. Class II Analysis (detailed design)
4. Convergence checking and iteration

The process continues until design parameters converge within specified tolerance.
"""

import os
import sys
import time
from typing import Dict, Tuple, List

# Add project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core modules
from design_variables import DesignParameters

# Import Class I modules  
from class1.main_class_I import perform_class_I_analysis

# Import Wing Optimization (using the provided updated script)
from class2.class_II_wing_sizing import optimize_wing_for_fuel_burn

# Import Class II modules
from class2.main_class_II_current_missing_param_updates import perform_class_II_analysis

# Import utilities
from utils.unit_conversions import *


def get_key_parameters(params: DesignParameters) -> Dict[str, float]:
    """
    Extract key parameters for convergence monitoring.
    
    These are the critical parameters that define the aircraft design
    and must converge for a stable solution.
    """
    return {
        'W_TO': params.weight.W_TO,
        'W_S': params.weight.W_S, 
        'T_W': params.weight.T_W,
        'S_w': params.wing.S_w,
        'A_w': params.wing.A_w_target,
        'CD0': params.wing.C_D0 if params.wing.C_D0 is not None else 0.020
    }


def check_convergence(params_previous: Dict[str, float], params_current: Dict[str, float], 
                     tolerance: float = 0.01) -> Tuple[bool, Dict[str, float]]:
    """
    Check if design has converged by comparing key parameters.
    
    Parameters:
        params_previous: Parameters from start of iteration
        params_current: Parameters from end of iteration  
        tolerance: Relative tolerance for convergence (default 1%)
        
    Returns:
        (converged, relative_differences)
    """
    relative_diffs = {}
    converged = True
    
    for param_name in params_current.keys():
        if param_name in params_previous:
            prev_val = params_previous[param_name]
            curr_val = params_current[param_name]
            
            if prev_val != 0:
                rel_diff = abs((curr_val - prev_val) / prev_val)
                relative_diffs[param_name] = rel_diff
                
                if rel_diff > tolerance:
                    converged = False
            elif curr_val != 0:
                relative_diffs[param_name] = float('inf')
                converged = False
            else:
                relative_diffs[param_name] = 0.0
    
    return converged, relative_diffs


def print_convergence_status(iteration: int, relative_diffs: Dict[str, float], 
                           converged: bool, tolerance: float) -> None:
    """Print formatted convergence status report."""
    
    print(f"\n{'='*60}")
    print(f"      CONVERGENCE CHECK - ITERATION {iteration}")
    print(f"{'='*60}")
    print(f"Tolerance: {tolerance:.1%}")
    print("-" * 60)
    
    for param_name, rel_diff in relative_diffs.items():
        status = "✅" if rel_diff <= tolerance else "❌" # Emojis for pass/fail, helps with readability
        if rel_diff == float('inf'):
            print(f"{status} {param_name:<12}: {'∞':>8} {'(FAIL)':>8}")
        else:
            print(f"{status} {param_name:<12}: {rel_diff:>7.1%} {'(PASS)' if rel_diff <= tolerance else '(FAIL)':>8}")
    
    print("-" * 60)
    
    if converged:
        print("🎉 DESIGN CONVERGED!")
    else:
        print("🔄 Continuing iteration...")
    
    print("="*60)


def update_parameters_from_class_i(params: DesignParameters, class_i_results: Dict) -> None:
    """Update parameters with Class I results (inline)."""
    
    print(f"    📝 Updating parameters from Class I results...")
    updates = 0
    
    # Weight parameters
    if 'W_TO' in class_i_results:
        params.weight.W_TO = class_i_results['W_TO']
        updates += 1
    if 'W_E' in class_i_results:
        params.weight.W_E = class_i_results['W_E']
        updates += 1
    if 'T_W' in class_i_results:
        params.weight.T_W = class_i_results['T_W']
        updates += 1
    if 'W_S' in class_i_results:
        params.weight.W_S = class_i_results['W_S']
        updates += 1
    if 'M_ff' in class_i_results:
        params.weight.M_ff = class_i_results['M_ff']
        print(f"        ⚠️  M_ff updated to {params.weight.M_ff} (from Class I results)")
        updates += 1
    
    # Wing parameters  
    if 'Lambda_025c_w' in class_i_results:
        params.wing.Lambda_025c_w = class_i_results['Lambda_025c_w']
        updates += 1
    if 'lambda_w' in class_i_results:
        params.wing.lambda_w = class_i_results['lambda_w']
        updates += 1
    if 'root_chord' in class_i_results:
        params.wing.root_chord = class_i_results['root_chord']
        updates += 1
    if 'tip_chord' in class_i_results:
        params.wing.tip_chord = class_i_results['tip_chord']
        updates += 1
    if 'mac' in class_i_results:
        params.wing.mac = class_i_results['mac']
        updates += 1
    if 't_c_w_max' in class_i_results:
        params.wing.t_c_w_max = class_i_results['t_c_w_max']
        params.wing.t_c_w_r = class_i_results['t_c_w_max']  # Assume root = max
        updates += 1
    
    # Performance parameters
    if 'L_D_cruise' in class_i_results:
        params.performance.L_D_cruise = class_i_results['L_D_cruise']
        updates += 1
    if 'L_D_loiter' in class_i_results:
        params.performance.L_D_loiter = class_i_results['L_D_loiter']
        updates += 1
    
    print(f"        ✅ Updated {updates} parameters from Class I")


def update_parameters_from_wing_optimization(params: DesignParameters, wing_results: Dict) -> None:
    """Update parameters with wing optimization results (inline)."""
    
    if not wing_results:
        print(f"    ⚠️  No wing optimization results to update")
        return
        
    print(f"    📝 Updating parameters from wing optimization...")
    updates = 0
    
    # Core wing parameters
    if 'A_w_optimal' in wing_results:
        params.wing.A_w_target = wing_results['A_w_optimal']
        params.wing.A_w_actual = wing_results['A_w_optimal']
        updates += 1
    if 'S_w_optimal' in wing_results:
        params.wing.S_w = wing_results['S_w_optimal']
        updates += 1
    if 'b_w_optimal' in wing_results:
        params.wing.b_w = wing_results['b_w_optimal']
        updates += 1
    if 'Lambda_025c_optimal' in wing_results:
        params.wing.Lambda_025c_w = wing_results['Lambda_025c_optimal']
        updates += 1
    if 'Lambda_LE_optimal' in wing_results:
        params.wing.Lambda_0_w = wing_results['Lambda_LE_optimal']
        updates += 1
    if 'Lambda_05c_optimal' in wing_results:
        params.wing.Lambda_05_w = wing_results['Lambda_05c_optimal']
        updates += 1
    if 'taper_ratio_optimal' in wing_results:
        params.wing.lambda_w = wing_results['taper_ratio_optimal']
        updates += 1
    if 'root_chord_optimal' in wing_results:
        params.wing.root_chord = wing_results['root_chord_optimal']
        updates += 1
    if 'tip_chord_optimal' in wing_results:
        params.wing.tip_chord = wing_results['tip_chord_optimal']
        updates += 1
    if 'MAC_optimal' in wing_results:
        params.wing.mac = wing_results['MAC_optimal']
        updates += 1
    if 'y_LEMAC_optimal' in wing_results:
        params.wing.y_LEMAC = wing_results['y_LEMAC_optimal']
        updates += 1
    if 't_c_optimal' in wing_results:
        params.wing.t_c_w_max = wing_results['t_c_optimal']
        params.wing.t_c_w_r = wing_results['t_c_optimal']
        updates += 1
    if 'dihedral_optimal' in wing_results:
        params.wing.Gamma_w = wing_results['dihedral_optimal']
        updates += 1
    if 'M_ff_optimal' in wing_results:
        params.weight.M_ff = wing_results['M_ff_optimal']
        print(f"        ⚠️  M_ff updated to {params.weight.M_ff} (from wing optimization results)")
        updates += 1
    if 'W_S_optimal' in wing_results:
        params.weight.W_S = wing_results['W_S_optimal']
        updates += 1
    print(f"        ✅ Updated {updates} parameters from wing optimization")


def update_parameters_from_class_ii(params: DesignParameters, class_ii_results: Dict) -> None:
    """Update parameters with Class II results (inline)."""
    
    print(f"    📝 Updating parameters from Class II results...")
    updates = 0
    
    # Weight parameters (final converged values)
    if 'W_TO' in class_ii_results:
        params.weight.W_TO = class_ii_results['W_TO']
        updates += 1
    if 'W_E' in class_ii_results:
        params.weight.W_E = class_ii_results['W_E']
        updates += 1
    if 'W_OE' in class_ii_results:
        params.weight.W_OE = class_ii_results['W_OE']
        updates += 1
    if 'W_F' in class_ii_results:
        params.weight.W_F = class_ii_results['W_F']
        updates += 1
    
    # Empennage parameters
    if 'S_h' in class_ii_results:
        params.empennage.S_h = class_ii_results['S_h']
        updates += 1
    if 'S_v' in class_ii_results:
        params.empennage.S_v = class_ii_results['S_v']
        updates += 1
    if 'S_t' in class_ii_results:
        params.empennage.S_t = class_ii_results['S_t']
        updates += 1
    if 'b_t' in class_ii_results:
        params.empennage.b_v = class_ii_results['b_t']
        updates += 1
    if 'dihedral_rad (gamma)' in class_ii_results:
        params.empennage.vtail_dihedral = class_ii_results['dihedral_rad (gamma)']
        updates += 1
    
    # Drag parameters
    if 'CD0' in class_ii_results:
        params.wing.C_D0 = class_ii_results['CD0']
        updates += 1
    
    # Landing gear (simplified)
    if 'x_mlg' in class_ii_results:
        params.cg.x_cg_landing_gear = class_ii_results['x_mlg']
        updates += 1
    
    print(f"        ✅ Updated {updates} parameters from Class II")


def master_design_process(config_file: str = 'design_config.yaml', 
                         max_iterations: int = 10, 
                         tolerance: float = 0.015,
                         verbose: bool = True) -> Tuple[DesignParameters, List[Dict], bool]:
    """
    Execute the complete two-phase iterative aircraft design process.
    
    Process Flow:
    1. Initialize design parameters from configuration
    2. For each iteration:
       a) Class I Analysis (initial estimates)
       b) Wing Planform Optimization (fuel burn minimization)  
       c) Class II Analysis (detailed design)
       d) Convergence check
    3. Continue until converged or max iterations reached
    
    Parameters:
        config_file (str): Path to YAML configuration file
        max_iterations (int): Maximum number of design iterations
        tolerance (float): Relative convergence tolerance (default 1.5%)
        verbose (bool): Enable detailed progress reporting
        
    Returns:
        (final_params, iteration_history, converged)
    """
    
    print(f"\n{'='*80}")
    print(f"                 MASTER AIRCRAFT DESIGN PROCESS")
    print(f"{'='*80}")
    print(f"Configuration: {config_file}")
    print(f"Max iterations: {max_iterations}")
    print(f"Tolerance: {tolerance:.1%}")
    print(f"{'='*80}")
    
    # Initialize design parameters
    try:
        params = DesignParameters()
        params.load_from_yaml(config_file)
        print(f"✅ Initialized design parameters from {config_file}")
        print(f"📊 Initial W_TO = {params.weight.W_TO:.0f} N")
        print(f"📊 Initial W_S = {params.weight.W_S:.0f} N/m²")
        print(f"📊 Initial T_W = {params.weight.T_W:.3f}")
    except Exception as e:
        print(f"❌ Failed to initialize parameters: {e}")
        raise
    
    # Initialize iteration tracking
    iteration_history = []
    converged = False
    start_time = time.time()
    
    # Main design iteration loop
    for iteration in range(1, max_iterations + 1):
        iteration_start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"                    DESIGN ITERATION {iteration}")
        print(f"{'='*80}")
        
        # Store parameters at start of iteration for convergence check
        params_start = get_key_parameters(params)
        if verbose:
            print(f"📊 Iteration {iteration} starting parameters:")
            for key, value in params_start.items():
                print(f"    {key}: {value:.4f}")
        
        # ================================================================
        # PHASE 1: CLASS I ANALYSIS 
        # ================================================================
        print(f"\n🔵 PHASE 1: CLASS I ANALYSIS")
        try:
            class_i_results = perform_class_I_analysis(params)
            if class_i_results:
                update_parameters_from_class_i(params, class_i_results)
                print(f"    ✅ Class I analysis completed successfully")
            else:
                print(f"    ⚠️  Class I analysis returned empty results")
        except Exception as e:
            print(f"    ❌ Class I analysis failed: {e}")
            if iteration == 1:
                print(f"    💥 Cannot continue without initial Class I estimates")
                raise
            print(f"    🔄 Continuing with previous iteration parameters")
        
        # ================================================================
        # PHASE 2: WING PLANFORM OPTIMIZATION
        # ================================================================  
        print(f"\n🟡 PHASE 2: WING PLANFORM OPTIMIZATION")
        try:
            wing_results = optimize_wing_for_fuel_burn(params)
            if wing_results:
                update_parameters_from_wing_optimization(params, wing_results)
                print(f"    ✅ Wing optimization completed successfully")
                if 'fuel_weight_N' in wing_results:
                    print(f"    📊 Optimized fuel weight: {wing_results['fuel_weight_N']:.0f} N")
            else:
                print(f"    ⚠️  Wing optimization returned no results")
        except Exception as e:
            print(f"    ❌ Wing optimization failed: {e}")
            print(f"    🔄 Continuing with current wing parameters")
        
        # ================================================================
        # PHASE 3: CLASS II ANALYSIS
        # ================================================================
        print(f"\n🟢 PHASE 3: CLASS II ANALYSIS")
        try:
            class_ii_results = perform_class_II_analysis(params, initial_W_TO_guess=params.weight.W_TO)
            if class_ii_results:
                update_parameters_from_class_ii(params, class_ii_results)
                print(f"    ✅ Class II analysis completed successfully")
                if 'W_TO' in class_ii_results:
                    print(f"    📊 Converged W_TO: {class_ii_results['W_TO']:.0f} N")
            else:
                print(f"    ⚠️  Class II analysis returned empty results")
        except Exception as e:
            print(f"    ❌ Class II analysis failed: {e}")
            print(f"    🔄 Continuing with current parameters")
        
        # ================================================================
        # PHASE 4: CONVERGENCE CHECK
        # ================================================================
        print(f"\n🔍 PHASE 4: CONVERGENCE CHECK")
        params_end = get_key_parameters(params)
        converged, relative_diffs = check_convergence(params_start, params_end, tolerance)
        
        # Calculate iteration time
        iteration_time = time.time() - iteration_start_time
        
        # Store iteration results for history
        iteration_results = {
            'iteration': iteration,
            'params_start': params_start,
            'params_end': params_end,
            'relative_diffs': relative_diffs,
            'converged': converged,
            'iteration_time': iteration_time,
            'class_i_results': class_i_results if 'class_i_results' in locals() else {},
            'wing_results': wing_results if 'wing_results' in locals() else {},
            'class_ii_results': class_ii_results if 'class_ii_results' in locals() else {}
        }
        iteration_history.append(iteration_results)
        
        # Print convergence status
        print_convergence_status(iteration, relative_diffs, converged, tolerance)
        print(f"⏱️  Iteration {iteration} completed in {iteration_time:.1f} seconds")
        
        # Check if converged
        if converged:
            total_time = time.time() - start_time
            print(f"\n🎉 DESIGN CONVERGED!")
            print(f"✅ Converged after {iteration} iterations in {total_time:.1f} seconds")
            break
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"                    DESIGN PROCESS COMPLETE")
    print(f"{'='*80}")
    print(f"Status: {'CONVERGED' if converged else 'MAX ITERATIONS REACHED'}")
    print(f"Iterations: {iteration}/{max_iterations}")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Average time per iteration: {total_time/iteration:.1f} seconds")
    
    # Final design summary
    final_params = get_key_parameters(params)
    print(f"\n📊 FINAL DESIGN PARAMETERS:")
    for key, value in final_params.items():
        print(f"    {key}: {value:.4f}")
    
    return params, iteration_history, converged


def print_final_design_summary(params: DesignParameters) -> None:
    """Print comprehensive final design summary."""
    
    print(f"\n{'='*80}")
    print(f"                     FINAL DESIGN SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n🎯 AIRCRAFT WEIGHTS:")
    print(f"    Take-off Weight (W_TO):     {params.weight.W_TO:.0f} N ({N_to_kg(params.weight.W_TO):.0f} kg)")
    print(f"    Empty Weight (W_E):         {params.weight.W_E if params.weight.W_E else 'N/A'}")
    print(f"    Operating Empty (W_OE):     {params.weight.W_OE:.0f} N")
    print(f"    Fuel Weight (W_F):          {params.weight.W_F:.0f} N")
    print(f"    Payload Weight (W_PL):      {params.weight.W_PL:.0f} N")
    
    print(f"\n✈️  WING DESIGN:")
    print(f"    Wing Area (S_w):            {params.wing.S_w:.2f} m²")
    print(f"    Wing Span (b_w):            {params.wing.b_w:.2f} m")
    print(f"    Aspect Ratio (A_w):         {params.wing.A_w_target:.2f}")
    print(f"    Wing Loading (W_S):         {params.weight.W_S:.0f} N/m²")
    print(f"    Sweep Angle (Λ_0.25c):      {np.rad2deg(params.wing.Lambda_025c_w):.1f}°")
    print(f"    Taper Ratio (λ):            {params.wing.lambda_w:.3f}")
    print(f"    Thickness-to-Chord (t/c):   {params.wing.t_c_w_max:.3f}")
    print(f"    Root Chord:                 {params.wing.root_chord:.3f} m")
    print(f"    Tip Chord:                  {params.wing.tip_chord:.3f} m")
    print(f"    MAC:                        {params.wing.mac:.3f} m")
    
    print(f"\n🚀 PROPULSION:")
    print(f"    Thrust-to-Weight (T_W):     {params.weight.T_W:.3f}")
    print(f"    Total Thrust:               {params.weight.T_W * params.weight.W_TO:.0f} N")
    print(f"    Number of Engines:          {params.engine.N_engines}")
    
    print(f"\n📈 PERFORMANCE:")
    print(f"    L/D Cruise:                 {params.performance.L_D_cruise:.2f}")
    print(f"    L/D Loiter:                 {params.performance.L_D_loiter:.2f}")
    print(f"    Zero-Lift Drag (CD0):       {params.wing.C_D0:.6f}")
    print(f"    Fuel Fraction:              {params.weight.M_ff:.3f}")
    
    print(f"\n🎚️  EMPENNAGE:")
    print(f"    Total Tail Area (S_t):      {params.empennage.S_t:.2f} m²")
    print(f"    Horizontal Area (S_h):      {params.empennage.S_h:.2f} m²") 
    print(f"    Vertical Area (S_v):        {params.empennage.S_v:.2f} m²")
    
    print(f"{'='*80}")


if __name__ == "__main__":
    """
    Run the master design process with default settings.
    """
    try:
        # Execute master design process
        final_params, history, converged = master_design_process(
            config_file='design_config.yaml',
            max_iterations=8, 
            tolerance=0.015,  # 1.5% convergence tolerance
            verbose=True
        )
        
        # Print final design summary
        print_final_design_summary(final_params)
        
        # Optionally save results
        # final_params.save_to_yaml('final_design.yaml')
        
    except Exception as e:
        print(f"\n💥 MASTER DESIGN PROCESS FAILED: {e}")
        import traceback
        traceback.print_exc()