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
D_fan = 0.508 # m, fan diameter
L_eng = 1.397 # m, engine length
Bpr = params.engine.Bpr # bypass ratio
eta_ft = params.engine.eta_fanturb # fan/turbine efficiency
tt4to = params.engine.tt4to # tt4 temp at takeoff
G = (tt4to/600)-1.25 # Specific gas turbine power
eta_nozz = params.engine.eta_nozz # nozzle efficiency
mdot_air = (T_to/a)*((1+Bpr)/(5*eta_nozz*G*(1+(eta_ft*Bpr))**0.5))

#print mass flow rate of air
print(f"Mass flow rate of air: {mdot_air:.2f} kg/s")

D_s = 0.14224 #spinner diameter, m
D_inlet = D_fan
spinner_inlet_ratio = 0.05 * (1+((0.1*1.225*a)/(mdot_air))+(3*Bpr)/(1+Bpr))
#print spinner inlet ratio
print(f"Spinner inlet ratio: {spinner_inlet_ratio:.2f}")

D_inlet = D_fan
l_n = 1.44 #nacelle length, m
D_n = D_inlet + (0.06*0.75*l_n) +0.03 #max nacelle diameter, m
print(f"Maximum nacelle diameter: {D_n:.2f} m")
D_ef = D_n*(1-(1/3)*0.75**2) #exit fan diameter, m
print(f"Nacelle exit diameter: {D_ef:.2f} m")