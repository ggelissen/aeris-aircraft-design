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

print(VA,VC)



#plt.figure(figsize=(10, 6))
# plt.plot(speeds, n_pos, label='Positive Maneuver Limit', color='blue')
# plt.plot(speeds, n_neg, label='Negative Maneuver Limit', color='blue')
# plt.plot(speeds, gust_pos, '--', label='Positive Gust Load', color='orange')
# plt.plot(speeds, gust_neg, '--', label='Negative Gust Load', color='orange')

# for v, label in zip([VS, VA, VC, VD], ['VS', 'VA', 'VC', 'VD']):
#     plt.axvline(x=v, color='gray', linestyle=':', label=label)

# plt.title('V-n Diagram (Imported Design Parameters)')
# plt.xlabel('Equivalent Airspeed (m/s)')
# plt.ylabel('Load Factor (n)')
# plt.grid(True)
# plt.legend(loc='upper right')
# plt.ylim(-4, 5)
# plt.xlim(0, VD + 10)
# plt.tight_layout()
# plt.show()






