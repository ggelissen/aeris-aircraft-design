import math
import yaml
import os
import sys
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 



def class_II_weight_estimation(params: DesignParameters,
                               initial_W_TO_N_guess: float,
                               max_iterations: int = 100,
                               tolerance: float = 0.005): 

    W_TO_N_current = initial_W_TO_N_guess
    params.weight.W_TO = W_TO_N_current 
    print(f"Starting Class II Weight Estimation with initial WTO: {W_TO_N_current:.2f} N")

    for i in range(max_iterations):
        
        # Recalculate empty weight based on the current W_TO_N_current (params.weight.W_TO)
        W_empty_N_calculated = (
            cw.wing_weight_N(params) +
            cw.landing_gear_weight_N(params) +
            cw.empennage_weight_N(params) +
            cw.propulsion_weight_N(params) +
            cw.fixed_equipment_weight_N(params) +
            cw.fuselage_weight_N(params) 
        )

        W_TO_N_new = (W_empty_N_calculated + params.weight.W_PL) / (params.weight.M_ff) #equation TODO, double check this 

        
        relative_difference = abs(W_TO_N_new - W_TO_N_current) / W_TO_N_new
        print("\n")
        print(f"Iteration {i+1}: W_TO_current = {W_TO_N_current:.2f} N, W_empty_calc = {W_empty_N_calculated:.2f} N, W_TO_new = {W_TO_N_new:.2f} N, Rel_Diff = {relative_difference:.6f}")        
        if relative_difference < tolerance:
            print(f"Class II WTO converged in {i+1} iterations.")
            params.weight.W_TO = W_TO_N_new # Final update to params
            return W_TO_N_new, True, i + 1, W_empty_N_calculated
        
        W_TO_N_current = W_TO_N_new
        params.weight.W_TO = W_TO_N_current # Update WTO in params for the next iteration's component calculations

    print(f"Class II WTO did not converge after {max_iterations} iterations.")
    params.weight.W_TO = W_TO_N_current 
    return W_TO_N_current, False, max_iterations, W_empty_N_calculated

def calculate_cg_longitudinal(params: DesignParameters, W_empty_N_calculated: float):
    """
    Calculates CG locations for various aircraft loading conditions and plots CG excursion.
    """

    # Calculate moments for OEW (Operating Empty Weight)
    moment_wing = cw.wing_weight_N(params) * params.cg.x_cg_wing
    moment_fuselage = cw.fuselage_weight_N(params) * params.cg.x_cg_fuselage
    moment_landing_gear = cw.landing_gear_weight_N(params) * params.cg.x_cg_landing_gear
    moment_empennage = cw.empennage_weight_N(params) * params.cg.x_cg_empennage
    moment_fixed_equipment = cw.fixed_equipment_weight_N(params) * params.cg.x_cg_fixed_equipment
    moment_propulsion = cw.propulsion_weight_N(params) * params.cg.x_cg_propulsion

    W_OE = W_empty_N_calculated # Why is this not calculated on the spot? But taken as input?
    moment_OE = (moment_wing + moment_fuselage + moment_landing_gear +
                 moment_empennage + moment_fixed_equipment + moment_propulsion)
    
    # Payload and fuel
    W_PL = params.weight.W_PL
    W_F = params.weight.W_F

    moment_payload = W_PL * params.cg.x_cg_payload
    moment_fuel = W_F * params.cg.x_cg_fuel

    conditions = {
        'OEW': (W_OE, moment_OE),
        'OEW + Payload': (W_OE + W_PL, moment_OE + moment_payload),
        'OEW + Fuel': (W_OE + W_F, moment_OE + moment_fuel),
        'OEW + Payload + Fuel (W_TO)': (W_OE + W_PL + W_F, moment_OE + moment_payload + moment_fuel),
    }

    cg_positions = {}
    for condition, (weight, moment) in conditions.items():
        cg = moment / weight if weight > 0 else None
        cg_positions[condition] = cg
        print(f"{condition}: CG = {cg:.2f} m, Weight = {weight:.2f} N")

    # Plotting CG Excursion
    plt.figure(figsize=(10, 5))
    labels = list(cg_positions.keys())
    cg_values = [cg_positions[k] for k in labels]
    weights = [conditions[k][0] for k in labels]

    plt.plot(cg_values, weights, marker='o', linestyle='-', color='navy')
    plt.title("CG Excursion Plot")
    plt.xlabel("CG Position from Nose (m)")
    plt.ylabel("Aircraft Weight (N)")
    plt.grid(True)
    for i, txt in enumerate(labels):
        plt.annotate(txt, (cg_values[i], weights[i]), textcoords="offset points", xytext=(0,10), ha='center')
    plt.tight_layout()
    plt.show()

    return cg_positions

def estimate_mac_leading_edge(params: DesignParameters, cg_OEW: float, target_CG_percent_MAC: float):

    x_LE_MAC = cg_OEW - target_CG_percent_MAC * params.wing.mac
    print(f"Estimated MAC Leading Edge location: {x_LE_MAC:.2f} m (to place CG at {target_CG_percent_MAC*100:.0f}% MAC)")
    return x_LE_MAC

if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    final_W_TO, converged, iterations, W_empty_final_N = class_II_weight_estimation(
        params=params,
        initial_W_TO_N_guess=DesignParameters().weight.W_TO,  
        max_iterations=100,
        tolerance=0.005
    )
    if converged:
        print(f"Final Take-Off Weight (W_TO): {final_W_TO:.2f} N after {iterations} iterations.")
    else:
        print(f"Final Take-Off Weight (W_TO): {final_W_TO:.2f} N after {iterations} iterations (not converged).")
    
    # cg_location = calculate_cg_longitudinal(params, W_empty_final_N)
    cg_positions = calculate_cg_longitudinal(params, W_empty_final_N)
    x_LE_MAC = estimate_mac_leading_edge(params, cg_positions['OEW'], target_CG_percent_MAC=0.30)
    print("Calculated CG locations (from nose):")
    for condition, cg in cg_positions.items():
        print(f"{condition}: {cg:.2f} m")


