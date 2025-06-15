
from math import sqrt, nan, isnan # Added nan, isnan for handling potential NaN values
import sys # For potential path debugging
import os  # For potential path debugging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))) 
from utils.unit_conversions import *
from design_variables import DesignParameters

import gas_property_relations as gpr
import numpy as np
# --- ISA Atmosphere and Humidity Calculation ---
class atmosphere:
    @staticmethod
    def temperature(h, delta_t_0=0.):
        """
        Returns ISA temperature at altitude h (meters), optionally with deviation delta_t_0 (K).
        """
        # Troposphere up to 11km
        if h < 11000:
            t = 288.15 - 0.0065 * h
        else:
            t = 216.65
        return t + delta_t_0

    @staticmethod
    def pressure(h):
        """
        Returns ISA pressure at altitude h (meters).
        """
        # Troposphere up to 11km
        if h < 11000:
            p = 101325 * (1 - 0.0065 * h / 288.15) ** 5.2561
        else:
            p = 22632.1 * np.exp(-9.80665 * (h - 11000) / (287.05 * 216.65))
        return p

    @staticmethod
    def saturation_vapor_pressure(t):
        """
        Returns saturation vapor pressure (Pa) at temperature t (K).
        """
        t_c = t - 273.15
        return 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))

# --- NOx Emission Index Calculation (Dallara/Schwartz/Kroo) ---
def ei_nox_dallara(pt_3, tt_3, h, relative_humidity=0.6, delta_t_isa=0.,
                   reduction_factor=0., lhv=43031.e3, lhv_ref=43031.e3):
    """
    Determines the NOx emission index according to Dallara/Schwartz/Kroo.

    :param pt_3: Total pressure before combustor in Pa
    :param tt_3: Total temperature before combustor in K
    :param h: Altitude in m
    :param relative_humidity: Relative humidity (0-1)
    :param delta_t_isa: ISA deviation in K
    :param reduction_factor: Fractional reduction in NOx (e.g. 0.4 for 40%)
    :param lhv: Lower heating value of fuel (J/kg)
    :param lhv_ref: Reference LHV (J/kg)
    :return: Emission index of NOx in kg/kg
    """
    ei = (2+28.5*((pt_3/1000)/3100)**0.5 * np.exp((tt_3-825)/250))/1000


    return ei
# --- The placeholder gpr class is removed, as we are attempting to use the import above. ---

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


