import math
import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 

def calculate_undercarriage_loading(W_TO: float, n_mlg: int = 2, n_nlg: int = 1, LCN: int = 40) -> tuple:
    """
    Calculate the undercarriage loading based on the takeoff weight and number of wheels.

    Parameters:
    W_TO (float): Takeoff weight in Newtons.
    n_mlg (int): Number of main landing gear wheels.
    n_nlg (int): Number of nose landing gear wheels.

    Returns:
    tuple: Tire pressure in kPa, static load on nose wheel in N, static load on main wheels in N.
    """

    tire_pressure = (430*math.log(LCN) -680) * 10e3 # in Pa
    tire_pressure_kg_cm2 = tire_pressure / 10  # Convert Pa to kg/cm^2

    static_frac_nlg = 0.08
    static_frac_mlg = 1 - static_frac_nlg

    W_nose = static_frac_nlg * W_TO
    W_main_total = static_frac_mlg * W_TO

    static_load_mlg = W_main_total / n_mlg
    static_load_nlg = W_nose / n_nlg

    # Convert static loads to kg
    static_load_nlg = static_load_nlg / 9.80665  # Convert N to kg
    static_load_mlg = static_load_mlg / 9.80665  # Convert N to kg

    return tire_pressure_kg_cm2, static_load_nlg, static_load_mlg


def estimate_tire_diameter(load_N: float, pressure_Pa: float) -> float:
    """
    Estimate the tire diameter based on the load and pressure.

    Parameters:
    load_N (float): Load on the tire in Newtons.
    pressure_Pa (float): Tire pressure in Pascals.

    Returns:
    float: Estimated tire diameter in meters.
    """

    load_kg = load_N / 9.80665
    pressure_bar = pressure_Pa / 100000  # Convert Pa to bar

    return 0.5* (load_kg / pressure_bar) ** (0.25)


def perform_undercarriage_sizing(params: DesignParameters) -> dict:
    """
    Perform undercarriage sizing based on the design parameters.

    Parameters:
    params (DesignParameters): Design parameters containing undercarriage specifications.

    Returns:
    dict: Undercarriage specifications including tire pressure, static loads, and tire diameters.
    """

    tire_pressure, static_load_nlg, static_load_mlg = calculate_undercarriage_loading(
        W_TO=params.weight.W_TO, 
        n_mlg=params.landing_gear.n_mlg, 
        n_nlg=params.landing_gear.n_nlg, 
        LCN=params.landing_gear.LCN)
    
    nose_diameter_m = estimate_tire_diameter(static_load_nlg, tire_pressure) 
    main_diameter_m = estimate_tire_diameter(static_load_mlg, tire_pressure)

    return {
        'tire_pressure': tire_pressure / 101325,  # Convert to bar
        'F_nlg': static_load_nlg,
        'F_mlg': static_load_mlg,
        'D_mlg': main_diameter_m,
        'D_nlg': nose_diameter_m,
    }


if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    # Perform undercarriage sizing
    undercarriage_specs = perform_undercarriage_sizing(params)

    # Print the results
    print("Undercarriage Sizing Results:")
    print(f"Tire Pressure: {undercarriage_specs['tire_pressure']:.2f} kg/cm2")
    print(f"Static Load on Nose Wheel (F_nlg): {undercarriage_specs['F_nlg']:.2f} kg")
    print(f"Static Load on Main Wheels (F_mlg): {undercarriage_specs['F_mlg']:.2f} kg")
    print(f"Main Tire Diameter (D_mlg): {undercarriage_specs['D_mlg']:.2f} m")
    print(f"Nose Tire Diameter (D_nlg): {undercarriage_specs['D_nlg']:.2f} m")