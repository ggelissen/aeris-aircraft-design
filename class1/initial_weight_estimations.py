import math
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from config.design_variables import DesignParameters
from class1.thrust_wing_loading import run_performance_diagram
# --- Constants ---
G = 9.80665  # Gravity constant in m/s^2


# --- Aerodynamics: Drag Polar and L/D ---
def get_drag_polar_params(aircraft_type):
    """
    Returns typical C_D0 and Oswald efficiency 'e' for an aircraft type.
    Source: Page 35 [cite: 61] or can be estimated using C_fe and S_wet/S (Pages 31-33 [cite: 51, 52, 53, 55]).
    This is a simplified placeholder.
    """
    if aircraft_type == "uav":
        return 0.020, 0.80  # From page 35 of ADSEE I Lecture 2
    elif aircraft_type == "business_jet":
        return 0.017, 0.8  # From page 35 of ADSEE I Lecture 2
    print(f"Warning: Drag polar parameters for {aircraft_type} not defined. Using default.")
    return 0.025, 0.8 # Default placeholder values

def calculate_L_D_cruise_jet(C_D0, A, e):
    """
    Calculates L/D for jet aircraft for maximum V*(L/D) (best range).
    Source: Page 39 [cite: 68]
    (L/D)_cruise = (3/4) * sqrt((pi*A*e)/(3*C_D0))
    """
    if C_D0 <= 0: return float('inf') # Avoid division by zero
    return (3/4) * math.sqrt((math.pi * A * e) / (3 * C_D0))

def calculate_L_D_loiter(C_D0, A, e):
    """
    Calculates L/D for loiter (maximum L/D).
    This is the same formula as prop cruise for max L/D.
    Source: Page 37 [cite: 66] (for general max L/D)
    """
    if C_D0 <= 0: return float('inf')
    return math.sqrt((math.pi * A * e) / (4 * C_D0))


# --- Fuel Fractions ---
def get_statistical_fuel_fractions(aircraft_type, segment_name):
    """
    Returns statistical mission segment fuel fractions (Wi+1/Wi).
    Source: Page 22 [cite: 41]
    This is a simplified placeholder.
    """
    fractions = {
        "business_jet": {
            "eng_start_warmup": 0.990, "taxi_out": 0.995, "take_off": 0.995,
            "climb": 0.980, "descent": 0.990, "land_taxi_shutdown": 0.992
        },
        "uav": {
            "eng_start_warmup": 0.990, "taxi_out": 0.990, "take_off": 0.990,
            "climb": 0.980, "descent": 0.990, "land_taxi_shutdown": 0.995
        }
    }
    # Example mission segments from page 46 for the business jet
    uav_specific = {
        "M1_eng_start_warmup": 0.990,
        "M2_taxi_out": 0.990,
        "M3_take_off": 0.990,
        "M4_climb1": 0.980,
        # M5_cruise1 is calculated
        "M6_descent1": 0.990,
        "M7_climb2_reserve": 0.990,
        # M8_cruise2_reserve is calculated
        # M9_loiter_reserve is calculated
        "M10_descent2_reserve": 0.990,
        "M11_land_taxi_shutdown": 0.995,
    }
    if aircraft_type == "uav" and segment_name in uav_specific:
        return uav_specific[segment_name]

    try:
        return fractions[aircraft_type][segment_name]
    except KeyError:
        print(f"Warning: Fuel fraction for {aircraft_type}, {segment_name} not found. Using 1.0.")
        return 1.0

def calculate_cruise_fuel_fraction_jet(R_m, V_ms, L_D_cruise, c_j_kg_Ns):
    """
    Calculates cruise fuel fraction (W_end/W_start) for jet aircraft.
    Source: Page 23, 26 [cite: 43, 44, 45]
    M_cruise = exp(- (R * g * c_j) / (V * (L/D)))
    """
    if V_ms <= 0 or L_D_cruise <= 0: return 0 # Avoid division by zero or nonsensical result
    exponent = -(R_m * G * c_j_kg_Ns) / (V_ms * L_D_cruise)
    return math.exp(exponent)

