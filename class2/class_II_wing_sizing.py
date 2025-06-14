
"""
Class II Wing Optimization Module - Fuel Burn Penalty Function

This module optimizes the wing planform by minimizing fuel burn, which elegantly
captures the trade-offs between:
- Drag (CD0) → affects L/D → affects fuel consumption
- Wing weight → affects W_TO → affects fuel consumption  
- Aspect ratio → affects L/D → affects fuel consumption

Uses only existing functions from project files:
- calculate_L_D_cruise_jet (from initial_weight_estimations.py)
- calculate_cruise_fuel_fraction_jet (from initial_weight_estimations.py)
- wing_weight_N (from component_weights.py)
- run_improved_drag_estimations (from improved_drag.py)
- Mission segment fuel fractions (from initial_weight_estimations.py)
"""

import numpy as np
import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import class1.preliminary_sizing.prelim_sizing_wing as psw
from class2.improved_drag import run_improved_drag_estimations
from class1.initial_weight_estimations import (
    calculate_L_D_cruise_jet, 
    calculate_cruise_fuel_fraction_jet,
    get_statistical_fuel_fractions
)
from utils.unit_conversions import *

# Import delta method
#try:
import delta_method_classII as dm
#DELTA_METHOD_AVAILABLE = True
#except ImportError:
  #  print("Warning: Delta method not available")
   # DELTA_METHOD_AVAILABLE = False

# Constants from initial_weight_estimations.py
G = 9.80665  # Gravity constant in m/s^2


