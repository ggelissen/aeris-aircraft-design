import numpy as np
import os
import sys
import matplotlib.pyplot as plt

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
Ds_i = D_s / D_inlet #spinner to inlet diameter ratio
spinner_inlet_ratio = 0.05 * (1+((0.1*1.225*a)/(mdot_air))+(3*Bpr)/(1+Bpr))
#print spinner inlet ratio
print(f"Spinner inlet ratio: {spinner_inlet_ratio:.2f}")
D_i = 1.65*((mdot_air/(1.225*a)+0.005)/(1-(Ds_i)**2))**0.5 #inlet diameter, m
print(f"Inlet diameter: {D_i:.2f} m")



D_inlet = D_fan
l_n = 1.44 #nacelle length, m
D_n = D_inlet + (0.06*0.75*l_n) +0.03 #max nacelle diameter, m
print(f"Maximum nacelle diameter: {D_n:.2f} m")
D_ef = D_n*(1-(1/3)*0.75**2) #exit fan diameter, m
print(f"Nacelle exit diameter: {D_ef:.2f} m")

# Constants
D_fan = 0.508               # Fan and core diameter
D_s = 0.14224               # Spinner diameter
D_ef = 0.49                 # Exit nacelle diameter
D_n = 0.63                  # Max nacelle diameter
L_eng = 1.397               # Engine core length
l_nacelle = L_eng + 0.2     # Total nacelle length with margins

# Radius values
R_fan = D_fan / 2
R_s = D_s / 2
R_ef = D_ef / 2
R_n = D_n / 2

# Nacelle shape profile
z_nacelle = np.array([-0.1, l_nacelle * 0.3, l_nacelle * 0.7, l_nacelle])
r_nacelle = np.array([R_fan, R_n, R_n, R_ef])

z_profile = np.concatenate([z_nacelle, z_nacelle[::-1]])
r_profile = np.concatenate([r_nacelle, -r_nacelle[::-1]])

# Engine core
core_z = [0, L_eng, L_eng, 0, 0]
core_r = [R_fan, R_fan, -R_fan, -R_fan, R_fan]

# Spinner (cone shape)
spinner_z = [-0.1, 0, 0]
spinner_r = [0, R_s, -R_s]

# Plot
plt.figure(figsize=(10, 4))
plt.plot(z_profile, r_profile, label="Nacelle Surface", color='steelblue')
plt.fill(core_z, core_r, color='gray', alpha=0.6, label="Engine Core")
plt.fill(spinner_z, spinner_r, color='red', label="Spinner")

# Labels and aesthetics
plt.title("Side View of Engine Nacelle with Spinner")
plt.xlabel("Length (m)")
plt.ylabel("Radius (m)")
plt.axis("equal")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()