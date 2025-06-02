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


# This code generates a V-n diagram (Flight Envelope) for a UAV based on the STANAG 4671 and EASA CS-23 standards.



# 1 - UAV Paramenters
W_N = params.weight.W_TO
W_kg = W_N / 9.81
S = params.wing.S_w
VS = params.stall_speed_clean # kts
VS = kts_to_ms(VS) # Convert speeds to m/s
VC = params.cruise_speed # m/s
rho = 1.225
CL_alpha = 5.0


# 2 - Load Factor Limits USAR.333
n_pos_limit = min(2.1 + (10900 / (W_kg + 4536)), 3.8)
n_neg_limit = -0.4 * n_pos_limit


# 3 - Required Speeds for the Diagram

# Design maneuvering speed
#VA = VS * np.sqrt(n_pos_limit) 

 
# Design dive speed (min 1.25*VC)
VD = 1.25 * VC   

# Create an array of speeds for the V-n diagram
velocity_aixs = np.linspace(0, VD, 1000)



# 4. Gust Velocity Calculation
def gust_velocity_at_altitude_VC(altitude_m):
    """Gust velocity at VC as a function of altitude based on STANAG 4671."""
    if altitude_m <= 6096:
        return 15.2
    elif 6096 < altitude_m <= 15240:
        return 15.2 - ((15.2 - 7.6) / (15240 - 6096)) * (altitude_m - 6096)
    else:
        return 7.6

def gust_velocity_at_altitude_VD(altitude_m):
    """Gust velocity at VD as a function of altitude based on STANAG 4671."""
    if altitude_m <= 6096:
        return 7.6
    elif 6096 < altitude_m <= 15240:
        return 7.6 - ((7.6 - 3.8) / (15240 - 6096)) * (altitude_m - 6096)
    else:
        return 3.8

# gust velocity -> USAR 333-c-(i)
altitude_m = params.cruise_altitude or 0
U_VC = gust_velocity_at_altitude_VC(altitude_m)
U_VD = gust_velocity_at_altitude_VD(altitude_m)

# Compute gust velocity as a function of V
U_gust = np.piecewise(velocity_aixs,
    [velocity_aixs <= VC, velocity_aixs > VC],
    [U_VC,
     lambda V: U_VC - ((U_VC - U_VD) / (VD - VC)) * (V - VC)]
)  


# 5. Load Factors Calculation


# 5.A Gust Loads
n_gust_pos = 1 + (rho * CL_alpha * S * velocity_aixs * U_gust) / (2 * W_N)
n_gust_neg = 1 - (rho * CL_alpha * S * velocity_aixs * U_gust) / (2 * W_N)



# 5.B Maneuver Loads
n_parabola = (velocity_aixs / VS) ** 2              # CLmax limit (stall speed parabola)
n_flat = np.full_like(velocity_aixs, n_pos_limit)   # Maximum positive load factor (flat line)

n_maneuver_pos = np.minimum(n_parabola, n_flat)     # --> Postive maneuver load factor (minimum of parabola and flat line)

# Determine VA as the point where parabola == flat line (intersection)
VA_index = np.argmax(n_parabola >= n_pos_limit)
VA = velocity_aixs[VA_index]


# Compute point where parabola reaches n_neg_limit
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

# 6. Plotting the V-n Diagram
# ____ PLOTTING ____
plt.figure(figsize=(10, 6))

# Maneuver limits
plt.plot(velocity_aixs, n_maneuver_pos, label='Positive Maneuver Limit', color='blue')
plt.plot(velocity_aixs, n_maneuver_neg, label='Negative Maneuver Limit', color='blue')

# Gust loads
plt.plot(velocity_aixs, n_gust_pos, '--', label='Positive Gust Load', color='orange')
plt.plot(velocity_aixs, n_gust_neg, '--', label='Negative Gust Load', color='orange')

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