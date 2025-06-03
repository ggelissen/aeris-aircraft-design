import pprint
from math import sqrt, nan, isnan # Added nan, isnan for handling potential NaN values

# # --- Placeholder for modules.propulsion_preliminary.gas_property_relations ---
# # IMPORTANT: Replace this with your actual gpr module for accurate results.
# # The functions below are highly simplified and will not yield correct thermodynamic values.
# class gpr:
#     """
#     Placeholder for Gas Property Relations module.
#     Replace with actual implementation for accurate results.
#     """
#     @staticmethod
#     def cp(t, gas="air", far=0.):
#         # Specific heat at constant pressure (J/kg.K)
#         if gas == "kerosene_in_air":
#             return 1148.0 + (far * 1000) # Very rough approximation
#         return 1005.0

#     @staticmethod
#     def s_o_s(t, gas="air", far=0.):
#         # Speed of sound (m/s)
#         k = gpr.gamma_gas(t, gas, far)
#         R = gpr.r_gas(gas, far)
#         if k < 0 or R < 0 or t < 0: return nan # Invalid input
#         return (k * R * t)**0.5 if (k * R * t) >= 0 else nan

#     @staticmethod
#     def prescribed_delta_h(p_in, t_in, delta_h, eta_pol, gas="air", far=0.):
#         # Calculates outlet conditions given an enthalpy change
#         # Simplified: Assumes constant cp
#         cp_val = gpr.cp(t_in, gas, far)
#         if cp_val == 0: return {"p_out": p_in, "t_out": t_in, "h_out": gpr.specific_enthalpy(t_in, gas, far)}

#         t_out = t_in + delta_h / cp_val
#         k = gpr.gamma_gas(t_in, gas, far)
        
#         if eta_pol == 0: # Avoid division by zero or invalid exponent
#             p_out = p_in 
#         elif t_in == 0: # Avoid division by zero if t_in is zero
#              p_out = p_in
#         elif delta_h > 0: # Compression
#             exponent = (k / (k - 1)) * eta_pol if (k-1)!=0 else 1
#             p_out = p_in * (t_out / t_in)**exponent if t_out/t_in >=0 else p_in
#         else: # Expansion
#             exponent = (k / (k - 1)) / eta_pol if (k-1)!=0 and eta_pol !=0 else 1
#             p_out = p_in * (t_out / t_in)**exponent if t_out/t_in >=0 else p_in
            
#         h_out = gpr.specific_enthalpy(t_out, gas, far)
#         return {"p_out": p_out, "t_out": t_out, "h_out": h_out}

#     @staticmethod
#     def prescribed_p_ratio(p_in, t_in, p_ratio, eta_pol, gas="air", far=0.):
#         # Calculates outlet conditions given a pressure ratio
#         # Simplified compressor/turbine polytropic relation
#         k = gpr.gamma_gas(t_in, gas, far)
#         p_out = p_in * p_ratio

#         if eta_pol == 0 or k == 1 or p_ratio < 0: # Avoid division by zero or invalid operations
#             t_out = t_in
#         elif p_ratio == 1.0:
#             t_out = t_in
#         elif p_ratio > 1.0:  # Compressor
#             t_out = t_in * (1 + (p_ratio**((k - 1) / k) - 1) / eta_pol) if k!=0 else t_in
#         else:  # Turbine (p_ratio < 1.0)
#             t_out = t_in * (1 - eta_pol * (1 - p_ratio**((k - 1) / k))) if k!=0 else t_in
        
#         h_out = gpr.specific_enthalpy(t_out, gas, far)
#         return {"p_out": p_out, "t_out": t_out, "h_out": h_out}

#     @staticmethod
#     def specific_enthalpy(t, gas="air", far=0.):
#         # Specific enthalpy (J/kg)
#         return gpr.cp(t, gas, far) * t

#     @staticmethod
#     def relative_pressure(t, gas="air", far=0., t_guess=None):
#         # Relative pressure (dimensionless) - Highly simplified
#         # This needs a proper gas data table or correlation.
#         k = gpr.gamma_gas(t, gas, far)
#         if t_guess is None: t_guess = 288.15 # Reference temperature
#         if t_guess == 0 or k == 1 or t < 0: return 1.0 
#         return (t / t_guess)**(k / (k - 1)) if (t/t_guess >=0) else 1.0

#     @staticmethod
#     def prescribed_relative_pressure(prt, gas="air", far=0., t_guess=288.15):
#         # Temperature from relative pressure - Highly simplified
#         k = gpr.gamma_gas(t_guess, gas, far)
#         if k == 0 or k == 1 or prt < 0: return t_guess
#         return t_guess * prt**((k - 1) / k) if (prt >=0) else t_guess

#     @staticmethod
#     def gamma_gas(t, gas="air", far=0.):
#         # Ratio of specific heats (gamma)
#         if gas == "kerosene_in_air":
#             return 1.33 + far * 10 # very rough
#         return 1.4

#     @staticmethod
#     def t_total_to_static(tt, mach, gas="air", far=0.):
#         # Converts total temperature to static temperature
#         k = gpr.gamma_gas(tt, gas, far)
#         if (1. + (k - 1.) / 2. * mach**2.) == 0: return tt
#         return tt / (1. + (k - 1.) / 2. * mach**2.)

#     @staticmethod
#     def r_gas(gas="air", far=0.):
#         # Specific gas constant (J/kg.K)
#         if gas == "kerosene_in_air": # Approx for combustion products
#             return 287.0 * (1 + far) # Simplified
#         return 287.0

