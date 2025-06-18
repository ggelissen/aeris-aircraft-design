#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
from math import sqrt, nan, isnan, log
import sys 
import os 
import numpy as np
import matplotlib.pyplot as plt

# --- Path setup to import project modules ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from utils.unit_conversions import * 
from design_variables import DesignParameters
import subsystems.propulsion.gas_property_relations as gpr

# --- ISA Atmosphere and NOx Calculation ---
class atmosphere:
    @staticmethod
    def get_altitude_from_pressure(p):
        p_sl = 101325.
        p_11k = 22632.1
        if p > p_11k:
             h = (288.15 / 0.0065) * (1 - (p / p_sl) ** (0.190263))
        else:
             h = 11000 - (287.05 * 216.65 / 9.80665) * log(p / p_11k)
        return h

def ei_nox_dallara(pt_3, tt_3, h):
    if any(isnan(val) for val in [pt_3, tt_3, h]):
        return nan
    ei = (2 + 28.5 * ((pt_3 / 1000) / 3100) ** 0.5 * np.exp((tt_3 - 825) / 250)) / 1000
    return ei

# --- Corrected Emissions Calculation ---
def emissions(mdot_f, ei_nox,
              ei_so4=2.0e-4, ei_soot=4.0e-5,
              ei_co2=3.16, ei_h2o=1.26,
              dt=1.):
    if isnan(mdot_f) or isnan(dt):
        return {"m_nox": nan, "m_co2": nan, "m_h2o": nan, "m_so4": nan, "m_soot": nan}
    
    m_nox = mdot_f * ei_nox * dt if not isnan(ei_nox) else nan
    m_co2 = mdot_f * ei_co2 * dt
    m_h2o = mdot_f * ei_h2o * dt
    m_so4 = mdot_f * ei_so4 * dt
    m_soot = mdot_f * ei_soot * dt

    return {"m_nox": m_nox, "m_co2": m_co2, "m_h2o": m_h2o, "m_so4": m_so4, "m_soot": m_soot}

