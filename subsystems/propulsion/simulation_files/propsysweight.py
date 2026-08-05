from math import sqrt, nan, isnan # Added nan, isnan for handling potential NaN values
import sys # For potential path debugging
import os  # For potential path debugging4
import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from utils.unit_conversions import *    
from config.design_variables import DesignParameters

    # Propulsion System Weight Calculation
def calculate_propulsion_system_weight(params: DesignParameters):
    lbs_to_kg = 0.45359237
    kg_to_lbs = 1 / lbs_to_kg
    n_to_lbf = 0.224809
    m_to_ft = 3.28084# Convert units
    #newtons to lbs
    N_to_lbf = 1 / n_to_lbf  # Convert newtons to pounds-force


    We = 516 #lbs, engine weight
    We_kg = We * lbs_to_kg  # convert to kg
    T_to = params.engine.T_TO * n_to_lbf  #lbf, thrust takeoff
    L_d = 7.28 #duct lenght, ft
    Kd = 1 #curved duct
    A_inl = 9.5 #inlet area, ft^2

    # W_ai = 11.45*(L_d*Kd*A_inl**0.5)**0.7331
    # W_ai_kg = W_ai * lbs_to_kg  # convert to kg

    Ksp = 6.47 #lbs/gal (density of Jet A-1)
    W_fuel = 8589/9.81  * kg_to_lbs # fuel weight in lbs
    W_fs = (0.4/Ksp) * W_fuel  # lbs, fuel system weight
    W_fs_kg = W_fs * lbs_to_kg  # convert to kg
    print(f"Fuel System Weight: {W_fs:.2f} lbs / {W_fs_kg:.2f} kg")


    L_fus = 10*m_to_ft  # fuselage length in ft
    Kec = 0.686
    W_ec = Kec *(L_fus**0.792) #Engine control weight in lbs
    W_ess = 38 #lbs, engine starter system weight

    W_nacelle = 0.065*T_to  # lbs, nacelle weight
    W_nacelle_kg = W_nacelle * lbs_to_kg  # convert to kg

    W_prop_sys = We + W_fs + W_ec + W_ess + W_nacelle  # total propulsion system weight in lbs
    W_prop_sys_kg = W_prop_sys * lbs_to_kg  # convert to kg

    #weight includes, engine, starter, fuel system, air induction systems and nacelle
    # nacelle weight includes pylon weight
    print(f"Propulsion System Weight: {W_prop_sys:.2f} lbs / {W_prop_sys_kg:.2f} kg")
    #print engine starter weight
    #print(f"Engine Starter System Weight: {W_ess:.2f} lbs / {W_ess_kg:.2f} kg")
    #print nacelle weight
    print(f"Nacelle Weight: {W_nacelle:.2f} lbs / {W_nacelle_kg:.2f} kg")

    W_electrical = 149 # kg, electrical system weight
    W_electrical_lbs = W_electrical * kg_to_lbs  # convert to lbs
    print(f"Electrical System Weight: {W_electrical_lbs:.2f} lbs / {W_electrical:.2f} kg")

    return {
        'propulsion_system_weight_kg': W_prop_sys_kg,
        'engine_weight_kg': We_kg,
        'fuel_system_weight_kg': W_fs_kg,
        'engine_control_weight_kg': W_ec * lbs_to_kg,
        'engine_starter_weight_kg': W_ess * lbs_to_kg,
        'nacelle_weight_kg': W_nacelle_kg,
        'electrical_system_weight_kg': W_electrical
    }

#run the function if this script is executed directly
if __name__ == "__main__":
    params = DesignParameters()
    propulsion_weights = calculate_propulsion_system_weight(params)
    pprint.pprint(propulsion_weights)
    # Uncomment the following line to see the design parameters
    # pprint.pprint(vars(params))
