import numpy as np
from scipy.optimize import minimize
import copy
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from analysis_loops.design_evaluator import evaluate_design_point

# Store the history of evaluations if needed for plotting or debugging
optimization_history = []

def objective_function(x: np.ndarray, base_params_template: DesignParameters) -> float:
    """
    Wrapper to be used for the design evaluation.

    Parameters:
    x (np.array): Array of design variables controlled by the optimizer.
                    Order must be consistent!
    base_params_template (DesignParameters): A template DesignParameters object.

    Returns:
        float: The objective value to be minimized.
    """
    global optimization_history
    current_params = copy.deepcopy(base_params_template)

    # Map x to DesignParameters
    # This mapping is crucial and depends on what you want to optimize.
    current_params.wing_span_m = x[0]
    current_params.wing_aspect_ratio = x[1]
    # current_params.engine_thrust_max_kN = x[2] # if optimizing thrust

    # Evaluate the design
    evaluated_params = evaluate_design_point(current_params)
    optimization_history.append(evaluated_params) # Store for later analysis

    # Define Objective Function
    # Example: Minimize Total Aircraft Weight
    objective = evaluated_params.total_aircraft_weight_kg

    # Handle Constraints
    # SciPy's SLSQP can handle constraints directly.
    # Alternatively, apply penalties to the objective if constraints are violated.
    # For this example, let's use a penalty approach.
    penalty = 0.0

    # Constraint 1: Lift >= Weight
    if evaluated_params.lift_N < evaluated_params.total_aircraft_weight_N:
        penalty += (evaluated_params.total_aircraft_weight_N - evaluated_params.lift_N) * 1000 # Large penalty factor
        # print(f"Opt Penalty: Lift < Weight. Penalty: {penalty}")

    # Constraint 2: Minimum Range
    min_required_range_km = current_params.cruise_range / 1000
    if evaluated_params.range_km < min_required_range_km:
        penalty += (min_required_range_km - evaluated_params.range_km) * 100 # Penalty for unmet range
        # print(f"Opt Penalty: Range < Target. Penalty: {penalty}")

    # Print current iteration for monitoring (optional)
    print(f"Iter DVs: Span={x[0]:.2f}, AR={x[1]:.2f} -> Obj={objective:.2f}, Pen={penalty:.2f}, Total={(objective + penalty):.2f} "
          f"| Wght={evaluated_params.total_aircraft_weight_kg:.2f}, Rng={evaluated_params.range_km:.2f}, L={evaluated_params.lift_N:.0f}, D={evaluated_params.drag_N:.0f}")

    return objective + penalty


def run_optimization():
    global optimization_history
    optimization_history = [] # Clear history for a new run

    initial_params = DesignParameters()

    # Define Initial Guess (x0) and Bounds for DVs
    # Order must match the `objective_function` mapping
    # x = [wing_span_m, wing_aspect_ratio]
    x0 = np.array([
        initial_params.wing_span_m,
        initial_params.wing_aspect_ratio
        # initial_params.engine_thrust_max_kN # if optimizing thrust
    ])

    bounds = [
        (25.0, 40.0),  # Bounds for wing_span_m
        (7.0, 12.0)    # Bounds for wing_aspect_ratio
        # (100.0, 200.0) # Bounds for engine_thrust_max_kN
    ]

    print(f"Starting optimization with initial guess: Span={x0[0]}, AR={x0[1]}")

    # SciPy's minimize function
    result = minimize(
        objective_function,
        x0,
        args=(initial_params,), # Extra arguments passed to objective_function
        method='SLSQP', # Sequential Least Squares Programming, handles bounds and constraints
        bounds=bounds,
        options={'disp': True, 'maxiter': 50, 'ftol': 1e-7} # disp True shows convergence messages
    )

    print("\nOptimization Finished:")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Optimal Design Variables (x): {result.x}")
    print(f"Optimal Objective Value: {result.fun}")

    # Retrieve the parameters of the best design found
    if result.success and optimization_history:
        # The 'result.x' gives the DVs, now re-evaluate to get the full DesignParameters object
        # for the optimal point without penalties (if any were applied for internal optimizer steps)
        optimal_values = result.x
        final_params = copy.deepcopy(initial_params)
        final_params.wing_span_m = optimal_values[0]
        final_params.wing_aspect_ratio = optimal_values[1]
        # final_params.engine_thrust_max_kN = optimal_values[2]

        final_evaluated_params = evaluate_design_point(final_params)
        print("\nFinal Evaluated Optimal Design:")
        print(final_evaluated_params)

    return result, optimization_history