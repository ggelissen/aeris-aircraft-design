
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




# This code generates a V-n diagram (Flight Envelope) for a UAV based on the STANAG 4671 and EASA CS-23 standards.



# 1 - UAV Paramenters
# Constants
CL_alpha = 5.0
chord = params.wing.mac # Mean Aerodynamic Chord (MAC) in m
CL_max_values = {
    "CLEAN": 1.3,
    "TAKE-OFF": 1.6,
    "LAND": 1.8
}
S = params.wing.S_w  # wing area (m²)
VC_TAS = params.cruise_speed # m/s
# Atmospheric densities
density_at_altitude = {
    "sea_level": 1.225,
    "cruise":  0.305965 # cruise (design) using ISA standard atmosphere values
    } 
VC = true_to_equivalent_air_speed(VC_TAS, density_at_altitude['cruise'], density_at_altitude['sea_level'])  # Convert True Airspeed (TAS) to Equivalent Airspeed (EAS) at sea level

altitude = {
    "sea_level": 0, # m
    "cruise":  params.cruise_altitude # m
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



def calc_load_factor_limits(weight_kg):
    n_pos_limit = min(2.1 + (10900 / (weight_kg + 4536)), 3.8)
    n_neg_limit = -0.4 * n_pos_limit
    return n_pos_limit, n_neg_limit

def calc_diagram_speed(weight_N, density, CL_max, VC):
    VS_TAS = np.sqrt((2 * weight_N) / (density * S * CL_max))
    VS = true_to_equivalent_air_speed(VS_TAS, density, density_at_altitude['sea_level'])  # Convert TAS to EAS at sea level
    VD = 1.25 * VC
    velocity_aixs = np.linspace(0, VD, 1000)
    return VS, VD, velocity_aixs

def calc_gust_velocity(altitude_m, velocity_aixs):
    #Gust velocity at VC as a function of altitude based on STANAG 4671.
    if altitude_m <= 6096:
        U_VC = 15.2
    elif 6096 < altitude_m <= 15240:
        U_VC = 15.2 - ((15.2 - 7.6) / (15240 - 6096)) * (altitude_m - 6096)
    else:
        U_VC = 7.6

    #Gust velocity at VD as a function of altitude based on STANAG 4671.
    if altitude_m <= 6096:
        U_VD = 7.6
    elif 6096 < altitude_m <= 15240:
        U_VD = 7.6 - ((7.6 - 3.8) / (15240 - 6096)) * (altitude_m - 6096)
    else:
        U_VD = 3.8


    # Compute gust velocity as a function of V
    U_gust = np.piecewise(velocity_aixs,
        [velocity_aixs <= VC, velocity_aixs > VC],
        [U_VC,
        lambda V: U_VC - ((U_VC - U_VD) / (VD - VC)) * (V - VC)]
    )  
    print(f"Gust velocity at altitude {altitude_m} m: U_VC = {U_VC} m/s, U_VD = {U_VD} m/s")
    return U_gust

def calc_gust_loads(velocity_aixs, U_gust, weight_N, density, chord):
    a = 2*np.pi # to be confirmed
    # wing loading
    W_S = weight_N / S  # in N/m²
    # aeroplane mass ratio
    ug = 2 * W_S / (density * chord * a * S * 9.80665)
    # gust alleviation factor
    kg = 0.88 * ug / (5.3 + ug)

    # EAS 
    #velocity_aixs_EAS
    n_gust_pos = 1 + kg * 1.225 * U_gust * velocity_aixs / (2 * W_S)
    n_gust_neg = 1 - kg * 1.225 * U_gust * velocity_aixs / (2 * W_S)

    #n_gust_pos = 1 + (density * CL_alpha * S * velocity_aixs * U_gust) / (2 * weight_N)
    #n_gust_neg = 1 - (density * CL_alpha * S * velocity_aixs * U_gust) / (2 * weight_N)

    return n_gust_pos, n_gust_neg

def calc_maneuver_loads(velocity_aixs, n_pos_limit, n_neg_limit, VS, VD):
    # I. Compute positive maneuver load factor
    n_parabola = (velocity_aixs / VS) ** 2              # CLmax limit (stall speed parabola)
    n_flat = np.full_like(velocity_aixs, n_pos_limit)   # Maximum positive load factor (flat line)

    n_maneuver_pos = np.minimum(n_parabola, n_flat)     # --> Postive maneuver load factor (minimum of parabola and flat line)

    # II. Compute negative maneuver load factor
    V_break = VS * np.sqrt(abs(n_neg_limit))

    n_maneuver_neg = np.piecewise(          # --> Negative maneuver load factor
        velocity_aixs,
        [velocity_aixs <= V_break,
        (velocity_aixs > V_break) & (velocity_aixs <= VC),
        (velocity_aixs > VC)],
        [
            lambda V: -((V / VS) ** 2),                         # Parabola (until it hits n_neg_limit)
            lambda V: n_neg_limit,                              # Flat line (from V_break to VC)
            lambda V: n_neg_limit * (VD - V) / (VD - VC)        # Linearly back to 0
        ]
    )

    return n_maneuver_pos, n_maneuver_neg

def plot_vn_diagram(velocity_aixs, n_pos_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, weight_label, VS, VC, VD):

    plt.figure(figsize=(10, 6))

    # Maneuver limits
    plt.plot(velocity_aixs, n_maneuver_pos, label='Positive Maneuver Limit', color='blue')
    plt.plot(velocity_aixs, n_maneuver_neg, label='Negative Maneuver Limit', color='blue')

    # Gust loads
    plt.plot(velocity_aixs, n_gust_pos, '--', label='Positive Gust Load', color='orange')
    plt.plot(velocity_aixs, n_gust_neg, '--', label='Negative Gust Load', color='orange')

    # Key speeds
    # Compute VA as the speed at which the parabola hits the flat limit
    VA_index = np.argmax(n_maneuver_pos >= n_pos_limit)
    VA = velocity_aixs[VA_index]

    # Custom color map for specific speeds
    speed_labels = ['VS', 'VA', 'VC', 'VD']
    speed_values = [VS, VA, VC, VD]
    color_map = {
        'VS': 'blue',
        'VA': 'gray',
        'VC': 'orange',
        'VD': 'red'
    }

    for v, label in zip(speed_values, speed_labels):
        plt.axvline(x=v, color=color_map[label], linestyle=':', label=label)

    # Labels and aesthetics
    plt.title('V-n Diagram (Flight Envelope)')
    plt.xlabel('Equivalent Airspeed (m/s)')
    plt.ylabel('Load Factor (n)')
    plt.grid(True)
    plt.legend(loc='upper right')
    plt.ylim(-4, 5)
    plt.xlim(0, VD + 10)
    plt.tight_layout()
    plt.show()





n_pos_limit, n_neg_limit = calc_load_factor_limits(weight_2_kg)
VS, VD, velocity_aixs = calc_diagram_speed(weight_2, density_at_altitude["cruise"], CL_max_values["CLEAN"], VC)
U_gust = calc_gust_velocity(altitude['cruise'], velocity_aixs)  # Assuming sea level altitude for gust calculations
n_gust_pos, n_gust_neg = calc_gust_loads(velocity_aixs, U_gust, weight_2, density_at_altitude["cruise"],chord)
n_maneuver_pos, n_maneuver_neg = calc_maneuver_loads(velocity_aixs, n_pos_limit, n_neg_limit, VS, VD)
# Plot the V-n diagram
plot_vn_diagram(velocity_aixs, n_pos_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, "MTOW", VS, VC, VD)
