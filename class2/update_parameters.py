# =============================================================================
# CLEAN PARAMETER UPDATE SYSTEM - Loop-Based Approach
# =============================================================================

def update_params_from_results(params, results: dict, param_mapping: dict, 
                              module_name: str = "", verbose: bool = True) -> int:
    """
    Generic function to update params object from results dictionary using a mapping.
    
    Parameters:
        params: DesignParameters object to update
        results: Dictionary containing calculated results
        param_mapping: Dictionary mapping result keys to parameter paths
        module_name: Name of module for logging purposes
        verbose: Whether to print update details
        
    Returns:
        int: Number of parameters successfully updated
    """
    updates_count = 0
    missing_results = []
    failed_updates = []
    
    if verbose and module_name:
        print(f"   📝 Updating {module_name} parameters in params object...")
    
    for result_key, param_path in param_mapping.items():
        if result_key in results:
            try:
                # Split the parameter path (e.g., 'wing.S_w' -> ['wing', 'S_w'])
                path_parts = param_path.split('.')
                
                # Navigate to the correct object (e.g., params.wing)
                obj = params
                for part in path_parts[:-1]:
                    obj = getattr(obj, part)
                
                # Get old value for logging
                old_val = getattr(obj, path_parts[-1], 'N/A') if verbose else None
                
                # Set the new value
                setattr(obj, path_parts[-1], results[result_key])
                
                if verbose:
                    new_val = results[result_key]
                    print(f"      {path_parts[-1]}: {old_val} → {new_val}")
                
                updates_count += 1
                
            except AttributeError as e:
                failed_updates.append(f"{result_key} → {param_path}: {str(e)}")
                
        else:
            missing_results.append(result_key)
    
    # Report any issues
    if missing_results and verbose:
        print(f"   ⚠️  Missing results: {missing_results}")
    
    if failed_updates:
        print(f"   ❌ Failed updates: {failed_updates}")
        # Optionally raise error if critical parameters fail
        # raise ValueError(f"Failed to update parameters: {failed_updates}")
    
    if verbose:
        print(f"   ✅ Updated {updates_count} parameters")
    
    return updates_count


# =============================================================================
# PARAMETER MAPPING DEFINITIONS
# =============================================================================

# Define mappings for each module - this is the key configuration
CLASS_I_WEIGHT_MAPPING = {
    'W_TO': 'weight.W_TO',
    'W_E': 'weight.W_E', 
    'W_F': 'weight.W_F',
    'W_OE': 'weight.W_OE',
    'W_tfo': 'weight.W_tfo',
    'M_ff': 'weight.M_ff',
    'L_D_cruise': 'performance.L_D_cruise',
    'L_D_loiter': 'performance.L_D_loiter',
    'W_F_used': 'weight.W_F_used',
    'W_F_res': 'weight.W_F_res',
}

CLASS_I_PERFORMANCE_MAPPING = {
    'T_W': 'weight.T_W',
    'W_S': 'weight.W_S',
}

CLASS_I_WING_MAPPING = {
    'Lambda_025c_w': 'wing.Lambda_025c_w',
    'Lambda_05c_w': 'wing.Lambda_05_w',        # Note: different name in params!
    'Lambda_LE_w': 'wing.Lambda_0_w',          # Note: different name in params!
    'lambda_w': 'wing.lambda_w',
    'root_chord': 'wing.root_chord',
    'tip_chord': 'wing.tip_chord',
    'mac': 'wing.mac',
    'y_LEMAC': 'wing.y_LEMAC',
    't_c_w_max': 'wing.t_c_w_max',
    'Gamma_w': 'wing.Gamma_w',
}

# For Class II (examples - you'll need to expand these)
CLASS_II_TAIL_MAPPING = {
    'S_h': 'empennage.S_h',
    'S_v': 'empennage.S_v', 
    'S_t': 'empennage.S_t',
    'b_t': 'empennage.b_v',                    # Note: different name in params!
    'dihedral_rad (gamma)': 'empennage.vtail_dihedral',
    'c_root_t': 'empennage.c_r',
    'c_tip_t': 'empennage.c_t',
    'taper_ratio_t': 'empennage.lambda_t',
    'aspect_ratio_t': 'empennage.A_t',
    'Lambda_025c_t': 'empennage.Lambda_t_025c',
    't_c_t': 'empennage.t_c_t',
}

CLASS_II_DRAG_MAPPING = {
    'CD0': 'wing.C_D0',
    # Add friction coefficients if needed
}

CLASS_II_WEIGHT_MAPPING = {
    'W_TO': 'weight.W_TO',
    'W_E': 'weight.W_E',
    'W_OE': 'weight.W_OE', 
    'W_F': 'weight.W_F',
}

