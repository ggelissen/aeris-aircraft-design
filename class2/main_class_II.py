import math
import yaml
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * # Assuming this contains necessary conversion functions

def class_II_weight_estimation(params: DesignParameters,
                               initial_W_TO_N_guess: float,
                               max_iterations: int = 100,
                               tolerance: float = 0.001): # Reduced tolerance for potentially faster convergence if appropriate
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
    params.weight.WTO = W_TO_N_current # Ensure the params object starts with the initial guess

    print(f"Starting Class II Weight Estimation with initial WTO: {W_TO_N_current:.2f} N")

    for i in range(max_iterations):
        # Update component weights that depend on WTO
        # Make sure your component_weights functions use params.weight.WTO
        # For example, wing_weight_N already takes WTO, but it's passed params.weight.WTO
        # which is updated below.

        # It's crucial that component weight functions like wing_weight_N
        # use the most current params.weight.WTO.
        # If they are instantiated or calculate values only once using an old WTO,
        # the iteration won't work correctly.

        # Recalculate empty weight based on the current W_TO_N_current (params.weight.WTO)
        W_empty_N_calculated = (
            cw.fuselage_weight_lb(params) +       # Ensure these functions use the updated params.weight.WTO
            cw.landing_gear_weight_lb(params) +   # if they are dependent on it.
            cw.wing_weight_N(params.weight.WTO, params.wing) + # This correctly uses the updated WTO
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
    params.weight.WTO = W_TO_N_current # Store the last calculated value
    return W_TO_N_current, False, max_iterations