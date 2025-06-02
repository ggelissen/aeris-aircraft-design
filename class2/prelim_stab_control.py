import math
import numpy as np
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from design_variables import DesignParameters
from utils.unit_conversions import *

# Using Arial font
plt.rcParams['font.family'] = 'Arial'


def calculate_lift_coefficient_tail(A_h: float, type: str) -> float:
    """
    Calculate the lift coefficient for the horizontal tail based on its aspect ratio and type.

    Parameters:
    A_h (float): Aspect ratio of the horizontal tail.
    type (str): Type of the horizontal tail. Options are 'full moving', 'adjustable', or 'fixed'.

    Returns:
    float: Lift coefficient for the horizontal tail.
    """
    if type == 'full moving':
        return -1
    elif type == 'adjustable':
        return -0.8
    elif type == 'fixed':
        return -0.35 * (A_h ** (1/3))
    else:
        raise ValueError("Invalid tail type. Choose from 'full moving', 'adjustable', or 'fixed'.")


def calculate_Mach_correction_factor(M: float) -> float:
    """
    Calculate the Mach correction factor based on the Mach number.

    Parameters:
    M (float): Mach number.

    Returns:
    float: Mach correction factor.
    """
    return math.sqrt(1 - M**2)


def calculate_lift_slope(A: float, beta: float, Lambda_05c: float, eta: float) -> float:
    """
    Calculate the lift coefficient slope based on the aspect ratio, beta, sweep angle, and eta.

    Parameters:
    A (float): Aspect ratio.
    beta (float): Mach correction factor.
    Lambda_05c (float): Sweep angle at 0.5c in radians.
    eta (float): Efficiency factor.

    Returns:
    float: Lift coefficient slope.
    """
    return (2 * math.pi * A) / (2 + math.sqrt(4 + ((A * beta / eta) ** 2) * (1 + (math.tan(Lambda_05c) ** 2) / (beta ** 2))))


def calculate_net_surface_area(S: float, c_r: float, bf: float) -> float:
    """
    Calculate the net surface area of the wing after accounting for the fuselage.

    Parameters:
    S (float): Total wing surface area.
    c_r (float): Root chord length.
    bf (float): Fuselage width.

    Returns:
    float: Net surface area of the wing.
    """
    return S - c_r * bf


def calculate_lift_slope_less_tail(C_L_alpha_w: float, b_w: float, b_f: float, S_net: float, S: float) -> float:
    """
    Calculate the lift slope of the wing without considering the tail contribution.

    Parameters:
    C_L_alpha_w (float): Lift coefficient slope of the wing.
    b_w (float): Wing span.
    b_f (float): Fuselage width.
    S_net (float): Net surface area of the wing.
    S (float): Total wing surface area.

    Returns:
    float: Lift slope of the aircraft without tail contribution.
    """
    return C_L_alpha_w * (1 + (2.15 * b_f / b_w)) * (S_net / S) + (math.pi / 2 * b_f**2 / S)


def calculate_x_ac(x_ac_w: float, b_f: float, h_f: float, l_fn: float, b_n: float, 
                   l_n: float, C_L_alpha_Ah: float, S: float, c: float, cg: float, 
                   b: float, lam: float, Lambda: float) -> float:
    """
    Calculate the aerodynamic center of the aircraft.

    Parameters:
    x_ac_w (float): Aerodynamic center of the wing.
    b_f (float): Fuselage width.
    h_f (float): Fuselage height.
    l_fn (float): Distance from nose to start of wing.
    b_n (float): Width of nacelle.
    l_n (float): Length of nacelle.
    C_L_alpha_Ah (float): Lift coefficient per unit area for horizontal tail.
    S (float): Total wing surface area.
    c (float): Mean aerodynamic chord.
    cg (float): Geometric chord (assumed to be equal to mac).
    b (float): Wing span.
    lam (float): Taper ratio.
    Lambda (float): Sweep angle at 0.25c in radians.

    Returns:
    float: Aerodynamic center of the aircraft.
    """
    fus_term_1 = (1.8 * b_f * h_f * l_fn) / (C_L_alpha_Ah * S * c)
    fus_term_2 = (0.273 * b_f * cg * (b - b_f)) / ((1 + lam) * c**2 * (b + 2.15 * b_f)) * math.tan(Lambda)
    nacelle_term = -4 * 2 * (b_n**2 * l_n) / (S * c * C_L_alpha_Ah)
    return x_ac_w - fus_term_1 + fus_term_2 + nacelle_term


