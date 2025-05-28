import math
import yaml
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
import component_weights as cw
from utils.unit_conversions import * 

def undercarriage_sizing(params:DesignParameters, surface_type='paved'):
    W_TO = params.weight.W_TO
    LCN = 40 # Load Classification Number, typical for light aircraft
    tire_pressure = (430*math.log(LCN) -680)*1000 # in kPa
    static_nose_fraction = 0.08
    static_main_fraction = 1 - static_nose_fraction
    W_nose = static_nose_fraction * W_TO
    W_main_total = static_main_fraction * W_TO
    num_main_wheels = 2
    num_nose_wheels = 1

    static_load_main = W_main_total / num_main_wheels
    static_load_nose = W_nose / num_nose_wheels

    print(f"Static Load on Nose Wheel: {static_load_nose:.2f} N")
    print(f"Static Load on Main Wheels: {static_load_main:.2f} N")

    def estimate_tire_diameter(laod_N, pressure_Pa):
        load_kg = load_N / G
        pressure_bar = pressure_Pa / 100000  # Convert Pa to bar
        return 0.5* (load_kg / pressure_bar) ** (0.25)
    
    main_diameter_m = estimate_tire_diameter(static_load_main, tire_pressure)
    nose_diameter_m = estimate_tire_diameter(static_load_nose, tire_pressure)

    print(f"Estimated Main Tire Diameter: {main_diameter_m:.2f} m")
    print(f"Estimated Nose Tire Diameter: {nose_diameter_m:.2f} m")

    return {
        'tire_pressure': tire_pressure,
        'static_load_nose': static_load_nose,
        'static_load_main': static_load_main,
        'main_diameter_m': main_diameter_m,
        'nose_diameter_m': nose_diameter_m,
        'num_main_wheels': num_main_wheels,
        'num_nose_wheels': num_nose_wheels
    }