#     @staticmethod
#     def massfp(tt, far, mach, gas="air"):
#         # Mass flow parameter (MFP) = mdot * sqrt(cp*T01/A1^2*P01^2)
#         # Or more commonly: mdot * sqrt(R*Tt) / (A * Pt) * sqrt(k) ... no, this is not it.
#         # MFP = M * sqrt(gamma/R) * (1 + (gamma-1)/2 * M^2)^(-(gamma+1)/(2*(gamma-1)))
#         # For choked flow M=1: MFP_choked = sqrt(gamma/R) * ( (gamma+1)/2 )^(-(gamma+1)/(2*(gamma-1)))
#         # Units: sqrt(K)/s or dimensionless depending on definition
#         # This placeholder returns a simplified choked MFP if M=1, otherwise scales linearly (very incorrect)
#         k = gpr.gamma_gas(tt, gas, far)
#         R = gpr.r_gas(gas, far)
#         if R == 0 or tt < 0 or k <= 1: return 0.001 # Avoid math errors with a small default

#         try:
#             if mach >= 1.0: # Choked or supersonic, use choked formula for simplicity here
#                 val = ((k + 1.) / 2.)**(-(k + 1.) / (2. * (k - 1.)))
#                 mfp_choked = (k / R)**0.5 * val if (k/R) >=0 else 0.001
#                 return mfp_choked
#             elif mach < 0:
#                  return 0.001
#             else: # Unchoked - very rough linear scaling for placeholder
#                 choked_val = ((k + 1.) / 2.)**(-(k + 1.) / (2. * (k - 1.)))
#                 mfp_choked = (k / R)**0.5 * choked_val if (k/R) >=0 else 0.001
#                 return mach * mfp_choked
#         except (ValueError, OverflowError, ZeroDivisionError):
#             return 0.001 # Default small value on error

#     @staticmethod
#     def compressor_eta_is_from_poly(eta_pol, pr, tt, gas="air", far=0.):
#         k = gpr.gamma_gas(tt, gas, far)
#         if eta_pol == 0 or pr <= 0 or k <= 1: return 0.85 # default
#         try:
#             term_pr_k = pr**((k - 1) / k)
#             # eta_is = ( Ttis - Ttin ) / ( Tt - Ttin )
#             # Tt/Ttin = 1 + ( (Pr^((k-1)/k)/eta_pol) - 1/eta_pol )
#             # Ttis/Ttin = Pr^((k-1)/k)
#             # eta_is = (Pr^((k-1)/k) - 1) / ( (Pr^((k-1)/k)/eta_pol) - 1/eta_pol ) is WRONG
#             # eta_is = (h_is - h_in) / (h_act - h_in) = (T_is - T_in) / (T_act - T_in)
#             # T_act/T_in = 1 + ( (PR^((k-1)/k) - 1) / eta_pol )
#             # T_is/T_in = PR^((k-1)/k)
#             # eta_is = (PR^((k-1)/k) - 1) / ( (1 + ( (PR^((k-1)/k) - 1) / eta_pol )) - 1 )
#             # eta_is = (PR^((k-1)/k) - 1) / ( (PR^((k-1)/k) - 1) / eta_pol ) = eta_pol. This is for small stage.
#             # For multi-stage: eta_is = (PR^((k-1)/k) - 1) / (PR^((k-1)/(k*eta_pol)) - 1)
#             if (pr**((k-1)/(k*eta_pol)) - 1) == 0: return eta_pol # approx
#             eta_is = (term_pr_k - 1) / (pr**((k-1)/(k*eta_pol)) - 1) if pr != 1.0 else 1.0
#             return min(max(eta_is, 0.5), 0.98)
#         except (ValueError, OverflowError, ZeroDivisionError):
#             return 0.85

#     @staticmethod
#     def turbine_eta_is_from_poly(eta_pol, pr, tt, gas="air", far=0.):
#         # pr here is P_out/P_in for turbine, so < 1
#         k = gpr.gamma_gas(tt, gas, far)
#         if eta_pol == 0 or pr <= 0 or pr > 1 or k <=1: return 0.88 # default
#         try:
#             # eta_is = (h_act - h_in) / (h_is - h_in) = (T_act - T_in) / (T_is - T_in)
#             # T_act/T_in = 1 - eta_pol * (1 - PR^((k-1)/k))
#             # T_is/T_in = PR^((k-1)/k)
#             # eta_is = (1 - eta_pol * (1 - PR^((k-1)/k)) - 1) / (PR^((k-1)/k) - 1)
#             # eta_is = -eta_pol * (1 - PR^((k-1)/k)) / (PR^((k-1)/k) - 1) = eta_pol. This is for small stage.
#             # For multi-stage: eta_is = (1 - PR^((k-1)*eta_pol/k)) / (1 - PR^((k-1)/k))
#             if (1 - pr**((k-1)/k)) == 0: return eta_pol # approx
#             eta_is = (1 - pr**(((k-1)*eta_pol)/k)) / (1 - pr**((k-1)/k)) if pr != 1.0 else 1.0
#             return min(max(eta_is, 0.5), 0.98)
#         except (ValueError, OverflowError, ZeroDivisionError):
#             return 0.88
# # --- End of Placeholder gpr ---

import modules.propulsion_preliminary.gas_property_relations as gpr

# --- Emissions Calculation Code (from emissions.py) ---
def fuelflow_to_emissionflow(mdot_f, ei):
    """
    Calculates the emission flow (in kg/s) from the fuel flow (kg/s) for a
    given emission index.

    :param mdot_f: Fuel mass flow in kg/s
    :param ei: Emission index of a species in kg/kg
    :return: Emission flow in kg/s
    """
    if isnan(mdot_f) or isnan(ei):
        return nan
    return mdot_f * ei