WING_OPTIMIZATION_MAPPING = {
    'A_w_optimal': 'wing.A_w_target',
    'S_w_optimal': 'wing.S_w',
    'b_w_optimal': 'wing.b_w',
    'Lambda_025c_optimal': 'wing.Lambda_025c_w',
    'Lambda_LE_optimal': 'wing.Lambda_0_w',
    'Lambda_05c_optimal': 'wing.Lambda_05_w',
    'taper_ratio_optimal': 'wing.lambda_w',
    'root_chord_optimal': 'wing.root_chord',
    'tip_chord_optimal': 'wing.tip_chord',
    'MAC_optimal': 'wing.mac',
    'y_LEMAC_optimal': 'wing.y_LEMAC',
    't_c_optimal': 'wing.t_c_w_max',
    'dihedral_optimal': 'wing.Gamma_w',
}


# =============================================================================
# DERIVED PARAMETER CALCULATIONS
# =============================================================================

def update_derived_parameters(params, verbose: bool = True) -> int:
    """
    Update parameters that are derived from other parameters.
    Call this after updating base parameters.
    """
    updates = 0
    
    if verbose:
        print("   🔧 Updating derived parameters...")
    
    # Wing area from W_TO and W_S
    if hasattr(params.weight, 'W_TO') and hasattr(params.weight, 'W_S'):
        if params.weight.W_TO and params.weight.W_S:
            old_S_w = getattr(params.wing, 'S_w', 'N/A')
            params.wing.S_w = params.weight.W_TO / params.weight.W_S
            if verbose:
                print(f"      S_w (derived): {old_S_w} → {params.wing.S_w:.2f} m²")
            updates += 1
    
    # Wing span from aspect ratio and area
    if hasattr(params.wing, 'A_w_target') and hasattr(params.wing, 'S_w'):
        if params.wing.A_w_target and params.wing.S_w:
            old_b_w = getattr(params.wing, 'b_w', 'N/A')
            params.wing.b_w = (params.wing.A_w_target * params.wing.S_w) ** 0.5
            if verbose:
                print(f"      b_w (derived): {old_b_w} → {params.wing.b_w:.2f} m")
            updates += 1
    
    # Root thickness from t/c ratio and chord
    if hasattr(params.wing, 't_c_w_r') and hasattr(params.wing, 'root_chord'):
        if params.wing.t_c_w_r and params.wing.root_chord:
            params.wing.t_r = params.wing.t_c_w_r * params.wing.root_chord
            if verbose:
                print(f"      t_r (root thickness): → {params.wing.t_r:.4f} m")
            updates += 1
    
    # Reference area (should equal wing area)
    if hasattr(params.wing, 'S_w') and params.wing.S_w:
        params.wing.S_ref = params.wing.S_w
        if verbose:
            print(f"      S_ref: → {params.wing.S_ref:.2f} m²")
        updates += 1
    
    # Actual aspect ratio (should equal target for preliminary design)
    if hasattr(params.wing, 'A_w_target') and params.wing.A_w_target:
        params.wing.A_w_actual = params.wing.A_w_target
        if verbose:
            print(f"      A_w_actual: → {params.wing.A_w_actual:.2f}")
        updates += 1
    
    # Also update t/c at root to match max (for preliminary design)
    if hasattr(params.wing, 't_c_w_max') and params.wing.t_c_w_max:
        params.wing.t_c_w_r = params.wing.t_c_w_max
        if verbose:
            print(f"      t_c_w_r: → {params.wing.t_c_w_r:.3f}")
        updates += 1
    
    if verbose:
        print(f"   ✅ Updated {updates} derived parameters")
    
    return updates


# =============================================================================
# CLEAN CLASS I ANALYSIS FUNCTION
# =============================================================================

def perform_class_I_analysis_CLEAN(params) -> dict:
    """
    Clean Class I analysis using the loop-based parameter update system.
    Much more readable and maintainable than manual if-statements.
    """
    print("\n" + "="*60)
    print("           RUNNING CLASS I ANALYSIS (CLEAN)")
    print("="*60)
    
    combined_results = {}
    total_updates = 0
    
    # =========================================================================
    # 1. INITIAL WEIGHT ESTIMATIONS
    # =========================================================================
    print("\n1. Initial Weight Estimations...")
    results_weights = run_initial_weight_estimations(params)
    combined_results.update(results_weights)
    
    # ✅ Clean parameter updates using mapping
    updates = update_params_from_results(
        params, results_weights, CLASS_I_WEIGHT_MAPPING, "weight"
    )
    total_updates += updates
    
    # =========================================================================
    # 2. PERFORMANCE CONSTRAINT ANALYSIS  
    # =========================================================================
    print("\n2. Performance Constraint Analysis (T/W vs W/S)...")
    results_thrust_area = run_performance_diagram(params)
    combined_results.update(results_thrust_area)
    
    # ✅ Clean parameter updates using mapping
    updates = update_params_from_results(
        params, results_thrust_area, CLASS_I_PERFORMANCE_MAPPING, "performance"
    )
    total_updates += updates
    
    # =========================================================================
    # 3. WING PRELIMINARY SIZING
    # =========================================================================  
    print("\n3. Wing Preliminary Sizing...")
    results_wing_sizing = run_preliminary_sizing_wing(params)
    combined_results.update(results_wing_sizing)
    
    # ✅ Clean parameter updates using mapping
    updates = update_params_from_results(
        params, results_wing_sizing, CLASS_I_WING_MAPPING, "wing geometry"
    )
    total_updates += updates
    
    # =========================================================================
    # 4. DERIVED PARAMETER UPDATES
    # =========================================================================
    print("\n4. Derived Parameter Updates...")
    derived_updates = update_derived_parameters(params)
    total_updates += derived_updates
    
    # =========================================================================
    # 5. FUSELAGE PRELIMINARY SIZING (Currently empty)
    # =========================================================================
    print("\n5. Fuselage Preliminary Sizing...")
    results_fuselage_sizing = run_preliminary_sizing_fuselage(params)
    combined_results.update(results_fuselage_sizing)
    print("   📝 Fuselage sizing currently empty - no parameters to update")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print(f"\n{'='*60}")
    print(f"   CLASS I ANALYSIS COMPLETE (CLEAN)")
    print(f"{'='*60}")
    print(f"✅ Total parameters updated: {total_updates}")
    print(f"📊 Results dictionary size: {len(combined_results)}")
    print(f"🔄 params object ready for next iteration")
    
    return combined_results