# --- Corrected Full Turbofan Analysis Function ---
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

    # 0 - freestream
    a_0 = gpr.s_o_s(ts_0, gas="air")
    v_0 = mach_0 * a_0 if not (isnan(mach_0) or isnan(a_0)) else nan
    state_0_delta_h = 0.5 * v_0 ** 2 if not isnan(v_0) else nan
    state_0 = gpr.prescribed_delta_h(p_in=ps_0, t_in=ts_0, delta_h=state_0_delta_h, eta_pol=1., gas="air")
    pt_0, tt_0 = state_0["p_out"], state_0["t_out"]
    hs_0 = gpr.specific_enthalpy(t=ts_0, gas="air")
    ht_0 = hs_0 + v_0 ** 2. / 2. if not (isnan(hs_0) or isnan(v_0)) else nan
    
    # 2 - inlet exit / fan entry
    tt_2 = tt_0
    pt_2 = pr_inl * pt_0 if not (isnan(pr_inl) or isnan(pt_0)) else nan
    ht_2 = ht_0

    # Component Calculations
    state_13 = gpr.prescribed_p_ratio(p_in=pt_2, t_in=tt_2, p_ratio=pr_fan, eta_pol=eta_fan, gas="air")
    pt_13, tt_13, ht_13 = state_13["p_out"], state_13["t_out"], state_13["h_out"]
    state_25 = gpr.prescribed_p_ratio(p_in=pt_13, t_in=tt_13, p_ratio=pr_lpc, eta_pol=eta_lpc, gas="air")
    pt_25, tt_25, ht_25 = state_25["p_out"], state_25["t_out"], state_25["h_out"]
    state_3 = gpr.prescribed_p_ratio(p_in=pt_25, t_in=tt_25, p_ratio=pr_hpc, eta_pol=eta_hpc, gas="air")
    pt_3, tt_3, ht_3 = state_3["p_out"], state_3["t_out"], state_3["h_out"]

    # 4 - Combustor exit (Robust Solver)
    far_4 = nan
    ht_4 = nan
    if not any(isnan(val) for val in [ht_3, tt_3, tt_4, eta_com, lhv]) and lhv > 0 and eta_com > 0:
        cp_approx_comb = 1150.
        if tt_4 > tt_3:
            far_4_current = (cp_approx_comb * (tt_4 - tt_3)) / (eta_com * lhv - cp_approx_comb * (tt_4 - tt_3)) if (eta_com * lhv - cp_approx_comb * (tt_4 - tt_3)) !=0 else 0.02
            far_4_current = max(0.001, min(far_4_current, 0.07))
        else:
            far_4_current = 0.0001
        far_4_previous = far_4_current + 1.0
        iterations = 0
        while abs(far_4_current - far_4_previous) > 1e-7 and iterations < 100:
            far_4_previous = far_4_current
            h_comb_exit_target_temp = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4_previous)
            if isnan(h_comb_exit_target_temp): far_4_candidate = nan; break
            denominator = eta_com * lhv - h_comb_exit_target_temp
            if abs(denominator) < 1e-3: far_4_candidate = far_4_previous; break
            numerator = h_comb_exit_target_temp - ht_3
            far_4_candidate = numerator / denominator
            if isnan(far_4_candidate): break
            far_4_current = far_4_previous + 0.6 * (far_4_candidate - far_4_previous)
            far_4_current = max(0.00001, min(far_4_current, 0.1))
            iterations += 1
        if abs(far_4_current - far_4_previous) <= 1e-7 and not isnan(far_4_current):
            far_4 = far_4_current
        else:
            far_4 = nan
    if not isnan(far_4):
        ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4)
        if isnan(ht_4): far_4 = nan
    else:
        ht_4 = nan
    pt_4 = pt_3 * pr_com
    
    # Turbine calculations...
    # (This section is complex and relies on the intermediate tau values, taken from mainprop.py)
    tau_0 = ht_0 / hs_0 if hs_0 != 0 else nan
    tau_fan = ht_13 / ht_2 if ht_2 != 0 else nan
    tau_lpc = ht_25 / ht_13 if ht_13 != 0 else nan
    tau_hpc = ht_3 / ht_25 if ht_25 != 0 else nan
    tau_lambda = ht_4 / hs_0 if hs_0 != 0 and not isnan(ht_4) else nan
    
    power_toh_nondim = power_toh / hs_0 if hs_0 != 0 else 0.0
    power_tol_nondim = power_tol / hs_0 if hs_0 != 0 else 0.0

    num_tau_hpt = tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh_nondim
    den_tau_hpt_bracket_term = cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda if tau_lambda != 0 else nan
    den_tau_hpt_bracket = (1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + den_tau_hpt_bracket_term if not isnan(den_tau_hpt_bracket_term) and not isnan(far_4) else nan
    den_tau_hpt = eta_mech_h * tau_lambda * den_tau_hpt_bracket if not isnan(den_tau_hpt_bracket) else nan
    tau_hpt = 1. - (num_tau_hpt / den_tau_hpt) if not isnan(den_tau_hpt) and den_tau_hpt != 0 else nan

    num_tau_lpt = tau_0 * (tau_fan * (tau_lpc - 1) + (1. + bpr) * (tau_fan - 1)) + (1. + bpr) * power_tol_nondim
    den_tau_lpt_bracket_term = (cooling_h + cooling_l/tau_hpt if tau_hpt !=0 else nan) * tau_0 * tau_lpc * tau_hpc / tau_lambda if tau_lambda != 0 else nan
    den_tau_lpt_bracket = (1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + den_tau_lpt_bracket_term if not isnan(den_tau_lpt_bracket_term) and not isnan(far_4) else nan
    den_tau_lpt = eta_mech_l * tau_lambda * tau_hpt * den_tau_lpt_bracket if not isnan(den_tau_lpt_bracket) and not isnan(tau_hpt) and tau_lambda !=0 else nan
    tau_lpt = 1. - (num_tau_lpt / den_tau_lpt) if not isnan(den_tau_lpt) and den_tau_lpt != 0 else nan
    
    ht_41, ht_44, ht_45, ht_5 = nan, nan, nan, nan
    tt_41, tt_44, tt_45, tt_5 = nan, nan, nan, nan
    pt_41, pt_44, pt_45, pt_5 = nan, nan, nan, nan
    far_41, far_45 = nan, nan
    
    if not any(isnan(val) for val in [ht_4, tau_hpt, tau_lpt]):
        ht_41 = ht_4 # Simplified mixing for now
        tt_41 = tt_4
        pt_41 = pt_4
        far_41 = far_4
        
        ht_44 = ht_41 * tau_hpt
        state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41, delta_h=ht_44-ht_41, eta_pol=eta_hpt, gas="kerosene_in_air", far=far_41)
        pt_44, tt_44 = state_44["p_out"], state_44["t_out"]

        ht_45 = ht_44 # Simplified mixing
        tt_45 = tt_44
        pt_45 = pt_44
        far_45 = far_41

        ht_5 = ht_45 * tau_lpt
        state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45, delta_h=ht_5 - ht_45, eta_pol=eta_lpt, gas="kerosene_in_air", far=far_45)
        pt_5, tt_5 = state_5["p_out"], state_5["t_out"]

    # Robust Nozzle Calculations
    # Core Nozzle (station 9)
    ht_9, tt_9, pt_9, far_9 = ht_5, tt_5, pt_5, far_45
    mach_9, ps_9, ts_9, v_9, rho_9 = nan, nan, nan, nan, nan
    if not any(isnan(x) for x in [pt_9, ps_0, tt_9, far_9]) and ps_0 != 0:
        p_ratio_9 = pt_9 / ps_0
        g_9 = gpr.gamma_gas(tt_9, gas="kerosene_in_air", far=far_9)
        if not isnan(g_9) and g_9 > 1 and p_ratio_9 > 0:
            pr_crit_9 = ((g_9 + 1.) / 2.)**(g_9 / (g_9 - 1.)) if (g_9 - 1.) != 0 else nan
            if not isnan(pr_crit_9) and p_ratio_9 >= pr_crit_9:  # Choked
                mach_9 = 1.0
                ts_9 = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
                ps_9 = pt_9 / pr_crit_9
            else:  # Unchoked
                mach_i_9_sq_term = p_ratio_9**((g_9 - 1.) / g_9) - 1.
                if mach_i_9_sq_term >= 0 and (g_9-1) != 0:
                    mach_9 = sqrt((2. / (g_9 - 1.)) * mach_i_9_sq_term)
                else: mach_9 = 0.0
                ts_9 = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
                ps_9 = ps_0
            a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
            v_9 = mach_9 * a_9 if not isnan(a_9) else nan
            r_9 = gpr.r_gas(gas="kerosene_in_air", far=far_9)
            rho_9 = ps_9 / (r_9 * ts_9) if not any(isnan(val) for val in [ps_9, r_9, ts_9]) and (r_9*ts_9)!=0 else nan

    # Bypass Nozzle (station 19)
    ht_19, tt_19, pt_19, far_19 = ht_13, tt_13, pt_13, 0.0
    mach_19, ps_19, ts_19, v_19, rho_19 = nan, nan, nan, nan, nan
    if not any(isnan(x) for x in [pt_19, ps_0, tt_19]) and ps_0 != 0:
        p_ratio_19 = pt_19 / ps_0
        g_19 = gpr.gamma_gas(tt_19, gas="air", far=far_19)
        if not isnan(g_19) and g_19 > 1 and p_ratio_19 > 0:
            pr_crit_19 = ((g_19 + 1.) / 2.)**(g_19 / (g_19 - 1.)) if (g_19 - 1.) != 0 else nan
            if not isnan(pr_crit_19) and p_ratio_19 >= pr_crit_19:  # Choked
                mach_19 = 1.0
                ts_19 = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
                ps_19 = pt_19 / pr_crit_19
            else:  # Unchoked
                mach_i_19_sq_term = p_ratio_19**((g_19 - 1.) / g_19) - 1.
                if mach_i_19_sq_term >= 0 and (g_19-1)!=0:
                    mach_19 = sqrt((2. / (g_19 - 1.)) * mach_i_19_sq_term)
                else: mach_19 = 0.0
                ts_19 = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
                ps_19 = ps_0
            a_19 = gpr.s_o_s(ts_19, gas="air", far=far_19) if not isnan(ts_19) else nan
            v_19 = mach_19 * a_19 if not isnan(a_19) else nan
            r_19 = gpr.r_gas(gas="air", far=far_19)
            rho_19 = ps_19 / (r_19 * ts_19) if not any(isnan(val) for val in [ps_19, r_19, ts_19]) and (r_19*ts_19)!=0 else nan

    # Final Performance Calculation
    sf = nan
    if not any(isnan(x) for x in [bleed_to, far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19]):
        net_thrust_norm = ((1.-bleed_to)*(1.+far_4)*v_9 + bpr*v_19) - (1.+bpr)*v_0
        if not (rho_9 == 0 or v_9 == 0):
            net_thrust_norm += (ps_9 - ps_0) * (1.-bleed_to)*(1.+far_4) / (rho_9 * v_9)
        if not (rho_19 == 0 or v_19 == 0):
            net_thrust_norm += (ps_19 - ps_0) * bpr / (rho_19 * v_19)
        if (1.+bpr) != 0:
            sf = net_thrust_norm / (1.+bpr)
    
    tsfc = nan
    fuel_flow_norm = far_4 * (1. - bleed_to - cooling_l - cooling_h) if not isnan(far_4) else nan
    if not isnan(fuel_flow_norm) and not isnan(sf) and sf != 0:
        tsfc = (fuel_flow_norm / (1.+bpr)) / sf

    output_dict = {'pt_3': pt_3, 'tt_3': tt_3, 'sf': sf, 'tsfc': tsfc}
    return sf, tsfc, nan, nan, nan, output_dict

