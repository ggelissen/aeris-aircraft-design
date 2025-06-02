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
    tire_pressure = (430*math.log(LCN) -680)*1000 # in Pa
    tire_pressure_kgcm2 = tire_pressure / 98070
    static_nose_fraction = 0.08
    static_main_fraction = 1 - static_nose_fraction
    W_nose = static_nose_fraction * W_TO
    W_main_total = static_main_fraction * W_TO
    num_main_wheels = 2
    num_nose_wheels = 1

    static_load_main = W_main_total / num_main_wheels
    static_load_nose = W_nose / num_nose_wheels
    static_load_main_kg = static_load_main / 9.81  # Convert to kg
    static_load_nose_kg = static_load_nose / 9.81  # Convert to kg
    print(f"Static Load on Nose Wheel: {static_load_nose_kg:.2f} kg")
    print(f"Static Load on Main Wheels: {static_load_main_kg:.2f} kg")
    print(f"Tire Pressure: {tire_pressure_kgcm2:.2f} kg/cm^2")

def undercarriage_positioning(params: DesignParameters):
    