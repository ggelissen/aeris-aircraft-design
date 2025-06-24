import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.unit_conversions import *
from design_variables import DesignParameters
from class1.preliminary_sizing.prelim_sizing_wing import calculate_sweep_angle_x_c, calculate_sweep_angle_LE

# TODO add winglet CD0_winglet
def calculate_CD0(S_ref: float, C_f_c: np.ndarray, FF_c: np.ndarray, IF_c: np.ndarray, S_wet_c: np.ndarray, CD_misc: np.ndarray) -> float:
    """
    Calculate the zero-lift drag coefficient (CD0) for a given configuration.

    Parameters:
    S_ref (float): Reference area in square meters.
    C_f_c (np.ndarray): Friction coefficient array.
    FF_c (np.ndarray): Form factor array.
    IF_c (np.ndarray): Interference factor array.
    S_wet_c (np.ndarray): Wetted area array.
    CD_misc (np.ndarray): Miscellaneous drag coefficient array.

    Returns:
    float: The calculated zero-lift drag coefficient.
    """
    #print(f"S_ref: {S_ref}, C_f_c: {C_f_c}, FF_c: {FF_c}, IF_c: {IF_c}, S_wet_c: {S_wet_c}, CD_misc: {CD_misc}")
    CD0 = 1 / S_ref * np.sum(C_f_c * FF_c * IF_c * S_wet_c) + np.sum(CD_misc) # TODO, why is there a sum over CD_misc? Shouldn't it be a single value?
    # if CD0 > 0.02:
    #     CD0 = 0.02  # Limit CD0 to a maximum of 0.02 as per design constraints
    CD0_tail = C_f_c[2] * FF_c[2] * IF_c[2] * S_wet_c[2] / S_ref # TODO, why is there a separate CD0_tail? Could've done this in a separate function...
    return CD0, CD0_tail


def calculate_skin_friction_coefficient(flow_ratio: tuple, Re: float, Mach: float) -> float:
    """
    Calculate the skin friction coefficient based on flow ratio, Reynolds number, and Mach number.

    Parameters:
    flow_ratio (tuple): Tuple containing the flow ratio (laminar, turbulent). E.g. (0.1, 0.9)
    Re (float): Reynolds number.
    Mach (float): Mach number.

    Returns:
    float: The calculated skin friction coefficient.
    """
    laminar, turbulent = flow_ratio
    C_f_lam = 1.328 / np.sqrt(Re)
    C_f_turb = 0.455 / (np.log10(Re) ** 2.58) * (1 + 0.144 * Mach ** 2) ** 0.65

    return laminar * C_f_lam + turbulent * C_f_turb


def calculate_Reynolds_number(V: float, rho: float, l: float, mu: float, k: float, Mach: float) -> float:
    """
    Calculate the Reynolds number based on velocity, density, characteristic length, dynamic viscosity, and Mach number.

    Parameters:
    V (float): Velocity in m/s.
    rho (float): Density in kg/m^3.
    l (float): Characteristic length in meters.
    mu (float): Dynamic viscosity in kg/(m·s).
    k (float): Roughness height in meters.
    Mach (float): Mach number.

    Returns:
    float: The calculated Reynolds number.
    """
    Re_1 = rho * V * l / mu
    Re_2 = 44.62 * ((l / k) ** 1.055) * (Mach ** 1.16)

    return min(Re_1, Re_2)


def calculate_form_factor(t_c: float, x_c: float, Mach_cr: float, Lambda_m: float) -> float:
    """
    Calculate the form factor based on thickness-to-chord ratio, position along the chord, chord length, Mach number, and sweep angle.

    Parameters:
    t_c (float): Thickness-to-chord ratio.
    x_c_m (float): Chord location of max thickness in meters.
    Mach_cr (float): Cruise Mach number.
    Lambda_m (float): Sweep angle at max thickness in radians.

    Returns:
    float: The calculated form factor.
    """
    return (1 + 0.6 / x_c * t_c + 100 * (t_c ** 4)) * (1.34 * Mach_cr ** 0.18 * np.cos(Lambda_m) ** 0.28)


def determine_interference_factor(component: str) -> float:
    """
    Determine the interference factor based on the component type.

    Parameters:
    component (str): Type of component ('wing', 'fuselage', 'empennage').

    Returns:
    float: The interference factor for the specified component.
    """
    interference_factors = {
        'wing': 1.0*1.04, # Based on high wing and winglet configuration # TODO, check assumptions here about winglets.
        # TODO Torenbeek 10.8.4, reduction of 10-15% of vortex drag for winglets. 
        'fuselage': 1.3*1.1, # Based on external nacelle on fuselage and landing gear struts
        'empennage': 1.03 # Based on V-tail configuration
    }
    
    return interference_factors.get(component, 1.0)  # Default to 1.0 if not found # TODO, this is not the way to go, if it fails, let it fail, don't return 1.0, we would like to know if something is wrong.


