import numpy as np



def calculate_wing_fuel_volume(S, b, t_c_w_r, lambda_w, tau_w):
    """
    Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
    Calculate the wing fuel volume based on the wing planform dimensions and thickness-to-chord ratio. (accuracy: +/- 10%)
    """
    V_WF = 0.54 * (S**2 / b) * t_c_w_r * ((1 + lambda_w * tau_w**0.5 + lambda_w**2 * tau_w) / (1 + lambda_w**2))
    return V_WF

def calculate_landing_gear_loading(W_TO, n_nlg, n_mlg, l_mlg, l_nlg):
    """
    Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
    Calculate the landing gear loading based on the maximum take-off weight and the number of landing gear units.
    """
    P_nlg = (W_TO * l_mlg) / (n_nlg * (l_mlg + l_nlg))
    P_mlg = (W_TO * l_nlg) / (n_mlg * (l_mlg + l_nlg))
    return P_nlg, P_mlg

def calculate_total_wetted_area(S_w, c_w_r, D_f, S_t, t_c_w_r, tau_w, lambda_w, t_c_t, lambda_t, l_f, l_n, lf_df):
    """
    Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
    Calculate the total wetted area based on the wing area, fuselage area, and empennage area.
    """
    S_exp_w = S_w - (c_w_r * D_f)

    S_wet_w = 2 * S_exp_w * (1 + 0.25 * t_c_w_r * (1 + tau_w * lambda_w) / (1 + lambda_w))
    S_wet_t = 2 * S_t * (1 + 0.25 * t_c_t * (1 + lambda_t) / (1 + lambda_t))
    S_wet_fus = np.pi * D_f * l_f * (0.5 + 0.135 * l_n / l_f)**(2/3) * (1.015 + 0.3 / (lf_df**1.5))
    S_wet_nac = 0  # Placeholder for nacelle wetted area calculation, to be defined based on specific parameters

    return S_wet_w + S_wet_t + S_wet_fus + S_wet_nac