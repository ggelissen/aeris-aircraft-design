#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
from math import sqrt, nan, isnan, log # Added nan, isnan, log for handling potential NaN values and altitude calc
import sys # For potential path debugging
import os  # For potential path debugging

# --- Mock imports for stand-alone execution ---
# In a real scenario, these would be your actual project modules.
try:
    # Attempt to import from the project structure
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from utils.unit_conversions import *
    from design_variables import DesignParameters
    import gas_property_relations as gpr
except (ImportError, ModuleNotFoundError):
    print("Warning: Could not import project modules. Using mock objects for stand-alone execution.")
    # Define placeholder classes/functions if the real ones aren't found
    # class MockGPR:
    #     """A mock class to simulate gas_property_relations for stand-alone run."""
    #     def s_o_s(self, t, gas="air", far=0.): return sqrt(1.4 * 287 * t) if not isnan(t) else nan
    #     def specific_enthalpy(self, t, gas="air", far=0.): return 1005 * t if not isnan(t) else nan
    #     def prescribed_delta_h(self, p_in, t_in, delta_h, eta_pol, gas="air", far=0.):
    #         if any(isnan(x) for x in [p_in, t_in, delta_h, eta_pol]): return {"p_out": nan, "t_out": nan, "h_out": nan}
    #         h_in = self.specific_enthalpy(t_in)
    #         h_out = h_in + delta_h
    #         t_out = h_out / 1005.
    #         cp = 1005.
    #         gamma = 1.4
    #         r = 287.
    #         # Simplified isentropic relation for pressure
    #         if delta_h > 0: # Compression
    #             p_out = p_in * (1 + (eta_pol * delta_h) / (cp * t_in))**(gamma/(gamma-1))
    #         else: # Expansion
    #             p_out = p_in * (1 + delta_h / (cp * t_in * eta_pol))**(gamma/(gamma-1))
    #         return {"p_out": p_out, "t_out": t_out, "h_out": h_out}

    #     def prescribed_p_ratio(self, p_in, t_in, p_ratio, eta_pol, gas="air", far=0.):
    #         if any(isnan(x) for x in [p_in, t_in, p_ratio, eta_pol]): return {"p_out": nan, "t_out": nan, "h_out": nan}
    #         gamma = 1.4
    #         cp = 1005.
    #         p_out = p_in * p_ratio
    #         # Simplified temperature change for compression
    #         t_out = t_in * (1 + (p_ratio**((gamma-1)/gamma) - 1) / eta_pol)
    #         h_out = self.specific_enthalpy(t_out)
    #         return {"p_out": p_out, "t_out": t_out, "h_out": h_out}
    #     def prescribed_h(self, h, gas="air", far=0.): return h / 1005. if not isnan(h) else nan
    #     def t_total_to_static(self, tt, m, gas="air", far=0.):
    #         gamma = 1.4
    #         return tt / (1 + (gamma-1)/2 * m**2) if not any(isnan(x) for x in [tt, m]) else nan
    #     def gamma_gas(self, t, gas="air", far=0.): return 1.4
    #     def r_gas(self, gas="air", far=0.): return 287.0
    # gpr = MockGPR()

    # class DesignParameters:
    #     """A mock DesignParameters class."""
    #     def __init__(self):
    #         self.engine = type('engine', (object,), {})()
    #         self.engine.Bpr = 3.3
    #         self.engine.prfan = 1.9
    #         self.engine.prlpc = 1.5
    #         self.engine.prhpc = 5.65
    #         self.engine.etafan = 0.915
    #         self.engine.etalpc = 0.9
    #         self.engine.etahpc = 0.9
    #         self.engine.etahpt = 0.93
    #         self.engine.etalpt = 0.93
    #         self.engine.etacom = 0.99
    #         self.engine.etamechl = 0.99
    #         self.engine.etamechh = 0.99
    #         self.engine.prcom = 0.99
    #         self.engine.prinlet = 0.98
    #         self.engine.bleedto = 0.0
    #         self.engine.power_tol = 0.0
    #         self.engine.power_toh = 0.0
    #         self.engine.cooling_l = 0.0
    #         self.engine.cooling_h = 0.0
    #         self.engine.lhv = 43.e6
    #         self.engine.T_TO = 7535. # N
    #         self.engine.T_cruise = 1800. 
    #     def load_from_yaml(self, filepath):
    #          print(f"Mock loading parameters from {filepath}")



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
        # Stratosphere from 11km to 20km
        elif h <= 20000:
            t = 216.65
        # Stratosphere from 20km to 32km
        else:
             t = 216.65 + 0.001 * (h - 20000)
        return t + delta_t_0

    @staticmethod
    def pressure(h):
        """
        Returns ISA pressure at altitude h (meters).
        """
        # Troposphere up to 11km
        if h < 11000:
            p = 101325 * (1 - 0.0065 * h / 288.15) ** 5.2561
        # Stratosphere from 11km to 20km
        elif h <= 20000:
            p = 22632.1 * np.exp(-9.80665 * (h - 11000) / (287.05 * 216.65))
        # Stratosphere from 20km to 32km
        else:
            p = 5474.89 * (1 + 0.001 * (h - 20000)/216.65) ** (-9.80665/(0.001*287.05))
        return p

    @staticmethod
    def get_altitude_from_pressure(p):
        """
        Estimates altitude (meters) from static pressure (Pa) based on ISA model.
        """
        p_sl = 101325.  # Pa
        p_11k = 22632.1 # Pa

        if p > p_11k: # Troposphere
             # h = (288.15 / 0.0065) * (1 - (p / p_sl) ** (1 / 5.2561))
             h = (288.15 / 0.0065) * (1 - (p / p_sl) ** (0.190263))
        else: # Stratosphere (up to 20km)
             h = 11000 - (287.05 * 216.65 / 9.80665) * log(p / p_11k)
        return h

    @staticmethod
    def saturation_vapor_pressure(t):
        """
        Returns saturation vapor pressure (Pa) at temperature t (K).
        """
        t_c = t - 273.15
        return 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))

    @staticmethod
    def specific_humidity(h, relative_humidity=0.6, delta_t_0=0.):
        """
        Returns specific humidity (g/kg) at altitude h (meters), relative humidity (0-1), and delta_t_0 (K).
        """
        t = atmosphere.temperature(h, delta_t_0)
        p = atmosphere.pressure(h)
        e_s = atmosphere.saturation_vapor_pressure(t)
        e = relative_humidity * e_s
        # Specific humidity (kg/kg)
        q = 0.622 * e / (p - (1 - 0.622) * e)
        return q * 1000  # Convert to g/kg

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
    :return: Emission index of NOx in kg_NOx/kg_fuel
    """
    if any(isnan(val) for val in [pt_3, tt_3, h]):
        return nan
        
    # humid = atmosphere.specific_humidity(h=h,
    #                                      relative_humidity=relative_humidity,
    #                                      delta_t_0=delta_t_isa)
    # The core formula
    ei = (2+28.5*((pt_3/1000)/3100)**0.5 * np.exp((tt_3-825)/250))/1000 #kg/kg

    return ei

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
            if isnan(ht_4i):
                far_4 = nan
                break
            denominator = (eta_com * lhv - ht_4i)
            if denominator == 0 or isnan(ht_3):
                far_4 = nan
                break
            far_4 = (ht_4i - ht_3) / denominator
            if isnan(far_4): break
            it += 1
        if it >= 50 and abs(far_4 - far_4i) > 0.00001 : far_4 = nan

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
        if g_9 > 1. and p_total_static_ratio_9 > 1:
            mach_i_9_sq_term = p_total_static_ratio_9 ** ((g_9 - 1.) / g_9) - 1.
            mach_i_9_sq = (2. / (g_9 - 1.)) * mach_i_9_sq_term
            mach_i_9 = sqrt(mach_i_9_sq)
            mach_9 = 1. if mach_i_9 >= 1. else mach_i_9
        else: mach_9 = 0.0

        ts_9 = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
        g_ts9 = gpr.gamma_gas(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        if not (isnan(g_ts9) or g_ts9 == 1 or isnan(tt_9) or isnan(ts_9) or ts_9 == 0):
            ps_9 = pt_9 / ((tt_9 / ts_9) ** (g_ts9 / (g_ts9 - 1.)))
        else: ps_9 = ps_0

        a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        v_9 = mach_9 * a_9 if not (isnan(mach_9) or isnan(a_9)) else nan
        r_9 = gpr.r_gas(gas="kerosene_in_air", far=far_9)
        rho_9 = ps_9 / (r_9 * ts_9) if not (isnan(ps_9) or isnan(r_9) or isnan(ts_9) or r_9 * ts_9 == 0) else nan

    # 19 - Bypass exhaust nozzle
    ht_19, tt_19, pt_19, far_19 = ht_13, tt_13, pt_13, 0.
    mach_19, ps_19, ts_19, v_19, rho_19 = nan, nan, nan, nan, nan

    if not isnan(pt_19) and not isnan(ps_0) and ps_0 != 0 and not isnan(tt_19):
        p_total_static_ratio_19 = pt_19 / ps_0
        g_19 = gpr.gamma_gas(tt_19, gas="air", far=far_19)
        if g_19 > 1. and p_total_static_ratio_19 > 1:
            mach_i_19_sq = (2. / (g_19 - 1.)) * (p_total_static_ratio_19 ** ((g_19 - 1.) / g_19) - 1.)
            mach_i_19 = sqrt(mach_i_19_sq)
            mach_19 = 1. if mach_i_19 >= 1. else mach_i_19
        else: mach_19 = 0.0

        ts_19 = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
        g_ts19 = gpr.gamma_gas(ts_19, gas="air", far=far_19) if not isnan(ts_19) else nan
        if not (isnan(g_ts19) or g_ts19 == 1 or isnan(tt_19) or isnan(ts_19) or ts_19 == 0):
            ps_19 = pt_19 / ((tt_19 / ts_19) ** (g_ts19 / (g_ts19 - 1.)))
        else: ps_19 = ps_0

        a_19 = gpr.s_o_s(ts_19, gas="air") if not isnan(ts_19) else nan
        v_19 = mach_19 * a_19 if not (isnan(mach_19) or isnan(a_19)) else nan
        r_19 = gpr.r_gas(gas="air", far=far_19)
        rho_19 = ps_19 / (r_19 * ts_19) if not (isnan(ps_19) or isnan(r_19) or isnan(ts_19) or r_19*ts_19 == 0) else nan

    sf = nan
    if not any(isnan(x) for x in [bleed_to, far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19]):
        if (1. + bpr) != 0:
            sf_term1 = (1. - bleed_to) * (1. + far_4) * v_9
            sf_term2 = bpr * v_19
            sf_term3 = (1. + bpr) * v_0
            sf_pressure_core = (ps_9 - ps_0) * (1 - bleed_to) * (1. + far_4) / (rho_9 * v_9) if not (isnan(rho_9) or rho_9 == 0 or isnan(v_9) or v_9 == 0) else 0.
            sf_pressure_bypass = (ps_19 - ps_0) * bpr / (rho_19 * v_19) if not (isnan(rho_19) or rho_19 == 0 or isnan(v_19) or v_19 == 0) else 0.
            sf_gross = sf_term1 + sf_term2 + sf_pressure_core + sf_pressure_bypass
            sf = (sf_gross - sf_term3) / (1. + bpr)
    
    tsfc = nan
    if not (isnan(far_4) or isnan(sf) or sf == 0 or isnan(bpr) or (1.+bpr) == 0):
        tsfc_den = sf * (1. + bpr)
        if tsfc_den != 0:
            tsfc = (far_4 * (1. - bleed_to - cooling_l - cooling_h)) / tsfc_den
    
    opr = pr_fan * pr_lpc * pr_hpc if not any(isnan(x) for x in [pr_fan, pr_lpc, pr_hpc]) else nan

    eta_thermal, eta_propulsive, eta_overall = nan, nan, nan
    
    v_19_id = v_19 + (ps_19 - ps_0) / (rho_19 * v_19) if not any(isnan(x) or x==0 for x in [v_19, rho_19, ps_19, ps_0]) else v_19
    v_9_id = v_9 + (ps_9 - ps_0) / (rho_9 * v_9) if not any(isnan(x) or x==0 for x in [v_9, rho_9, ps_9, ps_0]) else v_9

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
        pt_3=pt_3, tt_3=tt_3, pt_5=pt_5, tt_5=tt_5,
        eta_thermal=eta_thermal, eta_propulsive=eta_propulsive, eta_overall=eta_overall
    )

    if full_output:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    else:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall

def print_detailed_results(results, engine_name="Engine Run"):
    """Prints the turbofan analysis results."""
    if results is None or len(results) < 5: 
        print(f"\n--- {engine_name}: Incomplete or No Results ---")
        return

    sf, tsfc, eta_thermal, eta_propulsive, eta_overall = results[:5]
    print(f"\n--- {engine_name}: Performance Metrics ---")
    print(f"  Specific Thrust (SF):                   {sf:.2f} N/(kg/s)" if not isnan(sf) else "  Specific Thrust (SF):                   N/A")
    print(f"  Thrust Specific Fuel Consumption (TSFC):  {tsfc*1e6:.2f} mg/(N·s)" if not isnan(tsfc) else "  Thrust Specific Fuel Consumption (TSFC):  N/A")
    print(f"  Thermal Efficiency (eta_thermal):         {eta_thermal*100:.2f}%" if not isnan(eta_thermal) else "  Thermal Efficiency (eta_thermal):         N/A")
    print(f"  Propulsive Efficiency (eta_propulsive):   {eta_propulsive*100:.2f}%" if not isnan(eta_propulsive) else "  Propulsive Efficiency (eta_propulsive):   N/A")
    print(f"  Overall Efficiency (eta_overall):         {eta_overall*100:.2f}%" if not isnan(eta_overall) else "  Overall Efficiency (eta_overall):         N/A")

# --- Main Mission Simulation ---
def run_mission_simulation(params: DesignParameters):
    print("Starting Aircraft Mission Emissions Simulation...\n")
    tsfc_lst = np.array([])
    baseline_engine_config = {
        "bpr": params.engine.Bpr, "pr_fan": params.engine.prfan, "pr_lpc": params.engine.prlpc, "pr_hpc": params.engine.prhpc, "tt_4": 1400.,
        "eta_fan": params.engine.etafan, "eta_lpc": params.engine.etalpc, "eta_hpc": params.engine.etahpc,
        "eta_hpt": params.engine.etahpt, "eta_lpt": params.engine.etalpt,
        "eta_com": params.engine.etacom, "eta_mech_l": params.engine.etamechl, "eta_mech_h": params.engine.etamechh,
        "pr_com": params.engine.prcom, "pr_inl": params.engine.prinlet,
        "bleed_to": params.engine.bleedto, "power_tol": params.engine.power_tol, "power_toh": params.engine.power_toh,
        "cooling_l": params.engine.cooling_l, "cooling_h": params.engine.cooling_h,
        "lhv": params.engine.lhv, 
        "full_output": True
    }
    T_to = params.engine.T_TO #N, takeoff thrust 
    T_Cruise = params.engine.cruise_thrust #N, cruise thrust
    mission_segments = [
        {
            "name": "Engine Start & Warm-Up", "duration_minutes": 10,
            "target_thrust_N": 0.07*T_to,
            "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850},
        },
        {
            "name": "Taxi", "duration_minutes": 10,
            "target_thrust_N": 0.12 * T_to,
            "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 900},
        },
        {
            "name": "Take-off", "duration_minutes": 5,
            "target_thrust_N": T_to,
            "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1400},
        },
        {
            "name": "Climb", "duration_minutes": 20,
            "target_thrust_N": 0.85*T_to ,
            "flight_conditions": {"mach_0": 0.65, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 1300},
        },
        {
            "name": "Cruise", "duration_minutes": 400,
            "target_thrust_N": T_Cruise,
            "flight_conditions": {"mach_0": 0.85, "ts_0": 216.65, "ps_0": 18753.9}, # 40000ft
            "engine_params_override": {"tt_4": 1200},
        },
        {
            "name": "Diversion Cruise (460km)", "duration_minutes": 30, # Approx. for 460km @ M0.75 / 30000ft
            "target_thrust_N": T_Cruise, # Estimated for diversion cruise
            "flight_conditions": {"mach_0": 0.85, "ts_0": 228.7, "ps_0": 30090}, # 30000ft
            "engine_params_override": {"tt_4": 1200},
        },
        {
            "name": "Loiter ", "duration_minutes": 120,
            "target_thrust_N": 0.15*T_to, # Estimated for loiter
            "flight_conditions": {"mach_0": 0.25, "ts_0": 285.2, "ps_0": 95970}, # 1500ft
            "engine_params_override": {"tt_4": 950},
        },
        {
            "name": "Descent", "duration_minutes": 15,
            "target_thrust_N": 0.08*T_to,
            "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 900},
        },
        {
            "name": "Landing", "duration_minutes": 5,
            "target_thrust_N": 0.30*T_to,
            "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1000},
        },
        {
            "name": "Taxi & Shutdown", "duration_minutes": 15,
            "target_thrust_N": 0.07*T_to,
            "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850},
        },
    ]

    total_mission_emissions = {"m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0}
    total_fuel_used_kg = 0.0

    tsfc_lst = np.array([])
    for segment_idx, segment in enumerate(mission_segments):
        print(f"--- Processing Segment {segment_idx + 1}: {segment['name']} ---")
        dt_seconds = segment["duration_minutes"] * 60.0

        current_engine_params = baseline_engine_config.copy()
        current_engine_params.update(segment["flight_conditions"])
        if "engine_params_override" in segment:
            current_engine_params.update(segment["engine_params_override"])
        
        analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
        
        tf_results = None
        segment_fuel_kg = nan
        ei_nox = nan

        try:
            tf_results = turbofan_parametric_analysis(
                mach_0=current_engine_params["mach_0"],
                ts_0=current_engine_params["ts_0"],
                ps_0=current_engine_params["ps_0"],
                **analysis_params 
            )
        except Exception as e:
            print(f"  ERROR during turbofan_parametric_analysis for segment {segment['name']}: {e}")
            tsfc = nan 
        
        if tf_results and len(tf_results) > 5:
            tsfc = tf_results[1]
            output_dict = tf_results[5]
            
            # DYNAMICALLY CALCULATE EI_NOX
            ps_0 = current_engine_params["ps_0"]
            h_est = atmosphere.get_altitude_from_pressure(ps_0)
            pt_3 = output_dict.get('pt_3', nan)
            tt_3 = output_dict.get('tt_3', nan)
            ei_nox = ei_nox_dallara(pt_3, tt_3, h_est)

            print(f"  Flight Conditions: M{current_engine_params['mach_0']}, Est. Alt {h_est:.0f}m")
            print(f"  Combustor Inlet: Tt3={tt_3:.1f}K, Pt3={pt_3/1e5:.2f}bar")
            print(f"  Calculated EI NOx: {ei_nox*1000:.2f} g/kg_fuel" if not isnan(ei_nox) else "  Calculated EI NOx: N/A")
        else:
            tsfc = nan

        if isnan(tsfc) or tsfc <= 0: 
            print(f"  Warning: Invalid TSFC ({tsfc}). Emissions will be NaN.")
            mdot_f = nan
        else: # Valid TSFC path
            mdot_f = segment["target_thrust_N"] * tsfc
            segment_fuel_kg = mdot_f * dt_seconds
            tsfc_lst = np.append(tsfc_lst, tsfc)
            print(f"  Calculated TSFC: {tsfc*1e6:.2f} mg/Ns")
            print(f"  Target Thrust: {segment['target_thrust_N']:.0f} N -> Fuel Flow: {mdot_f:.4f} kg/s")
            print(f"  Fuel used this segment: {segment_fuel_kg:.2f} kg")

        segment_emissions_data = emissions(mdot_f, ei_nox, dt=dt_seconds)
        print(f"  Emissions for this segment (kg):")
        print(f"    m_nox: {segment_emissions_data['m_nox']:.4f}" if not isnan(segment_emissions_data.get('m_nox', nan)) else "    m_nox: NaN")
        
        # Accumulate totals
        if not isnan(segment_fuel_kg):
            if not isnan(total_fuel_used_kg):
                total_fuel_used_kg += segment_fuel_kg
        else:
            total_fuel_used_kg = nan

        for species_mass_key in total_mission_emissions.keys():
            if not isnan(segment_emissions_data.get(species_mass_key, nan)): 
                if not isnan(total_mission_emissions[species_mass_key]):
                    total_mission_emissions[species_mass_key] += segment_emissions_data[species_mass_key]
            else: 
                total_mission_emissions[species_mass_key] = nan
        print("-" * 40)

    print("\n--- Total Mission Summary ---")
    print(f"  Total Fuel Used: {total_fuel_used_kg:.2f} kg" if not isnan(total_fuel_used_kg) else "  Total Fuel Used: NaN kg")
    for species, total_mass in total_mission_emissions.items():
        print(f"  Total {species}: {total_mass:.2f} kg" if not isnan(total_mass) else f"  Total {species}: NaN kg")

    print("\nSimulation Finished.")
    return {"TSFC (kg/(Ns))": tsfc_lst, "Total Fuel Used (kg)": float(total_fuel_used_kg)}

if __name__ == '__main__':
    # Initialize mock or real parameters
    params = DesignParameters()
    try:
        # If a real config file exists, use it
        params.load_from_yaml("design_config.yaml")
    except (FileNotFoundError, AttributeError):
        # Otherwise, the mock parameters in the class definition will be used
        print("Note: 'design_config.yaml' not found. Running with default mock parameters.")

    run_mission_simulation(params)