def emissions(mdot_f, ei_nox,
              ei_so4=2.0e-4, ei_soot=4.0e-5,
              ei_co2=3.16, ei_h2o=1.26,
              dt=1.):
    """
    Estimates the emission flow (in kg/s) and the total emission (in kg) for
    a given time step, for several species, given the fuel flow (in kg/s).

    :param mdot_f: Fuel flow in kg/s
    :param ei_nox: Emission index of Nitrogen Oxides (NO and NO2) in kg/kg
    :param ei_so4:  Emission index of Sulfate in kg/kg
    :param ei_soot:  Emission index of soot in kg/kg
    :param ei_co2:  Emission index of Carbon Dioxide in kg/kg
    :param ei_h2o:  Emission index of Water in kg/kg
    :param dt: Time step under consideration in seconds
    :return: Dictionary with emission flows and total emissions for every
    specie considered
    """
    if isnan(mdot_f) or isnan(dt):
        # If mdot_f is NaN, all emissions will be NaN
        return dict(mdot_co2=nan, m_co2=nan,
                    mdot_h2o=nan, m_h2o=nan,
                    mdot_nox=nan, m_nox=nan,
                    mdot_so4=nan, m_so4=nan,
                    mdot_soot=nan, m_soot=nan)

    # Carbon dioxide
    mdot_co2 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_co2)
    m_co2 = mdot_co2 * dt

    # Water
    mdot_h2o = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_h2o)
    m_h2o = mdot_h2o * dt

    # Nitrogen oxides
    mdot_nox = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_nox)
    m_nox = mdot_nox * dt

    # Sulfur
    mdot_so4 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_so4)
    m_so4 = mdot_so4 * dt

    # Soot
    mdot_soot = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_soot)
    m_soot = mdot_soot * dt

    emissions_dict = dict(mdot_co2=mdot_co2, m_co2=m_co2,
                          mdot_h2o=mdot_h2o, m_h2o=m_h2o,
                          mdot_nox=mdot_nox, m_nox=m_nox,
                          mdot_so4=mdot_so4, m_so4=m_so4,
                          mdot_soot=mdot_soot, m_soot=m_soot
                          )
    return emissions_dict
# --- End of Emissions Calculation Code ---


