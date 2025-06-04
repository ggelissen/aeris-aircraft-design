# your_aircraft_project/run_openmdao_optimizer_v2.py
import sys
import os
import openmdao.api as om
import math

# Ensure the MDAO framework can be imported
# This assumes 'run_openmdao_optimizer_v2.py' is in 'your_aircraft_project/'
# and 'mdao_framework' is a subdirectory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mdao_framework.aircraft_model_v2 import AircraftModel
from design_variables import DesignParameters # To get initial values from YAML or defaults

# Conversion constant
N_PER_KG = 9.80665

def main_optimization_v2():
    # --- 0. Load Initial Parameters (from YAML via DesignParameters or use defaults) ---
    # Create a dummy YAML for testing if not present
    config_file = 'design_config.yaml' 
    if not os.path.exists(config_file):
        print(f"Warning: '{config_file}' not found. Using default DesignParameters.")
        initial_design_params = DesignParameters() # Uses class defaults
        # Manually set some key top-level requirements if not using YAML for this run:
        initial_design_params.range = 3500 * 1000 # m
        initial_design_params.cruise_mach = 0.78
        initial_design_params.cruise_altitude = 11000 # m
        initial_design_params.weight.W_PL = 6000 * N_PER_KG # N
        initial_design_params.engine.N_engines = 2
        initial_design_params.performance.e_oswald = 0.80
        initial_design_params.performance.CL_max_TO = 1.9
        initial_design_params.performance.CL_max_LAND = 2.2
        initial_design_params.engine.cruise_tsfc_kg_Ns = 1.6e-5
        initial_design_params.max_load_factor = 3.5
        initial_design_params.take_off_distance = 1800.0 # Target for constraint
        initial_design_params.stall_speed_land = 65.0 * 0.514444 # Target 65 knots in m/s
    else:
        initial_design_params = DesignParameters(initial_config_path=config_file)
        print(f"Loaded initial parameters from '{config_file}'")


    # --- 1. Build the Model (Problem Setup) ---
    prob = om.Problem()

    prob.model = AircraftModel(
        target_range_m=initial_design_params.range,
        cruise_mach_target=initial_design_params.cruise_mach,
        cruise_altitude_m=initial_design_params.cruise_altitude,
        max_payload_N=initial_design_params.weight.W_PL,
        crew_weight_N=initial_design_params.weight.W_crew,
        num_engines=initial_design_params.engine.N_engines,
        oswald_efficiency=initial_design_params.performance.e_oswald,
        CL_max_clean=initial_design_params.performance.CL_max_clean,
        CL_max_TO=initial_design_params.performance.CL_max_TO,
        CL_max_LAND=initial_design_params.performance.CL_max_LAND,
        engine_cruise_tsfc_kg_Ns=initial_design_params.engine.cruise_tsfc_kg_Ns,
        max_load_factor=initial_design_params.max_load_factor
        # Add other options if defined in AircraftModel.initialize()
    )

    # --- 2. Setup the Optimizer (Driver) ---
    prob.driver = om.ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'SLSQP'
    prob.driver.options['tol'] = 1e-6
    prob.driver.options['disp'] = True
    prob.driver.options['maxiter'] = 100 # Increased iterations
    # prob.driver.options['debug_print'] = ['desvars', 'nl_cons', 'objs']


    # --- Recorder (Optional) ---
    recorder = om.SqliteRecorder("optimization_history_v2.sql")
    prob.driver.add_recorder(recorder)
    prob.driver.recording_options['includes'] = [
        'weight_W_S', 'wing_A_w', 'weight_T_W', 'wing_Lambda_025c_w', 'fuselage_l_f', # DVs
        'calculated_W_TO', # Objective
        'range_constraint', 'take_off_distance_calc_m', 'stall_speed_LAND_mps', # Constraints
        'lift_equals_weight_constraint', 'thrust_equals_drag_constraint' 
    ]
    prob.driver.recording_options['record_derivatives'] = False


    # --- 3. Define Design Variables ---
    # Initial values from the DesignParameters instance
    prob.model.add_design_var('weight_W_S', lower=2000.0, upper=6000.0, 
                              ref=initial_design_params.weight.W_S, units='N/m**2')
    prob.model.add_design_var('wing_A_w', lower=7.0, upper=14.0, 
                              ref=initial_design_params.wing.A_w)
    prob.model.add_design_var('weight_T_W', lower=0.20, upper=0.50, 
                              ref=initial_design_params.weight.T_W)
    prob.model.add_design_var('wing_Lambda_025c_w', lower=math.radians(15.0), upper=math.radians(35.0), 
                              ref=initial_design_params.wing.Lambda_025c_w, units='rad')
    prob.model.add_design_var('fuselage_l_f', lower=20.0, upper=40.0, 
                              ref=initial_design_params.fuselage.l_f, units='m')
    
    # Add other DVs as needed, e.g., taper ratio, empennage sizing parameters
    prob.model.add_design_var('wing_lambda_w', lower=0.2, upper=0.6, ref=initial_design_params.wing.lambda_w)
    prob.model.add_design_var('emp_V_h', lower=0.5, upper=1.2, ref=initial_design_params.empennage.V_h)
    prob.model.add_design_var('emp_V_v', lower=0.04, upper=0.10, ref=initial_design_params.empennage.V_v)


    # --- 4. Define Objective ---
    prob.model.add_objective('calculated_W_TO', scaler=1e-5) # Minimize MTOW

    # --- 5. Define Constraints ---
    # Range constraint: achieved_range >= target_range.
    # 'range_constraint' from MissionPerformance is target - achieved, so it should be <= 0.
    prob.model.add_constraint('range_constraint', upper=0.0, scaler=1e-6) 

    # Take-off distance constraint
    if initial_design_params.take_off_distance:
        prob.model.add_constraint('take_off_distance_calc_m', upper=initial_design_params.take_off_distance, scaler=1e-3)
    
    # Stall speed constraint (landing)
    if initial_design_params.stall_speed_land:
        prob.model.add_constraint('stall_speed_LAND_mps', upper=initial_design_params.stall_speed_land, scaler=1e-1)

    # Cruise performance constraints (L=W, T=D)
    # These should be close to zero for steady cruise.
    prob.model.add_constraint('lift_equals_weight_constraint', lower=-1000.0, upper=1000.0, scaler=1e-4) # Allow some tolerance
    prob.model.add_constraint('thrust_equals_drag_constraint', lower=-1000.0, upper=5000.0, scaler=1e-4) # Allow some margin for T_avail > T_req

    # Optional: Constraint on fuel capacity vs fuel used
    # prob.model.add_constraint('missionperf.weight_W_F_used_mission', upper='missionperf.weight_W_F_capacity_input')
    # This requires W_F_capacity to be an input to MissionPerformance. For now, W_TO is sized.

    # --- 6. Finalize Problem Setup ---
    prob.setup(check=True, mode='fwd') # 'fwd' or 'rev' for derivatives. 'auto' is default.

    # --- 7. Set Initial Values for DVs and other important IndepVarComp-like inputs ---
    # These are inputs to the model that are not DVs but need initial values if not set by options.
    # The DVs themselves get their initial values from the 'ref' in add_design_var,
    # but it's good practice to explicitly set them using prob.set_val if 'ref' is not used or for clarity.
    
    prob.set_val('weight_W_S', initial_design_params.weight.W_S, units='N/m**2')
    prob.set_val('wing_A_w', initial_design_params.wing.A_w)
    prob.set_val('weight_T_W', initial_design_params.weight.T_W)
    prob.set_val('wing_Lambda_025c_w', initial_design_params.wing.Lambda_025c_w, units='rad')
    prob.set_val('fuselage_l_f', initial_design_params.fuselage.l_f, units='m')
    prob.set_val('wing_lambda_w', initial_design_params.wing.lambda_w)
    prob.set_val('emp_V_h', initial_design_params.empennage.V_h)
    prob.set_val('emp_V_v', initial_design_params.empennage.V_v)

    # Set initial W_TO (important for the Newton solver to start)
    # The value from DesignParameters is a good starting point.
    prob.set_val('weight_W_TO', initial_design_params.weight.W_TO, units='N')

    # Set other fixed inputs that might not be DVs or options but are inputs to components
    # (Many are now handled by options in AircraftModel)
    prob.set_val('propsys.engine_diameter_per', initial_design_params.engine.engine_diameter_per, units='m')
    prob.set_val('propsys.engine_length_per', initial_design_params.engine.engine_length_per, units='m')
    prob.set_val('aerocoeffs.wing_t_c_w_r', initial_design_params.wing.t_c_w_r)
    # ... any other top-level inputs to components ...


    # --- Optional: View N2 diagram ---
    # om.n2(prob, outfile="aircraft_model_v2_n2.html", show_browser=False)
    # print("N2 diagram saved to aircraft_model_v2_n2.html")

    # --- Run Model Once Before Optimization (for debugging) ---
    print("\n--- Running model once before optimization ---")
    prob.run_model()
    print_results("Initial Design Point", prob, initial_design_params)


    # --- 8. Run the Optimization ---
    print("\n--- Starting Optimization ---")
    failure = prob.run_driver()
    if failure:
        print("Optimization failed.")
    else:
        print("Optimization successful.")
    print("---------------------------\n")

    # --- 9. Print Results ---
    print_results("Optimal Design Point", prob, initial_design_params)
    
    # --- 10. Cleanup ---
    prob.cleanup()
    print(f"\nOptimization history saved to: optimization_history_v2.sql")
    print("Use 'openmdao view_recorder optimization_history_v2.sql' to view history.")


