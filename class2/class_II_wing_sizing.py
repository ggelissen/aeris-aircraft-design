
"""
Class II Wing Sizing - Sequential Approach

This module refines the Class I wing estimates using sophisticated methods 
from the wing optimization script, but in a sequential rather than optimization approach.

Uses the excellent methods from Wing_Planform_Adv_AC_Design_Delta_torenbeek_classII.py:
- Delta method for thickness-to-chord ratio
- Sophisticated sweep angle calculations  
- Proper Mach number effects

But integrates with our weight estimation and drag calculation approach.
"""

import numpy as np
import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import class2.component_weights as cw
import class2.improved_drag as drag_calc

# Import the excellent delta method from the wing optimization script
try:
    import delta_method_classII as dm
except ImportError:
    print("Warning: delta_method_classII not found. Using placeholder.")
    dm = None


def calculate_optimal_thickness_ratio(params: DesignParameters) -> float:
    """
    Calculate optimal thickness-to-chord ratio using the sophisticated delta method.
    This is one of the best methods from the wing optimization script.
    
    Parameters:
        params (DesignParameters): Design parameters object
        
    Returns:
        float: Optimal thickness-to-chord ratio
    """
    if dm is None:
        # Fallback if delta method not available
        print("  ⚠️  Using fallback t/c calculation")
        return 0.12  # Default value
    
    try:
        # Use the sophisticated delta method
        Mach_cruise = params.cruise_mach
        A_w = params.wing.A_w_target
        Lambda_w_deg = np.rad2deg(params.wing.Lambda_025c_w)
        
        # Calculate C_L_hat (design lift coefficient)
        W_TO = params.weight.W_TO
        S_w = params.wing.S_w
        q_cruise = 0.5 * params.cruise_density * params.cruise_speed**2
        C_L_hat = W_TO / (q_cruise * S_w)
        
        # Use delta method to calculate optimal t/c
        t_c_optimal = dm.calculate_tc_from_delta_method(Mach_cruise, A_w, Lambda_w_deg, C_L_hat)
        
        print(f"  ✅ Delta method t/c calculation: {t_c_optimal:.3f}")
        return max(0.08, min(0.18, t_c_optimal))  # Reasonable bounds
        
    except Exception as e:
        print(f"  ⚠️  Delta method failed: {e}, using fallback")
        return 0.12


def calculate_optimal_sweep_angle(params: DesignParameters) -> float:
    """
    Calculate optimal sweep angle using aerodynamic theory.
    Based on the methods from the wing optimization script.
    
    Parameters:
        params (DesignParameters): Design parameters object
        
    Returns:
        float: Optimal quarter-chord sweep angle in radians
    """
    Mach_cruise = params.cruise_mach
    Mach_dd = Mach_cruise + 0.015  # Drag divergence Mach
    Mach_kappa = 0.935  # Critical Mach for supercritical airfoil
    
    if Mach_cruise < 0.7:
        # Low speed - minimal sweep needed
        Lambda_025c = 0.0
    else:
        # High speed - sweep for compressibility
        Lambda_025c = np.arccos(0.75 * (Mach_kappa / Mach_dd))
    
    print(f"  ✅ Optimal sweep angle: {np.rad2deg(Lambda_025c):.1f}°")
    return Lambda_025c