def calculate_loiter_fuel_fraction_jet(E_s, L_D_loiter, c_j_kg_Ns):
    """
    Calculates loiter fuel fraction (W_end/W_start) for jet aircraft.
    Source: Based on endurance equation (similar to page 46 example [cite: 75, 76])
    M_loiter = exp(- (E * g * c_j) / (L/D))
    """
    if L_D_loiter <= 0: return 0
    exponent = -(E_s * G * c_j_kg_Ns) / L_D_loiter
    return math.exp(exponent)

# --- Weight Estimation ---
def get_empty_weight_coeffs(aircraft_type):
    """
    Returns coefficients 'a' and 'b' for W_E = a*W_TO + b.
    Source: Page 15 [cite: 26, 27]
    """
    if aircraft_type == "business_jet":
        return 0.5417, 579.96  # N, N/N
    elif aircraft_type == "uav":
        return 0.3765, 227.795  # N, N/N
    else:
        print(f"Warning: Coefficients for {aircraft_type} not defined. Using defaults.")
        return 0.5, 1000 # Default placeholder values

def class1_weight_estimation(
    aircraft_params, mission_params, reserve_params,
    verbose=True
):
    """
    Performs Class I weight estimation.
    aircraft_params: dict with "type", "A", "eta_p" (if prop), "c_j_kg_Ns" or "c_p_kg_J"
    mission_params: dict with "W_PL_N", "W_crew_N", "R_cruise1_m", "V_cruise_ms"
    reserve_params: dict with "type" ('fraction' or 'mission_extension'),
                     "M_res_fraction" (if type=='fraction'),
                     "R_cruise2_m", "E_loiter_s" (if type=='mission_extension')
    """
    ac_type = aircraft_params["type"]
    A = aircraft_params["A"] # Aspect Ratio
    M_tfo = aircraft_params.get("M_tfo", 0.001) # Trapped fuel and oil fraction [cite: 19]

    W_PL_N = mission_params["W_PL_N"]
    W_crew_N = mission_params["W_crew_N"]
    R_cruise1_m = mission_params["R_cruise1_m"]
    V_cruise_ms = mission_params["V_cruise_ms"]

    # --- 1. Calculate L/D ratios ---
    C_D0, oswald_e = get_drag_polar_params(ac_type)
    if "uav" in ac_type:
        A_winglet = A * 1.15 # Adjusted aspect ratio for UAVs with winglets
        #print(f"Aspect ratio normally {A}, using {A_winglet} for winglet effect.")
        L_D_cruise1 = calculate_L_D_cruise_jet(C_D0, A_winglet, oswald_e)
        L_D_loiter = calculate_L_D_loiter(C_D0, A_winglet, oswald_e) # Max L/D for loiter
        L_D_cruise2 = L_D_cruise1 # Assuming same L/D for alternate cruise
    else:
        raise ValueError(f"Unknown engine type for L/D calculation from aircraft_type: {ac_type}")

    if verbose:
        print(f"L/D Cruise1: {L_D_cruise1:.2f}, L/D Loiter: {L_D_loiter:.2f}")

    # --- 2. Calculate Mission Segment Fuel Fractions (M_i = W_i+1 / W_i) ---

    mission_segments_ff = [] # list of (name, M_i)

    if ac_type == "uav":
        m_s = get_statistical_fuel_fractions
        mission_segments_ff.extend([
            ("M1_eng_start_warmup", m_s(ac_type, "M1_eng_start_warmup")),
            ("M2_taxi_out", m_s(ac_type, "M2_taxi_out")),
            ("M3_take_off", m_s(ac_type, "M3_take_off")),
            ("M4_climb1", m_s(ac_type, "M4_climb1"))
        ])
        M5_cruise1 = calculate_cruise_fuel_fraction_jet(
            R_cruise1_m, V_cruise_ms, L_D_cruise1, aircraft_params["c_j_kg_Ns"]
        )
        mission_segments_ff.append(("M5_cruise1", M5_cruise1))
        mission_segments_ff.append(("M6_descent1", m_s(ac_type, "M6_descent1")))

        # Reserve mission segments (if applicable, these contribute to total M_ff for direct W_TO calc)
        if reserve_params["type"] == "mission_extension":
            mission_segments_ff.append(("M7_climb2_reserve", m_s(ac_type, "M7_climb2_reserve")))
            M8_cruise2_reserve = calculate_cruise_fuel_fraction_jet(
                reserve_params["R_cruise2_m"], V_cruise_ms, L_D_cruise2, aircraft_params["c_j_kg_Ns"]
            )
            mission_segments_ff.append(("M8_cruise2_reserve", M8_cruise2_reserve))
            M9_loiter_reserve = calculate_loiter_fuel_fraction_jet(
                reserve_params["E_loiter_s"], L_D_loiter, aircraft_params["c_j_kg_Ns"]
            )
            mission_segments_ff.append(("M9_loiter_reserve", M9_loiter_reserve))
            mission_segments_ff.append(("M10_descent2_reserve", m_s(ac_type, "M10_descent2_reserve")))

        mission_segments_ff.append(("M11_land_taxi_shutdown", m_s(ac_type, "M11_land_taxi_shutdown")))


    # --- 3. Calculate Overall Mission Fuel Fraction (M_ff_total = W_final / W_initial_total_mission) ---
    M_ff_total = 1.0
    for name, val in mission_segments_ff:
        M_ff_total *= val
        if verbose: print(f"Segment {name}: M_i = {val:.4f}")

    if verbose: print(f"Overall M_ff_total (W_final/W_TO for all segments): {M_ff_total:.4f}")

    # --- 4. Estimate Take-off Weight (W_TO) ---
    # W_TO = W_E + W_F + W_PL_total + W_tfo
    # W_E = a*W_TO + b
    # W_PL_total = W_PL_N + W_crew_N
    # W_tfo = M_tfo * W_TO
    # W_F = W_F_used + W_F_reserves

    a_coeff, b_const = get_empty_weight_coeffs(aircraft_params["type_for_coeffs"]) # Use specific key for coeffs

    # If reserves are by mission extension, they are already in M_ff_total.
    # W_F_total / W_TO = (1 - M_ff_total)
    # W_TO = (a*W_TO + b) + (1 - M_ff_total)*W_TO + (W_PL_N + W_crew_N) + M_tfo*W_TO
    # W_TO * (1 - a - (1 - M_ff_total) - M_tfo) = b + W_PL_N + W_crew_N
    # W_TO = (b + W_PL_N + W_crew_N) / (1 - a - (1 - M_ff_total) - M_tfo)

    W_PL_plus_crew = W_PL_N + W_crew_N
    
    fuel_term_coeff_of_W_TO = 0
    if reserve_params["type"] == "mission_extension" or ac_type == "uav":
        fuel_term_coeff_of_W_TO = (1.0 - M_ff_total)
    else:
        raise ValueError("Unsupported reserve type or aircraft combination for fuel term calculation.")

    denominator = 1.0 - a_coeff - fuel_term_coeff_of_W_TO - M_tfo
    
    if abs(denominator) < 1e-6 : # Avoid division by zero / unstable solution
        print("Error: Denominator in W_TO calculation is too small. Check inputs.")
        return None

    W_TO_N = (b_const + W_PL_plus_crew) / denominator

    # --- 5. Calculate other weights ---
    W_E_N = a_coeff * W_TO_N + b_const
    W_tfo_N = M_tfo * W_TO_N
    W_F_total_N = fuel_term_coeff_of_W_TO * W_TO_N
    W_OE_N = W_E_N + W_tfo_N + W_crew_N

    W_F_used_N = None
    W_F_res_N = None

    if ac_type == "uav" and reserve_params["type"] == "mission_extension":
        # Calculate M_ff for nominal mission (segments 1-6 and 11)
        M_ff_nominal = 1.0
        nominal_segments_keys = ["M1_eng_start_warmup", "M2_taxi_out", "M3_take_off",
                                 "M4_climb1", "M5_cruise1", "M6_descent1", "M11_land_taxi_shutdown"]
        temp_idx_segments = {name: val for name, val in mission_segments_ff}
        for key in nominal_segments_keys:
            if key in temp_idx_segments:
                 M_ff_nominal *= temp_idx_segments[key]
            else:
                if key == "M5_cruise1": M_ff_nominal *= M5_cruise1 
        
        W_F_used_N = (1.0 - M_ff_nominal) * W_TO_N
        W_F_res_N = W_F_total_N - W_F_used_N


    results = {
        "W_TO": W_TO_N,
        "W_E": W_E_N,
        "W_F": W_F_total_N,
        "W_OE": W_OE_N,
        "W_PL": W_PL_N, "W_crew": W_crew_N,
        "W_tfo": W_tfo_N,
        "M_ff": M_ff_total,
        "L_D_cruise": L_D_cruise1,
        "L_D_loiter": L_D_loiter,
        "W_F_used": W_F_used_N,
        "W_F_res": W_F_res_N,
    }

    if verbose:
        print(f"\n--- Results ---")
        print(f"Take-off Weight (W_TO): {W_TO_N:.2f} N ({N_to_kg(W_TO_N):.2f} kg)")
        print(f"Empty Weight (W_E): {W_E_N:.2f} N ({N_to_kg(W_E_N):.2f} kg)")
        print(f"Total Fuel Weight (W_F_total): {W_F_total_N:.2f} N ({N_to_kg(W_F_total_N):.2f} kg)")
        if W_F_used_N is not None:
            print(f"  Used Fuel (W_Fused): {W_F_used_N:.2f} N")
        if W_F_res_N is not None:
            print(f"  Reserve Fuel (W_Fres): {W_F_res_N:.2f} N")
            if W_F_used_N > 0: print(f"  M_res (W_Fres/W_Fused): {W_F_res_N/W_F_used_N if W_F_used_N else 0:.3f}")
        print(f"Operating Empty Weight (W_OE): {W_OE_N:.2f} N ({N_to_kg(W_OE_N):.2f} kg)")
        print(f"Payload Weight (W_PL): {W_PL_N:.2f} N")
        print(f"Crew Weight (W_crew): {W_crew_N:.2f} N")

    # Sanity Check from example on page 42 [cite: 77]
    # W_TO = a*W_TO + b + (1-M_ff_total)*W_TO + W_PL_plus_crew + M_tfo*W_TO
    # W_TO_check_coeff = a_coeff + (1-M_ff_total) + M_tfo if reserve_params["type"] == "mission_extension" else a_coeff + (1-M_ff_total)*(1+reserve_params["M_res_fraction"]) + M_tfo
    # W_TO_check = W_TO_check_coeff * W_TO_N + b_const + W_PL_plus_crew
    # print(f"Sanity Check: W_TO components sum: {W_E_N + W_F_total_N + W_PL_N + W_crew_N + W_tfo_N:.2f} (should be W_TO)")


    return results