def print_results(title, prob_instance, initial_params_ref):
    print(f"\n--- {title} ---")
    print(f"  Objective (Calculated W_TO): {prob_instance.get_val('calculated_W_TO', units='N'):.2f} N "
          f"({prob_instance.get_val('calculated_W_TO')/N_PER_KG:.2f} kg)")

    print("\n  Design Variables:")
    print(f"    Wing Loading (W/S): {prob_instance.get_val('weight_W_S', units='N/m**2'):.2f} N/m^2")
    print(f"    Wing Aspect Ratio (A_w): {prob_instance.get_val('wing_A_w'):.3f}")
    print(f"    Thrust-to-Weight (T/W): {prob_instance.get_val('weight_T_W'):.4f}")
    print(f"    Wing Sweep (Lambda_025c): {math.degrees(prob_instance.get_val('wing_Lambda_025c_w', units='rad')):.2f} deg")
    print(f"    Fuselage Length (l_f): {prob_instance.get_val('fuselage_l_f', units='m'):.2f} m")
    print(f"    Wing Taper (lambda_w): {prob_instance.get_val('wing_lambda_w'):.3f}")
    print(f"    HTP Volume (V_h): {prob_instance.get_val('emp_V_h'):.3f}")
    print(f"    VTP Volume (V_v): {prob_instance.get_val('emp_V_v'):.4f}")


    print("\n  Constraints:")
    print(f"    Range Constraint (Target - Achieved <= 0): {prob_instance.get_val('range_constraint', units='m'):.2f} m "
          f"(Achieved Range: {prob_instance.get_val('achieved_range_m')/1000:.1f} km vs Target: {initial_params_ref.range/1000:.1f} km)")
    
    tod_target = initial_params_ref.take_off_distance if initial_params_ref.take_off_distance else "N/A"
    print(f"    Take-off Distance (<= {tod_target} m): {prob_instance.get_val('take_off_distance_calc_m', units='m'):.2f} m")
    
    ssl_target_kn = (initial_params_ref.stall_speed_land / 0.514444) if initial_params_ref.stall_speed_land else "N/A"
    ssl_target_mps = initial_params_ref.stall_speed_land if initial_params_ref.stall_speed_land else "N/A"
    print(f"    Stall Speed Land (<= {ssl_target_mps:.1f} m/s or {ssl_target_kn:.1f} kts): "
          f"{prob_instance.get_val('stall_speed_LAND_mps', units='m/s'):.2f} m/s "
          f"({prob_instance.get_val('stall_speed_LAND_mps')/0.514444:.1f} kts)")
    
    print(f"    Cruise L-W (L-W ~ 0): {prob_instance.get_val('lift_equals_weight_constraint', units='N'):.2f} N")
    print(f"    Cruise T-D (T_avail-D_req >= 0): {prob_instance.get_val('thrust_equals_drag_constraint', units='N'):.2f} N")

    print("\n  Other Key Metrics:")
    print(f"    Wing Area (S_w): {prob_instance.get_val('winggeom.wing_S_w', units='m**2'):.2f} m^2")
    print(f"    Wing Span (b_w): {prob_instance.get_val('winggeom.wing_b_w', units='m'):.2f} m")
    print(f"    Cruise L/D: {prob_instance.get_val('cruise_L_D'):.2f}")
    print(f"    Cruise CL: {prob_instance.get_val('cruise_CL'):.3f}")
    print(f"    Calculated OEW: {prob_instance.get_val('weightest.weight_W_OE_calc', units='N')/N_PER_KG:.2f} kg")
    print(f"    Mission Fuel Used: {prob_instance.get_val('missionperf.weight_W_F_used_mission', units='N')/N_PER_KG:.2f} kg")
    print(f"    Reserve Fuel: {prob_instance.get_val('missionperf.weight_W_F_reserve', units='N')/N_PER_KG:.2f} kg")


if __name__ == "__main__":
    main_optimization_v2()