def calculate_downwash_effect(C_L_alpha_w: float, A: float, h_t: float, b: float) -> float:
    """
    Calculate the downwash effect on the lift coefficient.

    Parameters:
    C_L_alpha_w (float): Lift coefficient slope of the wing.
    A (float): Aspect ratio of the wing.
    h_t (float): Height of the tail above the wing.
    b (float): Wing span.

    Returns:
    float: Downwash effect on the lift coefficient.
    """
    return (2 * C_L_alpha_w) / (math.pi * A) * (1 / (1 + h_t / b))


def calculate_moment_coefficient_flaps(mu2: float, mu: float, delta_Cl_max: float, 
                                       c_prime_c: float, CL: float, Swf: float, S: float, 
                                       A: float, mu3: float, Lambda: float, x_ac: float, 
                                       c_bar: float) -> float:
    """
    Calculate the moment coefficient due to flaps.

    Parameters:
    mu (float): Flap deflection factor.
    mu2 (float): Flap effectiveness factor.
    mu3 (float): Flap effectiveness factor for the aspect ratio.
    delta_Cl_max (float): Maximum change in lift coefficient due to flaps.
    c_prime_c (float): Chord length at the flap location.
    CL (float): Lift coefficient.
    Swf (float): Wetted surface area of the wing.
    S (float): Total wing surface area.
    A (float): Aspect ratio of the wing.
    Lambda (float): Sweep angle at 0.25c in radians.
    x_ac (float): Aerodynamic center of the aircraft.
    c_bar (float): Mean aerodynamic chord.

    Returns:
    float: Moment coefficient due to flaps.
    """
    term1 = -mu * delta_Cl_max * (c_prime_c)
    term2 = (CL + delta_Cl_max * (1 - Swf / S)) * (1/8) * (c_prime_c) * (c_prime_c)

    flap_contribution = mu2 * (term1 - term2)
    aspect_ratio_term = 0.7 * (A / (1 + 2 / A)) * mu3 * delta_Cl_max * math.tan(math.radians(Lambda))

    Cm_1_4 = flap_contribution + aspect_ratio_term
    Cm_ac = Cm_1_4 - CL * (0.25 - x_ac / c_bar)

    return Cm_ac


def calculate_moment_coefficient_ac(Cm0: float, A: float, Lambda_025c: float, Cm_flaps: float,
                                    b_f: float, l_f: float, h_f: float, CL0: float, S: float,
                                    c: float, C_L_alpha_Ah: float) -> float:
    """
    Calculate the moment coefficient at the aerodynamic center.

    Parameters:
    Cm0 (float): Moment coefficient at the quarter chord.
    A (float): Aspect ratio of the wing.
    Lambda_025c (float): Sweep angle at 0.25c in radians.
    Cm_flaps (float): Moment coefficient due to flaps.
    b_f (float): Fuselage width.
    l_f (float): Fuselage length.
    h_f (float): Fuselage height.
    CL0 (float): Lift coefficient at zero angle of attack.
    S (float): Total wing surface area.
    c (float): Mean aerodynamic chord.
    C_L_alpha_Ah (float): Lift coefficient per unit area for horizontal tail.

    Returns:
    float: Moment coefficient at the aerodynamic center.
    """
    wing_term = Cm0 * (A * (math.cos(Lambda_025c))**2) / (A + 2 * math.cos(Lambda_025c))
    flaps_term = Cm_flaps
    fuselage_term = -1.8 * (1 - 2.5 * (b_f / l_f)) * (math.pi * b_f * h_f * l_f * CL0) / (4 * S * c * C_L_alpha_Ah)
    nacelle_term = 0  # Placeholder for nacelle term, if needed

    return wing_term + flaps_term + fuselage_term + nacelle_term


