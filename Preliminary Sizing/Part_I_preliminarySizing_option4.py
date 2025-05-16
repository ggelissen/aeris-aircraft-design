import math
import numpy as np

# Based on Part I "Preliminary Sizing of Airplanes" by Roskam
# For manned aircraft, use "5. Business Jet" (p. 5), Piaggio Douglas PD-808 VESPA-JET
# For unmanned aircraft, use "8. Military Trainers" (p. 5)


########################## Chapter 2: Estimating Take-Off Gross Weight, W_TO, Empty Weight, W_E, and Mission Fuel Weight, W_F ##########################


####     Determination of mission payload W_PL    ####

# Defined as essential instruments plus additional instruments
# Essential instruments = 300 kg
# Additional instruments = 600 kg (incl. Lidar)
#                        = 850 kg (incl. Lidar + Radiospectrometer)
#                        = 1100 kg (incl. Lidar + Radiospectrometer + Airborne Mass Spectrometer))


W_PL_lst = [300, 600, 850, 1100] # kg
W_PL = W_PL_lst[0] 
print(f"Payload weight: {W_PL:.2f} kg")


####    Guessing likely value of take-off weight W_TO    ####

# Reference manned aircraft: like transport performance   
W_TO = 3000 # kg
print(f"Take-off weight: {W_TO:.2f} kg")


####    Determination of mission fuel weight W_F    ####

# Constants for cruise
R_cruise = 8000e3         # m
V_cruise = 240          # m/s
L_D_cruise =  14     # range (13-15) frpm transport aircraft
c_j_cruise = 0.433/3600     # lbs/lbs/hr - range (0.5-0.9)

# Constants for loiter
L_D_loiter = 16         # range (14-18)
c_j_loiter = 0.433*0.75/3600       # lbs/lbs/hr - range (0.4-0.6)
E_loiter = 0.5*3600            # hr    TODO: check this value

# Fuel fractions for different mission profiles
# 1: engine start, 2: taxi, 3: take-off, 4: climb, 5: cruise, 6: loiter, 7: descent, 8: landing
W5_W4 = 1 / np.exp((R_cruise * c_j_cruise) / (V_cruise * L_D_cruise))
W6_W5 = 1/ np.exp((E_loiter * c_j_loiter) / (L_D_loiter))
fuel_fractions = {1: 0.99, 2: 0.995, 3: 0.995, 4: 0.98, 5: W5_W4, 6: W6_W5, 7: 0.99, 8: 0.992}

# Calculate fuel weight components
W_F_res = 0.05 * W_TO                            # reserve fuel weight
M_ff = math.prod(fuel_fractions.values())       # mission fuel fraction
W_F_used = (1 - M_ff) * W_TO                    # fuel weight used
W_F = W_F_used + W_F_res                        # total fuel weight

print(f"Fuel weight: {W_F:.2f} kg")


####   Determination of empty weight W_E    ####

# Calculate tentative weights
W_tfo = 0                               # neglected
W_crew = 100                            # no crew, since unmanned
W_OE_tent = W_TO - W_F - W_PL           # kg
W_E_tent = W_OE_tent - W_tfo - W_crew   # kg

# Calculate empty weight using Roskam interpolation method
A = 0.6545                               # based on "Business Jet"
B = -154.87                               # based on "Business Jet"
W_E = A * W_TO + B

# Compare interpolated weight with tentative weight
error = W_E - W_E_tent
print(f"Interpolated empty weight: {W_E:.2f} kg")
print(f"Tentative empty weight: {W_E_tent:.2f} kg")
print(f"Error: {error:.2f} kg")



########################## Chapter 3: Estimating Wing Area, S, Take-Off Thrust T_TO, and Max. Lift Coefficient, C_L_max ##########################

#### Sizing for stall speed V_S ####

# Constants
V_stall = 61                        # kts (according to Roskam / CS-23)
V_stall = V_stall * 0.514444        # m/s
rho_cruise = 0.4135                 # kg/m^3 (at 8000 m) #  TODO: check this value
rho_TO = 1.225                      # kg/m^3 (at sea level)
rho_L = 1.225                       # kg/m^3 (at sea level)

# Lift coefficients obtained from Roskam (p. 91)
C_L_max = 1.9          # clean configuration (1.4-1.8)
C_L_max_TO = 2.2        # take-off configuration (1.6-2.2)
C_L_max_L = 2.6         # landing configuration (1.6-2.6)

# Calculate wing loading
W_S = 0.5 * V_stall ** 2 * rho_cruise * C_L_max     # clean configuration
W_S_TO = 0.5 * V_stall ** 2 * rho_TO * C_L_max_TO   # take-off configuration
W_S_L = 0.5 * V_stall ** 2 * rho_L * C_L_max_L      # landing configuration

# Calculate wing area
S = W_TO / W_S
S_TO = W_TO / W_S_TO
S_L = W_TO / W_S_L


#### Sizing for take-off distance ####
T_W = W_S_TO / (C_L_max_TO * 1795.5)  # thrust-to-weight ratio
T_TO = T_W * W_TO * 9.81  # thrust in N
print(f"Take-off thrust: {T_TO:.2f} N")
# TO BE CONTINUED ....