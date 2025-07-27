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
#from design_variables import DesignParameters
import class1.preliminary_sizing.prelim_sizing_wing as psw
from class2.improved_drag import run_improved_drag_estimations
from class1.initial_weight_estimations import (
    calculate_L_D_cruise_jet, 
    calculate_cruise_fuel_fraction_jet,
    get_statistical_fuel_fractions
)
from utils.unit_conversions import *
from class2.updater import update_parameters_from_class_ii
from class2.main_class_II import perform_class_II_analysis
#try:
import delta_method_classII as dm
#DELTA_METHOD_AVAILABLE = True
#except ImportError:
  #  print("Warning: Delta method not available")
   # DELTA_METHOD_AVAILABLE = False

# Constants from initial_weight_estimations.py
G = 9.80665  # Gravity constant in m/s^2


def calculate_fuel_burn_penalty(A_w: float, S_w: float, sweep_deg: float, t_c: float, 
                               params, W_TO_baseline: float) -> float:
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
    if not isinstance(params, DesignParameters):
        raise TypeError("params must be an instance of DesignParameters")
    
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
        
        #print(f"Original wing parameters: {original_values}") # Works correctly now
        # Calculate current wing weight (to subtract from baseline W_TO), before updating params with trial values
        from class2.component_weights import wing_weight_N
        #print("     Calculating current wing weight before trial parameters...")
        #print(f"WTO_baseline: {params.weight.W_TO:.2f} N")
        W_wing_current = wing_weight_N(params)

        #print(f"     Current wing weight: {W_wing_current:.2f} N")
        # Update params with trial wing parameters
        params.wing.A_w_actual = A_w
        params.wing.A_w_target = A_w  # Keep both consistent        
        params.wing.S_w = S_w
        params.wing.S_ref = S_w  # Reference area for drag calculations
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
        Lambda_05c = psw.calculate_sweep_angle_x_c(params.wing.Lambda_0_w, params.wing.root_chord, params.wing.b_w, 0.5, params.wing.lambda_w)
        params.wing.Lambda_05_w = Lambda_05c
        
        # Calculate new wing weight with trial parameters
        #print(f"     Calculating wing weight with trial parameters: A_w={A_w:.2f}, S_w={S_w:.2f} m², sweep={sweep_deg:.1f}°, t/c={t_c:.4f}")
        W_wing_trial = wing_weight_N(params)
        # print(f"     Trial wing weight: {W_wing_trial:.2f} N, with W_TO_baseline = {W_TO_baseline:.2f} N")
        # Adjust W_TO: remove current wing, add trial wing
        W_TO_adjusted = W_TO_baseline - W_wing_current + W_wing_trial
        W_TO_adjusted_no_fuel = W_TO_adjusted - params.weight.W_F  # Adjust for fuel weight
        #print(f"Difference in W_TO due to wing weight: {W_wing_trial - W_wing_current:.2f} N")
        params.weight.W_TO = W_TO_adjusted
        
        # Step 1: Calculate CD0 using improved_drag with trial parameters
        drag_results = run_improved_drag_estimations(params)
        CD0 = drag_results.get('CD0')  # Default if calculation fails
        # Step 2: Calculate L/D using existing function from initial_weight_estimations.py
        # Assume reasonable Oswald efficiency for modern wing
        e_oswald = 0.9 # Typical value for clean wing # for winglets TODO Torenbeek said that Induced drag 
        #is reduced by 15% with winglets, so thought we could use 1.15 factor here. Not sure
        A_w_winglets = params.wing.A_w_actual * 1.15  # Adjusted aspect ratio with winglets
        L_D_cruise = calculate_L_D_cruise_jet(CD0, A_w_winglets, e_oswald)
        
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
        
        M_ff_nominal = M_ff_total  # Store used fuel fraction for debugging
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
        L_D_loiter = calculate_L_D_loiter(CD0, A_w_winglets, e_oswald)
        from class1.initial_weight_estimations import calculate_loiter_fuel_fraction_jet
        M_loiter = calculate_loiter_fuel_fraction_jet(
            params.loiter_time, L_D_loiter, c_j_kg_Ns
        )
        M_ff_total *= M_loiter
        
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M10_descent2_reserve")
        M_ff_total *= get_statistical_fuel_fractions(aircraft_type, "M11_land_taxi_shutdown")
        
        M_ff_nominal *= get_statistical_fuel_fractions(aircraft_type, "M11_land_taxi_shutdown")

        #print(f"     Total fuel fraction M_ff_total: {M_ff_total:.6f} (includes all mission segments)")
        # Step 5: Calculate total fuel weight
        # From initial_weight_estimations.py: W_F_total = (1 - M_ff_total) * W_TO
        W_F_total_N = (1.0 - M_ff_total) * W_TO_adjusted
        W_F_used_N = (1.0 - M_ff_nominal) * W_TO_adjusted
        params.weight.M_ff = M_ff_total  # Update params with total fuel weight
        params.weight.M_ff_nominal = M_ff_nominal  # Store nominal fuel fraction for debugging
        #print(f"     Total fuel weight W_F_total: {W_F_total_N:.2f} N (from W_TO_adjusted = {W_TO_adjusted:.2f} N)")
        # Updated W_TO after fuel burn calculation
        W_TO_adjusted2 = W_TO_adjusted_no_fuel + W_F_total_N
        #print(f"     Updated W_TO after fuel burn: {W_TO_adjusted2:.2f} N")
        W_S_adjusted = W_TO_adjusted2 / params.wing.S_w  # Update wing loading
        # print(f"     Updated W_TO after fuel burn: {W_TO_adjusted2:.2f} N, W/S = {W_S_adjusted:.2f} N/m²")
        # Restore wing parameters
        wing_params = ['A_w_actual', 'A_w_target', 'S_w', 'b_w', 'Lambda_025c_w', 
                    'Lambda_05_w', 'Lambda_0_w', 't_c_w_r', 't_c_w_max', 
                    'lambda_w', 'root_chord', 'tip_chord']
        for param in wing_params:
            if param in original_values:
                setattr(params.wing, param, original_values[param])

        # Restore weight parameters  
        if 'W_TO' in original_values:
            params.weight.W_TO = original_values['W_TO']
        
        # Ensure fuel weight is positive and reasonable
        if W_F_total_N <= 0 or W_F_total_N > W_TO_adjusted * 0.8:
            return 1e6  # High penalty for unrealistic fuel weight
        
        if W_S_adjusted > params.weight.W_S_max:
            #print(f"    ⚠️  Warning: W/S exceeds maximum ({W_S_adjusted:.2f} N/m² > {params.weight.W_S_max:.2f} N/m²)")
            print(f"    ⚠️  Warning: W/S exceeds maximum ({W_S_adjusted:.2f} N/m² > {params.weight.W_S_max:.2f} N/m²), returning high penalty")
            return 1e6
        
        testing_dict = {'W_TO_adjusted': W_TO_adjusted2, 'W_TO_baseline': W_TO_baseline,
                        'Wing Weight Current': W_wing_current,
                        'Wing Weight Trial': W_wing_trial, 'W_S_adjusted': W_S_adjusted,}
        #print(f"    ✅  Fuel burn calculation successful: W_F_total = {W_F_total_N:.2f} N, W_TO_adjusted = {W_TO_adjusted2:.2f} N, W/S = {W_S_adjusted:.2f} N/m²")

        return W_F_total_N, L_D_cruise, L_D_loiter, M_ff_total, M_ff_nominal, CD0, W_S_adjusted, testing_dict
        
    except Exception as e:
        print(f"    ⚠️  Fuel burn calculation failed: {e}")
        
        # Restore original values even if failed
        try:
            # Restore wing parameters
            wing_params = ['A_w_actual', 'A_w_target', 'S_w', 'b_w', 'Lambda_025c_w', 
                        'Lambda_05_w', 'Lambda_0_w', 't_c_w_r', 't_c_w_max', 
                        'lambda_w', 'root_chord', 'tip_chord']
            for param in wing_params:
                if param in original_values:
                    setattr(params.wing, param, original_values[param])

            # Restore weight parameters  
            if 'W_TO' in original_values:
                params.weight.W_TO = original_values['W_TO']
        except:
            pass
        print("    ⚠️  Returning high penalty due to calculation failure.")
        return 1e6


