import math
import numpy as np
import matplotlib.pyplot as plt
import os

def determine_payload_weight():
    W_PL_lst = [300, 600, 850, 1100] # kg
    W_PL = W_PL_lst[1]
    print(f"Payload weight: {W_PL:.2f} kg")
    return W_PL

def guess_takeoff_weight():
    W_TO = 3700 # kg
    print(f"Take-off weight: {W_TO:.2f} kg")
    return W_TO

def determine_fuel_weight(W_TO):
    # Constants for cruise
    R_cruise = 7000e3         # m
    V_cruise = 240          # m/s
    L_D_cruise = 15
    c_j_cruise = 0.685/3600       # lbs/lbs/hr
    # Constants for loiter
    L_D_loiter = 17
    c_j_loiter = 0.75*0.685/3600
    E_loiter = 2*3600
    # Fuel fractions for different mission profiles
    W5_W4 = 1 / np.exp((R_cruise * c_j_cruise) / (V_cruise * L_D_cruise))
    W6_W5 = 1/ np.exp((E_loiter * c_j_loiter) / (L_D_loiter))
    fuel_fractions = {1: 0.99, 2: 0.99, 3: 0.99, 4: 0.98, 5: W5_W4, 6: W6_W5, 7: 0.99, 8: 0.995}
    M_ff = math.prod(fuel_fractions.values())
    W_F_used = (1 - M_ff) * W_TO
    W_F = W_F_used * 1.05
    print(f"Fuel weight: {W_F:.2f} kg")
    return W_F

def determine_empty_weight(W_TO, W_F, W_PL):
    W_tfo = 0
    W_crew = 0
    W_OE_tent = W_TO - W_F - W_PL
    W_E_tent = W_OE_tent - W_tfo - W_crew
    A = 0.3765
    B = 227.795
    W_E = A * W_TO + B
    error = W_E - W_E_tent
    print(f"Interpolated empty weight: {W_E:.2f} kg")
    print(f"Tentative empty weight: {W_E_tent:.2f} kg")
    print(f"Error: {error:.2f} kg")
    return W_E, W_E_tent, error

def estimate_wing_area_and_thrust(W_TO):
    V_stall = 61 * 0.514444
    rho_cruise = 0.4135
    rho_TO = 1.225
    rho_L = 1.225
    C_L_max = 1.8
    C_L_max_TO = 2.0
    C_L_max_L = 2.2
    W_S = 0.5 * V_stall ** 2 * rho_cruise * C_L_max
    W_S_TO = 0.5 * V_stall ** 2 * rho_TO * C_L_max_TO
    W_S_L = 0.5 * V_stall ** 2 * rho_L * C_L_max_L
    S = W_TO / W_S
    S_TO = W_TO / W_S_TO
    S_L = W_TO / W_S_L
    print(f"Wing loading: {W_S:.2f} N/m^2")
    print(f"Wing loading (take-off): {W_S_TO:.2f} N/m^2")
    print(f"Wing loading (landing): {W_S_L:.2f} N/m^2")
    print(f"Wing area: {S:.2f} m^2")
    T_W = W_S_TO / (C_L_max_TO * 1795.5)
    T_TO = T_W * W_TO * 9.81
    print(f"Take-off thrust: {T_TO:.2f} N")
    return S, T_TO

def plot_payload_range_diagram(W_TO, V_cruise, L_D_cruise, c_j_cruise):
    payload_weights = np.linspace(300, 1100, 10)
    ranges = []
    for W_PL in payload_weights:
        W_OE_tent = W_TO - W_PL
        W_F_tent = W_TO - W_OE_tent - W_PL
        M_ff = 1 - (W_F_tent / W_TO)
        R_cruise = V_cruise * L_D_cruise * np.log(1 / M_ff) / c_j_cruise
        ranges.append(R_cruise / 1e3)
    plt.figure(figsize=(10, 6))
    plt.plot(ranges, payload_weights, marker='o', label='Payload-Range Curve')
    plt.title('Payload-Range Diagram')
    plt.xlabel('Range (km)')
    plt.ylabel('Payload Weight (kg)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig('payload_range_diagram.pdf')
    plt.show()


if __name__ == "__main__":
    W_PL = determine_payload_weight()
    W_TO = guess_takeoff_weight()
    W_F = determine_fuel_weight(W_TO)
    W_E, W_E_tent, error = determine_empty_weight(W_TO, W_F, W_PL)
    S, T_TO = estimate_wing_area_and_thrust(W_TO)
    # Use cruise constants from fuel weight function for payload-range diagram
    V_cruise = 240
    L_D_cruise = 15
    c_j_cruise = 0.685/3600
    plot_payload_range_diagram(W_TO, V_cruise, L_D_cruise, c_j_cruise)