def calculate_total_wetted_area(S_w, c_w_r, D_f, S_t, t_c_w_r, tau_w, lambda_w, t_c_t, lambda_t, l_f, l_n, lf_df) -> np.ndarray:
    """
    Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
    Calculate the total wetted area based on the wing area, fuselage area, and empennage area.
    """
    S_exp_w = S_w - (c_w_r * D_f)

    S_wet_w = 2 * S_exp_w * (1 + 0.25 * t_c_w_r * (1 + tau_w * lambda_w) / (1 + lambda_w))
    S_wet_t = 2 * S_t * (1 + 0.25 * t_c_t * (1 + lambda_t) / (1 + lambda_t))
    S_wet_fus = np.pi * D_f * l_f * (0.5 + 0.135 * l_n / l_f)**(2/3) * (1.015 + 0.3 / (lf_df**1.5))

    return np.array([S_wet_fus, S_wet_w, S_wet_t])


def calculate_misc_drag_coefficient(Mach_dd: float, Mach_cr: float) -> float:
    """
    Calculate the miscellaneous drag coefficient based on design Mach number and cruise Mach number.
    Note: Only wave drag is considered, since fuselage and wing flaps have not been designed completely.

    Parameters:
    Mach_dd (float): Design drag divergence Mach number.
    Mach_cr (float): Cruise Mach number.

    Returns:
    float: The calculated miscellaneous drag coefficient.
    """
    if Mach_cr > Mach_dd:
        return 0.0
    else:
        return 0.002 * (1 + 2.5 * (Mach_dd - Mach_cr) / 0.05) ** (-1)
    

def run_improved_drag_estimations(params: DesignParameters) -> dict:
    """
    Run the improved drag estimations based on the design parameters.
    
    Parameters:
    params (DesignParameters): The design parameters containing all necessary data for drag calculations.
    
    Returns:
    dict: The total zero-lift drag coefficient (CD0) for the aircraft configuration plus skin friction coefficients (C_f).
    """
    #print(f"Surface Area of the wing: {params.wing.S_w:.2f} m^2 and the reference area: {params.wing.b_w}")
    Re = calculate_Reynolds_number(V=params.cruise_speed, rho=params.cruise_density, l=params.wing.root_chord, mu=1.4436e-5, k=0.152e-5, Mach=params.cruise_mach)
    
    C_f_lst = np.array([
        # Fuselage skin friction coefficient
        calculate_skin_friction_coefficient(flow_ratio=(0.1, 0.9), Re=Re, Mach=params.cruise_mach),
        # Wing skin friction coefficient
        calculate_skin_friction_coefficient(flow_ratio=(.35, .65), Re=Re, Mach=params.cruise_mach),
        # Tail skin friction coefficient
        calculate_skin_friction_coefficient(flow_ratio=(.35, .65), Re=Re, Mach=params.cruise_mach)
    ])

    Lambda_LE = calculate_sweep_angle_LE(Lambda_025c=params.wing.Lambda_025c_w, c_root=params.wing.root_chord, b=params.wing.b_w, taper_ratio=params.wing.lambda_w)
    Lambda_m = calculate_sweep_angle_x_c(Lambda_LE=Lambda_LE, c_root=params.wing.root_chord, b=params.wing.b_w, x_c=params.wing.x_c_m, taper_ratio=params.wing.lambda_w)

    FF_lst = np.array([
        # Fuselage form factor
        1,
        # Wing form factor
        calculate_form_factor(t_c=params.wing.t_c_w_r, x_c=params.wing.x_c_m, Mach_cr=params.cruise_mach, Lambda_m=Lambda_m),
        # Tail form factor
        calculate_form_factor(t_c=params.empennage.t_c_t, x_c=params.wing.x_c_m, Mach_cr=params.cruise_mach, Lambda_m=Lambda_m)])

    IF_lst = np.array([determine_interference_factor('fuselage'), determine_interference_factor('wing'), determine_interference_factor('empennage')])

    S_wet_lst = calculate_total_wetted_area(S_w=params.wing.S_w, c_w_r=params.wing.root_chord, D_f=params.fuselage.D_f, S_t=params.empennage.S_t,
                                            t_c_w_r=params.wing.t_c_w_r, tau_w=params.wing.tau_w, lambda_w=params.wing.lambda_w, t_c_t=params.empennage.t_c_t, 
                                            lambda_t=params.empennage.lambda_t, l_f=params.fuselage.l_f, l_n=params.fuselage.l_n, lf_df=params.fuselage.lf_df)

    CD_misc = calculate_misc_drag_coefficient(params.cruise_mach + 0.03, params.cruise_mach)

    CD0, CD0_tail = calculate_CD0(params.wing.S_ref, C_f_lst, FF_lst, IF_lst, S_wet_lst, CD_misc) # TODO, If S_ref is the same as S_w, might as well use S_w here.
    
    # Prepare C_f_lst for output TODO, not sure if this is the best way to do it, but it works for now.
    C_f_lst = {
        'fuselage': C_f_lst[0],
        'wing': C_f_lst[1],
        'tail': C_f_lst[2]
    }

    return {'CD0': CD0,
            'CD0_tail': CD0_tail,
            'C_f': C_f_lst}


if __name__ == "__main__":
    from design_variables import DesignParameters
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    CD0 = run_improved_drag_estimations(params)
    print(f"Total zero-lift drag coefficient (CD0): {CD0['CD0']:.6f}")
    print(f"Total zero-lift drag coefficient for tail (CD0_tail): {CD0['CD0_tail']:.6f}")
    print(f"Skin friction coefficients (C_f): {CD0['C_f']}")