def optimize_wing_for_fuel_burn(params) -> dict:
    """
    Optimize wing planform by minimizing fuel burn.
    
    This function finds the wing configuration (A_w, S_w, sweep, t/c) that
    minimizes total mission fuel weight, elegantly capturing all trade-offs.
    
    Parameters:
        params (DesignParameters): Current design parameters
        
    Returns:
        dict: Optimized wing parameters that minimize fuel burn
    """
    from class2.component_weights import wing_weight_N
    from class1.thrust_wing_loading import run_performance_diagram
    print("  - Optimizing wing planform for minimum fuel burn...")
    
    # Use current W_TO as baseline for wing weight adjustment
    W_TO_baseline = params.weight.W_TO
    print(f"    📏 Baseline in Wing Opt W_TO = {W_TO_baseline:.0f} N")
    # Calculate baseline L/D for fuel fraction estimation
    baseline_drag = run_improved_drag_estimations(params)
    baseline_CD0 = baseline_drag.get('CD0')
    print(f"    📊 Baseline CD0 = {baseline_CD0:.6f} (from improved_drag)")
    baseline_A_w = params.wing.A_w_target
    e_oswald = 0.9   # Typical Oswald efficiency for clean wing with winglets
    # Typical value for clean wing # for winglets TODO Torenbeek said that Induced drag 
    #is reduced by 15% with winglets, so thought we could use 1.15 factor here. Not sure
    A_w_winglets_baseline = baseline_A_w * 1.15  # Adjusted aspect ratio with winglets
    baseline_L_D = calculate_L_D_cruise_jet(baseline_CD0, A_w_winglets_baseline, e_oswald)
    
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
    A_w_range = np.linspace(11, 12,2)           # Aspect ratio
    S_w_range = np.linspace(5,20 , 40)          # Wing area (m²)  
    sweep_deg_range = np.linspace(5, 40, 10)    # Sweep angle (deg)
    
    # Initialize best solution tracking
    best_fuel_weight = float('inf')
    best_params = {}
    
    total_evaluations = 0
    successful_evaluations = 0
    #print(f"    🔍 Evaluating {len(A_w_range) * len(S_w_range) * len(sweep_deg_range)} design points...")
    #class_ii_results = perform_class_II_analysis(params, initial_W_TO_guess=params.weight.W_TO)  # Run Class II analysis to update params
    #update_parameters_from_class_ii(params, class_ii_results)  # Update params with Class II results
    W_wing_baseline_start = wing_weight_N(params)
    # Grid search optimization
    for A_w in A_w_range:
        params.wing.A_w_target = A_w  # Update target aspect ratio
        for S_w in S_w_range:
            params.wing.S_w = S_w  # Update wing area
            params.wing.S_ref = S_w 
            # Check wing loading constraint first (quick elimination)

            for sweep_deg in sweep_deg_range:
                params.wing.Lambda_025c_w = np.deg2rad(sweep_deg)
                
                W_TO_baseline = params.weight.W_TO  # Use baseline W_TO for wing weight calculation
                W_wing_trial = wing_weight_N(params)  # Current wing weight with baseline parameters
                W_TO_baseline = W_TO_baseline - W_wing_baseline_start + W_wing_trial  # Adjust W_TO for trial wing weight
                wing_loading = W_TO_baseline / S_w
                updated_WS_TW = run_performance_diagram(params)

                params.weight.W_S = updated_WS_TW['W_S']  # Update W/S from performance diagram
                params.weight.T_W = updated_WS_TW['T_W']  # Update T/W from performance diagram

                if wing_loading < 1500 or wing_loading > params.weight.W_S:  # N/m² - reasonable bounds
                    continue

                if W_TO_baseline * params.weight.T_W > 9300:
                    #print(f" W_TO_baseline * T_W = {W_TO_baseline * params.weight.T_W:.0f} N, T_W = {params.weight.T_W:.2f} N/N, W_TO_baseline = {W_TO_baseline:.0f} N, ")
                    continue
                #print(f" W_TO_baseline * T_W = {W_TO_baseline * params.weight.T_W:.0f} N, T_W = {params.weight.T_W:.2f} N/N, W_TO_baseline = {W_TO_baseline:.0f} N, ")

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
                C_L_design = 1.1 * 0.5 * (W_S_start_cruise + W_S_end_cruise) / q_cruise # From ADSEE II, TODO, document safety factor.
                #print(f" CL_design = {C_L_design:.3f} (before delta method), ")
                #C_L_design = max(C_L_design, 0.2)  # Ensure C_L_design is not too low
                # print(f" C_L_design (before delta method) = {C_L_design:.3f} ")
                # Correction for sweep, no longer doing it as the delta method takes in airfoil Cl directly, not section Cl, or aifoil Cl
                #C_L_design_corrected = C_L_design / np.cos(np.deg2rad(sweep_deg))**2  
                #print(f"C_L_design = {C_L_design:.3f} (sweep={sweep_deg:.1f}°), CL_design_corrected = {C_L_design_corrected:.3f}")
                t_c = dm.calculate_tc_from_delta_method(
                    target_cruise_mach=params.cruise_mach,
                    aspect_ratio=A_w,
                    sweep_deg=sweep_deg,
                    cl_des=C_L_design
                )
                #print(f" t/c from delta method = {t_c:.3f} (sweep={sweep_deg:.1f}°), ")
                total_evaluations += 1
                #print(f"t/c from delta method = {t_c:.3f} (sweep={sweep_deg:.1f}°), C_L_design = {C_L_design:.3f}")

                # Check t/c ratio
                if t_c < 0.05 or t_c > 0.20:  # Reasonable bounds for UAV wing
                    #print(f"    Skipping configuration: A_w={A_w:.1f}, S_w={S_w:.1f} m², "
                    #      f"sweep={sweep_deg:.1f}°, t/c={t_c:.3f} (out of bounds), C_L_design={C_L_design_corrected:.3f}")
                    continue  # Skip this configuration, move on to next! 
                # Calculate fuel burn penalty for this configuration
                try:
                    # from class1.initial_weight_estimations import (
                    #     calculate_L_D_cruise_jet, 
                    #     calculate_cruise_fuel_fraction_jet,
                    #     get_statistical_fuel_fractions,
                    #     calculate_loiter_fuel_fraction_jet
                    # )
                    # from class1.initial_weight_estimations import calculate_L_D_loiter
                    #print(f"    Evaluating: A_w={A_w:.1f}, S_w={S_w:.1f} m², sweep={sweep_deg:.1f}°, t/c={t_c:.3f}")
                    fuel_weight, L_D_opt, L_D_loit_opt, M_ff_opt, M_ff_nominal, CDO_opt, W_S_opt, test_dict= calculate_fuel_burn_penalty(
                        A_w, S_w, sweep_deg, t_c, params, W_TO_baseline
                    )
                    successful_evaluations += 1
                    #print(f"   Successful evaluation: A_w={A_w:.1f}, S_w={S_w:.1f} m², ")
                    if fuel_weight < best_fuel_weight and W_S_opt < params.weight.W_S_max and W_S_opt > 3000:
                        winner_dict = test_dict.copy()  # Copy the test dictionary for the winning configuration
                        #print(f"CD0_opt = {CDO_opt:.6f}, L/D_opt = {L_D_opt:.2f}, M_ff_opt = {M_ff_opt:.4f}")
                        # L_D_loiter = calculate_L_D_loiter(
                        #     baseline_CD0,  A_w * 1.15, e_oswald)

                        # M_ff_opt = get_statistical_fuel_fractions(
                        #     aircraft_type, "M1_eng_start_warmup"
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M2_taxi_out"
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M3_take_off"
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M4_climb1"
                        # ) * baseline_cruise_fuel_fraction
                        # M_ff_opt *= get_statistical_fuel_fractions(
                        #     aircraft_type, "M6_descent1"
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M7_climb2_reserve"
                        # ) * calculate_cruise_fuel_fraction_jet(
                        #     params.diversion_distance, V_cruise_ms, L_D_opt, c_j_kg_Ns
                        # ) * calculate_loiter_fuel_fraction_jet(
                        #     params.loiter_time, L_D_loiter, c_j_kg_Ns
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M10_descent2_reserve"
                        # ) * get_statistical_fuel_fractions(
                        #     aircraft_type, "M11_land_taxi_shutdown"
                        # )
                        best_fuel_weight = fuel_weight
                        best_params = {
                            'A_w_optimal': A_w,
                            'S_w_optimal': S_w,
                            'sweep_deg_optimal': sweep_deg,
                            't_c_optimal': t_c,
                            'fuel_weight_N': fuel_weight,
                            'wing_loading_optimal': W_S_opt,
                            'fuel_fraction_optimal': fuel_weight / W_TO_baseline,
                            'C_L_design_optimal': C_L_design,
                            'L_D_optimal': L_D_opt,
                            'L_D_loit_optimal': L_D_loit_opt,
                            'M_ff_optimal': M_ff_opt,
                            'M_ff_nominal': M_ff_nominal,
                            
                        }
                        
                        #print(f"    New best: A_w={A_w:.1f}, S_w={S_w:.1f}m², sweep={sweep_deg:.1f}°")
                        #print(f"    Fuel weight: {fuel_weight:.0f} N ({fuel_weight/W_TO_baseline:.1%} of W_TO)")
                        
                except Exception as e:
                    print(f"    ⚠️  Evaluation failed for A_w={A_w:.2f}, S_w={S_w:.2f} m², sweep={sweep_deg:.1f}°: {e}")
                    # Skip failed evaluations
                    continue
    #print(winner_dict)
                
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
        W_s_optimal = best_params['wing_loading_optimal']
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
            'dihedral_optimal': dihedral_opt,
            'W_S_optimal': W_s_optimal,
        })
        
    else:
        print(f"    No feasible solution found")
        best_params = {}
    
    return best_params


if __name__ == "__main__":
    from design_variables import DesignParameters
    from class1.main_class_I import perform_class_I_analysis
    from class2.updater import update_parameters_from_class_i
    # Test the fuel burn optimization
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    class_i_results = perform_class_I_analysis(params)
    update_parameters_from_class_i(params, class_i_results)  # Update params with Class I results
    print(f" W_TO from Class I: {params.weight.W_TO:.0f} N")
    print("Testing Wing Optimization for Fuel Burn...")
    results = optimize_wing_for_fuel_burn(params)
    
    print(f"Failed configurations sweep angles: {results.get('failed_configurations', [])}")
    print("\n--- Fuel Burn Optimization Results ---")
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")