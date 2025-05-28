import numpy as np

#ADVANCED AIRCRAFT DESIGN
#   - PROPULSION INTEGRATION
#       - L.17 PROPELLER SLIPSTREAM EFFECTS: Not relevant
#       - L.18 Engine Intakes: Relevant
#       - L.19 Exhaust & Thrust reversers: Relevant
#       - L.20 Wing integration: Relevant

#High-speed design requirements:
#MFR (mass flow ratio) <=1
#Super velocities outside intake critical
#Cross section engine flow indep. inlet shape
#Mass flow varies w/ engine setting, altitude & airspeed
#Intake area closely to req. mass flow
#Extern. cowling shd. prevent shock waves
#    
#Design conditions:
#Stream tube diameter <= throat diameter
#Typical mach 0.85: thicker engine
#Typical mach 0.98: Thin lip/low external curvature
#    
#Low-speed design requirements:  
#MFR > 1.0
#Highest super velocities near throat area
#Velocity distribution over throat area ot uniform
#M_TH > 0.8 -> large decrease in tot. press. recov. & efficiency
#Max. M_TH is crit. at low speed due req. engine mass flow largest @ take-off & init. climb
#Ave. limited M_TH < 0.8 to prevent shock waves


#One dimensional isentropic flow relation:
#Note:  High mf (given A_TH) leads to high throat Mach numbers
#       M_TH <= 1
#       If M_TH > 0.8 -> shock waves/total press. loss

m_dot = 0
T_TO = 7000 # Take-off thrust in N
p_T = 0
M_TH = 0
gamma = 1.4
R = 287
A_INF = 0
A_HL = 0

# MFR = A_INF / A_HL
# The formula for A_TH was causing a runtime error due to (1-gamma) in the exponent.
# For a typical turbojet/turbofan, this part of the formula might be different or M_TH is usually less than 1.
# A_TH = m_dot * np.sqrt(T_T) / p_T * (M_TH*(1+(gamma-1)/2*M_TH**2)**((gamma+1)/(2*(1-gamma)))*np.sqrt(gamma/R))**(-1)
# Placeholder for A_TH to avoid error if not directly used in this modification:
A_TH = 0


#Fuselage-mounted: align intake with local flow (upwash)

#Nozzle function:
#   - Convert energy into kinetic energy through expansion
m_e_dot = 0
V_e = 0
V_INF = 0
A_e = 0 # exhaust area
p_e = 0
p_0 = 0 # back pressure

T = m_e_dot * (V_e - V_INF) + A_e * (p_e - p_0)

#Exhaust efficiency coefficients:
F_actual = 0
m_dot_actual = 0
V_actual = F_actual / m_dot_actual if m_dot_actual != 0 else 0
V_ideal = 0
m_dot_ideal = 0
C_V = V_actual / V_ideal if V_ideal != 0 else 0
C_D = m_dot_actual / m_dot_ideal if m_dot_ideal != 0 else 0

#Nozzle thrust coefficient:
C_T = C_V * C_D
#Turbofan:
F_actual_fancore = 0
F_ideal_fan = 0
F_ideal_core = 0
C_T_tf = F_actual_fancore / (F_ideal_fan + F_ideal_core) if (F_ideal_fan + F_ideal_core) != 0 else 0

# #Case: un-choked nozzle, p_0/p_T > 0.528 (cold flow) or p_T / p_0 < 1.89
# # p_T = 0 # stagnation pressure - already defined earlier, commented out to avoid redefinition
# V_ideal_unchoked = 0
# if p_T != 0: # Avoid division by zero or calculations with uninitialized p_T
#     V_ideal_unchoked = np.sqrt(2*gamma*R*T_T/(gamma-1)*(1-(p_0/p_T)**((gamma-1)/gamma))) if (gamma-1) !=0 and T_T !=0 else 0
# m_dot_ideal_unchoked = 0
# if R*T_T != 0 and p_T != 0: # Avoid division by zero
#     m_dot_ideal_unchoked = A_e * p_T * np.sqrt(2*gamma/(gamma-1)*1/(R*T_T)*((p_0/p_T)**(2/gamma)-(p_0/p_T)**((gamma+1)/gamma))) if (gamma-1) !=0 else 0


# #Case: choked nozzle, p_0/p_T < 0.528 (cold flow) or
# V_ideal_choked = np.sqrt(2*gamma*R*T_T/(gamma-1)) if (gamma-1) !=0 else 0 # Corrected to use V_ideal_choked
# m_dot_ideal_choked = 0
# if R*T_T != 0: # Avoid division by zero
#     m_dot_ideal_choked = (2*gamma/(gamma+1))**((gamma+1)/(2*(gamma-1)))*A_e*p_T*np.sqrt(gamma/(R*T_T)) if (gamma-1) !=0 else 0


#Lower nozzle area results in lower discharge coefficient/higher NPR for same thrust requirement.
#Shorter core exhaust -> reduced total press. drop & reduced scrubbing drag