def refine_wing_geometry(params: DesignParameters) -> dict:
    """
    Refine wing geometry using Class II methods while keeping Class I sizing.
    
    This function:
    1. Keeps wing area and span from Class I (no optimization)
    2. Refines thickness-to-chord ratio using delta method
    3. Refines sweep angle using aerodynamic theory
    4. Calculates detailed geometry parameters
    5. Updates wing weight using our component weight method
    
    Parameters:
        params (DesignParameters): Design parameters object
        
    Returns:
        dict: Refined wing parameters
    """
    print("  🔧 Refining wing geometry using Class II methods...")
    
    # Keep Class I sizing (area and span)
    S_w = params.wing.S_w
    b_w = params.wing.b_w
    A_w = b_w**2 / S_w  # Recalculate aspect ratio
    
    print(f"    Using Class I sizing: S_w = {S_w:.2f} m², b_w = {b_w:.2f} m, A_w = {A_w:.1f}")
    
    # 1. Calculate optimal thickness-to-chord ratio (sophisticated delta method)
    t_c_optimal = calculate_optimal_thickness_ratio(params)
    
    # 2. Calculate optimal sweep angle (aerodynamic theory)
    Lambda_025c_optimal = calculate_optimal_sweep_angle(params)
    
    # 3. Update wing parameters
    params.wing.t_c_w_r = t_c_optimal
    params.wing.t_c_w_t = t_c_optimal  # Assume constant for now
    params.wing.Lambda_025c_w = Lambda_025c_optimal
    params.wing.A_w_actual = A_w
    
    # 4. Calculate other sweep angles (using methods from wing optimization script)
    taper_ratio = params.wing.lambda_w  # Keep existing taper ratio
    c_root = 2 * S_w / (b_w * (1 + taper_ratio))
    c_tip = c_root * taper_ratio
    
    # Calculate sweep angles at different chord positions
    # Leading edge sweep
    Lambda_LE = np.arctan2(np.tan(Lambda_025c_optimal) + 0.25 * 2 * c_root / b_w * (1 - taper_ratio), 1)
    
    # Half-chord sweep  
    Lambda_05c = np.arctan2(np.tan(Lambda_LE) - 0.5 * 2 * c_root / b_w * (1 - taper_ratio), 1)
    
    # Update parameters
    params.wing.Lambda_0_w = Lambda_LE
    params.wing.Lambda_05_w = Lambda_05c
    params.wing.root_chord = c_root
    params.wing.tip_chord = c_tip
    
    # 5. Calculate wing weight using our component weight method (not optimization)
    try:
        W_wing_new = cw.wing_weight_N(params)
        print(f"    Updated wing weight: {W_wing_new:.2f} N")
    except Exception as e:
        print(f"    ⚠️  Wing weight calculation failed: {e}")
        W_wing_new = None
    
    results = {
        'A_w_refined': A_w,
        't_c_w_refined': t_c_optimal,
        'Lambda_025c_w_refined': Lambda_025c_optimal,
        'Lambda_LE_w_refined': Lambda_LE,
        'Lambda_05c_w_refined': Lambda_05c,
        'c_root_refined': c_root,
        'c_tip_refined': c_tip,
        'W_wing_refined': W_wing_new
    }
    
    print(f"  ✅ Wing geometry refinement complete")
    return results


def run_class_II_wing_sizing(params: DesignParameters) -> dict:
    """
    Main function for Class II wing sizing.
    
    This is a sequential refinement approach that uses the best methods
    from the wing optimization script but integrates with our design process.
    
    Parameters:
        params (DesignParameters): Design parameters object
        
    Returns:
        dict: Refined wing parameters
    """
    print("\n🔧 Running Class II Wing Sizing (Sequential Refinement)...")
    
    # Store initial values for comparison
    initial_t_c = params.wing.t_c_w_r
    initial_sweep = np.rad2deg(params.wing.Lambda_025c_w)
    
    print(f"  Initial values: t/c = {initial_t_c:.3f}, Λ₁/₄ = {initial_sweep:.1f}°")
    
    # Refine wing geometry
    results = refine_wing_geometry(params)
    
    # Update drag calculation with refined geometry
    try:
        drag_results = drag_calc.run_improved_drag_estimations(params)
        results.update(drag_results)
        print(f"  ✅ Updated CD0 with refined geometry: {drag_results.get('CD0', 'N/A'):.6f}")
    except Exception as e:
        print(f"  ⚠️  Drag recalculation failed: {e}")
    
    # Summary
    final_t_c = params.wing.t_c_w_r
    final_sweep = np.rad2deg(params.wing.Lambda_025c_w)
    
    print(f"  Final values: t/c = {final_t_c:.3f}, Λ₁/₄ = {final_sweep:.1f}°")
    print(f"  Changes: Δt/c = {final_t_c - initial_t_c:+.3f}, ΔΛ₁/₄ = {final_sweep - initial_sweep:+.1f}°")
    
    return results


if __name__ == "__main__":
    # Test the Class II wing sizing
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    
    results = run_class_II_wing_sizing(params)
    
    print("\n" + "="*50)
    print("    CLASS II WING SIZING RESULTS")
    print("="*50)
    for key, value in results.items():
        if isinstance(value, (int, float)):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")