# --- Turbofan Analysis Code (from turbofan_parametric_analysis.py) ---
def turbofan_parametric_analysis(
        mach_0, ts_0, ps_0,  # flight conditions
        bpr, pr_fan, pr_lpc, pr_hpc, tt_4,  # design variables
        eta_fan, eta_lpc, eta_hpc, eta_hpt, eta_lpt,  # polytropic efficiencies
        eta_com=0.99, eta_mech_l=0.99, eta_mech_h=0.99,  # other efficiencies
        pr_com=0.95, pr_inl=0.98,
        bleed_to=0., power_tol=0., power_toh=0.,
        cooling_l=0., cooling_h=0.,
        lhv=43.e6,  # lower heating value J/kg
        full_output=True):
    """
    Carries out thermodynamic on-design / parametric analysis for a turbofan.
    (Docstring adapted)
    Returns: sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict (if full_output)
             or sf, tsfc, eta_thermal, eta_propulsive, eta_overall
    """
    # 0 - freestream
    a_0 = gpr.s_o_s(ts_0)
    v_0 = mach_0 * a_0 if not (isnan(mach_0) or isnan(a_0)) else nan
    
    state_0_delta_h = 0.5 * v_0 ** 2 if not isnan(v_0) else nan
    state_0 = gpr.prescribed_delta_h(p_in=ps_0, t_in=ts_0, delta_h=state_0_delta_h, eta_pol=1.)
    pt_0 = state_0["p_out"]
    tt_0 = state_0["t_out"]
    hs_0 = gpr.specific_enthalpy(t=ts_0)
    ht_0 = hs_0 + v_0 ** 2. / 2. if not (isnan(hs_0) or isnan(v_0)) else nan
    tau_0 = ht_0 / hs_0 if hs_0 != 0 and not isnan(ht_0) else nan
    
    # 2 - inlet exit / fan entry
    tt_2 = tt_0
    pt_2 = pr_inl * pt_0 if not (isnan(pr_inl) or isnan(pt_0)) else nan
    ht_2 = ht_0

    # 13 - fan exit
    state_13 = gpr.prescribed_p_ratio(p_in=pt_2, t_in=tt_2, p_ratio=pr_fan, eta_pol=eta_fan)
    pt_13 = state_13["p_out"]
    tt_13 = state_13["t_out"]
    ht_13 = state_13["h_out"]
    tau_fan = ht_13 / ht_2 if ht_2 != 0 and not isnan(ht_13) else nan

    # 25 - LPC exit
    state_25 = gpr.prescribed_p_ratio(p_in=pt_13, t_in=tt_13, p_ratio=pr_lpc, eta_pol=eta_lpc)
    pt_25 = state_25["p_out"]
    tt_25 = state_25["t_out"]
    ht_25 = state_25["h_out"]
    tau_lpc = ht_25 / ht_13 if ht_13 != 0 and not isnan(ht_25) else nan

    # 3 - HPC exit
    state_3 = gpr.prescribed_p_ratio(p_in=pt_25, t_in=tt_25, p_ratio=pr_hpc, eta_pol=eta_hpc)
    pt_3 = state_3["p_out"]
    tt_3 = state_3["t_out"]
    ht_3 = state_3["h_out"]
    tau_hpc = ht_3 / ht_25 if ht_25 != 0 and not isnan(ht_3) else nan

    # 4 - Combustor exit
    far_4 = nan
    if not isnan(ht_3):
        far_4i = 0.02 # Initial guess
        far_4 = 0.03
        it = 0
        while abs(far_4 - far_4i) > 0.00001 and it < 50:
            far_4i = far_4
            ht_4i = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4i)
            denominator = (eta_com * lhv - ht_4i)
            if denominator == 0 or isnan(ht_4i) or isnan(ht_3) or isnan(eta_com) or isnan(lhv):
                far_4 = nan
                break
            far_4 = (ht_4i - ht_3) / denominator
            if isnan(far_4): break
            it += 1
        if it >= 50 : far_4 = nan

    pt_4 = pt_3 * pr_com if not (isnan(pt_3) or isnan(pr_com)) else nan
    ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4)
    tau_lambda = ht_4 / hs_0 if hs_0 != 0 and not isnan(ht_4) else nan
    
    # Simplified calculations for tau_m1, tau_hpt, etc. due to complexity and gpr placeholders
    # These will likely be NaN or inaccurate with placeholder GPR
    tau_m1 = nan
    if not isnan(tau_lambda) and tau_lambda != 0:
        den_tau_m1 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h)
        if den_tau_m1 != 0 and not isnan(far_4):
            tau_m1_num = (((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) +
                       cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda))
            tau_m1 = tau_m1_num / den_tau_m1 if not isnan(tau_m1_num) else nan


    tau_hpt = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4):
        den_tau_hpt_expr = (eta_mech_h * tau_lambda *
                          ((1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) +
                           cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda))
        if den_tau_hpt_expr != 0 and not isnan(den_tau_hpt_expr):
            tau_hpt_num = (tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh)
            if not isnan(tau_hpt_num):
                 tau_hpt = (1. - tau_hpt_num / den_tau_hpt_expr)


    ht_41 = ht_4 * tau_m1 if not (isnan(ht_4) or isnan(tau_m1)) else nan
    
    far_41 = nan
    if not isnan(far_4):
        den_far_41_main = (1. - bleed_to - cooling_h - cooling_l)
        if den_far_41_main != 0:
            den_far_41 = (1. + (cooling_h / den_far_41_main))
            far_41 = far_4 / den_far_41 if den_far_41 != 0 else nan


    pt_41 = pt_4
    tt_41 = gpr.prescribed_h(ht_41, gas="kerosene_in_air", far=far_41) if not isnan(ht_41) else nan

    # 44 - HPT exit
    ht_44 = ht_41 * tau_hpt if not (isnan(ht_41) or isnan(tau_hpt)) else nan
    state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41,
                                      delta_h=(ht_44 - ht_41) if not (isnan(ht_44) or isnan(ht_41)) else nan,
                                      eta_pol=eta_hpt,
                                      gas="kerosene_in_air", far=far_41)
    pt_44 = state_44["p_out"]
    tt_44 = state_44["t_out"]

    # Simplified tau_m2, tau_lpt
    tau_m2 = nan # Placeholder
    ht_45 = ht_44 * tau_m2 if not (isnan(ht_44) or isnan(tau_m2)) else nan # Placeholder
    far_45 = far_41 # Approximation
    pt_45 = pt_44
    tt_45 = gpr.prescribed_h(ht_45, gas="kerosene_in_air", far=far_45) if not isnan(ht_45) else nan


    tau_lpt = nan # Placeholder
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(tau_hpt) and tau_hpt !=0 and not isnan(far_4):
        den_tau_lpt_main = (eta_mech_l * tau_lambda * tau_hpt *
                      ((1. - bleed_to - cooling_h - cooling_l) *
                       (1. + far_4) + (cooling_h + cooling_l / tau_hpt) *
                       tau_0 * tau_lpc * tau_hpc / tau_lambda))
        if den_tau_lpt_main != 0 and not isnan(den_tau_lpt_main):
            tau_lpt_num = (tau_0 * ((tau_lpc * tau_fan - 1) + bpr * (tau_fan - 1)) + (1. + bpr) * power_tol)
            if not isnan(tau_lpt_num):
                tau_lpt = 1. - tau_lpt_num / den_tau_lpt_main


    ht_5 = ht_45 * tau_lpt if not (isnan(ht_45) or isnan(tau_lpt)) else nan
    state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45,
                                     delta_h=(ht_5 - ht_45) if not (isnan(ht_5) or isnan(ht_45)) else nan,
                                     eta_pol=eta_lpt,
                                     gas="kerosene_in_air", far=far_45)
    pt_5 = state_5["p_out"]
    tt_5 = state_5["t_out"]

    # 9 - Core exhaust nozzle
    ht_9, tt_9, pt_9, far_9 = ht_5, tt_5, pt_5, far_45
    mach_9 = nan
    ps_9 = nan
    ts_9 = nan
    v_9 = nan
    rho_9 = nan

    if not isnan(pt_9) and not isnan(ps_0) and ps_0 != 0 and not isnan(tt_9) and not isnan(far_9):
        p_total_static_ratio_9 = pt_9 / ps_0
        g_9 = gpr.gamma_gas(tt_9, gas="kerosene_in_air", far=far_9)
        if g_9 > 1. and p_total_static_ratio_9 > 0:
            try:
                mach_i_9_sq = (2. / (g_9 - 1.)) * (p_total_static_ratio_9 ** ((g_9 - 1.) / g_9) - 1.)
                mach_i_9 = sqrt(mach_i_9_sq) if mach_i_9_sq >=0 else 1.0
                mach_9 = 1. if mach_i_9 >= 1. else mach_i_9
            except (ValueError, OverflowError, ZeroDivisionError): mach_9 = 1.
        elif p_total_static_ratio_9 <=1: mach_9 = 0.0
        else: mach_9 = 1.0 # Default to choked if unsure

        ts_9_val = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
        ts_9 = ts_9_val if not isnan(ts_9_val) else tt_9 / (1 + (g_9-1)/2 * mach_9**2) # fallback simple
        
        g_ts9 = gpr.gamma_gas(ts_9, gas="kerosene_in_air", far=far_9)
        if not (isnan(g_ts9) or g_ts9 == 1 or isnan(tt_9) or ts_9 == 0):
             p_total_static_ratio_ts9 = (tt_9 / ts_9) ** (g_ts9 / (g_ts9 - 1.)) if (tt_9/ts_9 >=0) else 1.0
             ps_9 = pt_9 / p_total_static_ratio_ts9 if p_total_static_ratio_ts9 != 0 else ps_0
        else: ps_9 = ps_0 # Fallback

        a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9)
        v_9 = mach_9 * a_9 if not (isnan(mach_9) or isnan(a_9)) else nan
        r_9 = gpr.r_gas(gas="kerosene_in_air", far=far_9)
        rho_9 = ps_9 / (r_9 * ts_9) if not (isnan(ps_9) or isnan(r_9) or isnan(ts_9) or r_9 * ts_9 == 0) else nan


    # 19 - Bypass exhaust nozzle
    ht_19, tt_19, pt_19, far_19 = ht_13, tt_13, pt_13, 0.
    mach_19 = nan
    ps_19 = nan
    ts_19 = nan
    v_19 = nan
    rho_19 = nan

    if not isnan(pt_19) and not isnan(ps_0) and ps_0 != 0 and not isnan(tt_19):
        p_total_static_ratio_19 = pt_19 / ps_0
        g_19 = gpr.gamma_gas(tt_19, gas="air", far=far_19)
        if g_19 > 1. and p_total_static_ratio_19 > 0:
            try:
                mach_i_19_sq = (2. / (g_19 - 1.)) * (p_total_static_ratio_19 ** ((g_19 - 1.) / g_19) - 1.)
                mach_i_19 = sqrt(mach_i_19_sq) if mach_i_19_sq >=0 else 1.0
                mach_19 = 1. if mach_i_19 >= 1. else mach_i_19
            except (ValueError, OverflowError, ZeroDivisionError): mach_19 = 1.
        elif p_total_static_ratio_19 <=1: mach_19 = 0.0
        else: mach_19 = 1.0

        ts_19_val = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
        ts_19 = ts_19_val if not isnan(ts_19_val) else tt_19 / (1 + (g_19-1)/2 * mach_19**2) # fallback simple

        g_ts19 = gpr.gamma_gas(ts_19, gas="air", far=far_19)
        if not (isnan(g_ts19) or g_ts19 == 1 or isnan(tt_19) or ts_19 == 0):
            p_total_static_ratio_ts19 = (tt_19 / ts_19) ** (g_ts19 / (g_ts19 - 1.)) if (tt_19/ts_19 >=0) else 1.0
            ps_19 = pt_19 / p_total_static_ratio_ts19 if p_total_static_ratio_ts19 != 0 else ps_0
        else: ps_19 = ps_0

        a_19 = gpr.s_o_s(ts_19, gas="air")
        v_19 = mach_19 * a_19 if not (isnan(mach_19) or isnan(a_19)) else nan
        r_19 = gpr.r_gas(gas="air", far=far_19)
        rho_19 = ps_19 / (r_19 * ts_19) if not (isnan(ps_19) or isnan(r_19) or isnan(ts_19) or r_19*ts_19 == 0) else nan

    # Specific Thrust SF (N / (kg/s of total air flow))
    # Note: Original SF might be per unit core air flow or total air flow. Assuming total air flow here.
    # SF = [ (1-bleed_to)*(1+far_4)*v_9 + bpr*v_19 - (1+bpr)*v_0 ] / (1+bpr)
    #      + [ (ps_9-ps_0)*A9_effective + (ps_19-ps_0)*A19_effective ] / mdot_air_total
    # This is complex. The provided code calculates SF differently.
    # The original code's SF definition:
    # sf_term1 = (1 - bleed_to) * (1. + far_4) * v_9
    # sf_term2 = bpr * v_19
    # sf_term3 = (1. + bpr) * v_0
    # sf_pressure_core = (ps_9 - ps_0) * (1 - bleed_to) * (1. + far_4) / (rho_9 * v_9) if (rho_9 * v_9) != 0 else 0.0
    # sf_pressure_bypass = (ps_19 - ps_0) * bpr / (rho_19 * v_19) if (rho_19 * v_19) != 0 else 0.0
    # sf_gross = sf_term1 + sf_term2 + sf_pressure_core + sf_pressure_bypass
    # sf = (sf_gross - sf_term3) / (1. + bpr) if (1. + bpr) !=0 else nan
    # This SF is specific thrust per unit of total incoming air mdot_0 = mdot_core + mdot_bypass

    sf = nan
    if not any(isnan(x) for x in [bleed_to, far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19]):
        if (1. + bpr) != 0:
            sf_term1 = (1. - bleed_to) * (1. + far_4) * v_9
            sf_term2 = bpr * v_19
            sf_term3 = (1. + bpr) * v_0
            
            sf_pressure_core = 0.0
            if rho_9 != 0 and v_9 != 0 and not (isnan(rho_9) or isnan(v_9)):
                 sf_pressure_core = (ps_9 - ps_0) * (1 - bleed_to) * (1. + far_4) / (rho_9 * v_9)

            sf_pressure_bypass = 0.0
            if rho_19 != 0 and v_19 != 0 and not (isnan(rho_19) or isnan(v_19)):
                sf_pressure_bypass = (ps_19 - ps_0) * bpr / (rho_19 * v_19)
            
            sf_gross = sf_term1 + sf_term2 + sf_pressure_core + sf_pressure_bypass
            sf = (sf_gross - sf_term3) / (1. + bpr)
        else:
            sf = nan
    else: # one of the components is nan
        sf = nan


    # Thrust specific fuel consumption TSFC = mdot_f / F_n = far_core / SF_based_on_core_air
    # TSFC = far_4 * mdot_core / (SF * mdot_total_air)
    # mdot_core = mdot_total_air / (1+bpr)
    # far_4 is based on core air. mdot_f = far_4 * mdot_air_core_at_combustor_entry
    # mdot_air_core_at_combustor_entry = mdot_air_core_fan_exit * (1 - bleed_to - cooling_l - cooling_h)
    # For simplicity, if SF is N/(kg/s total air), and we need (kg fuel/s)/N:
    # TSFC = (mdot_fuel / mdot_total_air) / SF
    # mdot_fuel / mdot_total_air = (far_4 * mdot_core_comb_entry) / (mdot_core_fan_exit * (1+bpr))
    # mdot_core_comb_entry / mdot_core_fan_exit = (1-bleed_to-cooling_l-cooling_h)
    # So, (mdot_fuel / mdot_total_air) = far_4 * (1-bleed_to-cooling_l-cooling_h) / (1+bpr)
    # TSFC = (far_4 * (1. - bleed_to - cooling_l - cooling_h)) / (sf * (1. + bpr)) if sf*(1+bpr) != 0 else nan
    # The original code has:
    # tsfc = far_4 * (1. - bleed_to - cooling_l - cooling_h) / den_tsfc where den_tsfc = (1. + bpr) * sf
    tsfc = nan
    if not (isnan(far_4) or isnan(sf) or isnan(bpr) or (sf * (1.+bpr) == 0)):
        tsfc_num = far_4 * (1. - bleed_to - cooling_l - cooling_h)
        tsfc_den = sf * (1. + bpr)
        tsfc = tsfc_num / tsfc_den if tsfc_den != 0 else nan


    # OPR
    opr = pr_fan * pr_lpc * pr_hpc if not any(isnan(x) for x in [pr_fan, pr_lpc, pr_hpc]) else nan

    # Efficiencies (Simplified / Placeholder)
    eta_thermal = nan
    eta_propulsive = nan
    eta_overall = nan

    # Using simplified definition for eta_thermal = Net Work / Heat Input
    # Net Work = 0.5 * mdot_core_exit * v9_eff^2 + 0.5 * mdot_bypass * v19_eff^2 - 0.5 * mdot_total * v0^2
    # Heat Input = mdot_fuel * LHV = far_4_eff * mdot_core_comb_entry * LHV
    # eta_thermal = (0.5*(1-bleed_to)*(1+far_4)*v_9**2 + 0.5*bpr*v_19**2 - 0.5*(1+bpr)*v_0**2) / (far_4*(1-bleed_to-cool_l-cool_h)*lhv * (1+bpr)) <- this is not quite right
    # Original code:
    # v_19_id = v_19 ; if rho_19 !=0 and v_19 !=0: v_19_id += (ps_19 - ps_0) / (rho_19 * v_19)
    # v_9_id = v_9; if rho_9 !=0 and v_9 !=0: v_9_id += (ps_9 - ps_0) / (rho_9 * v_9)
    # num_eta_thermal = bpr * (v_19_id ** 2.) / 2. + (1. - bleed_to) * (1. + far_4) * (v_9_id ** 2.) / 2. - (1. + bpr) * (v_0 ** 2.) / 2.
    # den_eta_thermal = (1. - bleed_to - cooling_h - cooling_l) * far_4 * lhv
    # eta_thermal = num_eta_thermal / den_eta_thermal if den_eta_thermal != 0 else nan
    v_19_id = v_19
    v_9_id = v_9
    if not (isnan(v_19) or isnan(rho_19) or rho_19 == 0 or v_19 == 0 or isnan(ps_19) or isnan(ps_0)):
        v_19_id += (ps_19 - ps_0) / (rho_19 * v_19)
    if not (isnan(v_9) or isnan(rho_9) or rho_9 == 0 or v_9 == 0 or isnan(ps_9) or isnan(ps_0)):
        v_9_id += (ps_9 - ps_0) / (rho_9 * v_9)

    if not any(isnan(x) for x in [bpr, v_19_id, bleed_to, far_4, v_9_id, v_0, cooling_h, cooling_l, lhv]):
        num_eta_thermal = bpr * (v_19_id ** 2.) / 2. + \
                          (1. - bleed_to) * (1. + far_4) * (v_9_id ** 2.) / 2. - \
                          (1. + bpr) * (v_0 ** 2.) / 2.
        den_eta_thermal = (1. - bleed_to - cooling_h - cooling_l) * far_4 * lhv
        eta_thermal = num_eta_thermal / den_eta_thermal if den_eta_thermal != 0 else nan
    
    # eta_propulsive = Thrust * v0 / Net Kinetic Energy increase rate
    # eta_propulsive = (SF * (1+bpr) * v0) / num_eta_thermal (using num_eta_thermal as KE increase)
    if not (isnan(sf) or isnan(bpr) or isnan(v_0) or isnan(num_eta_thermal) or num_eta_thermal == 0):
        eta_propulsive = (sf * (1.+bpr) * v_0) / num_eta_thermal


    if not (isnan(eta_thermal) or isnan(eta_propulsive)):
        eta_overall = eta_thermal * eta_propulsive
    
    # Simplified output for brevity with placeholder GPR
    output_dict = dict(
        mach_0=mach_0, ts_0=ts_0, ps_0=ps_0, bpr=bpr, tt_4=tt_4,
        pr_fan=pr_fan, pr_lpc=pr_lpc, pr_hpc=pr_hpc, opr=opr,
        far_4=far_4, tsfc=tsfc, sf=sf,
        v_9=v_9, v_19=v_19,
        tt_3=tt_3, tt_5=tt_5, tt_9=tt_9, tt_19=tt_19,
        eta_thermal=eta_thermal, eta_propulsive=eta_propulsive, eta_overall=eta_overall
    )

    if full_output:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    else:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall

