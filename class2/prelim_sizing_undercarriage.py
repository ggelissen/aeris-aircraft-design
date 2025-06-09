import math
import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 
from main_class_II import *



def perform_undercarriage_positioning(params: DesignParameters):
    """
    Calculate the undercarriage positioning based on design parameters.

    Parameters:
    params (DesignParameters): Design parameters object containing aircraft specifications.
    
    from Roskam p.218 part 2
    """
    
    l_m = 1.5*math.tan(params.landing_gear.tipback_angle)
    l_n = (1/params.landing_gear.static_frac_nlg - 1) * l_m
    x_nlg = 5.01  - l_n
    x_mlg = 5.01 + l_m
    P_n = (params.weight.W_TO*l_m)/(l_m+l_n)
    n_s = 2
    P_m = (params.weight.W_TO*l_n)/(n_s*(l_m+l_n))
    nose_load = P_n / params.weight.W_TO
    main_load = n_s*P_m / params.weight.W_TO
    y_mlg = (l_n+l_m)/(math.sqrt(((l_n**2) * (math.tan(params.landing_gear.overturn_angle)**2))/(params.cg.z_cg**2) -1))
   
    tire_pressure = (430*math.log(params.landing_gear.LCN) -680) * 10e3 # in Pa
    tire_pressure_kg_cm2 = tire_pressure / 10  # Convert Pa to kg/cm^2

    static_load_nlg = P_n / 9.80665  # Convert N to kg
    static_load_mlg = P_m / 9.80665  # Convert N to kg

    

    return x_nlg, x_mlg, y_mlg, l_m, l_n, P_n, P_m, nose_load, main_load, tire_pressure_kg_cm2, static_load_nlg, static_load_mlg


if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    undercarriage_positioning = perform_undercarriage_positioning(params)
    # Print the undercarriage sizing results
    print("Undercarriage Sizing Results:")
    print(f"Nose Gear X Position (x_nlg): {undercarriage_positioning[0]:.2f} m")
    print(f"Main Gear X Position (x_mlg): {undercarriage_positioning[1]:.2f} m")
    print(f"Main Gear Y Position (y_mlg): {undercarriage_positioning[2]:.2f} m")
    print(f"Length between cg and mlg (l_m): {undercarriage_positioning[3]:.2f} m")
    print(f"Lenfth between cg and nlg (l_n): {undercarriage_positioning[4]:.2f} m")
    print(f"Nose Gear Load (P_n): {undercarriage_positioning[5]:.2f} N")
    print(f"Main Gear Load (P_m): {undercarriage_positioning[6]:.2f} N")
    print(f"Nose Gear Load Fraction: {undercarriage_positioning[7]:.2f}")
    print(f"Main Gear Load Fraction: {undercarriage_positioning[8]:.2f}")
    print(f"Tire Pressure: {undercarriage_positioning[9]:.2f} kg/cm²")
    print(f"Static Load on Nose Gear (static_load_nlg): {undercarriage_positioning[10]:.2f} kg")
    print(f"Static Load on Main Gear (static_load_mlg): {undercarriage_positioning[11]:.2f} kg")
 
