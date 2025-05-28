
# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *

params = DesignParameters()
params.load_from_yaml('design_config.yaml')


# Constants
CL_max_values = {
    "CLEAN": 1.3,
    "TAKE-OFF": 1.6,
    "LAND": 1.8
}
S = params.wing.S_w  # wing area (m²)

# Atmospheric densities
rho_table = {
    "sea_level": 1.225,
    "12100m":  0.305965 # using ISA standard atmosphere values
    } 

# Weight Scenarios
# in [N]
weight_1 = params.weight.W_OE # Operational Empty Weight (OEW) in N
weight_2 = params.weight.W_TO # Maximum Take-Off Weight (MTOW) in N
weight_3 = params.weight.W_OE + params.weight.W_PL # OEW + Payload in N

# in [kg]
weight_1_kg = N_to_kg(weight_1)
weight_2_kg = N_to_kg(weight_2)
weight_3_kg = N_to_kg(weight_3)


# Positive load factor formula (STANAG 4671 USAR.337)
def calc_positive_limit_load_factor(weight_kg):
    n_pos = min(2.1 + (10900 / (weight_kg + 4536)), 3.8)
    return n_pos


# Stall speed (clean)
def calc_stall_speed(weight_N, rho,CL_max):
    return np.sqrt((2 * weight_N) / (rho * S * CL_max))

# Maneuvering speed
def calc_maneuver_speed(VS, n_pos):
    return VS * np.sqrt(n_pos)

# Dive speed
def calc_dive_speed(VC):
    VD = 1.25 * VC 
    return VD

# Compute all speeds for one case
def compute_speed_profile(weight_N, VC, rho, CL_max):
    VS = calc_stall_speed(weight_N, rho, CL_max)
    n_pos = calc_positive_limit_load_factor(weight_N)
    VA = calc_maneuver_speed(VS, n_pos)
    VD = calc_dive_speed(VC)
    return {"VS": VS, "VA": VA, "VC": VC, "VD": VD}

# Compute all scenarios
def compute_all_profiles(weights_N, VC, CL_max_dict):
    results = []
    for cl_label, cl_value in CL_max_dict.items():
        for weight_label, weight in weights_N.items():
            for alt_label, rho in rho_table.items():
                speeds = compute_speed_profile(weight, VC, rho, cl_value)
                results.append({
                    "CL_max type": cl_label,
                    "CL_max": cl_value,
                    "Weight": weight_label,
                    "Altitude": alt_label,
                    "VS [m/s]": round(speeds["VS"], 2),
                    "VA [m/s]": round(speeds["VA"], 2),
                    "VC [m/s]": round(speeds["VC"], 2),
                    "VD [m/s]": round(speeds["VD"], 2)
                })
    return results
            

# Example weights (in N)
weights_N = {
    "OEW": 11973.3,
    "MTOW": 30787.8,
    "OEW+Payload": 11973.3 + 5884
}

# Example cruise speed (mission-defined)
VC = 75  # m/s

# Compute all profiles
all_profiles = compute_all_profiles(weights_N, VC, CL_max_values)
df = pd.DataFrame(all_profiles)

# Optional: sort for readability
df = df.sort_values(by=["CL_max type", "Weight", "Altitude"])

# Print the table
print(df.to_string(index=False))