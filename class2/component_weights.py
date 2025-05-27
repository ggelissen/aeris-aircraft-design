import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters


# --- Constants ---
G = 9.80665  # Acceleration due to gravity (m/s^2)


params = DesignParameters()
params.load_from_yaml('design_config.yaml')

S_emp = params.empennage.S_t

def wing_weight_N(WTO, wing_params):
    #choose the appropriate method based on the wing type

def fuselage_weight_lb(params: DesignParameters):
    #equation from Gundlach
    l_f_ft = m_to_ft(params.fuselage.l_f)   # ft
    W_PL_LBS = N_to_lbf(params.weight.W_PL)              # lbs
    V_eqMax = params.max_eq_velocity        # kts
    N_z = params.max_load_factor            # g
    
    F_MG = 1.07     # 1.07 if main gear on fuselage, 1 if on wing
    F_NG = 1.04     # 1.04 if nose gear on fuselage, 1 if on wing
    F_press = 1     # 1.0 if unpressurized, 1.08 if pressurized
    F_VT = 1        # 1 if vertical tail not included, 1.1 if included
    F_matl = 1      #1 is carbonfiber or metal, 2 if fiberglass or unknown, 2.187 if wood
   
    W_fus_lb = 0.5257 * F_MG * F_NG * F_press * F_VT * F_matl * l_f_ft**0.3796 * (W_PL_LBS * N_z)**0.4863 * V_eqMax**2

    return W_fus_lb



def landing_gear_weight_lb(params: DesignParameters):
    # equation from gundlach
    F_lg = 0.04  # range from 0.03 - 0.06
    W_lg_lb = F_lg * N_to_lbf(params.weight.WTO)  # lb
    return W_lg_lb


def empennage_weight_lb(params: DesignParameters):
    #equation from Gundlach
    WA_emp = 0.5  #for composite tail, 0.8-1.2 for metal gen aviation, 3.5-8 for supersonic fighters
    W_HT = WA_emp * m2_to_ft2(params.empennage.S_h)
    W_VT = WA_emp * m2_to_ft2(params.empennage.S_v)
    W_emp = W_HT*math.cos**2(params.empennage.vtail_dihedral) + W_VT*math.sin**2(params.empennage.vtail_dihedral)
    return W_emp

def propulsion_weight_lb(params: DesignParameters):
    # equation from Gundlach
    F_nac = 0.06                     #0.055 for low bypass turbofan, 0.065 for high bypass turbofan
    F_fs = 0.692 # estimation for MALE single engine [torenbeek]
    E1 = 0.67 # estimation for Male single engine [torenbeek]
    T_max = N_to_lbf(params.engine.engine_max_thrust)   # lbf
    W_nacelle_lb = F_nac*T_max                  #lbf
    W_fuel_system_lb = F_fs * N_to_lbf(params.weight.W_F)**E1  # lbf
    #W_ai = air induction system?
    W_propulsion_lb = W_nacelle_lb + N_to_lbf(params.engine.engine_weight) + W_fuel_system_lb  # lbf
    return W_propulsion_lb

#fixed equipment weight estimation

def fixed_equipment_weight_lb(params: DesignParameters):
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
    W_FCS = F_FCS * m2_to_ft2(params.control_surface.S_a) * params.max_eq_velocity**2 
    W_fixed_equipment_lb = W_avion + W_FCS
    return W_fixed_equipment_lb