# --- Main Simulation Runner ---
def run_mission_simulation_comparison():
    print("Starting Aircraft Mission Comparison Simulation...\n")

    T_TO_AERIS = 8232
    T_TO_HALO = 121478
    T_TO_PHLAB = 19423
    T_CRUISE_AERIS = 1324

    aircraft_configs = {
        "AERIS": {
            "num_engines": 1,
            "baseline_engine_config": { "bpr": 3.3, "pr_fan": 1.9, "pr_lpc": 1.5, "pr_hpc": 5.65, "tt_4": 1400., "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TO_AERIS, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1400}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.55, "ts_0": 242.7, "ps_0": 46560}, "engine_params_override": {"tt_4": 1300}},
                {"name": "Cruise", "duration_minutes": 120, "target_thrust_N": T_CRUISE_AERIS, "flight_conditions": {"mach_0": 0.7, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1200}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 900}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.30, "ts_0": 282.65, "ps_0": 95970}, "engine_params_override": {"tt_4": 950}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1000}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TO_AERIS, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
            ]
        },
        "HALO": {
            "num_engines": 2,
            "baseline_engine_config": { "bpr": 4.2, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 24.0, "tt_4": 1500., "eta_fan": 0.92, "eta_lpc": 0.91, "eta_hpc": 0.90, "eta_hpt": 0.93, "eta_lpt": 0.94, "lhv": 43.e6, "cooling_h": 0.05, "cooling_l": 0.03 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TO_HALO, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TO_HALO, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 950}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TO_HALO, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1600}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.90 * T_TO_HALO, "flight_conditions": {"mach_0": 0.65, "ts_0": 235.2, "ps_0": 34567}, "engine_params_override": {"tt_4": 1500}},
                {"name": "Cruise", "duration_minutes": 400, "target_thrust_N": 0.3 * T_TO_HALO, "flight_conditions": {"mach_0": 0.85, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1400}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TO_HALO, "flight_conditions": {"mach_0": 0.55, "ts_0": 242.7, "ps_0": 55720}, "engine_params_override": {"tt_4": 1000}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TO_HALO, "flight_conditions": {"mach_0": 0.35, "ts_0": 268.65, "ps_0": 75271}, "engine_params_override": {"tt_4": 980}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TO_HALO, "flight_conditions": {"mach_0": 0.28, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1100}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TO_HALO, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
            ]
        },
        "PH-LAB (Citation II)": {
            "num_engines": 2,
            "baseline_engine_config": { "bpr": 2.6, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 7, "tt_4": 1200, "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 800}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TO_PHLAB, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1300}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.60, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1200}},
                {"name": "Cruise", "duration_minutes": 120, "target_thrust_N": 0.3 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.7, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1100}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 900}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.28, "ts_0": 285.2, "ps_0": 95970}, "engine_params_override": {"tt_4": 880}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 950}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TO_PHLAB, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 800}},
            ]
        }
    }

    results_per_aircraft = {}

    for aircraft_name, config in aircraft_configs.items():
        print(f"\n===== Simulating: {aircraft_name} =====\n")
        
        total_fuel_kg = 0.0
        total_emissions = {"m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0}
        num_engines = config["num_engines"]
        
        for i, segment in enumerate(config["mission_segments"]):
            print(f"--- Processing Segment {i+1}/{len(config['mission_segments'])}: {segment['name']} ---")
            dt_seconds = segment["duration_minutes"] * 60.0

            current_engine_params = config["baseline_engine_config"].copy()
            current_engine_params.update(segment["flight_conditions"])
            if "engine_params_override" in segment:
                current_engine_params.update(segment["engine_params_override"])

            # **FIX**: Divide total aircraft thrust by the number of engines
            target_thrust_per_engine = segment["target_thrust_N"] / num_engines
            
            analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
            
            try:
                tf_results = turbofan_parametric_analysis(mach_0=current_engine_params["mach_0"], ts_0=current_engine_params["ts_0"], ps_0=current_engine_params["ps_0"], **analysis_params)
                tsfc = tf_results[1]
                
                if isnan(tsfc) or tsfc <= 0:
                    print(f"  Warning: Invalid TSFC ({tsfc}) for {segment['name']}. Skipping segment.")
                    continue

                mdot_f_per_engine = target_thrust_per_engine * tsfc
                segment_fuel_kg = mdot_f_per_engine * dt_seconds * num_engines
                total_fuel_kg += segment_fuel_kg

                output_dict = tf_results[5]
                tt_3 = output_dict.get('tt_3', nan)
                pt_3 = output_dict.get('pt_3', nan)
                h_alt = atmosphere.get_altitude_from_pressure(current_engine_params["ps_0"])
                ei_nox = ei_nox_dallara(pt_3, tt_3, h_alt)
                
                segment_emissions_data = emissions(mdot_f_per_engine * num_engines, ei_nox, dt=dt_seconds)
                for key in total_emissions:
                    if not isnan(segment_emissions_data.get(key, nan)):
                        total_emissions[key] += segment_emissions_data[key]

                print(f"  Thrust per engine: {target_thrust_per_engine:.0f} N, TSFC: {tsfc:.4e}, Total Fuel: {segment_fuel_kg:.2f} kg")

            except Exception as e:
                print(f"  ERROR during analysis for segment {segment['name']}: {e}")

        results_per_aircraft[aircraft_name] = {"Total Fuel (kg)": total_fuel_kg, "Total Emissions (kg)": total_emissions}
        print(f"\n--- Total for {aircraft_name} ---")
        print(f"  Total Fuel Used: {total_fuel_kg:.2f} kg")
        for species, mass in total_emissions.items():
            print(f"  Total {species.replace('m_', '').upper()}: {mass:.2f} kg")

    # Optional: Add back the comparison logic if needed

    return results_per_aircraft

if __name__ == '__main__':
    run_mission_simulation_comparison()