def calculate_all_coefficients(params: DesignParameters) -> dict:
    """
    Calculate all necessary coefficients for the aircraft stability and control analysis.

    Parameters:
    params (DesignParameters): Design parameters containing all aircraft specifications.

    Returns:
    dict: Contains calculated coefficients.
    """
    C_L_h = calculate_lift_coefficient_tail(params.empennage.A_h, params.empennage.type)
    beta_cruise = calculate_Mach_correction_factor(params.cruise_mach)
    beta_landing = calculate_Mach_correction_factor(params.landing_mach)
    
    C_L_alpha_h_cruise = calculate_lift_slope(params.empennage.A_h, beta_cruise, params.wing.Lambda_05c, params.wing.eta)
    C_L_alpha_h_landing = calculate_lift_slope(params.empennage.A_h, beta_landing, params.wing.Lambda_05c, params.wing.eta)
    
    C_L_alpha_w_cruise = calculate_lift_slope(params.wing.A, beta_cruise, params.wing.Lambda_05c, params.wing.eta)
    C_L_alpha_w_landing = calculate_lift_slope(params.wing.A, beta_landing, params.wing.Lambda_05c, params.wing.eta)

    S_net_val = calculate_net_surface_area(params.wing.S_w, params.wing.c_r, params.fuselage.b_f)
    
    C_LA_A_h_cruise = calculate_lift_slope_less_tail(C_L_alpha_w_cruise, params.wing.b_w, params.fuselage.b_f,
                                                     S_net_val, params.wing.S_w)
    
    C_LA_A_h_landing = calculate_lift_slope_less_tail(C_L_alpha_w_landing, params.wing.b_w, params.fuselage.b_f,
                                                       S_net_val, params.wing.S_w)

    x_ac_cruise = calculate_x_ac(params.cg.x_ac_w, params.fuselage.b_f, params.fuselage.h_f,
                                 params.fuselage.l_fn, params.engine.b_n, params.engine.l_n,
                                 C_LA_A_h_cruise, params.wing.S_w, params.wing.mac,
                                 params.wing.mac, params.wing.b_w, params.wing.lambda_w,
                                 params.wing.Lambda_w)

    x_ac_landing = calculate_x_ac(params.cg.x_ac_w, params.fuselage.b_f, params.fuselage.h_f,
                                    params.fuselage.l_fn, params.engine.b_n, params.engine.l_n,
                                    C_LA_A_h_landing, params.wing.S_w, params.wing.mac,
                                    params.wing.mac, params.wing.b_w, params.wing.lambda_w,
                                    params.wing.Lambda_w)
    
    d_e_d_alpha_val = calculate_downwash_effect(C_L_alpha_w_cruise, params.wing.A_w, params.empennage.h_t, params.wing.b_w)

    C_m_flaps_val = calculate_moment_coefficient_flaps(params.control_surface.mu2, params.control_surface.mu, params.performance.delta_Cl_max,
                                                         params.control_surface.c_prime_c, C_LA_A_h_landing,
                                                            params.wing.S_wf, params.wing.S_w, params.wing.A_w,
                                                            params.control_surface.mu3, params.wing.Lambda_w, x_ac_landing,
                                                            params.wing.mac)
    
    CL0 = params.performance.CL_max_TO - C_LA_A_h_landing * params.performance.stall_angle
    C_m_ac_landing = calculate_moment_coefficient_ac(params.performance.Cm0, params.wing.A_w, params.wing.Lambda_025c,
                                                        C_m_flaps_val, params.fuselage.b_f, params.fuselage.l_f,
                                                        params.fuselage.h_f, CL0, params.wing.S_w,
                                                        params.wing.mac, C_LA_A_h_landing)
    
    return {
        "C_L_h": C_L_h,
        "beta_cruise": beta_cruise,
        "beta_landing": beta_landing,
        "C_L_alpha_h_cruise": C_L_alpha_h_cruise,
        "C_L_alpha_h_landing": C_L_alpha_h_landing,
        "C_L_alpha_w_cruise": C_L_alpha_w_cruise,
        "C_L_alpha_w_landing": C_L_alpha_w_landing,
        "C_LA_A_h_cruise": C_LA_A_h_cruise,
        "C_LA_A_h_landing": C_LA_A_h_landing,
        "x_ac_cruise": x_ac_cruise,
        "x_ac_landing": x_ac_landing,
        "d_e_d_alpha": d_e_d_alpha_val,
        "C_m_flaps": C_m_flaps_val,
        "CL0": CL0,
        "C_m_ac_landing": C_m_ac_landing
    }


def calculate_stability_point(x_ac: float, C_L_alpha_h: float, C_L_alpha_Ah: float, d_e_d_alpha: float, Sh_S: float, l_h: float, c: float, Vh_V: float, S_M: float) -> float:
    """
    Calculate a stability point based on the aerodynamic center, lift coefficients, and downwash effect.
    """
    return x_ac + (C_L_alpha_h / (C_L_alpha_Ah)) * (1 - d_e_d_alpha) * (Sh_S * l_h / c) * Vh_V**2 - S_M


