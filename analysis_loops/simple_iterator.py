import numpy as np
import math as m
import os
import sys
import copy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from analysis_loops.design_evaluator import evaluate_design_point

def run_parameter_sweep():
    results = []
    base_params = DesignParameters()

    # Example: Sweep wing span and aspect ratio
    wing_spans_to_test = [28.0, 30.0, 32.0, 34.0]
    aspect_ratios_to_test = [8.0, 9.0, 10.0]

    print(f"{'Span (m)':<10} {'AR':<5} {'Weight (kg)':<12} {'Range (km)':<12} {'Feasible':<10}")
    print("-" * 50)

    for span in wing_spans_to_test:
        for ar in aspect_ratios_to_test:
            iter_params = copy.deepcopy(base_params)
            iter_params.wing_span_m = span
            iter_params.wing_aspect_ratio = ar
            # Potentially set other DVs

            evaluated_params = evaluate_design_point(iter_params)
            results.append(evaluated_params)

            print(f"{evaluated_params.wing_span_m:<10.1f} "
                  f"{evaluated_params.wing_aspect_ratio:<5.1f} "
                  f"{evaluated_params.total_aircraft_weight_kg:<12.2f} "
                  f"{evaluated_params.range_km:<12.2f} "
                  f"{str(evaluated_params.is_feasible):<10}")
    return results