# =============================================================================
# CLASS II EXAMPLE (same clean approach)
# =============================================================================

def perform_class_II_analysis_CLEAN(params, initial_W_TO_guess: float = None) -> dict:
    """
    Clean Class II analysis using the same loop-based approach.
    """
    print("\n" + "="*60)
    print("           RUNNING CLASS II ANALYSIS (CLEAN)")
    print("="*60)
    
    combined_results = {}
    total_updates = 0
    
    # 1. Tail Sizing
    print("\n1. Tail Sizing...")
    try:
        tail_results = run_preliminary_sizing_tail(params)
        combined_results.update(tail_results)
        
        updates = update_params_from_results(
            params, tail_results, CLASS_II_TAIL_MAPPING, "tail"
        )
        total_updates += updates
        
    except Exception as e:
        print(f"   ⚠️  Tail sizing failed: {e}")
    
    # 2. Improved Drag Estimation  
    print("\n2. Improved Drag Estimation...")
    try:
        drag_results = run_improved_drag_estimations(params)
        combined_results.update(drag_results)
        
        updates = update_params_from_results(
            params, drag_results, CLASS_II_DRAG_MAPPING, "drag"
        )
        total_updates += updates
        
    except Exception as e:
        print(f"   ⚠️  Drag estimation failed: {e}")
    
    # 3. Component Weight Estimation
    print("\n3. Detailed Component Weight Estimation...")
    try:
        final_W_TO, converged, iterations, W_empty_final = class_II_weight_estimation(
            params=params,
            initial_W_TO_N_guess=initial_W_TO_guess or params.weight.W_TO,
            max_iterations=100,
            tolerance=0.005
        )
        
        # Create weight results dictionary
        weight_results = {
            "W_TO": final_W_TO,
            "W_E": W_empty_final,
            "W_OE": W_empty_final + params.weight.W_crew,
            "W_F": final_W_TO * (1 - params.weight.M_ff),
        }
        combined_results.update(weight_results)
        
        # Update using clean mapping
        updates = update_params_from_results(
            params, weight_results, CLASS_II_WEIGHT_MAPPING, "final weights"
        )
        total_updates += updates
        
    except Exception as e:
        print(f"   ⚠️  Weight estimation failed: {e}")
    
    print(f"\n✅ Class II Analysis Complete. Updated {total_updates} parameters.")
    return combined_results


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def add_parameter_mapping(mapping_dict: dict, result_key: str, param_path: str):
    """Helper to easily add new parameter mappings."""
    mapping_dict[result_key] = param_path

def validate_mapping(params, mapping: dict) -> list:
    """Validate that all parameter paths in mapping exist in params object."""
    invalid_paths = []
    
    for result_key, param_path in mapping.items():
        try:
            path_parts = param_path.split('.')
            obj = params
            for part in path_parts[:-1]:
                obj = getattr(obj, part)
            # Check if final attribute exists (don't need to get value)
            if not hasattr(obj, path_parts[-1]):
                invalid_paths.append(param_path)
        except AttributeError:
            invalid_paths.append(param_path)
    
    return invalid_paths


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Test the clean system
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    
    # Validate mappings first
    print("Validating parameter mappings...")
    invalid = validate_mapping(params, CLASS_I_WEIGHT_MAPPING)
    if invalid:
        print(f"Invalid weight mappings: {invalid}")
    
    # Run clean Class I analysis
    results = perform_class_I_analysis_CLEAN(params)
    
    print("\nFinal params state:")
    print(f"W_TO: {params.weight.W_TO}")
    print(f"S_w: {params.wing.S_w}")
    print(f"mac: {params.wing.mac}")