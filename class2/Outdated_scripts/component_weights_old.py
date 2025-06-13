import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...')))
from utils.unit_conversions import *
from design_variables import DesignParameters


# --- Constants ---
G = 9.80665  # Acceleration due to gravity (m/s^2)

# This initialization is only for standalone testing of this file, 
# the master script will pass its own params object.
#params = DesignParameters()
#params.load_from_yaml('design_config.yaml')


def wing_weight_N(params: DesignParameters):
    #choose the appropriate method based on the wing type
    #Torenbeek for light transport with takeoff weight below 12500 lbs
    W_TO_lb = N_to_lbf(params.weight.W_TO)  # Convert takeoff weight to lbf
    b_w_ft = m_to_ft(params.wing.b_w)  # Convert wing span to feet
    
    W_wing_lb = 0.00125 * (W_TO_lb)*(b_w_ft/math.cos(params.wing.Lambda_05_w))**0.75 * (1+(6.3*math.cos(params.wing.Lambda_05_w)/b_w_ft)**0.5)* params.max_load_factor**0.55*(m2_to_ft2(params.wing.S_w)*b_w_ft/(m_to_ft(params.wing.t_r)*params.weight.W_TO*math.cos(params.wing.Lambda_05_w)))**0.3
    W_wing_N = lbf_to_N(W_wing_lb)  # Convert to Newtons for consistency
    print(f"Wing weight (N): {W_wing_N:.2f}")
    return W_wing_N

def fuselage_weight_N(params: DesignParameters):
    # Fuselage weight estimation using Gundlach Eq. 6.40
    F_MG = 1.07     # 1.07 if main gear on fuselage, 1 if on wing
    F_NG = 1.04     # 1.04 if nose gear on fuselage, 1 if on wing
    F_press = 1     # 1.0 if unpressurized, 1.08 if pressurized
    F_VT = 1        # 1 if vertical tail not included, 1.1 if included
    F_matl = 1      # 1 is carbonfiber or metal, 2 if fiberglass or unknown, 2.187 if wood

    L_struct_ft = m_to_ft(params.fuselage.l_f)  # Fuselage length in ft
    W_carried_lbf = N_to_lbf(params.weight.W_PL)  # Carried weight in lbf
    N_Z = params.max_load_factor

    W_fus_lb = (
        0.5257 * F_MG * F_NG * F_press * F_VT * F_matl
        * (L_struct_ft ** 0.3796)
        * ((W_carried_lbf * N_Z) ** 0.4863)
        * (params.max_eq_velocity)**2 # TODO, there was a factor 1.3 here! Remove it?, seems like it as per 6.40?
        # Why is max_eq_velocity divided by 100?
    )
    W_fus_N = lbf_to_N(W_fus_lb)  # Convert to Newtons for consistency
    print(f"Fuselage weight (N): {W_fus_N:.2f}")
    return W_fus_N


def landing_gear_weight_N(params: DesignParameters):
    # equation from gundlach
    F_lg = 0.04  # range from 0.03 - 0.06 # TODO, questionable, assumption. Why?
    W_lg_lb = F_lg * N_to_lbf(params.weight.W_TO)  # lb
    W_lg_N = lbf_to_N(W_lg_lb)  # Convert to Newtons for consistency
    print(f"Landing gear weight (N): {W_lg_N:.2f}")
    return W_lg_N


def empennage_weight_N(params: DesignParameters):
    #equation from Gundlach 6.37 to 6.39 TODO use with caution! Rule of thumb by Gundlach
    WA_emp = 0.8  #for composite tail, 0.8-1.2 for metal gen aviation, 3.5-8 for supersonic fighters
    W_HT = WA_emp * m2_to_ft2(params.empennage.S_h) # TODO: Change to v tail
    W_VT = WA_emp * m2_to_ft2(params.empennage.S_v)
    W_emp = W_HT*math.cos(params.empennage.vtail_dihedral)**2 + W_VT*math.sin(params.empennage.vtail_dihedral)**2
    W_emp_N = lbf_to_N(W_emp)  # Convert to Newtons for consistency
    print(f"Empennage weight (N): {W_emp_N:.2f}")
    return W_emp_N

def propulsion_weight_N(params: DesignParameters):
    # equation from Gundlach
    F_nac = 0.055                     #0.055 for low bypass turbofan, 0.065 for high bypass turbofan
    F_fs = 0.692 # estimation for MALE single engine [torenbeek] Gundlach page 214
    E1 = 0.67 # estimation for Male single engine [torenbeek]
    T_max = N_to_lbf(params.engine.engine_max_thrust)   # lbf
    W_nacelle_lb = F_nac*T_max                  #lbf
    W_fuel_system_lb = F_fs * N_to_lbf(params.weight.W_F)**E1  # lbf
    #W_ai = air induction system?
    W_propulsion_lb = W_nacelle_lb + N_to_lbf(params.engine.engine_weight) + W_fuel_system_lb  # lbf
    #W_propulsion_N = 477.22 * 9.81  # Convert to Newtons for consistency TODO this was hardcoded, remove it
    W_propulsion_N = lbf_to_N(W_propulsion_lb)  # Convert to Newtons for consistency
    print(f"Propulsion weight (N): {W_propulsion_N:.2f}")
    return W_propulsion_N

def fixed_equipment_weight_N(params: DesignParameters):
    W_autopilot = 50 #10-50 lb for MALE UAS
    W_AirDataSystem = 1 #0.5-1 lb 
    W_GPS = 0.5 #lb
    W_INS = 22 #8-22 lb
    W_processor = 25 #lb not sure about this one
    W_wiring = 0.35 #0.2-0.35 lb
    W_line_of_sight = 2 #not sure about this one
    W_SATCOM = 85 #lb
    W_avion = W_autopilot + W_AirDataSystem + W_GPS + W_INS + W_processor + W_wiring + W_line_of_sight + W_SATCOM
    F_FCS = 0.0002 #0.00007 - 0.0002
    W_FCS = F_FCS * m2_to_ft2(params.control_surface.S_a) * (params.max_eq_velocity)**2 
    W_fixed_equipment_lb = W_avion + W_FCS
    W_fixed_equipment_N = lbf_to_N(W_fixed_equipment_lb)  # Convert to Newtons for consistency
    print(f"Fixed equipment weight (N): {W_fixed_equipment_N:.2f}")
    return W_fixed_equipment_N