def calculate_controllability_point(x_ac: float, C_m_ac: float, C_L_alpha_h: float, C_L_h: float, Sh_S: float, l_h: float, c: float, Vh_V: float) -> float:
    """
    Calculate a controllability point based on the aerodynamic center, moment coefficient, and lift coefficients.
    """
    return x_ac - (C_m_ac / (C_L_alpha_h)) + (C_L_h / C_L_alpha_h) * (Sh_S * l_h / c) * Vh_V**2


def plot_scissor_plot(stability_vals_SM: np.ndarray, stability_vals_noSM: np.ndarray, controllability_vals: np.ndarray, Sh_S_range: np.ndarray):
    """
    Plot the scissor plot for stability and controllability.
    """
    plt.figure(figsize=(6, 4), tight_layout=True)
    plt.plot(stability_vals_SM, Sh_S_range, label="Stability", color="blue")
    plt.plot(stability_vals_noSM, Sh_S_range, label="Neutral Stability", linestyle="--", color="grey")
    plt.plot(controllability_vals, Sh_S_range, label="Controllability", color="red")
    plt.xlabel(r"$x_{cg}/MAC$", fontsize=14)
    plt.ylabel(r"$S_h/S$", fontsize=14)
    plt.xlim(-0.1, 1.1)
    plt.ylim(0, 0.4)
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.legend(fontsize=14)
    plt.grid()

    # # Add a bolded double-sided arrow for CG range 0.192295
    # plt.annotate(
    #     "", 
    #     xy=(most_aft_cg, 0.192295), xytext=(most_forward_cg, 0.192295),
    #     arrowprops=dict(arrowstyle="<->", linewidth=1.5, color="black")
    # )
    # plt.vlines([most_aft_cg, most_forward_cg], [0, 0], [0.4, 0.4], color='black', alpha=0.5, linewidth=2)

    # # Add a label for the CG range near the arrow
    # plt.text(0.47, 0.2, r"CG Range", fontsize=12, verticalalignment="bottom", horizontalalignment="center")

    # Fill below the stability graph
    plt.fill_betweenx(Sh_S_range, 1.5, stability_vals_SM, color='red', alpha=0.2)  # -1 ensures filling extends to the left boundary

    # Fill below the controllability graph
    plt.fill_betweenx(Sh_S_range, -1, controllability_vals, color='red', alpha=0.2)  # -1 ensures filling extends to the left boundary

    plt.show()

"""
# CG Range values
most_aft_cg = 0.646490637
# CG range from the data sheet (0.192295 to 0.50818)
most_forward_cg = 0.295223034
# CG range from the data sheet (0.192295 to 0.50818)

# Aircraft geometries
S = 61                              # data sheet
b = 27.05                           # data sheet
c = 2.3                             # data sheet
cg = c                              # assumption from slides
A = 12 * 1.2                        # data sheet + 20% increase

S_h = 11.73                         # data sheet
b_fh = 7.1842                       # span of horizontal stabilizer, measured from drawing
l_h = 12.84                         # data sheet
h_t = 2.903                         # vertical distance from wing to tail, measured from drawing
Ah = A_h(b_fh, S_h)                 # aspect ratio of horizontal stabilizer
Vh_V = math.sqrt(0.95)              # ADSEE III, lecture 7, slide 42

bf = 2.865                          # data sheet (fuselage width)
lf = 27.165                         # data sheet (fuselage length)
l_fn = 11.3                         # measured from drawing (distance from nose to start of wing)
S_net_val = S_net(S, 2.57, bf)      # S_net = S - c_r * b_f
S_wf = S_net_val * 2                # from definition of wetted surface (x2 because of top and bottom of the wing considered)

x_ac_c_w = 0.25                     # ADSEE III, lecture 7, slide 37
lam = 1.59 / 2.57                   # taper ratio, cr/ct (values from data sheet)
Lambda = math.radians(0)            # measured from drawing (angle of incidence of the wing) 
c_prime_c = 1.057                   # assumed from graph (Lecture 8, slide 22)

bn = 0.91565 * 1.25                 # width of nacelle, measured form drawing + 25% increase
ln = 2.46634 * 1.3                  # distance from propeller blade to 0.25c, measured from drawing. ADSEE III, lecture 7, slide 40 (source Torenbeek) + 30% increase


# Flight conditions
M_cruise = 0.46*Vh_V                # data sheet
M_landing = 0.170843671*Vh_V        # M_landing = V_app / sqrt(gamma * R * T) (gamma = 1.4, R = 287 J/(kg*K), T = 288.15 K)
CL_TO = 1.723943133                 # calculated in excel (parameters sheet)
C_L_A_h_cruise = 0.673264           # calculated in excel (parameters sheet)
C_L_A_h_landing = 1.597719616       # calculated in excel (parameters sheet)
delta_Cl_max = 0.3912               # XFOIL
Cm0 = -0.017                        # XFOIL
beta_cruise = beta(M_cruise)    # beta = sqrt(1 - M^2)
beta_landing = beta(M_landing)  # beta = sqrt(1 - M^2)
stall_angle = 15 * math.pi / 180    # from online sources: CAA, Wikipedia, SKYbrary,


# Constants
eta = 0.95                          # airfoil efficiency factor, from ADSEE II (Sam Summaries)
S_M = 0.05                          # stability margin, ADSEE III, lecture 7, slide 51

K_A = 1.0                           # Roskam
K_lambda = 0.97                     # Roskam
K_H = 1.27                          # Roskam

mu = 0.2                            # assumed from graph (Lecture 8, slide 20)
mu2 = 0.5                           # from graph (Lecture 8, slide 21)
mu3 = 0.0575                        # from graph (Lecture 8, slide 21)
"""