def calculate_fuel_burn_penalty(A_w: float, S_w: float, sweep_deg: float, t_c: float, 
                               params: DesignParameters, W_TO_baseline: float) -> float:
    """
    Calculate fuel burn penalty for given wing parameters.
    
    This function:
    1. Updates wing parameters with trial values
    2. Calculates new CD0 using improved_drag
    3. Calculates L/D using calculate_L_D_cruise_jet 
    4. Calculates cruise fuel fraction using calculate_cruise_fuel_fraction_jet
    5. Calculates total mission fuel fraction using statistical fuel fractions
    6. Adjusts W_TO by removing old wing weight and adding new wing weight
    7. Calculates total fuel weight W_F_total
    
    Lower fuel weight = better design!
    
    Parameters:
        A_w (float): Trial aspect ratio
        S_w (float): Trial wing area (m²)
        sweep_deg (float): Trial sweep angle (degrees)
        t_c (float): Trial thickness-to-chord ratio
        params (DesignParameters): Design parameters (temporarily modified)
        W_TO_baseline (float): Current baseline take-off weight
        
    Returns:
        float: Total fuel weight in N (penalty to minimize)
    """
    
    try:
        # Store original values to restore later
        original_values = {
            'A_w_actual': params.wing.A_w_actual,
            'A_w_target': params.wing.A_w_target,            
            'S_w': params.wing.S_w,
            'b_w': params.wing.b_w,
            'Lambda_025c_w': params.wing.Lambda_025c_w,
            'Lambda_05_w': params.wing.Lambda_05_w,
            'Lambda_0_w': params.wing.Lambda_0_w,
            't_c_w_r': params.wing.t_c_w_r,
            't_c_w_max': params.wing.t_c_w_max,
            'lambda_w': params.wing.lambda_w,
            'root_chord': params.wing.root_chord,
            'tip_chord': params.wing.tip_chord,
            'W_TO': params.weight.W_TO
        }
        
        # Calculate current wing weight (to subtract from baseline W_TO), before updating params with trial values
        from class2.component_weights import wing_weight_N
        #print("     Calculating current wing weight before trial parameters...")
        W_wing_current = wing_weight_N(params)
        
        # Update params with trial wing parameters
        params.wing.A_w_actual = A_w
        params.wing.A_w_target = A_w  # Keep both consistent        
        params.wing.S_w = S_w
        params.wing.b_w = math.sqrt(A_w * S_w)
        params.wing.Lambda_025c_w = np.deg2rad(sweep_deg) # Todo, supposed to be in radians, ok.
        params.wing.t_c_w_r = t_c
        params.wing.t_c_w_max = t_c
        
        # Calculate complete wing geometry using PSW functions
        taper_ratio = psw.calculate_taper_ratio(params.wing.Lambda_025c_w)
        params.wing.lambda_w = taper_ratio
        
        c_root, c_tip = psw.calculate_chord_lengths(params.wing.S_w, params.wing.b_w, taper_ratio)
        params.wing.root_chord = c_root
        params.wing.tip_chord = c_tip
        
        # Calculate sweep angles using existing functions TODO check this.
        Lambda_LE = psw.calculate_sweep_angle_LE(params.wing.Lambda_025c_w, c_root, params.wing.b_w, taper_ratio)
        params.wing.Lambda_0_w = Lambda_LE
        Lambda_05c = psw.calculate_sweep_angle_x_c(Lambda_LE, c_root, params.wing.b_w, 0.5, taper_ratio)
        params.wing.Lambda_05_w = Lambda_05c
        
        # Calculate new wing weight with trial parameters
        #print(f"     Calculating wing weight with trial parameters: A_w={A_w:.2f}, S_w={S_w:.2f} m², sweep={sweep_deg:.1f}°, t/c={t_c:.4f}")
        W_wing_trial = wing_weight_N(params)
        
        # Adjust W_TO: remove current wing, add trial wing
        W_TO_adjusted = W_TO_baseline - W_wing_current + W_wing_trial
        #print(f"Difference in W_TO due to wing weight: {W_wing_trial - W_wing_current:.2f} N")
        params.weight.W_TO = W_TO_adjusted
        
        # Step 1: Calculate CD0 using improved_drag with trial parameters
        drag_results = run_improved_drag_estimations(params)
        CD0 = drag_results.get('CD0')  # Default if calculation fails
        #print(f"     Calculated CD0: {CD0:.6f} (from improved_drag)")
        # Step 2: Calculate L/D using existing function from initial_weight_estimations.py
        # Assume reasonable Oswald efficiency for modern wing
        e_oswald = 0.9 *1.15 # Typical value for clean wing # for winglets TODO check
        L_D_cruise = calculate_L_D_cruise_jet(CD0, A_w, e_oswald)
        
        # Step 3: Calculate cruise fuel fraction using existing function
        R_cruise_m = params.range  # Mission range
        V_cruise_ms = params.cruise_speed  # Cruise speed
        c_j_kg_Ns = lb_hr_lbf_to_kg_Ns(params.engine.cruise_tsfc)  # TSFC in SI units
        
        M_cruise_fuel_fraction = calculate_cruise_fuel_fraction_jet(
            R_cruise_m, V_cruise_ms, L_D_cruise, c_j_kg_Ns
        )
        # print(f"     Calculated cruise fuel fraction: {M_cruise_fuel_fraction:.6f}, with parameters:\n"
        #       f"     R_cruise_m = {R_cruise_m:.1f} m, V_cruise_ms = {V_cruise_ms:.1f} m/s, "
        #       f"L/D_cruise = {L_D_cruise:.2f}, c_j_kg_Ns = {c_j_kg_Ns:.6f} kg/(N·s)")
        # Step 4: Calculate other mission segment fuel fractions using existing functions
        aircraft_type = "uav"  # From initial_weight_estimations.py
        
        # Mission segments (from initial_weight_estimations.py UAV example)
        M_ff_total = 1.0
        
        # Statistical fuel fractions for non-cruise segments
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M1_eng_start_warmup")
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M2_taxi_out") 
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M3_take_off")
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M4_climb1")
        M_ff_total *= M_cruise_fuel_fraction  # Cruise segment
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M6_descent1")
        
        # Reserve segments (if applicable)
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M7_climb2_reserve")
        # Reserve cruise - use same L/D but shorter range
        reserve_range = params.diversion_distance
        M_reserve_cruise = calculate_cruise_fuel_fraction_jet(
            reserve_range, V_cruise_ms, L_D_cruise, c_j_kg_Ns
        )
        M_ff_total *= M_reserve_cruise
        
        # Reserve loiter - use loiter L/D
        from class1.initial_weight_estimations import calculate_L_D_loiter
        L_D_loiter = calculate_L_D_loiter(CD0, A_w, e_oswald)
        from class1.initial_weight_estimations import calculate_loiter_fuel_fraction_jet
        M_loiter = calculate_loiter_fuel_fraction_jet(
            params.loiter_time, L_D_loiter, c_j_kg_Ns
        )
        M_ff_total *= M_loiter
        
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M10_descent2_reserve")
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M11_land_taxi_shutdown")
        
        # Step 5: Calculate total fuel weight
        # From initial_weight_estimations.py: W_F_total = (1 - M_ff_total) * W_TO
        W_F_total_N = (1.0 - M_ff_total) * W_TO_adjusted
        
        # Restore original values TODO, why
        for key, value in original_values.items():
            if '.' in key:
                obj_name, attr_name = key.split('.')
                obj = getattr(params, obj_name)
                setattr(obj, attr_name, value)
            else:
                if hasattr(params.wing, key):
                    setattr(params.wing, key, value)
                elif hasattr(params.weight, key):
                    setattr(params.weight, key, value)
        
        # Ensure fuel weight is positive and reasonable
        if W_F_total_N <= 0 or W_F_total_N > W_TO_adjusted * 0.8:
            return 1e6  # High penalty for unrealistic fuel weight
        
        return W_F_total_N
        
    except Exception as e:
        print(f"    ⚠️  Fuel burn calculation failed: {e}")
        
        # Restore original values even if failed
        try:
            for key, value in original_values.items():
                if hasattr(params.wing, key):
                    setattr(params.wing, key, value)
                elif hasattr(params.weight, key):
                    setattr(params.weight, key, value)
        except:
            pass
        
        return 1e6


