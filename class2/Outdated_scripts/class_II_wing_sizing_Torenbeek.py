"""
Class II Wing Sizing Module - Using Existing Torenbeek Methods

This module adapts the sophisticated methods from the wing planform optimization script
for Class II analysis WITHOUT the full optimization loop. It uses:
- Proper Torenbeek input calculations
- Actual delta method for t/c
- Current design state (not optimization)
- Existing WPF calculation methods (without the optimization)
"""

import numpy as np
import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import class1.preliminary_sizing.prelim_sizing_wing as psw

# Import the wing optimization functions to use their methods
try:
    from Wing_Planform_Adv_AC_Design_Delta_torenbeek_classII import (
        calculate_torenbeek_inputs_from_params,
        calculate_WPF_transonic
    )
    import delta_method_classII as dm
    ADVANCED_METHODS_AVAILABLE = True
except ImportError:
    print("Warning: Advanced wing methods not available. Using Class I methods only.")
    ADVANCED_METHODS_AVAILABLE = False


def run_class_II_wing_sizing(params: DesignParameters) -> dict:
    """
    Perform Class II wing sizing using the existing Torenbeek methods.
    
    This function uses the current design state and applies the sophisticated
    calculation methods from the wing optimization script WITHOUT doing 
    a full optimization. It calculates refined wing parameters using:
    - Current MTOW and wing area from iterative design
    - Proper Torenbeek input calculations  
    - Delta method for accurate t/c calculation
    - Existing WPF methods for validation
    
    Parameters:
        params (DesignParameters): Current design parameters
        
    Returns:
        dict: Refined wing parameters using Class II methods
    """
    
    print("  - Running Class II Wing Sizing (using Torenbeek methods)...")
    
    if not ADVANCED_METHODS_AVAILABLE:
        print("    ⚠️  Advanced methods not available. Using Class I results.")
        # Fall back to Class I wing sizing if advanced methods not available
        class_i_results = psw.run_preliminary_sizing_wing(params)
        return {f"{key}_refined": value for key, value in class_i_results.items()}
    
    try:
        # Step 1: Use existing Torenbeek input calculations
        print("    📊 Calculating Torenbeek inputs from current design state...")
        torenbeek_inputs = calculate_torenbeek_inputs_from_params(params)
        
        # Step 2: Use current design variables (not optimization)
        W_TO = params.weight.W_TO
        S_w = params.wing.S_w
        cruise_mach = params.cruise_mach
        
        # Calculate current aspect ratio and wing loading
        A_w_current = params.wing.A_w_target
        wing_loading_Pa = W_TO / S_w
        
        # Step 3: Calculate design lift coefficient at cruise (proper method)
        q_hat_Pa = torenbeek_inputs["q_hat_Pa"]
        C_L_design = W_TO / (q_hat_Pa * S_w) if q_hat_Pa > 0 and S_w > 0 else 0.4
        
        print(f"    📊 Current state: W_TO={W_TO:.0f}N, S_w={S_w:.1f}m², C_L_design={C_L_design:.3f}")
        
        # Step 4: Use existing sweep calculation (from Class I)
        Lambda_025c_rad = psw.calculate_sweep_angle_025c_rad(cruise_mach, params.wing.Mach_cross)
        Lambda_025c_deg = np.rad2deg(Lambda_025c_rad)
        
        # Step 5: **KEY ENHANCEMENT - Use proper delta method for t/c**
        print(f"    🔬 Calculating t/c using delta method...")
        print(f"        Inputs: Mach={cruise_mach:.3f}, A_w={A_w_current:.1f}, Sweep={Lambda_025c_deg:.1f}°, C_L={C_L_design:.3f}")
        
        t_c_refined = dm.calculate_tc_from_delta_method(
            target_cruise_mach=cruise_mach,
            A_w=A_w_current,
            Lambda_w_deg=Lambda_025c_deg,
            C_L_hat=C_L_design
        )
        
        print(f"        ✅ Delta method result: t/c = {t_c_refined:.4f}")
        
        # Step 6: Calculate other wing geometry using existing methods
        taper_ratio = psw.calculate_taper_ratio(Lambda_025c_rad)
        b_w = math.sqrt(A_w_current * S_w)
        c_root, c_tip = psw.calculate_chord_lengths(S_w, b_w, taper_ratio)
        MAC, y_LEMAC = psw.calculate_MAC_and_y_LEMAC(c_root, c_tip, b_w)
        
        # Calculate other sweep angles
        Lambda_LE = psw.calculate_sweep_angle_LE(Lambda_025c_rad, c_root, b_w, taper_ratio)
        Lambda_05c = psw.calculate_sweep_angle_x_c(Lambda_LE, c_root, b_w, 0.5, taper_ratio)
        dihedral_rad = psw.calculate_dihedral_angle_rad(Lambda_025c_rad)
        
        # Step 7: Optional - Calculate WPF for validation (not optimization)
        try:
            wpf_value = calculate_WPF_transonic(
                torenbeek_inputs["phi_3"], torenbeek_inputs["phi_2"], 
                torenbeek_inputs["F_prop"], C_L_design, A_w_current, 
                Lambda_025c_rad, torenbeek_inputs["e_hat"], 
                cruise_mach, torenbeek_inputs["C_f"], torenbeek_inputs["C_Dc"]
            )
            print(f"    📈 Wing Penalty Function: {wpf_value:.4f} (for reference)")
        except Exception as e:
            print(f"    ⚠️  WPF calculation failed: {e}")
            wpf_value = None
        
        # Prepare results
        results = {
            'S_w_refined': S_w,
            'b_w_refined': b_w,
            'A_w_refined': A_w_current,
            'Lambda_025c_w_refined': Lambda_025c_rad,
            'Lambda_05c_w_refined': Lambda_05c,
            'Lambda_LE_w_refined': Lambda_LE,
            'lambda_w_refined': taper_ratio,
            'root_chord_refined': c_root,
            'tip_chord_refined': c_tip,
            'mac_refined': MAC,
            'y_LEMAC_refined': y_LEMAC,
            't_c_w_refined': t_c_refined,  # This is the key Class II enhancement using delta method
            'Gamma_w_refined': dihedral_rad,
            'C_L_design': C_L_design,
            'wing_loading_Pa': wing_loading_Pa,
            'WPF_value': wpf_value,
            'torenbeek_inputs_used': True
        }
        
        print(f"    ✅ Class II wing sizing complete using Torenbeek methods.")
        print(f"    📊 Key results: t/c = {t_c_refined:.4f}, Wing loading = {wing_loading_Pa:.0f} Pa")
        
        return results
        
    except Exception as e:
        print(f"    ⚠️  Class II wing sizing failed: {e}")
        print(f"    🔄 Falling back to Class I wing sizing...")
        
        # Fall back to Class I methods if anything fails
        try:
            class_i_results = psw.run_preliminary_sizing_wing(params)
            return {f"{key}_refined": value for key, value in class_i_results.items()}
        except:
            return {}


if __name__ == "__main__":
    # Test the Class II wing sizing
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    
    print("Testing Class II Wing Sizing...")
    results = run_class_II_wing_sizing(params)
    
    print("\n--- Class II Wing Sizing Results ---")
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    print("✅ Test complete")