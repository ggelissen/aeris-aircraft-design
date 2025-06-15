import math
import yaml
import os
import sys
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from class2.component_weights import get_final_weight_breakdown  # Only import this function
from class2.prelim_sizing_tail import run_preliminary_sizing_tail
from class2.prelim_sizing_undercarriage import perform_undercarriage_positioning
from class2.improved_drag import run_improved_drag_estimations
from utils.unit_conversions import *

def class_II_weight_estimation(params: DesignParameters,
                               initial_W_TO_N_guess: float,
                               max_iterations: int = 100,
                               tolerance: float = 0.005): 
    """
    Iterative Class II weight estimation using detailed component weight calculations.
    This is the original implementation from main_class_II.py.
    
    Parameters:
        params (DesignParameters): Design parameters object
        initial_W_TO_N_guess (float): Initial guess for take-off weight in N
        max_iterations (int): Maximum number of iterations
        tolerance (float): Convergence tolerance
        
    Returns:
        tuple: (final_W_TO, converged, iterations, W_empty_final)
    """
    import class2.component_weights as cw  # Import component weight functions
    
    W_TO_N_current = initial_W_TO_N_guess
    params.weight.W_TO = W_TO_N_current 
    print(f"Starting Class II Weight Estimation with initial WTO: {W_TO_N_current:.2f} N")

    for i in range(max_iterations):
        
        # Recalculate empty weight based on the current W_TO_N_current (params.weight.W_TO)
        W_empty_N_calculated = (
            cw.wing_weight_N(params) +
            cw.landing_gear_weight_N(params) +
            cw.empennage_weight_N(params) +
            cw.propulsion_weight_N(params) +
            cw.fixed_equipment_weight_N(params) +
            cw.fuselage_weight_N(params) 
        )

        W_TO_N_new = (W_empty_N_calculated + params.weight.W_PL) / (params.weight.M_ff)

        
        relative_difference = abs(W_TO_N_new - W_TO_N_current) / W_TO_N_new
        print(f"Iteration {i+1}: W_TO_current = {W_TO_N_current:.2f} N, W_empty_calc = {W_empty_N_calculated:.2f} N, W_TO_new = {W_TO_N_new:.2f} N, Rel_Diff = {relative_difference:.6f}")        
        if relative_difference < tolerance:
            print(f"Class II WTO converged in {i+1} iterations.")
            params.weight.W_TO = W_TO_N_new # Final update to params
            return W_TO_N_new, True, i + 1, W_empty_N_calculated
        
        W_TO_N_current = W_TO_N_new
        params.weight.W_TO = W_TO_N_current # Update WTO in params for the next iteration's component calculations

    print(f"Class II WTO did not converge after {max_iterations} iterations.")
    params.weight.W_TO = W_TO_N_current 
    return W_TO_N_current, False, max_iterations, W_empty_N_calculated

def calculate_cg_longitudinal(params: DesignParameters, weight_results: dict) -> dict:
    """
    Calculates CG locations for various aircraft loading conditions.
    
    Parameters:
        params (DesignParameters): Design parameters object
        weight_results (dict): Results from Class II weight estimation
    
    Returns:
        dict: CG positions for different loading conditions
    """
    print("  - Calculating longitudinal CG positions...")
    
    # Get component weights from the final weight breakdown
    weight_breakdown = get_final_weight_breakdown(params)
    
    # Calculate moments for OEW (Operating Empty Weight)
    moment_wing = weight_breakdown["W_wing"] * params.cg.x_cg_wing
    moment_fuselage = weight_breakdown["W_fuselage"] * params.cg.x_cg_fuselage
    moment_landing_gear = weight_breakdown["W_landing_gear"] * params.cg.x_cg_landing_gear
    moment_empennage = weight_breakdown["W_empennage"] * params.cg.x_cg_empennage
    moment_fixed_equipment = weight_breakdown["W_fixed_equipment"] * params.cg.x_cg_fixed_equipment
    moment_propulsion = weight_breakdown["W_propulsion"] * params.cg.x_cg_propulsion

    W_OE = weight_results["W_OE"]
    moment_OE = (moment_wing + moment_fuselage + moment_landing_gear +
                 moment_empennage + moment_fixed_equipment + moment_propulsion)
    
    # Payload and fuel
    W_PL = params.weight.W_PL
    W_F = weight_results["W_F"]

    moment_payload = W_PL * params.cg.x_cg_payload
    moment_fuel = W_F * params.cg.x_cg_fuel

    conditions = {
        'OEW': (W_OE, moment_OE),
        'OEW + Payload': (W_OE + W_PL, moment_OE + moment_payload),
        'OEW + Fuel': (W_OE + W_F, moment_OE + moment_fuel),
        'OEW + Payload + Fuel (W_TO)': (W_OE + W_PL + W_F, moment_OE + moment_payload + moment_fuel),
    }

    cg_positions = {}
    for condition, (weight, moment) in conditions.items():
        cg = moment / weight if weight > 0 else None
        cg_positions[condition] = cg

    return cg_positions