def print_detailed_results(results, engine_name="Engine Run"):
    """Prints the turbofan analysis results."""
    if results is None or len(results) < 5: # Expecting at least 5 for non-full, 6 for full
        print(f"\n--- {engine_name}: Incomplete or No Results ---")
        if results: print(results)
        return

    sf, tsfc, eta_thermal, eta_propulsive, eta_overall = results[:5]
    output_dict = results[5] if len(results) > 5 else {}

    print(f"\n--- {engine_name}: Performance Metrics ---")
    print(f"  Specific Thrust (SF):                       {sf:.2f} N/(kg/s)" if not isnan(sf) else "  Specific Thrust (SF):                       N/A")
    print(f"  Thrust Specific Fuel Consumption (TSFC):    {tsfc*1e6:.2f} mg/(N·s)" if not isnan(tsfc) else "  Thrust Specific Fuel Consumption (TSFC):    N/A")
    print(f"  Thermal Efficiency (eta_thermal):           {eta_thermal*100:.2f}%" if not isnan(eta_thermal) else "  Thermal Efficiency (eta_thermal):           N/A")
    print(f"  Propulsive Efficiency (eta_propulsive):     {eta_propulsive*100:.2f}%" if not isnan(eta_propulsive) else "  Propulsive Efficiency (eta_propulsive):     N/A")
    print(f"  Overall Efficiency (eta_overall):           {eta_overall*100:.2f}%" if not isnan(eta_overall) else "  Overall Efficiency (eta_overall):           N/A")
    
    opr_val = output_dict.get('opr', nan)
    print(f"  Overall Pressure Ratio (OPR):               {opr_val:.2f}" if not isnan(opr_val) else "  Overall Pressure Ratio (OPR):               N/A")

    if output_dict: # Print more details if available
        print(f"\n--- {engine_name}: Selected Cycle Parameters (from output_dict) ---")
        for key, value in output_dict.items():
             print(f"  {key:<20}: {value:.4f}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")
    print("--- End of Report ---")