def optimize_wing_for_fuel_burn(params: DesignParameters) -> dict:
    """
    Optimize wing planform by minimizing fuel burn.
    
    This function finds the wing configuration (A_w, S_w, sweep, t/c) that
    minimizes total mission fuel weight, elegantly capturing all trade-offs.
    
    Parameters:
        params (DesignParameters): Current design parameters
        
    Returns:
        dict: Optimized wing parameters that minimize fuel burn
    """
    
    print("  - Optimizing wing planform for minimum fuel burn...")
    
    # Use current W_TO as baseline for wing weight adjustment
    W_TO_baseline = params.weight.W_TO
    
    # Calculate baseline L/D for fuel fraction estimation
    baseline_drag = run_improved_drag_estimations(params)
    baseline_CD0 = baseline_drag.get('CD0', 0.020)
    baseline_A_w = params.wing.A_w_target
    e_oswald = 0.9 * 1.15  # Typical Oswald efficiency for clean wing with winglets
    baseline_L_D = calculate_L_D_cruise_jet(baseline_CD0, baseline_A_w, e_oswald)
    
    # Calculate baseline cruise fuel fraction
    R_cruise_m = params.range
    V_cruise_ms = params.cruise_speed
    c_j_kg_Ns = lb_hr_lbf_to_kg_Ns(params.engine.cruise_tsfc)
    
    baseline_cruise_fuel_fraction = calculate_cruise_fuel_fraction_jet(
        R_cruise_m, V_cruise_ms, baseline_L_D, c_j_kg_Ns
    )
    
    # Calculate fuel fractions for segments before cruise
    aircraft_type = "uav"
    fuel_fraction_before_cruise = 1.0
    fuel_fraction_before_cruise *= get_statistical_fuel_fractions(aircraft_type, "M1_eng_start_warmup")
    fuel_fraction_before_cruise *= get_statistical_fuel_fractions(aircraft_type, "M2_taxi_out") 
    fuel_fraction_before_cruise *= get_statistical_fuel_fractions(aircraft_type, "M3_take_off")
    fuel_fraction_before_cruise *= get_statistical_fuel_fractions(aircraft_type, "M4_climb1")
    
    rho_cruise = params.cruise_density  # kg/m³
    V_cruise = params.cruise_speed
    q_cruise = 0.5 * rho_cruise * V_cruise**2

    print(f"    📊 Baseline W_TO = {W_TO_baseline:.0f} N")
    print(f"    🎯 Objective: Minimize total mission fuel weight")
    
    # Define optimization ranges (reasonable for business jet UAV)
    A_w_range = np.linspace(7, 12, 15)           # Aspect ratio
    S_w_range = np.linspace(5, 22, 15)          # Wing area (m²)  
    sweep_deg_range = np.linspace(25, 40, 15)    # Sweep angle (deg)
    
    # Initialize best solution tracking
    best_fuel_weight = float('inf')
    best_params = {}
    
    total_evaluations = 0
    successful_evaluations = 0
    failed_configurations = {}
    print(f"    🔍 Evaluating {len(A_w_range) * len(S_w_range) * len(sweep_deg_range)} design points...")
    
    # Grid search optimization
    for A_w in A_w_range:
        params.wing.A_w_target = A_w  # Update target aspect ratio
        for S_w in S_w_range:
            params.wing.S_w = S_w  # Update wing area
            # Check wing loading constraint first (quick elimination)
            wing_loading = W_TO_baseline / S_w
            if wing_loading < 1500 or wing_loading > 7000:  # N/m² - reasonable bounds
                continue
                
            for sweep_deg in sweep_deg_range:
                params.wing.Lambda_025c_w = np.deg2rad(sweep_deg)
                
                # CALCULATE C_L_DESIGN BEFORE DELTA METHOD CALL
                # Using baseline fuel fractions and trial S_w
                W_start_cruise = W_TO_baseline * fuel_fraction_before_cruise
                W_end_cruise = W_start_cruise * baseline_cruise_fuel_fraction
                # print(f" Using fuel fractions: "
                #       f"before cruise = {fuel_fraction_before_cruise:.3f}, "
                #       f"cruise = {baseline_cruise_fuel_fraction:.3f}")
                # Your formula for C_L_design:
                W_S_start_cruise = W_start_cruise / S_w
                W_S_end_cruise = W_end_cruise / S_w  
                C_L_design = 1.1 / q_cruise * 0.5 * (W_S_start_cruise + W_S_end_cruise) # It 
                
                # print(f" C_L_design (before delta method) = {C_L_design:.3f} ")
                # Correction for sweep TODO, big difference whether this is included or not!
                C_L_design_corrected = C_L_design / np.cos(np.deg2rad(sweep_deg))**2  # Not sure if Delta method does this internally, but let's be safe
                #print(f"C_L_design = {C_L_design:.3f} (sweep={sweep_deg:.1f}°), CL_design_corrected = {C_L_design_corrected:.3f}")
                t_c = dm.calculate_tc_from_delta_method(
                    target_cruise_mach=params.cruise_mach,
                    aspect_ratio=A_w,
                    sweep_deg=sweep_deg,
                    cl_des=C_L_design_corrected
                )


                total_evaluations += 1
                
                # Check t/c ratio
                if t_c < 0.05 or t_c > 0.20:  # Reasonable bounds for UAV wing
                    #print(f"    ❌ Skipping configuration: A_w={A_w:.1f}, S_w={S_w:.1f} m², "
                    #      f"sweep={sweep_deg:.1f}°, t/c={t_c:.3f} (out of bounds), C_L_design={C_L_design_corrected:.3f}")
                    continue  # Skip this configuration, move on to next! 

                # Calculate fuel burn penalty for this configuration
                try:
                    fuel_weight = calculate_fuel_burn_penalty(
                        A_w, S_w, sweep_deg, t_c, params, W_TO_baseline
                    )
                    successful_evaluations += 1
                    
                    if fuel_weight < best_fuel_weight:
                        best_fuel_weight = fuel_weight
                        best_params = {
                            'A_w_optimal': A_w,
                            'S_w_optimal': S_w,
                            'sweep_deg_optimal': sweep_deg,
                            't_c_optimal': t_c,
                            'fuel_weight_N': fuel_weight,
                            'wing_loading_optimal': W_TO_baseline / S_w,
                            'fuel_fraction_optimal': fuel_weight / W_TO_baseline
                        }
                        
                        #print(f"    New best: A_w={A_w:.1f}, S_w={S_w:.1f}m², sweep={sweep_deg:.1f}°")
                        #print(f"    Fuel weight: {fuel_weight:.0f} N ({fuel_weight/W_TO_baseline:.1%} of W_TO)")
                        
                except Exception as e:
                    # Skip failed evaluations
                    continue
    
    success_rate = successful_evaluations / total_evaluations if total_evaluations > 0 else 0
    print(f"    Optimization complete: {successful_evaluations}/{total_evaluations} evaluations successful ({success_rate:.1%}) Most likely due to Cl of airfoil being out of Delta method bounds.")
    
    if best_params:
        print(f"        Optimal wing configuration:")
        print(f"        Aspect Ratio = {best_params['A_w_optimal']:.2f}")
        print(f"        Wing Area = {best_params['S_w_optimal']:.2f} m²") 
        print(f"        Sweep Angle = {best_params['sweep_deg_optimal']:.1f}°")
        print(f"        t/c Ratio = {best_params['t_c_optimal']:.3f}")
        print(f"        Wing Loading = {best_params['wing_loading_optimal']:.0f} N/m²")
        print(f"        Fuel Weight = {best_params['fuel_weight_N']:.0f} N ({best_params['fuel_fraction_optimal']:.1%} of W_TO)")
        
        # Calculate complete wing geometry with optimal parameters
        A_w_opt = best_params['A_w_optimal']
        S_w_opt = best_params['S_w_optimal']
        b_w_opt = math.sqrt(A_w_opt * S_w_opt)
        Lambda_025c_opt = np.deg2rad(best_params['sweep_deg_optimal'])
        
        # Add complete geometry to results using existing functions
        taper_ratio_opt = psw.calculate_taper_ratio(Lambda_025c_opt)
        c_root_opt, c_tip_opt = psw.calculate_chord_lengths(S_w_opt, b_w_opt, taper_ratio_opt)
        MAC_opt, y_LEMAC_opt = psw.calculate_MAC_and_y_LEMAC(c_root_opt, c_tip_opt, b_w_opt)
        Lambda_LE_opt = psw.calculate_sweep_angle_LE(Lambda_025c_opt, c_root_opt, b_w_opt, taper_ratio_opt)
        Lambda_05c_opt = psw.calculate_sweep_angle_x_c(Lambda_LE_opt, c_root_opt, b_w_opt, 0.5, taper_ratio_opt)
        dihedral_opt = psw.calculate_dihedral_angle_rad(Lambda_025c_opt)
        
        # Update best_params with complete geometry
        best_params.update({ 
            'b_w_optimal': b_w_opt,
            'Lambda_025c_optimal': Lambda_025c_opt,
            'Lambda_LE_optimal': Lambda_LE_opt,
            'Lambda_05c_optimal': Lambda_05c_opt,
            'taper_ratio_optimal': taper_ratio_opt,
            'root_chord_optimal': c_root_opt,
            'tip_chord_optimal': c_tip_opt,
            'MAC_optimal': MAC_opt,
            'y_LEMAC_optimal': y_LEMAC_opt,
            'dihedral_optimal': dihedral_opt
        })
        
    else:
        print(f"    No feasible solution found")
        best_params = {}
    
    return best_params


if __name__ == "__main__":
    # Test the fuel burn optimization
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    
    print("Testing Wing Optimization for Fuel Burn...")
    results = optimize_wing_for_fuel_burn(params)
    
    print(f"Failed configurations sweep angles: {results.get('failed_configurations', [])}")
    print("\n--- Fuel Burn Optimization Results ---")
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")