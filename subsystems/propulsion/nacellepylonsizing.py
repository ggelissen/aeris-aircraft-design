import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters

params = DesignParameters()
params.load_from_yaml("design_config.yaml")

#speed of sound in air at sea level
a = (1.4 * 287.05 * 288.15) ** 0.5  # m/s, speed of sound at sea level at ISA + 15C
T_to = params.engine.T_TO
D_fan = 0.53 # m, fan diameter
L_eng = 1.397 # m, engine length
Bpr = params.engine.Bpr
print(f"Bypass Ratio: {Bpr}")