def estimate_mac_leading_edge(cg_OEW: float, target_CG_percent_MAC: float, mac_length: float) -> dict:
    """
    Estimates the MAC leading edge position to place CG at target location.
    
    Parameters:
        cg_OEW (float): CG position at Operating Empty Weight
        target_CG_percent_MAC (float): Target CG position as fraction of MAC (e.g., 0.30)
        mac_length (float): Mean Aerodynamic Chord length
    
    Returns:
        dict: MAC leading edge position
    """
    x_LE_MAC = cg_OEW - target_CG_percent_MAC * mac_length
    return {"x_LE_MAC": x_LE_MAC}

def perform_class_II_analysis(params: DesignParameters, initial_W_TO_guess: float = None) -> dict:
    """
    Perform Class II analysis on the design parameters.
    
    This function orchestrates the detailed design phase including:
    - Class II wing sizing (using delta method for t/c)
    - Tail sizing
    - Landing gear positioning  
    - Improved drag estimation
    - Detailed component weight estimation with convergence
    - Center of gravity analysis
    
    Parameters:
        params (DesignParameters): Design parameters object
        initial_W_TO_guess (float): Initial guess for take-off weight. If None, uses params.weight.W_TO
    
    Returns:
        dict: Combined results from all Class II analysis modules
    """
    print("\n" + "="*60)
    print("           RUNNING CLASS II ANALYSIS")
    print("="*60)
    
    # Use provided guess or fall back to current W_TO
    if initial_W_TO_guess is None:
        initial_W_TO_guess = params.weight.W_TO
    
    print(f"\nStarting Class II with initial W_TO guess: {initial_W_TO_guess:.2f} N")
    
    combined_results = {}
    
    # 1. Class II Wing Sizing (using delta method)
    print("\n1. Class II Wing Sizing...")
    try:
        from class2.class_II_wing_sizing import optimize_wing_for_fuel_burn
        
        wing_class_ii_results = optimize_wing_for_fuel_burn(params)
        combined_results.update(wing_class_ii_results)
        
        # Update wing parameters directly with refined results (inline, no separate function)
        if 'Lambda_025c_w_optimal' in wing_class_ii_results:
            params.wing.Lambda_025c_w = wing_class_ii_results['Lambda_025c_w_optimal']
        if 'Lambda_05c_w_optimal' in wing_class_ii_results:
            params.wing.Lambda_05_w = wing_class_ii_results['Lambda_05c_w_optimal'] 
        if 'Lambda_LE_w_optimal' in wing_class_ii_results:
            params.wing.Lambda_0_w = wing_class_ii_results['Lambda_LE_w_optimal']
        if 'lambda_w_optimal' in wing_class_ii_results:
            params.wing.lambda_w = wing_class_ii_results['lambda_w_optimal']
        if 'root_chord_optimal' in wing_class_ii_results:
            params.wing.root_chord = wing_class_ii_results['root_chord_optimal']
        if 'tip_chord_optimal' in wing_class_ii_results:
            params.wing.tip_chord = wing_class_ii_results['tip_chord_optimal']
        if 'mac_optimal' in wing_class_ii_results:
            params.wing.mac = wing_class_ii_results['mac_optimal']
        if 'y_LEMAC_optimal' in wing_class_ii_results:
            params.wing.y_LEMAC = wing_class_ii_results['y_LEMAC_optimal']
        if 't_c_w_optimal' in wing_class_ii_results:
            params.wing.t_c_w_max = wing_class_ii_results['t_c_w_optimal']
            params.wing.t_c_w_r = wing_class_ii_results['t_c_w_optimal']  # Assume root = max for now
        if 'Gamma_w_optimal' in wing_class_ii_results:
            params.wing.Gamma_w = wing_class_ii_results['Gamma_w_optimal']
        
        print(f"   ✅ Class II wing sizing complete. Refined t/c = {wing_class_ii_results.get('t_c_w_optimal', 'N/A'):.3f}")
    except Exception as e:
        print(f"   ⚠️  Class II wing sizing failed: {e}")
        wing_class_ii_results = {}
    
    # 2. Tail Sizing
    print("\n1. Tail Sizing...")
    try:
        tail_results = run_preliminary_sizing_tail(params)
        combined_results.update(tail_results)
        
        # Update parameters directly with tail results
        if 'S_h' in tail_results:
            params.empennage.S_h = tail_results['S_h']
        if 'S_v' in tail_results:
            params.empennage.S_v = tail_results['S_v']
        if 'S_t' in tail_results:
            params.empennage.S_t = tail_results['S_t']
        if 'b_t' in tail_results:
            params.empennage.b_v = tail_results['b_t']
        if 'dihedral_rad (gamma)' in tail_results:
            params.empennage.vtail_dihedral = tail_results['dihedral_rad (gamma)']
        if 'Lambda_025c_t' in tail_results:
            params.empennage.Lambda_t_025c = tail_results['Lambda_025c_t']
        if 'aspect_ratio_t' in tail_results:
            params.empennage.A_t = tail_results['aspect_ratio_t']
        if 'taper_ratio_t' in tail_results:
            params.empennage.lambda_t = tail_results['taper_ratio_t']
        if 't_c_t' in tail_results:
            params.empennage.t_c_t = tail_results['t_c_t']
        if 'c_root_t' in tail_results:
            params.empennage.c_r = tail_results['c_root_t']
        if 'c_tip_t' in tail_results:
            params.empennage.c_t = tail_results['c_tip_t']

        print(f"   ✅ Tail sizing complete. S_t = {tail_results.get('S_t', 'N/A'):.2f} m²")
    except Exception as e:
        print(f"   ⚠️  Tail sizing failed: {e}")
        tail_results = {}
    
    # 2. Landing Gear Positioning
    print("\n2. Landing Gear Positioning...")
    try:
        undercarriage_results = perform_undercarriage_positioning(params)
        combined_results.update(undercarriage_results)
        print(f"   ✅ Landing gear positioning complete.")
    except Exception as e:
        print(f"   ⚠️  Landing gear positioning failed: {e}")
        undercarriage_results = {}
    
    # 3. Improved Drag Estimation
    print("\n3. Improved Drag Estimation...")
    try:
        drag_results = run_improved_drag_estimations(params)
        combined_results.update(drag_results)
        
        # Update parameters directly with drag results
        if 'CD0' in drag_results:
            params.wing.C_D0 = drag_results['CD0']
            
        print(f"   ✅ Drag estimation complete. CD0 = {drag_results.get('CD0', 'N/A'):.6f}")
    except Exception as e:
        print(f"   ⚠️  Drag estimation failed: {e}")
        drag_results = {}
    
    # 4. Detailed Component Weight Estimation with Convergence
    print("\n4. Detailed Component Weight Estimation...")
    try:
        final_W_TO, converged, iterations, W_empty_final = class_II_weight_estimation(
            params=params,
            initial_W_TO_N_guess=initial_W_TO_guess,
            max_iterations=100,
            tolerance=0.005
        )
        
        # Store weight results
        weight_results = {
            "W_TO": final_W_TO,
            "W_E": W_empty_final,
            "W_OE": W_empty_final + params.weight.W_crew,
            "W_F": final_W_TO * (1 - params.weight.M_ff),
            "converged": converged,
            "iterations": iterations
        }
        combined_results.update(weight_results)
        
        if converged:
            print(f"   ✅ Weight estimation converged. Final W_TO: {final_W_TO:.2f} N")
        else:
            print(f"   ⚠️  Weight estimation did not converge. Final W_TO: {final_W_TO:.2f} N")
            
    except Exception as e:
        print(f"   ⚠️  Weight estimation failed: {e}")
        weight_results = {"W_TO": initial_W_TO_guess, "converged": False}
        combined_results.update(weight_results)
    
    # 5. Center of Gravity Analysis
    print("\n5. Center of Gravity Analysis...")
    try:
        cg_results = calculate_cg_longitudinal(params, weight_results)
        combined_results.update(cg_results)
        
        # Estimate MAC leading edge position
        if 'OEW' in cg_results and hasattr(params.wing, 'mac'):
            mac_results = estimate_mac_leading_edge(
                cg_OEW=cg_results['OEW'],
                target_CG_percent_MAC=0.30,  # 30% MAC is typical
                mac_length=params.wing.mac
            )
            combined_results.update(mac_results)
        
        print(f"   ✅ CG analysis complete.")
    except Exception as e:
        print(f"   ⚠️  CG analysis failed: {e}")
    
    print(f"\n✅ Class II Analysis Complete. Generated {len(combined_results)} parameters.")
    return combined_results


if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    
    analysis_results = perform_class_II_analysis(params)
    
    print("\n" + "="*40)
    print("       CLASS II RESULTS SUMMARY")
    print("="*40)
    for key, value in analysis_results.items():
        if isinstance(value, (int, float)):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")