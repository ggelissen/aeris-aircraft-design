import math
import yaml
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 
def class_II_weight_estimation(params: DesignParameters,
                               initial_W_TO_N_guess: float,
                               max_iterations: int = 100,
                               tolerance: float = 0.01): 
    """
    Performs Class II weight estimation for a UAV iteratively.

    Args:
        params: DesignParameters object containing all aircraft parameters.
        initial_W_TO_N_guess: Initial guess for the Take-Off Weight in Newtons.
        max_iterations: Maximum number of iterations to attempt convergence.
        tolerance: Convergence tolerance for the relative difference in W_TO.

    Returns:
        A tuple containing:
            - float: Converged Take-Off Weight in Newtons (or last calculated if no convergence).
            - bool: True if converged, False otherwise.
            - int: Number of iterations performed.
    """
    W_TO_N_current = initial_W_TO_N_guess
    params.weight.WTO = W_TO_N_current 
    print(f"Starting Class II Weight Estimation with initial WTO: {W_TO_N_current:.2f} N")

    for i in range(max_iterations):
        
        # Recalculate empty weight based on the current W_TO_N_current (params.weight.WTO)
        W_empty_N_calculated = (
            cw.fuselage_weight_lb(params) +      
            cw.landing_gear_weight_lb(params) +   
            cw.wing_weight_N(params.weight.WTO, params.wing) + 
            cw.empennage_weight_lb(params) +
            cw.propulsion_weight_lb(params) +
            cw.fixed_equipment_weight_lb(params)
        )

        W_TO_N_new = (W_empty_N_calculated + params.weight.W_PL) / (1 - params.weight.M_ff)

        relative_difference = abs(W_TO_N_new - W_TO_N_current) / W_TO_N_new
        print(f"Iteration {i+1}: WTO_current = {W_TO_N_current:.2f} N, W_empty_calc = {W_empty_N_calculated:.2f} N, WTO_new = {W_TO_N_new:.2f} N, Rel_Diff = {relative_difference:.6f}")

        if relative_difference < tolerance:
            print(f"Class II WTO converged in {i+1} iterations.")
            params.weight.WTO = W_TO_N_new # Final update to params
            return W_TO_N_new, True, i + 1
        
        W_TO_N_current = W_TO_N_new
        params.weight.WTO = W_TO_N_current # Update WTO in params for the next iteration's component calculations

    print(f"Class II WTO did not converge after {max_iterations} iterations.")
    params.weight.WTO = W_TO_N_current 
    return W_TO_N_current, False, max_iterations

