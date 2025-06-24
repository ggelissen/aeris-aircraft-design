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
import matplotlib
matplotlib.use('Agg')
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
from class2.main_class_II import perform_class_II_analysis

# Import utilities
from utils.unit_conversions import *

from class1.thrust_wing_loading import run_performance_diagram
from class2.updater import update_parameters_from_class_ii, update_parameters_from_class_i, update_parameters_from_wing_optimization
def get_key_parameters(params: DesignParameters) -> Dict[str, float]:
    """
    Extract key parameters for convergence monitoring.
    
    These are the critical parameters that define the aircraft design
    and must converge for a stable solution.
    """
    return {
        'W_OEW': params.weight.W_OE,
        'W_TO': params.weight.W_TO,
        'W_S': params.weight.W_S, 
        'T_W': params.weight.T_W,
        'S_w': params.wing.S_w,
        'A_w': params.wing.A_w_target,
        'CD0': params.wing.C_D0 if params.wing.C_D0 is not None else 0.020
    }

def perform_wing_loading_consistency_check(params: DesignParameters, 
                                          class_i_results: Dict,
                                          iteration: int) -> Tuple[bool, str]:
    """
    Smart consistency check that recalculates W_S and checks constraints.
    
    This implements your approach:
    1. Recalculate W_S = W_TO / S_w with latest knowledge
    2. Compare with wing optimization result
    3. If different, update to recalculated value
    4. Check if within Class I constraints
    5. Force re-iteration if needed for re-optimization
    
    Returns:
        (needs_reoptimization, reason)
    """
    print(f"\n    🔍 SMART CONSISTENCY CHECK - ITERATION {iteration}")
    print(f"    {'='*50}")
    
    # Get current values
    current_W_TO = params.weight.W_TO
    current_S_w = params.wing.S_w
    wing_opt_W_S = params.weight.W_S  # From wing optimization
    
    # Recalculate W_S with latest knowledge
    recalculated_W_S = current_W_TO / current_S_w
    
    print(f"    📊 Wing Loading Analysis:")
    print(f"       Current W_TO: {current_W_TO:.0f} N")
    print(f"       Current S_w:  {current_S_w:.3f} m²")
    print(f"       Wing Opt W_S: {wing_opt_W_S:.1f} N/m²")
    print(f"       Recalc W_S:   {recalculated_W_S:.1f} N/m²")
    
    # Calculate discrepancy
    discrepancy = abs(recalculated_W_S - wing_opt_W_S) / wing_opt_W_S
    print(f"       Discrepancy:  {discrepancy:.1%}")
    
    # Check if significant discrepancy exists
    SIGNIFICANT_THRESHOLD = 0.02  # 2% threshold for re-optimization
    
    if discrepancy > SIGNIFICANT_THRESHOLD:
        print(f"    🔄 SIGNIFICANT DISCREPANCY DETECTED ({discrepancy:.1%} > {SIGNIFICANT_THRESHOLD:.1%})")
        
        # Update to recalculated value
        old_W_S = params.weight.W_S
        params.weight.W_S = recalculated_W_S
        print(f"       ✅ Updated W_S: {old_W_S:.1f} → {recalculated_W_S:.1f} N/m²")
        
        # Check constraint from Class I (maximum allowable W_S)
        W_S_max = params.weight.W_S_max
        
        if W_S_max is not None:
            print(f"       📋 Class I W_S constraint: ≤ {W_S_max:.1f} N/m²")
            
            if recalculated_W_S <= W_S_max:
                print(f"       ✅ Within Class I constraint ({recalculated_W_S:.1f} ≤ {W_S_max:.1f})")
                
                # Higher wing loading is better (smaller wing), so this is good
                if recalculated_W_S > wing_opt_W_S:
                    reason = f"Higher W_S achievable ({recalculated_W_S:.1f} > {wing_opt_W_S:.1f}) - re-optimize for smaller wing"
                    print(f"       🎯 {reason}")
                    return True, reason
                else:
                    reason = f"Lower W_S required ({recalculated_W_S:.1f} < {wing_opt_W_S:.1f}) - re-optimize for constraint compliance"
                    print(f"       ⚠️  {reason}")
                    return True, reason
                    
            else:
                print(f"       ❌ EXCEEDS Class I constraint ({recalculated_W_S:.1f} > {W_S_max:.1f})")
                
                # Constrain to maximum and force re-optimization
                params.weight.W_S = W_S_max
                params.wing.S_w = current_W_TO / W_S_max  # Update wing area accordingly
                
                reason = f"W_S constrained to Class I limit ({W_S_max:.1f}) - re-optimize with constraint"
                print(f"       🔧 {reason}")
                print(f"       ✅ Updated S_w: {current_S_w:.3f} → {params.wing.S_w:.3f} m²")
                return True, reason
        else:
            print(f"       ⚠️  No Class I W_S constraint found - proceeding with recalculated value")
            reason = f"W_S updated to consistent value ({recalculated_W_S:.1f}) - re-optimize"
            return True, reason
    
    else:
        print(f"    ✅ WING LOADING CONSISTENT ({discrepancy:.1%} ≤ {SIGNIFICANT_THRESHOLD:.1%})")
        return False, "Wing loading consistent"
    
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

