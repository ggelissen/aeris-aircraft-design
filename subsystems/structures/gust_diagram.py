# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
sns.set_style("whitegrid")


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from config.design_variables import *

params = DesignParameters()
params.load_from_yaml('design_config.yaml')



# Data and Constants
rho = 1.225  # air density in kg/m^3 0.42552 for FL320
rho_cruise = params.cruise_density # air density at cruise altitude in kg/m^3
mac = params.wing.mac  # Mean Aerodynamic Chord in m
Cl_alpha = params.performance.CL_alpha  # Lift curve slope in per radian
W_S_revised = (params.weight.W_OE + params.weight.W_PL + params.weight.W_F * params.weight.Fuel_Fuselage_Fraction)/params.wing.S_w
print(f"W_S_revised: {W_S_revised}")

mu_g = (W_S_revised) / (9.80665*0.5 * rho_cruise * mac * Cl_alpha)
K_g_var = (0.88 * mu_g) / (5.3 + mu_g)

knot_to_mps = 0.514444  # Conversion factor from knots to m/s
VB = equivalent_to_true_air_speed(70, params.cruise_density, 1.225)  #TAS in m/s 
VC = params.cruise_speed  # Cruise speed TAS in m/s
VD = VD = 1.25 * VC   # Dive speed (VD) TAS [m/s]
print(f"VB: {VB}, VC: {VC}, VD: {VD}")

V_values_var = [VB, VC, VD]  # Airspeeds TAS in m/s
u_values_var = [15.2, 10.21, 10.21/2]  # Gust intensities in m/s STANAG 4671
#u_values_var = [u*0.3048 for u in [66, 50, 25]]
# Convert TAS to EAS:
V_values_var = [v*(rho_cruise/rho)**0.5 for v in V_values_var] # EAS [m/s]

# Compute total load factor n
n_values_positive_revised = [1 + (rho * V * Cl_alpha * K_g_var * u) / (2 * W_S_revised) for V, u in zip(V_values_var, u_values_var)]
n_values_negative_revised = [1 - (rho * V * Cl_alpha * K_g_var * u) / (2 * W_S_revised) for V, u in zip(V_values_var, u_values_var)]
V_values_extended = [0] + V_values_var
n_values_positive_extended = [1] + n_values_positive_revised
n_values_negative_extended = [1] + n_values_negative_revised
print(f"n_values_positive_extended: {n_values_positive_extended}")
print(f"n_values_negative_extended: {n_values_negative_extended}")

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(V_values_extended, n_values_positive_extended, color='blue')
plt.plot(V_values_extended, n_values_negative_extended, color='blue')
plt.plot([V_values_var[-1], V_values_var[-1]], [n_values_positive_revised[-1], n_values_negative_revised[-1]], color='blue')

# Vertical dotted lines and speed names
colors = ['green', 'orange', 'red']
speed_names = ["$\mathbf{V_B}$", "$\mathbf{V_{cruise}}$", "$\mathbf{V_{D}}$"]
for i, (V, u, color, speed_name) in enumerate(zip(V_values_var, u_values_var, colors, speed_names)):
    plt.axvline(V, color=color, linestyle='--', linewidth=1)
    plt.text(V - 4, 1.2, speed_name, fontsize=20, ha='center', va='center', color=color, weight = 'bold')
    
    # Add dotted lines from v=0 and n=1 to the gust points
    plt.plot([0, V], [1, n_values_positive_extended[i+1]], color='blue', linestyle='--', linewidth=1)
    plt.plot([0, V], [1, n_values_negative_extended[i+1]], color='blue', linestyle='--', linewidth=1)

    # Convert gust intensities to fps for annotation
    u_fps = u * 3.28084
    plt.text(V, n_values_positive_extended[i+1]-0.1, f"{u_fps:.2f} fps", fontsize=14, ha='right', va='top', color='purple')

# Points for max and min at Vcruise
plt.scatter(V_values_var[1], n_values_positive_revised[1], color='darkblue', s=50, zorder=5)
plt.scatter(V_values_var[1], n_values_negative_revised[1], color='darkblue', s=50, zorder=5)

# Load factor values at cruise speed
plt.text(V_values_var[1], n_values_positive_revised[1], f"n={n_values_positive_revised[1]:.3f}", fontsize=17.5, ha='right', va='bottom', color='darkblue', weight='bold')
plt.text(V_values_var[1], n_values_negative_revised[1], f"n={n_values_negative_revised[1]:.3f}", fontsize=17.5, ha='right', va='top', color='darkblue', weight='bold')

plt.axhline(1, color='black',linewidth=0.5)
plt.xlabel("Equivalent Airspeed (V) [m/s]", fontsize=16)
plt.ylabel("Total Load Factor (n)", fontsize=16)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
plt.grid(True)
plt.tight_layout()
plt.show()
print(1.55*n_values_positive_revised[1]*0.7)



