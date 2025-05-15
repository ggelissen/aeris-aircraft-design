import math
import numpy as np

# Based on Part II "Preliminary Configuration Design and Integration of the Propulsion System" by Roskam
# For manned aircraft, use "5. Business Jet"
# For unmanned aircraft, use "8. Military Trainers"


########################## Chapter 6: Class I Method for Wing Planform Design and for Sizing and Locating Lateral Control Surfaces ##########################

# Wing Geometric Data

dihedral = 1.0          # degrees
incidence = 1.0         # degrees
aspect_ratio = 8.0
sweep = 25.0            # degrees
wing_type = "mid"       # "high", "shoulder", "mid", "low"
tip_chord = 0.642       # m
root_chord = 1.487      # m
taper_ratio = tip_chord / root_chord
wing_thickness = 0.14
tau_w = 1.0

# Calculate wing fuel volume
#V_WF = 0.54((S**2)/b)(wing_thickness)((1+taper_ratio*tau_w**(0.5)+taper_ratio**2*tau_w)/(1+taper_ratio)**2)


########################## Chapter 7: Class I Method for Verifying Clean Airplane C_L_max and for Sizing High Lift Devices ##########################

# NOT FOR TRADE-OFF PROCESS


########################## Chapter 8: Class I Method for Empennage Sizing and Disposition and for Control Surface Sizing and Disposition ##########################




########################## Chapter 9: Class I Method for Landing Gear Sizing and Disposition ##########################







########################## Chapter 10: Class I Weight and Balance Analysis ##########################







########################## Chapter 11: Class I Method for Stability and Control Analysis ##########################







########################## Chapter 12: Class I Method for Drag Polar Determination ##########################


def calculate_drag_properties(inputs):

    W_TO, S, a, b, c, d = inputs
    W_TO_lb = W_TO * 2.20462  # Convert weight to pounds

    # Calculate the wetted surface area
    S_wet_lb = 10 ** (c + d * np.log10(W_TO_lb))
    S_wet = S_wet_lb / 10.764  # Convert from ft^2 to m^2

    # Calculate equivalent parasite area
    f_lb = 10 ** (a + b * np.log10(S_wet_lb))
    f = f_lb / 10.764  # Convert from ft^2 to m^2

    # Calculate zero-lift drag coefficient
    C_D0 = f / S

    return {"S_wet_lb": S_wet_lb, "S_wet": S_wet, "f_lb": f_lb, "f": f, "C_D0": C_D0}

# Example usage
if __name__ == "__main__":

    # Roskam Part I, p 122, Table 3.4/5 (c_f=0.0030, military trainer)
    UAV_Option = {"W_TO": 4000, "S": 11.0, "a": -2.5229, "b": 1.00000, "c": -1.1868, "d": 0.9609}

    # Roskam Part I, p 122, Table 3.4/5 (c_f=0.0030, business jet)
    Manned_Option = {"W_TO": 9500, "S": 25.0, "a": -2.5229, "b": 1.00000, "c": 0.2263, "d": 0.6977}

    results_UAV = calculate_drag_properties(list(UAV_Option.values()))
    results_Manned = calculate_drag_properties(list(Manned_Option.values()))

    print("UAV Option:")
    print(f"Wetted surface area: {results_UAV['S_wet_lb']:.2f} ft^2, {results_UAV['S_wet']:.2f} m^2")
    print(f"Equivalent parasite area: {results_UAV['f_lb']:.2f} ft^2, {results_UAV['f']:.2f} m^2")
    print(f"Zero-lift drag coefficient: {results_UAV['C_D0']:.4f}")

    print("\nManned Option:")
    print(f"Wetted surface area: {results_Manned['S_wet_lb']:.2f} ft^2, {results_Manned['S_wet']:.2f} m^2")
    print(f"Equivalent parasite area: {results_Manned['f_lb']:.2f} ft^2, {results_Manned['f']:.2f} m^2")
    print(f"Zero-lift drag coefficient: {results_Manned['C_D0']:.4f}")