if __name__ == "__main__":
    # Load design parameters from YAML file
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    coefficients = calculate_all_coefficients(params)

    # Create a table
    table = PrettyTable()
    table.field_names = ["Parameter", "Value"]

    # Add rows to the table
    table.add_row(["C_L_h", coefficients['C_L_h'].__round__(4)])
    table.add_row(["Beta @ cruise", coefficients['beta_cruise'].__round__(4)])
    table.add_row(["Beta @ landing", coefficients['beta_landing'].__round__(4)])
    table.add_row(["C_L_alpha_h @ cruise", coefficients['C_L_alpha_h_cruise'].__round__(4)])
    table.add_row(["C_L_alpha_h @ landing", coefficients['C_L_alpha_h_landing'].__round__(4)])
    table.add_row(["C_L_alpha_w @ cruise", coefficients['C_L_alpha_w_cruise'].__round__(4)])
    table.add_row(["C_L_alpha_w @ landing", coefficients['C_L_alpha_w_landing'].__round__(4)])
    table.add_row(["C_LA_A_h @ cruise", coefficients['C_LA_A_h_cruise'].__round__(4)])
    table.add_row(["C_LA_A_h @ landing", coefficients['C_LA_A_h_landing'].__round__(4)])
    table.add_row(["x_ac @ cruise", coefficients['x_ac_cruise'].__round__(4)])
    table.add_row(["x_ac @ landing", coefficients['x_ac_landing'].__round__(4)])
    table.add_row(["d_e/d_alpha", coefficients['d_e_d_alpha'].__round__(4)])
    table.add_row(["CL0", coefficients['CL0'].__round__(4)])
    table.add_row(["C_m_ac @ landing", coefficients['C_m_ac_landing'].__round__(4)])

    # Print the table
    print(table)

    # Define the range for Sh_S
    Sh_S_range = np.linspace(0.0, 0.6, 500)

    # Compute stability and controllability values
    stability_vals_noSM = [
        calculate_stability_point(coefficients['x_ac_cruise'], coefficients['C_L_alpha_h_cruise'],
                                  coefficients['C_LA_A_h_cruise'], coefficients['d_e_d_alpha'],
                                  Sh_S, params.empennage.l_h, params.wing.mac, params.wing.Vh_V, 0)
        for Sh_S in Sh_S_range
    ]
    stability_vals_SM = [
        calculate_stability_point(coefficients['x_ac_cruise'], coefficients['C_L_alpha_h_cruise'],
                                  coefficients['C_LA_A_h_cruise'], coefficients['d_e_d_alpha'],
                                  Sh_S, params.empennage.l_h, params.wing.mac, params.wing.Vh_V, params.performance.S_M)
        for Sh_S in Sh_S_range
    ]
    controllability_vals = [
        calculate_controllability_point(coefficients['x_ac_landing'], coefficients['C_m_ac_landing'],
                                        coefficients['C_L_alpha_h_landing'], coefficients['C_L_h'],
                                        Sh_S, params.empennage.l_h, params.wing.mac, params.wing.Vh_V)
        for Sh_S in Sh_S_range
    ]

    # Plot the scissor plot
    plot_scissor_plot(stability_vals_SM, stability_vals_noSM, controllability_vals, Sh_S_range)