# --- End of Turbofan Analysis Code ---


# --- Main Mission Simulation ---
def run_mission_simulation():
    print("Starting Aircraft Mission Emissions Simulation...\n")

    # --- Define Mission Segments ---
    # For each segment, you need to provide:
    # - name: Name of the segment
    # - duration_minutes: Duration in minutes
    # - target_thrust_N: Required thrust for this segment (per engine)
    # - flight_conditions: mach_0, ts_0 (K), ps_0 (Pa)
    # - engine_params: Parameters for turbofan_parametric_analysis.
    #   Many (like BPR, component efficiencies) will be constant for an engine.
    #   Others (like tt_4, pressure ratios) might be adjusted for thrust,
    #   but here we use a baseline set and rely on TSFC scaling.
    # - ei_nox: NOx emission index (kg_NOx / kg_fuel) for this segment.

    # Baseline Engine Parameters (example values, adjust as needed)
    # These are assumed constant for the specific engine type.
    baseline_engine_config = {
        "bpr": 2.65, "pr_fan": 1.9, "pr_lpc": 1.5, "pr_hpc": 5.65, "tt_4": 1400.,
        "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9,
        "eta_hpt": 0.93, "eta_lpt": 0.93,
        "eta_com": 0.99, "eta_mech_l": 0.99, "eta_mech_h": 0.99,
        "pr_com": 0.95, "pr_inl": 0.98,
        "bleed_to": 0., "power_tol": 0., "power_toh": 0.,
        "cooling_l": 0., "cooling_h": 0.,
        "lhv": 43.e6, # J/kg
        "full_output": True
    }

    mission_segments = [
        {
            "name": "Engine Start & Warm-Up", "duration_minutes": 10,
            "target_thrust_N": 5000, # Example: Idle thrust
            "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, # Ground
            "engine_params_override": {"tt_4": 900}, # Lower TIT for idle
            "ei_nox": 0.005 # Lower for idle
        },
        {
            "name": "Taxi", "duration_minutes": 10,
            "target_thrust_N": 7000, # Example: Taxi thrust
            "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, # Ground slow movement
            "engine_params_override": {"tt_4": 950},
            "ei_nox": 0.006
        },
        {
            "name": "Take-off", "duration_minutes": 5,
            "target_thrust_N": 70000, # Example: Max Take-off thrust
            "flight_conditions": {"mach_0": 0.25, "ts_0": 288.15, "ps_0": 101325}, # Near ground, accelerating
            "engine_params_override": {"tt_4": 1500, "pr_fan": 2.0, "pr_hpc": 6.0}, # Higher settings for TO
            "ei_nox": 0.025 # Higher for max power
        },
        {
            "name": "Climb", "duration_minutes": 30,
            "target_thrust_N": 55000, # Example: Max Climb thrust
            "flight_conditions": {"mach_0": 0.70, "ts_0": 240.0, "ps_0": 40000}, # Mid-altitude example
            "engine_params_override": {"tt_4": 1450},
            "ei_nox": 0.020
        },
        {
            "name": "Cruise", "duration_minutes": 400,
            "target_thrust_N": 25000, # Example: Cruise thrust
            "flight_conditions": {"mach_0": 0.80, "ts_0": 216.65, "ps_0": 18753.9}, # Cruise altitude
            "engine_params_override": {}, # Use baseline tt_4 or specify cruise tt_4
            "ei_nox": 0.015
        },
        {
            "name": "Descent", "duration_minutes": 15,
            "target_thrust_N": 8000, # Example: Descent/Idle thrust
            "flight_conditions": {"mach_0": 0.50, "ts_0": 250.0, "ps_0": 50000}, # Mid-descent example
            "engine_params_override": {"tt_4": 1000},
            "ei_nox": 0.008
        },
        {
            "name": "Landing", "duration_minutes": 5,
            "target_thrust_N": 10000, # Example: Approach/Landing thrust
            "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, # Near ground
            "engine_params_override": {"tt_4": 1050},
            "ei_nox": 0.010
        },
        {
            "name": "Taxi & Shutdown", "duration_minutes": 5,
            "target_thrust_N": 5000, # Example: Idle thrust
            "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, # Ground
            "engine_params_override": {"tt_4": 900},
            "ei_nox": 0.005
        },
    ]

    total_mission_emissions = {
        "m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0
    }
    
    print("IMPORTANT NOTE: The underlying gas property relations (gpr) are placeholders.")
    print("Results will not be thermodynamically accurate until a proper 'gpr' module is used.\n")

    for segment in mission_segments:
        print(f"--- Processing Segment: {segment['name']} ---")

        dt_seconds = segment["duration_minutes"] * 60.0

        # Prepare engine parameters for this segment
        current_engine_params = baseline_engine_config.copy()
        current_engine_params.update(segment["flight_conditions"])
        if "engine_params_override" in segment:
            current_engine_params.update(segment["engine_params_override"])
        
        # Call turbofan analysis
        # Ensure only valid parameters are passed by removing non-analysis keys
        analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
        
        tf_results = turbofan_parametric_analysis(
            mach_0=current_engine_params["mach_0"],
            ts_0=current_engine_params["ts_0"],
            ps_0=current_engine_params["ps_0"],
            **analysis_params # Pass the rest of BPR, pr_fan etc.
        )
        
        # sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict = tf_results
        # We only need tsfc for mdot_f calculation from target thrust
        tsfc = tf_results[1] # tsfc is the second element

        if isnan(tsfc) or tsfc <= 0: # Check for invalid TSFC
            print(f"  Warning: Invalid TSFC ({tsfc:.4e}) calculated for segment {segment['name']}. Emissions will be NaN.")
            print(f"  Input conditions: M0={current_engine_params['mach_0']}, Ts0={current_engine_params['ts_0']}, Ps0={current_engine_params['ps_0']}")
            print(f"  Engine params used: pr_fan={current_engine_params.get('pr_fan')}, tt_4={current_engine_params.get('tt_4')}")
            mdot_f = nan
            segment_emissions_data = emissions(mdot_f, segment["ei_nox"], dt=dt_seconds)
        else:
            mdot_f = segment["target_thrust_N"] * tsfc
            print(f"  Flight Conditions: M0={current_engine_params['mach_0']}, Ts0={current_engine_params['ts_0']:.2f}K, Ps0={current_engine_params['ps_0']:.0f}Pa")
            print(f"  Calculated TSFC: {tsfc:.4e} (kg_fuel/s)/N")
            print(f"  Target Thrust: {segment['target_thrust_N']:.0f} N")
            print(f"  Calculated Fuel Flow (mdot_f): {mdot_f:.4f} kg/s")

            # Calculate emissions for the segment
            segment_emissions_data = emissions(mdot_f, segment["ei_nox"], dt=dt_seconds)
            print(f"  Emissions for this segment (kg):")
            for species, mass in segment_emissions_data.items():
                if species.startswith("m_"): # Only print total mass for the segment
                    print(f"    {species}: {mass:.4f}" if not isnan(mass) else f"    {species}: NaN")

        # Accumulate total emissions
        for species_mass_key in total_mission_emissions.keys():
            if not isnan(segment_emissions_data[species_mass_key]):
                 total_mission_emissions[species_mass_key] += segment_emissions_data[species_mass_key]
            else: # If any segment emission is NaN, total becomes NaN
                 total_mission_emissions[species_mass_key] = nan
        print("-" * 40)

    print("\n--- Total Mission Emissions ---")
    for species, total_mass in total_mission_emissions.items():
        print(f"  Total {species}: {total_mass:.2f} kg" if not isnan(total_mass) else f"  Total {species}: NaN kg")

    print("\nSimulation Finished.")