# --- Turbofan Analysis Code) ---
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
    if not isnan(ht_3) and not isnan(tt_4) and not isnan(eta_com) and not isnan(lhv):
        far_4i = 0.02 # Initial guess
        far_4 = 0.03
        it = 0
        while abs(far_4 - far_4i) > 0.00001 and it < 50:
            far_4i = far_4
            ht_4i = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4i)
            if isnan(ht_4i): # Check if ht_4i became NaN
                far_4 = nan
                break
            denominator = (eta_com * lhv - ht_4i)
            if denominator == 0 or isnan(ht_3):
                far_4 = nan
                break
            far_4 = (ht_4i - ht_3) / denominator
            if isnan(far_4): break # Check if far_4 became NaN
            it += 1
        if it >= 50 and abs(far_4 - far_4i) > 0.00001 : far_4 = nan # Non-convergence

    pt_4 = pt_3 * pr_com if not (isnan(pt_3) or isnan(pr_com)) else nan
    ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4) if not isnan(tt_4) and not isnan(far_4) else nan
    tau_lambda = ht_4 / hs_0 if hs_0 != 0 and not isnan(ht_4) and not isnan(hs_0) else nan
    
    # 41 - Nozzle Vane mixing process (HPT entry)
    tau_m1 = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc):
        den_tau_m1 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h)
        if den_tau_m1 != 0:
            tau_m1_num = (((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) +
                           cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda))
            if not isnan(tau_m1_num):
                tau_m1 = tau_m1_num / den_tau_m1

    # HPT work
    tau_hpt = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_fan) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(eta_mech_h) and not isnan(bpr) and not isnan(power_toh):
        den_tau_hpt_expr_val_part = ((1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) +
                                  cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda)
        if not isnan(den_tau_hpt_expr_val_part):
            den_tau_hpt_expr = eta_mech_h * tau_lambda * den_tau_hpt_expr_val_part
            if den_tau_hpt_expr != 0:
                tau_hpt_num = (tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh)
                if not isnan(tau_hpt_num):
                    tau_hpt = (1. - tau_hpt_num / den_tau_hpt_expr)

    ht_41 = ht_4 * tau_m1 if not (isnan(ht_4) or isnan(tau_m1)) else nan
    
    far_41 = nan
    if not isnan(far_4):
        den_far_41_main = (1. - bleed_to - cooling_h - cooling_l)
        if den_far_41_main != 0:
            den_far_41_sub = (cooling_h / den_far_41_main)
            if not isnan(den_far_41_sub):
                den_far_41 = (1. + den_far_41_sub)
                if den_far_41 != 0:
                    far_41 = far_4 / den_far_41

    pt_41 = pt_4
    tt_41 = gpr.prescribed_h(ht_41, gas="kerosene_in_air", far=far_41) if not isnan(ht_41) and not isnan(far_41) else nan

    # 44 - HPT exit
    ht_44 = ht_41 * tau_hpt if not (isnan(ht_41) or isnan(tau_hpt)) else nan
    delta_h_hpt = ht_44 - ht_41 if not (isnan(ht_44) or isnan(ht_41)) else nan
    state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41,
                                     delta_h=delta_h_hpt,
                                     eta_pol=eta_hpt,
                                     gas="kerosene_in_air", far=far_41)
    pt_44 = state_44["p_out"]
    tt_44 = state_44["t_out"]

    # 45 - HPT end nozzle vane mixing process (LPT entry)
    tau_m2 = nan
    if not isnan(far_4) and not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_lambda) and tau_lambda != 0 and \
       not isnan(tau_m1) and tau_m1 != 0 and \
       not isnan(tau_hpt) and tau_hpt != 0:
        den_tau_m2_main = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + cooling_l)
        if den_tau_m2_main != 0:
            tau_m2_num_term = cooling_l * tau_0 * tau_lpc * tau_hpc / (tau_lambda * tau_m1 * tau_hpt)
            if not isnan(tau_m2_num_term):
                tau_m2_num = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + tau_m2_num_term
                if not isnan(tau_m2_num):
                    tau_m2 = tau_m2_num / den_tau_m2_main
    
    ht_45 = ht_44 * tau_m2 if not (isnan(ht_44) or isnan(tau_m2)) else nan
    
    far_45 = nan
    if not isnan(far_4):
        den_far_45_main = (1. - bleed_to - cooling_h - cooling_l)
        if den_far_45_main != 0:
            den_far_45_sub = (cooling_l + cooling_h) / den_far_45_main
            if not isnan(den_far_45_sub):
                den_far_45 = (1. + den_far_45_sub)
                if den_far_45 != 0:
                    far_45 = far_4 / den_far_45
        
    pt_45 = pt_44
    tt_45 = gpr.prescribed_h(ht_45, gas="kerosene_in_air", far=far_45) if not isnan(ht_45) and not isnan(far_45) else nan

    # 5 - LPT exit
    tau_lpt = nan
    if not isnan(eta_mech_l) and not isnan(tau_lambda) and tau_lambda != 0 and \
       not isnan(tau_hpt) and tau_hpt != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_fan) and not isnan(bpr) and not isnan(power_tol):
        
        term_cool_l_eff = cooling_l / tau_hpt
        if not isnan(term_cool_l_eff):
            term_bracket_coeffs = (cooling_h + term_cool_l_eff) * tau_0 * tau_lpc * tau_hpc / tau_lambda
            if not isnan(term_bracket_coeffs):
                den_tau_lpt_bracket = (1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + term_bracket_coeffs
                if not isnan(den_tau_lpt_bracket):
                    den_tau_lpt_main = eta_mech_l * tau_lambda * tau_hpt * den_tau_lpt_bracket
                    if den_tau_lpt_main != 0:
                        tau_lpt_num_term1 = tau_0 * ((tau_lpc * tau_fan - 1.) + bpr * (tau_fan - 1.))
                        tau_lpt_num_term2 = (1. + bpr) * power_tol
                        if not isnan(tau_lpt_num_term1) and not isnan(tau_lpt_num_term2):
                            tau_lpt_num = tau_lpt_num_term1 + tau_lpt_num_term2
                            tau_lpt = 1. - (tau_lpt_num / den_tau_lpt_main)

    ht_5 = ht_45 * tau_lpt if not (isnan(ht_45) or isnan(tau_lpt)) else nan

    # Debug print before the failing call
    # print(f"DEBUG LPT Input: pt_45={pt_45}, tt_45={tt_45}, ht_45={ht_45}, ht_5_calc_before_state5={ht_5}, eta_lpt={eta_lpt}, far_45={far_45}, tau_lpt={tau_lpt}")

    delta_h_lpt = ht_5 - ht_45 if not (isnan(ht_5) or isnan(ht_45)) else nan
    state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45,
                                     delta_h=delta_h_lpt,
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
                mach_i_9_sq_term = p_total_static_ratio_9 ** ((g_9 - 1.) / g_9) - 1.
                if mach_i_9_sq_term >= 0:
                    mach_i_9_sq = (2. / (g_9 - 1.)) * mach_i_9_sq_term
                    mach_i_9 = sqrt(mach_i_9_sq)
                    mach_9 = 1. if mach_i_9 >= 1. else mach_i_9
                else: # Should not happen if p_total_static_ratio_9 > 1
                    mach_9 = 0.0 if p_total_static_ratio_9 <= 1 else 1.0 # Approx
            except (ValueError, OverflowError, ZeroDivisionError): mach_9 = 1.
        elif p_total_static_ratio_9 <=1: mach_9 = 0.0
        else: mach_9 = 1.0 

        ts_9_val = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
        ts_9 = ts_9_val if not isnan(ts_9_val) else (tt_9 / (1 + (g_9-1)/2 * mach_9**2) if (1 + (g_9-1)/2 * mach_9**2) != 0 else nan)
        
        g_ts9 = gpr.gamma_gas(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        if not (isnan(g_ts9) or g_ts9 == 1 or isnan(tt_9) or isnan(ts_9) or ts_9 == 0):
            t_ratio_ts9 = tt_9 / ts_9
            if t_ratio_ts9 >=0:
                p_total_static_ratio_ts9 = t_ratio_ts9 ** (g_ts9 / (g_ts9 - 1.))
                ps_9 = pt_9 / p_total_static_ratio_ts9 if p_total_static_ratio_ts9 != 0 else ps_0
            else: ps_9 = ps_0 # Fallback if t_ratio is negative
        else: ps_9 = ps_0 

        a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
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
                mach_i_19_sq_term = p_total_static_ratio_19 ** ((g_19 - 1.) / g_19) - 1.
                if mach_i_19_sq_term >=0:
                    mach_i_19_sq = (2. / (g_19 - 1.)) * mach_i_19_sq_term
                    mach_i_19 = sqrt(mach_i_19_sq)
                    mach_19 = 1. if mach_i_19 >= 1. else mach_i_19
                else:
                    mach_19 = 0.0 if p_total_static_ratio_19 <=1 else 1.0
            except (ValueError, OverflowError, ZeroDivisionError): mach_19 = 1.
        elif p_total_static_ratio_19 <=1: mach_19 = 0.0
        else: mach_19 = 1.0

        ts_19_val = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
        ts_19 = ts_19_val if not isnan(ts_19_val) else (tt_19 / (1 + (g_19-1)/2 * mach_19**2) if (1 + (g_19-1)/2 * mach_19**2) != 0 else nan)

        g_ts19 = gpr.gamma_gas(ts_19, gas="air", far=far_19) if not isnan(ts_19) else nan
        if not (isnan(g_ts19) or g_ts19 == 1 or isnan(tt_19) or isnan(ts_19) or ts_19 == 0):
            t_ratio_ts19 = tt_19 / ts_19
            if t_ratio_ts19 >=0:
                p_total_static_ratio_ts19 = t_ratio_ts19 ** (g_ts19 / (g_ts19 - 1.))
                ps_19 = pt_19 / p_total_static_ratio_ts19 if p_total_static_ratio_ts19 != 0 else ps_0
            else: ps_19 = ps_0
        else: ps_19 = ps_0

        a_19 = gpr.s_o_s(ts_19, gas="air") if not isnan(ts_19) else nan
        v_19 = mach_19 * a_19 if not (isnan(mach_19) or isnan(a_19)) else nan
        r_19 = gpr.r_gas(gas="air", far=far_19)
        rho_19 = ps_19 / (r_19 * ts_19) if not (isnan(ps_19) or isnan(r_19) or isnan(ts_19) or r_19*ts_19 == 0) else nan

    sf = nan
    if not any(isnan(x) for x in [bleed_to, far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19]): # Check all inputs to SF
        if (1. + bpr) != 0:
            sf_term1 = (1. - bleed_to) * (1. + far_4) * v_9
            sf_term2 = bpr * v_19
            sf_term3 = (1. + bpr) * v_0
            
            sf_pressure_core = 0.0
            if not (isnan(rho_9) or rho_9 == 0 or isnan(v_9) or v_9 == 0):
                sf_pressure_core = (ps_9 - ps_0) * (1 - bleed_to) * (1. + far_4) / (rho_9 * v_9)

            sf_pressure_bypass = 0.0
            if not (isnan(rho_19) or rho_19 == 0 or isnan(v_19) or v_19 == 0):
                sf_pressure_bypass = (ps_19 - ps_0) * bpr / (rho_19 * v_19)
            
            sf_gross = sf_term1 + sf_term2 + sf_pressure_core + sf_pressure_bypass
            sf = (sf_gross - sf_term3) / (1. + bpr)
    
    tsfc = nan
    if not (isnan(far_4) or isnan(sf) or sf == 0 or isnan(bpr) or (1.+bpr) == 0): # Added sf != 0 check
        tsfc_num = far_4 * (1. - bleed_to - cooling_l - cooling_h)
        tsfc_den = sf * (1. + bpr) # Denominator for TSFC
        if tsfc_den != 0:
            tsfc = tsfc_num / tsfc_den
    
    opr = pr_fan * pr_lpc * pr_hpc if not any(isnan(x) for x in [pr_fan, pr_lpc, pr_hpc]) else nan

    eta_thermal = nan
    eta_propulsive = nan
    eta_overall = nan
    num_eta_thermal = nan # Initialize to ensure it's defined

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
        if not isnan(den_eta_thermal) and den_eta_thermal != 0:
            eta_thermal = num_eta_thermal / den_eta_thermal
    
    if not (isnan(sf) or isnan(bpr) or isnan(v_0) or isnan(num_eta_thermal) or num_eta_thermal == 0):
        eta_propulsive = (sf * (1.+bpr) * v_0) / num_eta_thermal

    if not (isnan(eta_thermal) or isnan(eta_propulsive)):
        eta_overall = eta_thermal * eta_propulsive
    
    output_dict = dict(
        mach_0=mach_0, ts_0=ts_0, ps_0=ps_0, bpr=bpr, tt_4=tt_4,
        pr_fan=pr_fan, pr_lpc=pr_lpc, pr_hpc=pr_hpc, opr=opr,
        far_4=far_4, tsfc=tsfc, sf=sf,
        v_9=v_9, v_19=v_19,
        tt_3=tt_3, tt_5=tt_5, tt_9=tt_9, tt_19=tt_19, # tt_3 and tt_4 already here
        eta_thermal=eta_thermal, eta_propulsive=eta_propulsive, eta_overall=eta_overall,
        # Adding more variables that were in the original detailed output for reference
        pt_0=pt_0, pt_2=pt_2, pt_13=pt_13, pt_25=pt_25, pt_3=pt_3, pt_4=pt_4,
        pt_41=pt_41, pt_44=pt_44, pt_45=pt_45, pt_5=pt_5, pt_9=pt_9, pt_19=pt_19,
        tt_0=tt_0, tt_2=tt_2, tt_13=tt_13, tt_25=tt_25, tt_41=tt_41, tt_44=tt_44,
        tau_0=tau_0, tau_fan=tau_fan, tau_lpc=tau_lpc, tau_hpc=tau_hpc,
        tau_m1=tau_m1, tau_hpt=tau_hpt, tau_m2=tau_m2, tau_lpt=tau_lpt
    )

    if full_output:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    else:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall

def print_detailed_results(results, engine_name="Engine Run"):
    """Prints the turbofan analysis results."""
    if results is None or len(results) < 5: 
        print(f"\n--- {engine_name}: Incomplete or No Results ---")
        if results: print(results)
        return

    sf, tsfc, eta_thermal, eta_propulsive, eta_overall = results[:5]
    output_dict = results[5] if len(results) > 5 else {}

    print(f"\n--- {engine_name}: Performance Metrics ---")
    print(f"  Specific Thrust (SF):                           {sf:.2f} N/(kg/s)" if not isnan(sf) else "  Specific Thrust (SF):                           N/A")
    print(f"  Thrust Specific Fuel Consumption (TSFC):        {tsfc*1e6:.2f} mg/(N·s)" if not isnan(tsfc) else "  Thrust Specific Fuel Consumption (TSFC):        N/A")
    print(f"  Thermal Efficiency (eta_thermal):               {eta_thermal*100:.2f}%" if not isnan(eta_thermal) else "  Thermal Efficiency (eta_thermal):               N/A")
    print(f"  Propulsive Efficiency (eta_propulsive):         {eta_propulsive*100:.2f}%" if not isnan(eta_propulsive) else "  Propulsive Efficiency (eta_propulsive):         N/A")
    print(f"  Overall Efficiency (eta_overall):               {eta_overall*100:.2f}%" if not isnan(eta_overall) else "  Overall Efficiency (eta_overall):               N/A")
    
    opr_val = output_dict.get('opr', nan)
    print(f"  Overall Pressure Ratio (OPR):                   {opr_val:.2f}" if not isnan(opr_val) else "  Overall Pressure Ratio (OPR):                   N/A")

    if output_dict: 
        print(f"\n--- {engine_name}: Selected Cycle Parameters (from output_dict) ---")
        # Define an order for printing, grouping related parameters
        ordered_keys = [
            'mach_0', 'ts_0', 'ps_0', 'bpr', 'tt_4', 'lhv', # tt_4 is already here
            'pr_inl', 'pr_fan', 'pr_lpc', 'pr_hpc', 'pr_com', 'opr',
            'eta_fan', 'eta_lpc', 'eta_hpc', 'eta_hpt', 'eta_lpt',
            'eta_com', 'eta_mech_l', 'eta_mech_h',
            'bleed_to', 'power_tol', 'power_toh', 'cooling_l', 'cooling_h',
            'tau_0', 'tau_fan', 'tau_lpc', 'tau_hpc', 'tau_m1', 'tau_hpt', 'tau_m2', 'tau_lpt',
            'far_4', 'far_41', 'far_45', 
            'tt_0', 'pt_0', 'tt_2', 'pt_2', 'tt_13', 'pt_13', 'tt_25', 'pt_25',
            'tt_3', 'pt_3', # Added tt_3 here
            'tt_41', 'pt_41', 'tt_44', 'pt_44', 'tt_45', 'pt_45',
            'tt_5', 'pt_5', 'tt_9', 'pt_9', 'tt_19', 'pt_19',
            'v_9', 'v_19',
            'sf', 'tsfc', 'eta_thermal', 'eta_propulsive', 'eta_overall'
        ]
        printed_keys = set()
        for key in ordered_keys:
            if key in output_dict:
                value = output_dict[key]
                print(f"  {key:<20}: {value:.4f}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")
                printed_keys.add(key)
        
        # Print any remaining keys from output_dict not in ordered_keys
        remaining_keys = set(output_dict.keys()) - printed_keys
        if remaining_keys:
            print("\n  --- Other Parameters (Not in Ordered List) ---")
            for key in sorted(list(remaining_keys)):
                value = output_dict[key]
                print(f"  {key:<20}: {value:.4f}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")

    print("--- End of Report ---")

# --- End of Turbofan Analysis Code ---


# --- Main Mission Simulation ---
def run_mission_simulation(params: DesignParameters):
    print("Starting Aircraft Mission Emissions Simulation...\n")

    baseline_engine_config = {
        "bpr": params.engine.Bpr, "pr_fan": params.engine.prfan, "pr_lpc": params.engine.prlpc, "pr_hpc": params.engine.prhpc, "tt_4": 1400., # tt_4 is max design TIT
        "eta_fan": params.engine.etafan, "eta_lpc": params.engine.etalpc, "eta_hpc": params.engine.etahpc,
        "eta_hpt": params.engine.etahpt, "eta_lpt": params.engine.etalpt,
        "eta_com": params.engine.etacom, "eta_mech_l": params.engine.etamechl, "eta_mech_h": params.engine.etamechh,
        "pr_com": params.engine.prcom, "pr_inl": params.engine.prinlet,
        "bleed_to": params.engine.bleedto, "power_tol": params.engine.power_tol, "power_toh": params.engine.power_toh,
        "cooling_l": params.engine.cooling_l, "cooling_h": params.engine.cooling_h,
        "lhv": params.engine.lhv, 
        "full_output": True
    }
    T_to = params.engine.T_TO
    T_cruise = params.engine.cruise_thrust #N, takeoff thrust 
    mission_segments = [
        {
            "name": "Engine Start & Warm-Up", "duration_minutes": 10,
            "target_thrust_N": 0.07*T_to, # Approx 7% of 7540N
            "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850}, 
            "ei_nox": 0.004 
        },
        {
            "name": "Taxi", "duration_minutes": 10,
            "target_thrust_N": 0.12 * T_to, # Approx 12% of 7540N
            "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 900},
            "ei_nox": 0.005
        },
        {
            "name": "Take-off", "duration_minutes": 5,
            "target_thrust_N": T_to, # Given
            "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1400}, # Max TIT, slightly increased PRs
            "ei_nox": 0.020 
        },
        {
            "name": "Climb", "duration_minutes": 20,
            "target_thrust_N": 0.85*T_to , # Approx 85% of 9220N
            "flight_conditions": {"mach_0": 0.65, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 1300},
            "ei_nox": 0.018
        },
        {
            "name": "Cruise", "duration_minutes": 400,
            "target_thrust_N": T_cruise, # Approx 30% of 9220N
            "flight_conditions": {"mach_0": 0.85, "ts_0": 216.65, "ps_0": 18753.9}, # 40000ft
            "engine_params_override": {"tt_4": 1200}, 
            "ei_nox": 0.012
        },
        {
            "name": "Diversion Cruise (460km)", "duration_minutes": 34, # Approx. for 460km @ M0.75 / 30000ft
            "target_thrust_N": T_cruise, # Estimated for diversion cruise
            "flight_conditions": {"mach_0": 0.75, "ts_0": 228.7, "ps_0": 30090}, # 30000ft
            "engine_params_override": {"tt_4": 1200},
            "ei_nox": 0.011
        },
        {
            "name": "Loiter (2 hours)", "duration_minutes":155,
            "target_thrust_N": 0.15*T_to, 
            "flight_conditions": {"mach_0": 0.25, "ts_0": 285.2, "ps_0": 95970}, # 1500ft
            "engine_params_override": {"tt_4": 950},
            "ei_nox": 0.005
        },
        {
            "name": "Descent (to Diversion Airport)", "duration_minutes": 15,
            "target_thrust_N": 0.08*T_to,
            "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 900},
            "ei_nox": 0.006
        },
        {
            "name": "Landing (at Diversion Airport)", "duration_minutes": 5,
            "target_thrust_N": 0.30*T_to, 
            "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1000},
            "ei_nox": 0.008
        },
        {
            "name": "Taxi & Shutdown (at Diversion Airport)", "duration_minutes": 15,
            "target_thrust_N": 0.07*T_to, # Approx 7% of 7540N
            "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850},
            "ei_nox": 0.004
        },
    ]

    total_mission_emissions = {
        "m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0
    }
    total_fuel_used_kg = 0.0 # Initialize total fuel used
    
    print("Attempting to use the external 'subsystems.propulsion.gas_property_relations' module.")
    print("If this script fails with a ModuleNotFoundError, ensure the module is correctly placed and accessible.\n")

    tsfc_lst = np.array([]) # Initialize TSFC list for all segments

    for segment_idx, segment in enumerate(mission_segments): # Added enumerate for segment index
        print(f"--- Processing Segment {segment_idx + 1}: {segment['name']} ---")

        dt_seconds = segment["duration_minutes"] * 60.0

        current_engine_params = baseline_engine_config.copy()
        current_engine_params.update(segment["flight_conditions"])
        if "engine_params_override" in segment:
            current_engine_params.update(segment["engine_params_override"])
        
        analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
        
        tf_results = None # Initialize tf_results to None
        segment_fuel_kg = nan # Initialize segment fuel to NaN

        try:
            tf_results = turbofan_parametric_analysis(
                mach_0=current_engine_params["mach_0"],
                ts_0=current_engine_params["ts_0"],
                ps_0=current_engine_params["ps_0"],
                **analysis_params 
            )
        except Exception as e:
            print(f"  ERROR during turbofan_parametric_analysis for segment {segment['name']}: {e}")
            print(f"  Problematic inputs might be: M0={current_engine_params['mach_0']}, Ts0={current_engine_params['ts_0']}, Ps0={current_engine_params['ps_0']}")
            print(f"  Engine params: {analysis_params}")
            tsfc = nan 
            segment_emissions_data = emissions(nan, segment["ei_nox"], dt=dt_seconds)

        if tf_results is not None and len(tf_results) > 1: # Check if tf_results was successfully assigned
            tsfc = tf_results[1]
        else: 
            tsfc = nan


        if isnan(tsfc) or tsfc <= 0: 
            print(f"  Warning: Invalid or zero TSFC ({tsfc}) calculated for segment {segment['name']}. Emissions will be NaN.")
            if tf_results is not None and len(tf_results) > 5:
                print_detailed_results(tf_results, f"Details for {segment['name']} (Invalid TSFC)")

            mdot_f = nan
            segment_emissions_data = emissions(mdot_f, segment["ei_nox"], dt=dt_seconds)
            # segment_fuel_kg remains nan
        else: # Valid TSFC path
            mdot_f = segment["target_thrust_N"] * tsfc
            segment_fuel_kg = mdot_f * dt_seconds # Calculate fuel for this segment
            print(f"  Flight Conditions: M0={current_engine_params['mach_0']}, Ts0={current_engine_params['ts_0']:.2f}K, Ps0={current_engine_params['ps_0']:.0f}Pa")
            tsfc_lst = np.append(tsfc_lst, tsfc) # Append valid TSFC to the list
            print(f"  Calculated TSFC: {tsfc:.4e} (kg_fuel/s)/N")
            print(f"  Target Thrust: {segment['target_thrust_N']:.0f} N")
            print(f"  Calculated Fuel Flow (mdot_f): {mdot_f:.4f} kg/s")
            print(f"  Fuel used this segment: {segment_fuel_kg:.2f} kg" if not isnan(segment_fuel_kg) else "  Fuel used this segment: NaN kg")


            segment_emissions_data = emissions(mdot_f, segment["ei_nox"], dt=dt_seconds)
            print(f"  Emissions for this segment (kg):")
            for species, mass in segment_emissions_data.items():
                if species.startswith("m_"): 
                    print(f"    {species}: {mass:.4f}" if not isnan(mass) else f"    {species}: NaN")
            
            # --- Added this block to print detailed results for successful segments ---
            if tf_results is not None and len(tf_results) > 5:
                print_detailed_results(tf_results, f"Details for {segment['name']} (Successful TSFC)")
            # ----------------------------------------------------------------------
        
        # Accumulate total fuel
        if not isnan(segment_fuel_kg):
            if not isnan(total_fuel_used_kg): # Only add if total is not already NaN
                total_fuel_used_kg += segment_fuel_kg
        else:
            total_fuel_used_kg = nan # If any segment fuel is NaN, total becomes NaN


        for species_mass_key in total_mission_emissions.keys():
            if not isnan(segment_emissions_data.get(species_mass_key, nan)): 
                if not isnan(total_mission_emissions[species_mass_key]): # Only add if total for this species is not already NaN
                    total_mission_emissions[species_mass_key] += segment_emissions_data[species_mass_key]
            else: 
                total_mission_emissions[species_mass_key] = nan 
        print("-" * 40)
        # Removed del locals()['tf_results'] as it's better to let it be redefined or go out of scope naturally

    print("\n--- Total Mission Summary ---")
    print(f"  Total Fuel Used: {total_fuel_used_kg:.2f} kg" if not isnan(total_fuel_used_kg) else "  Total Fuel Used: NaN kg")
    for species, total_mass in total_mission_emissions.items():
        print(f"  Total {species}: {total_mass:.2f} kg" if not isnan(total_mass) else f"  Total {species}: NaN kg")

    print("\nSimulation Finished.")

    return {"TSFC (kg/(Ns))": tsfc_lst, "Total Fuel Used (kg)": float(total_fuel_used_kg)}

if __name__ == '__main__':
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")
    results = run_mission_simulation(params)