# --- Payload-Range Diagram ---
def calculate_payload_range_points(design_results, aircraft_params, mission_segments_config, W_P_max_structural_N, W_F_max_capacity_N, num_points=10):
    """
    Calculates points for a payload-range diagram.
    Source: Based on procedure from Page 64 [cite: 105]
    mission_segments_config: defines how to calculate M_pre_cruise, M_post_cruise_total, K_cruise
    """
    print("\n--- Payload-Range Diagram Calculation (Simplified) ---")
    W_MTO_design = design_results["W_TO_N"]
    W_OE_N = design_results["W_OE_N"] # This is W_E + W_tfo + W_crew

    # These need to be defined based on the mission profile structure
    # M_pre_cruise: Product of M_i for segments before main cruise (e.g., M1*M2*M3*M4)
    # M_post_cruise_total: Product of M_i for all segments after main cruise until landing (e.g., M6*M7*M8*M9*M10*M11 for business jet example)
    # K_cruise_factor: (V / (g*cj)) * L_D for jet, or (eta_p / (g*cp)) * L_D for prop
    
    m_s_ff = dict(design_results["mission_segments_detailed_ff"])
    
    M_pre_cruise = m_s_ff.get("M1_eng_start_warmup",1) * m_s_ff.get("M2_taxi_out",1) * \
                   m_s_ff.get("M3_take_off",1) * m_s_ff.get("M4_climb1",1)

    M_post_cruise_total = m_s_ff.get("M6_descent1",1) * m_s_ff.get("M7_climb2_reserve",1) * \
                          m_s_ff.get("M8_cruise2_reserve",1) * m_s_ff.get("M9_loiter_reserve",1) * \
                          m_s_ff.get("M10_descent2_reserve",1) * m_s_ff.get("M11_land_taxi_shutdown",1)
                          
    V_cruise_ms = mission_segments_config["V_cruise_ms"] # Assuming passed in a suitable config
    L_D_cruise = design_results["L_D_cruise1"]

    if "uav" in aircraft_params["type"]:
        c_j = aircraft_params["c_j_kg_Ns"]
        K_cruise_factor = (V_cruise_ms / (G * c_j)) * L_D_cruise if (G * c_j) != 0 else float('inf')
    else:
        K_cruise_factor = float('inf')

    payload_range_data = []

    # Point 1: Max structural payload, MTOW = design MTOW
    W_P_N = W_P_max_structural_N
    current_W_TO = W_MTO_design
    
    W4 = current_W_TO * M_pre_cruise
    # W_OE_N for P-R should be W_E_structural + W_tfo + W_crew.
    # Assuming W_OE_N from design results is appropriate (i.e., crew weight fixed, W_E structural based on W_MTO_design)
    W5_num = W_OE_N + W_P_N
    W5_den = M_post_cruise_total
    
    if W5_num <=0 or W5_den <= 0 or W4/ (W5_num/W5_den) <=1 : R_m = 0
    else: R_m = K_cruise_factor * math.log(W4 / (W5_num / W5_den)) if K_cruise_factor != float('inf') else 0
    payload_range_data.append({"W_P_kg": N_to_kg(W_P_N), "R_km": m_to_km(max(0,R_m)), "Segment": "Max Payload"})
    print(f"P-R Point (Max Payload): W_P={N_to_kg(W_P_N):.0f} kg, R={m_to_km(max(0,R_m)):.0f} km")

    # Point 2: Design Payload (should match original calculation if W_P_max_structural_N is design payload)
    W_P_N = design_results["W_PL_N"] # Design Payload
    current_W_TO = W_MTO_design
    W4 = current_W_TO * M_pre_cruise
    W5_num = W_OE_N + W_P_N
    if W5_num <=0 or W5_den <= 0 or W4/ (W5_num/W5_den) <=1 : R_m = 0
    else: R_m = K_cruise_factor * math.log(W4 / (W5_num / W5_den)) if K_cruise_factor != float('inf') else 0
    payload_range_data.append({"W_P_kg": N_to_kg(W_P_N), "R_km": m_to_km(max(0,R_m)), "Segment": "Design Point"})
    print(f"P-R Point (Design): W_P={N_to_kg(W_P_N):.0f} kg, R={m_to_km(max(0,R_m)):.0f} km (Original R_design: {m_to_km(mission_segments_config['R_cruise1_m']):.0f} km)")


    # Point 3: Ferry Range (Zero Payload, MTOW limited by fuel capacity OR design MTOW)
    W_P_N = 0 # Zero Payload
    # Option A: Tanks full, W_TO = W_OE + W_F_max_capacity
    # This W_TO must be <= W_MTO_design
    current_W_TO_ferry_fuel_limited = W_OE_N + W_F_max_capacity_N
    current_W_TO = min(current_W_TO_ferry_fuel_limited, W_MTO_design)

    W4 = current_W_TO * M_pre_cruise
    W5_num = W_OE_N + W_P_N # W_P_N is 0
    if W5_num <=0 or W5_den <= 0 or W4/ (W5_num/W5_den) <=1 : R_m = 0
    else: R_m = K_cruise_factor * math.log(W4 / (W5_num / W5_den)) if K_cruise_factor != float('inf') else 0
    payload_range_data.append({"W_P_kg": N_to_kg(W_P_N), "R_km": m_to_km(max(0,R_m)), "Segment": "Ferry Range"})
    print(f"P-R Point (Ferry): W_P={N_to_kg(W_P_N):.0f} kg, R={m_to_km(max(0,R_m)):.0f} km (W_TO={N_to_kg(current_W_TO):.0f} kg)")

    # Additional points for the curve (payload trade-off with full tanks)
    # Iterate payload from design down to zero, assuming tanks are full up to W_MTO_design
    payload_steps = [design_results["W_PL_N"] * f for f in [0.75, 0.5, 0.25]]
    for W_P_step_N in payload_steps:
        if W_P_step_N < 0: continue
        # W_TO is W_OE + W_P + W_F_max, capped at W_MTO_design
        current_W_TO_step = min(W_OE_N + W_P_step_N + W_F_max_capacity_N, W_MTO_design)
        W4_step = current_W_TO_step * M_pre_cruise
        W5_num_step = W_OE_N + W_P_step_N
        
        if W5_num_step <=0 or W5_den <= 0 or W4_step / (W5_num_step/W5_den) <=1 : R_m_step = 0
        else: R_m_step = K_cruise_factor * math.log(W4_step / (W5_num_step / W5_den)) if K_cruise_factor != float('inf') else 0
        
        payload_range_data.append({"W_P_kg": N_to_kg(W_P_step_N), "R_km": m_to_km(max(0,R_m_step)), "Segment": "Fuel Capacity Limited"})
        print(f"P-R Point (Fuel Ltd): W_P={N_to_kg(W_P_step_N):.0f} kg, R={m_to_km(max(0,R_m_step)):.0f} km (W_TO={N_to_kg(current_W_TO_step):.0f} kg)")
        
    return sorted(payload_range_data, key=lambda x: x["W_P_kg"], reverse=True)



