# Make V-n diagram, taking into account loads from the wake of the previous aircraft
# make use of https://ntrs.nasa.gov/api/citations/20140000839/downloads/20140000839.pdf page 280 and further
# as well as https://ntrs.nasa.gov/api/citations/20160010341/downloads/20160010341.pdf

# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *

params = DesignParameters()
params.load_from_yaml('design_config.yaml')



# UAV Paramenters
W_N = params.weight.W_TO
W_kg = W_N / 9.81
S = params.wing.S_w
VS = params.stall_speed_clean # kts
VS = kts_to_ms(VS) # Convert speeds to m/s
VC = params.cruise_speed # m/s
rho = 1.225
CL_alpha = 5.0


# Load Factor Limts - USAR.333
n_pos_limit = min(2.1 + (10900 / (W_kg + 4536)), 3.8)
n_neg_limit = -0.4 * n_pos_limit


# Design maneuvering speed
VA = VS * np.sqrt(n_pos_limit)  
# Design dive speed (min 1.25*VC)
VD = 1.25 * VC   

if VA > VC:
    print("Warning: VA is greater than VC, which is not allowed. Check your design parameters.")

speeds = np.linspace(0, VD, 1000)


# ____ GUST LOADS ____
# gust velocity -> USAR 333-c-(i)
U_VC = 15.2  # gust speed at VC in m/s
U_VD = 7.6   # gust speed at VD in m/s

# Compute gust velocity as a function of V
U_gust = np.piecewise(speeds,
    [speeds <= VC, speeds > VC],
    [U_VC,
     lambda V: U_VC - ((U_VC - U_VD) / (VD - VC)) * (V - VC)]
)  

# gust load factors -> from STANAG 4671 / EASA CS-23
n_gust_pos = 1 + (rho * CL_alpha * S * speeds * U_gust) / (2 * W_N)
n_gust_neg = 1 - (rho * CL_alpha * S * speeds * U_gust) / (2 * W_N)


# ____ MANEUVERING LOADS ____
n_pos = np.piecewise(speeds,
    [speeds <= VC, speeds > VC],
    [lambda v: n_pos_limit,
     lambda v: n_pos_limit * (VD - v) / (VD - VC)]
)
n_neg = np.piecewise(speeds,
    [speeds <= VC, speeds > VC],
    [lambda v: n_neg_limit,
     lambda v: n_neg_limit * (VD - v) / (VD - VC)]
)


# ____ PLOTTING ____
plt.figure(figsize=(10, 6))

# Maneuver limits
plt.plot(speeds, n_pos, label='Positive Maneuver Limit', color='blue')
plt.plot(speeds, n_neg, label='Negative Maneuver Limit', color='blue')

# Gust loads
plt.plot(speeds, n_gust_pos, '--', label='Positive Gust Load', color='orange')
plt.plot(speeds, n_gust_neg, '---', label='Negative Gust Load', color='orange')

# Key speeds
# Custom color map for specific speeds
speed_labels = ['VS', 'VA', 'VC', 'VD']
speed_values = [VS, VA, VC, VD]
color_map = {
    'VS': 'green',
    'VA': 'gray',
    'VC': 'gray',
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