#Noise damping:
#   - Chevrons (no thrust loss, smaller cowling, mixing fan with external flow)
#   - Mixing core flow with fan flow
#   - Convoluted mixers

#Thrust reversing: reduce brake wear/decrease ground roll distance under special circumstances.
#Inlet-Fan Cowl-Reverser-Core Nozzle-Pylon
#Target type: slide 57

Engines_W = ["FJ44-1AP","FJ44-3AP","FJ44-4A","FJ33-5A"] #Engine Type
Weight_W = [212.3,234.1,304,144.7] #Engine Weight (kg)
m_dot_W = [] #Unused in this modification, kept as is
Thrust_W = [9340,13340,16010,8230] #Engine Thrust (N)
TSFC_W = [0.4332,0.46,0.4,0.486] #Engine SFC (g/KN/s)
Conversion_factor = 13.77/0.486 #Unused in this modification, kept as is
#Convert TSFC to g/kN/s for all the engines
TSFC_W = [tsfc * Conversion_factor for tsfc in TSFC_W]  # Convert TSFC to g/kN/s


#Create thrust ranges for which different engines are suitable
def get_engine_for_thrust(T_TO):
    if T_TO < 7500:
        return "FJ33-5A"
    elif 7500 <= T_TO < 9000:
        return "FJ44-1AP"
    elif 9000 <= T_TO < 12000:
        return "FJ44-3AP"
    else: # T_TO >= 12000
        return "FJ44-4A"

#Engine selection based on thrust requirements
def select_engine(T_TO):
    engine_name = get_engine_for_thrust(T_TO)
    try:
        index = Engines_W.index(engine_name)
        return {
            "engine": engine_name,
            "weight": Weight_W[index],
            "thrust": Thrust_W[index], # Max thrust of the engine
            "tsfc": TSFC_W[index]
        }
    except ValueError:
        # This case should ideally not be reached if get_engine_for_thrust maps to Engines_W
        print(f"Error: Engine {engine_name} not found in the database.")
        return None

#Calculate fuel burn in kg/hr
def calculate_fuel_burn_kghr(tsfc_g_kN_s, thrust_N):
    thrust_kN = thrust_N / 1000.0
    fuel_burn = tsfc_g_kN_s * thrust_kN * 3.6 # (g/kN/s) * kN * (kg/1000g) * (3600s/hr) = kg/hr
    return fuel_burn

#give prompt asking for take-off thrust and then gives the engine selection
def main():
    try:
        T_TO = float(input("Enter the required take-off thrust (N): "))
        if T_TO <= 0:
            print("Required take-off thrust must be positive.")
            return

        print("\n--- Initial Engine Selection (based on predefined ranges) ---")
        engine_selection = select_engine(T_TO)

        if engine_selection:
            print(f"Recommended Engine: {engine_selection['engine']}")
            print(f"  Weight: {engine_selection['weight']} kg")
            print(f"  Max Thrust: {engine_selection['thrust']} N")
            print(f"  TSFC: {engine_selection['tsfc']} g/kN/s")

            if engine_selection['thrust'] >= T_TO:
                fuel_burn_selected = calculate_fuel_burn_kghr(engine_selection['tsfc'], T_TO)
                print(f"  Calculated take-off fuel burn at {T_TO:.0f} N: {fuel_burn_selected:.2f} kg/hr")
            else:
                print(f"  Warning: Recommended engine's max thrust ({engine_selection['thrust']} N) is less than required thrust ({T_TO:.0f} N).")
        else:
            print("No engine could be recommended based on the input thrust and predefined ranges.")


        print("\n\n--- Engine Comparison (Fuel Burn at Required Take-off Thrust) ---")
        print(f"Calculating for a required take-off thrust of {T_TO:.0f} N:\n")

        found_suitable_engine = False
        for i in range(len(Engines_W)):
            engine_name = Engines_W[i]
            max_thrust_N = Thrust_W[i]
            tsfc_val = TSFC_W[i]
            weight_kg = Weight_W[i]

            print(f"Engine: {engine_name}")
            print(f"  Max Thrust: {max_thrust_N} N")
            print(f"  Weight: {weight_kg} kg")
            print(f"  TSFC: {tsfc_val} g/kN/s")

            if max_thrust_N >= T_TO:
                fuel_burn = calculate_fuel_burn_kghr(tsfc_val, T_TO)
                print(f"  Fuel burn at {T_TO:.0f} N: {fuel_burn:.2f} kg/hr")
                found_suitable_engine = True
            else:
                print(f"  Not powerful enough to provide {T_TO:.0f} N of thrust.")
            print("-" * 20) # Separator

        if not found_suitable_engine:
            print(f"\nNo engine in the list is capable of providing the required take-off thrust of {T_TO:.0f} N.")

    except ValueError:
        print("Invalid input. Please enter a numeric value for thrust.")

#Take-off thrust -> required thrust engine -> required engines -> compare cruise efficiency (Either lower setting higher performance or full setting lower performance)
if __name__ == "__main__":
    main()