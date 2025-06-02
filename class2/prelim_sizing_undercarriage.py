import math
import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 
from main_class_II import *

def perform_undercarriage_sizing(params: DesignParameters) -> dict:
     
    """
    Calculate the undercarriage loading based on the takeoff weight and number of wheels.

    Returns a dict with keys:
      'tire_pressure'   (kg/cm²),
      'F_nlg'           (static load on each nose wheel in kg),
      'F_mlg'           (static load on each main wheel in kg),
      'static_load_nlg' (static load on nose wheel in N),
      'static_load_mlg' (static load on each main wheel in N),
      'W_nose'          (total nose‐gear load in N),
      'W_main_total'    (total main‐gear load in N).
    """
    tire_pressure = (430*math.log(params.landing_gear.LCN) -680) * 10e3 # in Pa
    tire_pressure_kg_cm2 = tire_pressure / 10  # Convert Pa to kg/cm^2

    W_nose = params.landing_gear.static_frac_nlg * params.weight.W_TO
    W_main_total = params.landing_gear.static_frac_mlg * params.weight.W_TO

    static_load_mlg = W_main_total / params.landing_gear.n_mlg
    static_load_nlg = W_nose / params.landing_gear.n_nlg

    # Convert static loads to kg
    static_load_nlg_kg = static_load_nlg / 9.80665  # Convert N to kg
    static_load_mlg_kg = static_load_mlg / 9.80665  # Convert N to kg

    return {
        'tire_pressure':   tire_pressure_kg_cm2,
        'F_nlg':           static_load_nlg_kg,
        'F_mlg':           static_load_mlg_kg,
        'static_load_nlg': static_load_nlg,
        'static_load_mlg': static_load_mlg,
        'W_nose':          W_nose,
        'W_main_total':    W_main_total
    }
# with these values check torenbeek plot for wheel sizing


def perform_undercarriage_positioning(params: DesignParameters, W_main_total: float) -> tuple:
    """
    Calculate the undercarriage positioning based on design parameters.

    Parameters:
    params (DesignParameters): Design parameters object containing aircraft specifications.


    """

    tipback_rad = params.landing_gear.tipback_angle* math.pi / 180  # Convert degrees to radians
    x_cg = 4.6
    x_nlg = x_cg - params.cg.z_cg / math.tan(tipback_rad)  # X position of NLG in meters
    wheelbase = (params.weight.W_TO *(x_cg - x_nlg)) / W_main_total
    x_mlg = x_nlg + wheelbase

    # #track
    # track = 2* (params.cg.z_cg) / math.tan(math.radians(params.landing_gear.lat_tipover_angle))

    # y_mlg = track / 2  # Y position of NLG in meters
    
    return x_nlg, x_mlg


if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    # Perform undercarriage sizing
    undercarriage_sizing = perform_undercarriage_sizing(params)

    # Print the results
    print("Undercarriage Sizing Results:")
    print(f"Tire Pressure: {undercarriage_sizing['tire_pressure']:.2f} kg/cm2")
    print(f"Static Load on Nose Wheel (F_nlg): {undercarriage_sizing['F_nlg']:.2f} kg")
    print(f"Static Load on Main Wheels (F_mlg): {undercarriage_sizing['F_mlg']:.2f} kg")
    print(f"Static Load on Nose Wheel (N): {undercarriage_sizing['static_load_nlg']:.2f} N")
    print(f"Static Load on Main Wheels (N): {undercarriage_sizing['static_load_mlg']:.2f} N")
    print(f"Total Nose Gear Load (W_nose): {undercarriage_sizing['W_nose']:.2f} N")
    print(f"Total Main Gear Load (W_main_total): {undercarriage_sizing['W_main_total']:.2f} N")

    # Perform undercarriage positioning
    undercarriage_positioning = perform_undercarriage_positioning(params, W_main_total=undercarriage_sizing['W_main_total'])

    # Print the undercarriage positioning results
    print("\nUndercarriage Positioning Results:")
    print(f"Nose Gear X Position (x_nlg): {undercarriage_positioning[0]:.2f} m")
    print(f"Main Gear X Position (x_mlg): {undercarriage_positioning[1]:.2f} m")
    # print(f"Track Width: {undercarriage_positioning[3]:.2f} m")