if __name__ == '__main__':
    run_mission_simulation()

    # --- Example of using the original emissions function directly ---
    # print("\n--- Direct Emissions Function Example ---")
    # specific_fuel_flow = 0.0495  # kg/s
    # specific_ei_nox = 0.012    # kg/kg
    # direct_results = emissions(mdot_f=specific_fuel_flow, ei_nox=specific_ei_nox, dt=3600) # Example for 1 hour
    # pp = pprint.PrettyPrinter(indent=2, width=80, compact=False)
    # print(f"Emission Results for mdot_f = {specific_fuel_flow} kg/s (dt = {3600}s):")
    # pp.pprint(direct_results)
    # print("-" * 30)

    # --- Example of using the turbofan analysis directly ---
    # print("\n--- Direct Turbofan Analysis Example (from original script) ---")
    # r_direct_tf = turbofan_parametric_analysis(
    #     mach_0=0.80, ts_0=216.65, ps_0=18753.9,
    #     bpr=2.65, pr_fan=1.9, pr_lpc=1.5, pr_hpc=5.65, tt_4=1400.,
    #     eta_fan=0.915, eta_lpc=0.9, eta_hpc=0.9, eta_hpt=0.93, eta_lpt=0.93,
    #     full_output=True
    # )
    # print_detailed_results(r_direct_tf, "Direct Turbofan Run Example")
