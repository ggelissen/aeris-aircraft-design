

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from class1.initial_weight_estimations import run_initial_weight_estimations
from class1.thrust_wing_loading import run_performance_diagram
from class1.preliminary_sizing.prelim_sizing_wing import run_preliminary_sizing_wing
from class1.preliminary_sizing.prelim_sizing_fus import run_preliminary_sizing_fuselage

def perform_class_I_analysis(params: DesignParameters) -> DesignParameters:
    """
    Perform Class I analysis on the design parameters.
    
    Parameters:
        params (DesignParameters): An instance of DesignParameters containing the design variables.
    
    Returns:
        DesignParameters: The updated design parameters object after Class I analysis.
    """
    results_weights = run_initial_weight_estimations(params)
    results_thrust_area = run_performance_diagram(params)
    results_wing_sizing = run_preliminary_sizing_wing(params)
    results_fuselage_sizing = run_preliminary_sizing_fuselage(params)

    return results_weights | results_thrust_area | results_wing_sizing | results_fuselage_sizing


if __name__ == "__main__":

    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    analysis_results = perform_class_I_analysis(params)
    
    for key, value in analysis_results.items():
        print(f"{key}: {round(value, 3) if isinstance(value, float) else value}")