def master_design_process(params_in: DesignParameters = None,
                         config_file: str = 'design_config.yaml', 
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
        params_in (DesignParameters): Optional initial parameters to override config
        config_file (str): Path to YAML configuration file
        max_iterations (int): Maximum number of design iterations
        tolerance (float): Relative convergence tolerance (default 1.5%)
        verbose (bool): Enable detailed progress reporting
        
    Returns:
        (final_params, iteration_history, converged)
    """
    if verbose:
        print(f"\n{'='*80}")
        print(f"                 MASTER AIRCRAFT DESIGN PROCESS")
        print(f"{'='*80}")
        print(f"Configuration: {config_file}")
        print(f"Max iterations: {max_iterations}")
        print(f"Tolerance: {tolerance:.1%}")
        print(f"{'='*80}")
    
    if params_in:
        params = params_in
        print("✅ Using pre-configured DesignParameters object.")
    else:
        try:
            params = DesignParameters()
            params.load_from_yaml(config_file)
            print(f"✅ Initialized design parameters from {config_file}")
        except Exception as e:
            print(f"❌ Failed to initialize parameters from {config_file}: {e}")
            raise

    print(f"📊 Initial W_TO = {params.weight.W_TO:.0f} N")
    print(f"📊 Initial W_S = {params.weight.W_S:.0f} N/m²")
    print(f"📊 Initial T_W = {params.weight.T_W:.3f}")
    
    # Initialize iteration tracking
    iteration_history = []
    converged = False
    start_time = time.time()
    
    # Main design iteration loop
    for iteration in range(1, max_iterations + 1):
        iteration_start_time = time.time()
        if verbose:
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
        
        #params_class_i_key = get_key_parameters(params)
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
                    if verbose:
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
            print(f"    Initial W_TO guess for Class II: {params.weight.W_TO:.0f} N")
            class_ii_results = perform_class_II_analysis(params, initial_W_TO_guess=params.weight.W_TO)
            if class_ii_results:
                update_parameters_from_class_ii(params, class_ii_results)
                print(f"    ✅ Class II analysis completed successfully")
                if 'W_TO' in class_ii_results:
                    if verbose:
                        print(f"    📊 Converged W_TO: {class_ii_results['W_TO']:.0f} N")
                # Update wing loading consistency check
                W_S_post_class_ii = params.weight.W_TO / params.wing.S_w
                params.weight.W_S = W_S_post_class_ii
            else:
                print(f"    ⚠️  Class II analysis returned empty results")
        except Exception as e:
            print(f"    ❌ Class II analysis failed: {e}")
            print(f"    🔄 Continuing with current parameters")
        
        # updated_TW_SW = run_performance_diagram(params)
        # params.weight.T_W = updated_TW_SW['T_W']
        # params.weight.W_S = updated_TW_SW['W_S']
        # ================================================================
        # PHASE 4: CONVERGENCE CHECK
        # ================================================================
        print(f"\n🔍 PHASE 4: CONVERGENCE CHECK")
        params_end = get_key_parameters(params)
        converged, relative_diffs = check_convergence(params_start, params_end, tolerance)
        
        # # Check convergence against class I constraints
        # converged_inner, relative_diffs_inner = check_convergence(params_class_i_key, params_end, tolerance)

        # if not converged_inner:
        #     print(f"    ❌ Class I constraints not met, re-iterating...")
        #     converged = False
        #     relative_diffs.update(relative_diffs_inner)

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
        if verbose:
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
    if verbose:
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
    #print(f"    Empty Weight (W_E):         {params.weight.W_E if params.weight.W_E else 'N/A'}")
    print(f"    Operating Empty (W_OE):     {params.weight.W_OE:.0f} N")
    print(f"    Fuel Weight (W_F):          {params.weight.W_F:.0f} N")
    print(f"    Fuel Weight Used (W_FU):    {params.weight.W_F_used:.0f} N")
    print(f"    Payload Weight (W_PL):      {params.weight.W_PL:.0f} N")
    
    print(f"\n✈️  WING DESIGN:")
    print(f"    Wing Area (S_w):            {params.wing.S_w:.2f} m²")
    print(f"    Wing Span (b_w):            {params.wing.b_w:.2f} m")
    print(f"    Aspect Ratio (A_w):         {params.wing.A_w_target:.2f}")
    print(f"    Wing Loading (W_S):         {params.weight.W_S:.0f} N/m²")
    print(f"    Sweep Angle (Λ_0.25c):      {np.rad2deg(params.wing.Lambda_025c_w):.1f}°")
    print(f"    Sweep Angle Leading  Edge (Λ_LE): {np.rad2deg(params.wing.Lambda_0_w):.1f}°")
    print(f"    Design Lift Coefficient (C_L): {params.wing.CL:.3f}")
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
    print(f"    Zero-Lift Drag Tail (CD0_tail): {params.empennage.CD0_tail:.6f}")
    print(f"    Fuel Fraction:              {params.weight.M_ff:.3f}")
    
    print(f"\n🎚️  EMPENNAGE:")
    print(f"    Total Tail Area (S_t):      {params.empennage.S_t:.2f} m²")
    print(f"    Horizontal Area (S_h):      {params.empennage.S_h:.2f} m²") 
    print(f"    Vertical Area (S_v):        {params.empennage.S_v:.2f} m²")
    print(f"    V-Tailcal Span (b_v):       {params.empennage.b_v:.2f} m")
    print(f"    Dihedral V-tail (Gamma):    {np.rad2deg(params.empennage.vtail_dihedral):.2f} deg")
    print(f"    Root Chord (c_r):           {params.empennage.c_r :.2f} m")
    print(f"    Tip Chord (c_t):            {params.empennage.c_t:.2f} m")
    print(f"    Taper Ratio (λ_t):          {params.empennage.lambda_t:.3f}")
    print(f"    Aspect Ratio (A_t):         {params.empennage.A_t:.2f}")
    print(f"    Sweep Angle (Λ_0.25c_t):    {np.rad2deg(params.empennage.Lambda_t_025c ):.1f}°")
    print(f"    Thickness-to-Chord (t/c_t): {params.empennage.t_c_t:.3f}")




    print(f"{'='*80}")


if __name__ == "__main__":
    """
    Run the master design process with default settings.
    """
    try:
        # Execute master design process
        final_params, history, converged = master_design_process(
            params_in=None,  # Use default parameters from config file
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