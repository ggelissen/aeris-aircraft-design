import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.design_variables import DesignParameters
from class1.initial_weight_estimations import run_initial_weight_estimations
from class1.thrust_wing_loading import run_performance_diagram
from class1.prelim_sizing_wing import run_preliminary_sizing_wing
from class1.prelim_sizing_fus import run_preliminary_sizing_fuselage
from class2.updater import update_parameters_from_class_i
def perform_class_I_analysis(params: DesignParameters) -> dict:
    """
    Perform Class I analysis on the design parameters.
    
    This function orchestrates the initial design phase including:
    - Initial weight estimations
    - Performance constraint analysis (T/W vs W/S)
    - Wing preliminary sizing
    - Fuselage preliminary sizing (placeholder)
    
    Parameters:
        params (DesignParameters): An instance of DesignParameters containing the design variables.
    
    Returns:
        dict: The combined results from all Class I analysis modules.
    """
    print("\n" + "="*60)
    print("           RUNNING CLASS I ANALYSIS")
    print("="*60)
    
    # Run individual Class I modules
    print("\n1. Initial Weight Estimations...")
    results_weights = run_initial_weight_estimations(params)
    params = update_parameters_from_class_i(params, results_weights)

    print("\n2. Performance Constraint Analysis (T/W vs W/S)...")
    results_thrust_area = run_performance_diagram(params)
    params = update_parameters_from_class_i(params, results_thrust_area)

    print("\n3. Wing Preliminary Sizing...")
    results_wing_sizing = run_preliminary_sizing_wing(params)
    params = update_parameters_from_class_i(params, results_wing_sizing)

    print("\n4. Fuselage Preliminary Sizing...") # Empty function, and will remain empty, done in class II
    results_fuselage_sizing = run_preliminary_sizing_fuselage(params)
    params = update_parameters_from_class_i(params, results_fuselage_sizing)
    
    # Combine all results
    combined_results = {**results_weights, **results_thrust_area, 
                       **results_wing_sizing, **results_fuselage_sizing}
    
    print(f"\n✅ Class I Analysis Complete. Generated {len(combined_results)} parameters.")
    return combined_results


if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    analysis_results = perform_class_I_analysis(params)
    
    print("\n" + "="*40)
    print("       CLASS I RESULTS SUMMARY")
    print("="*40)
    for key, value in analysis_results.items():
        print(f"{key}: {round(value, 3) if isinstance(value, float) else value}")