# --- Plot Payload-Range Diagram ---
def plot_payload_range_diagram(pr_data, export_path=None):
    """
    Plots the payload-range diagram from a list of dicts with keys 'W_P_kg' and 'R_km'.
    If export_path is given, saves the figure to that path.
    Adds a label for the design point.
    """
    payloads = [pr_data[0]['W_P_kg']] + [point['W_P_kg'] for point in pr_data]
    ranges = [0] + [point['R_km'] for point in pr_data]
    segments = [point['Segment'] for point in pr_data]
    plt.figure(figsize=(8, 4))
    plt.plot(ranges, payloads, marker='o', label='Payload-Range Curve')
    # Add label for the design point
    for r, p, s in zip(ranges[1:], payloads[1:], segments):
        if s == 'Design Point':
            plt.annotate('Design Point', (r, p), textcoords="offset points", xytext=(25,5), ha='left', fontsize=11, fontweight='bold', color='k', arrowprops=dict(arrowstyle='->', color='k'))
    plt.xlabel('Range (km)')
    plt.ylabel('Payload Weight (kg)')
    plt.ylim(0, max(payloads) * 1.1)
    plt.xlim(0, max(ranges) * 1.05)
    plt.grid(True)
    plt.tight_layout()
    if export_path:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        plt.savefig(export_path)


def run_initial_weight_estimations(params: DesignParameters) -> dict:
    """
    Runs the initial weight estimation.
    """

    uav_aircraft_params = {
        "type": "uav",
        "type_for_coeffs": "uav",
        "A": params.wing.A_w_target,
        "c_j_kg_Ns": lb_hr_lbf_to_kg_Ns(params.engine.cruise_tsfc),
        "M_tfo": params.weight.M_tfo
    }
    uav_mission_params = {
        "W_PL_N": params.weight.W_PL,
        "W_crew_N": params.weight.W_crew,
        "R_cruise1_m": params.range,
        "V_cruise_ms": params.cruise_speed
    }
    uav_reserve_params = {
        "type": "mission_extension",
        "R_cruise2_m": params.diversion_distance,
        "E_loiter_s": params.loiter_time
    }

    results = class1_weight_estimation(uav_aircraft_params, uav_mission_params, uav_reserve_params, verbose=False)

    return results


if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")
    results = run_initial_weight_estimations(params)
    print(results)