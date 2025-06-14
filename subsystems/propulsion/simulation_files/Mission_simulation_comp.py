#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
from math import sqrt, nan, isnan, log
import sys 
import os 
import numpy as np

# --- Corrected Path Setup ---
# This adds the project's root directory ('DSEGroup17') to the Python path,
# allowing it to find all sub-modules like 'utils' and 'subsystems'.
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
sys.path.append(project_root)

# --- Direct Module Imports ---
try:
    from utils.unit_conversions import *
    from design_variables import DesignParameters
    from subsystems.propulsion import gas_property_relations as gpr
    print("Successfully imported project modules.")
except (ImportError, ModuleNotFoundError) as e:
    print("---")
    print(f"WARNING: Could not import project modules ({e}). The script will terminate.")
    print("Please ensure your project structure is correct and all dependencies are installed.")
    print("---")
    sys.exit(1) # Exit if essential modules are missing

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

# --- Emissions Calculation ---
def emissions(mdot_f, ei_nox, dt=1., ei_co2=3.16, ei_h2o=1.26):
    if isnan(mdot_f) or isnan(dt):
        return {"m_nox": nan, "m_co2": nan, "m_h2o": nan}
    m_nox = mdot_f * ei_nox * dt if not isnan(ei_nox) else nan
    m_co2 = mdot_f * ei_co2 * dt
    m_h2o = mdot_f * ei_h2o * dt
    return {"m_nox": m_nox, "m_co2": m_co2, "m_h2o": m_h2o}

# --- Full Turbofan Analysis Function ---
def turbofan_parametric_analysis(mach_0, ts_0, ps_0, bpr, pr_fan, pr_lpc, pr_hpc, tt_4, eta_fan, eta_lpc, eta_hpc, eta_hpt, eta_lpt, eta_com=0.99, eta_mech_l=0.99, eta_mech_h=0.99, pr_com=0.95, pr_inl=0.98, bleed_to=0., power_tol=0., power_toh=0., cooling_l=0., cooling_h=0., lhv=43.e6, full_output=True):
    a_0 = gpr.s_o_s(ts_0); v_0 = mach_0 * a_0
    state_0_delta_h = 0.5 * v_0**2
    state_0 = gpr.prescribed_delta_h(p_in=ps_0, t_in=ts_0, delta_h=state_0_delta_h, eta_pol=1.)
    pt_0, tt_0 = state_0["p_out"], state_0["t_out"]
    hs_0 = gpr.specific_enthalpy(t=ts_0)
    ht_0 = hs_0 + 0.5 * v_0**2
    tt_2 = tt_0; pt_2 = pr_inl * pt_0; ht_2 = ht_0
    state_13 = gpr.prescribed_p_ratio(p_in=pt_2, t_in=tt_2, p_ratio=pr_fan, eta_pol=eta_fan)
    pt_13, tt_13, ht_13 = state_13["p_out"], state_13["t_out"], state_13["h_out"]
    state_25 = gpr.prescribed_p_ratio(p_in=pt_13, t_in=tt_13, p_ratio=pr_lpc, eta_pol=eta_lpc)
    pt_25, tt_25, ht_25 = state_25["p_out"], state_25["t_out"], state_25["h_out"]
    state_3 = gpr.prescribed_p_ratio(p_in=pt_25, t_in=tt_25, p_ratio=pr_hpc, eta_pol=eta_hpc)
    pt_3, tt_3, ht_3 = state_3["p_out"], state_3["t_out"], state_3["h_out"]
    far_4i = 0.02; far_4 = 0.03; it = 0
    while abs(far_4 - far_4i) > 1e-5 and it < 50:
        far_4i = far_4
        ht_4i = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4i)
        if isnan(ht_4i): far_4 = nan; break
        denominator = (eta_com * lhv - ht_4i)
        if denominator == 0: far_4 = nan; break
        far_4 = (ht_4i - ht_3) / denominator
        if isnan(far_4): break
        it += 1
    if it >= 50: far_4 = nan
    pt_4 = pt_3 * pr_com
    ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4)
    tau_lambda = ht_4 / hs_0
    tau_0 = ht_0 / hs_0
    tau_fan = ht_13 / ht_2
    tau_lpc = ht_25 / ht_13
    tau_hpc = ht_3 / ht_25
    den_tau_m1 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h)
    tau_m1 = (((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda)) / den_tau_m1 if den_tau_m1 != 0 else nan
    den_tau_hpt_expr = eta_mech_h * tau_lambda * ((1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda) if not isnan(far_4) else nan
    tau_hpt = (1. - (tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh/hs_0) / den_tau_hpt_expr) if den_tau_hpt_expr != 0 else nan
    ht_41 = ht_4 * tau_m1
    far_41 = far_4 / (1 + cooling_h / ((1 - bleed_to - cooling_h-cooling_l)*(1+far_4))) if ((1 - bleed_to - cooling_h-cooling_l)*(1+far_4))!=0 else nan
    pt_41 = pt_4
    tt_41 = gpr.prescribed_h(ht_41, gas="kerosene_in_air", far=far_41)
    ht_44 = ht_41 * tau_hpt
    delta_h_hpt = ht_44 - ht_41
    state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41, delta_h=delta_h_hpt, eta_pol=eta_hpt, gas="kerosene_in_air", far=far_41)
    pt_44, tt_44 = state_44["p_out"], state_44["t_out"]
    den_tau_m2 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + cooling_l)
    tau_m2 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + cooling_l * tau_0 * tau_lpc * tau_hpc / (tau_lambda * tau_m1 * tau_hpt)) / den_tau_m2 if den_tau_m2!=0 and not any(isnan(x) for x in [tau_lambda, tau_m1, tau_hpt]) and (tau_lambda*tau_m1*tau_hpt)!=0 else nan
    ht_45 = ht_44 * tau_m2
    far_45 = far_4 / (1 + (cooling_l + cooling_h) / ((1 - bleed_to - cooling_h-cooling_l)*(1+far_4))) if ((1 - bleed_to - cooling_h-cooling_l)*(1+far_4)) != 0 else nan
    pt_45 = pt_44
    tt_45 = gpr.prescribed_h(ht_45, gas="kerosene_in_air", far=far_45)
    den_tau_lpt = eta_mech_l * tau_lambda * tau_hpt * ((1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + (cooling_h + cooling_l/tau_hpt) * tau_0 * tau_lpc * tau_hpc / tau_lambda) if not any(isnan(x) for x in [tau_lambda, tau_hpt, far_4]) and tau_lambda!=0 and tau_hpt!=0 else nan
    tau_lpt = 1. - (tau_0 * ((tau_lpc * tau_fan - 1.) + bpr * (tau_fan - 1.)) + (1. + bpr) * power_tol/hs_0) / den_tau_lpt if den_tau_lpt!=0 else nan
    ht_5 = ht_45 * tau_lpt
    delta_h_lpt = ht_5 - ht_45
    state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45, delta_h=delta_h_lpt, eta_pol=eta_lpt, gas="kerosene_in_air", far=far_45)
    pt_5, tt_5 = state_5["p_out"], state_5["t_out"]
    g_9 = gpr.gamma_gas(tt_5, gas="kerosene_in_air", far=far_45); mach_9 = sqrt((2./(g_9-1.)) * ((pt_5/ps_0)**((g_9-1.)/g_9) - 1.)) if g_9 > 1 and pt_5/ps_0 > 1 else 0.
    mach_9 = min(mach_9, 1.0)
    ts_9 = gpr.t_total_to_static(tt_5, mach_9, gas="kerosene_in_air", far=far_45)
    ps_9 = pt_5 / (ts_9/tt_5)**(-g_9/(g_9-1)) if tt_5!=0 and (g_9-1)!=0 else ps_0
    v_9 = mach_9 * gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_45)
    rho_9 = ps_9 / (gpr.r_gas(gas="kerosene_in_air", far=far_45)*ts_9) if (gpr.r_gas(gas="kerosene_in_air", far=far_45)*ts_9)!=0 else nan
    g_19 = gpr.gamma_gas(tt_13, gas="air"); mach_19 = sqrt((2./(g_19-1.)) * ((pt_13/ps_0)**((g_19-1.)/g_19) - 1.)) if g_19 > 1 and pt_13/ps_0 > 1 else 0.
    mach_19 = min(mach_19, 1.0)
    ts_19 = gpr.t_total_to_static(tt_13, mach_19, gas="air")
    ps_19 = pt_13 / (ts_19/tt_13)**(-g_19/(g_19-1)) if tt_13!=0 and (g_19-1)!=0 else ps_0
    v_19 = mach_19 * gpr.s_o_s(ts_19, gas="air")
    rho_19 = ps_19 / (gpr.r_gas(gas="air")*ts_19) if (gpr.r_gas(gas="air")*ts_19)!=0 else nan
    sf_gross = (1.-bleed_to)*(1.+far_4)*v_9 + bpr*v_19 + (ps_9-ps_0)*(1-bleed_to)*(1+far_4)/(rho_9*v_9 if rho_9*v_9!=0 else 1) + (ps_19-ps_0)*bpr/(rho_19*v_19 if rho_19*v_19!=0 else 1)
    sf = (sf_gross - (1.+bpr)*v_0)/(1.+bpr) if (1.+bpr)!=0 else nan
    tsfc = (far_4*(1.-bleed_to-cooling_l-cooling_h)) / (sf*(1.+bpr)) if sf!=0 and (1.+bpr)!=0 and not isnan(far_4) else nan
    output_dict = {'pt_3': pt_3, 'tt_3': tt_3, 'sf': sf, 'tsfc': tsfc}
    return sf, tsfc, nan, nan, nan, output_dict

# --- Main Simulation Runner ---
def run_mission_simulation(aircraft_name: str, config: dict):
    print(f"--- Running Simulation for: {aircraft_name.upper()} ---")
    num_engines = config["num_engines"]
    engine_params = config["baseline_engine_config"]
    mission_segments = config["mission_segments"]
    
    total_fuel = 0.0
    total_emissions = {"m_nox": 0.0, "m_co2": 0.0, "m_h2o": 0.0}
    all_segments_valid = True

    for seg in mission_segments:
        print(f"  Processing Segment: {seg['name']}")
        current_params = engine_params.copy()
        current_params.update(seg["flight_conditions"])
        if "engine_params_override" in seg:
            current_params.update(seg["engine_params_override"])
        
        analysis_args = {k: v for k, v in current_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
        
        try:
            sf, tsfc, _, _, _, results_dict = turbofan_parametric_analysis(
                mach_0=current_params["mach_0"], ts_0=current_params["ts_0"], ps_0=current_params["ps_0"], **analysis_args
            )
            if isnan(tsfc) or tsfc <= 0: raise ValueError("Invalid TSFC calculated")
        except Exception as e:
            print(f"    ERROR: Calculation failed for this segment. {e}")
            all_segments_valid = False
            continue

        thrust_per_engine = seg["target_thrust_N"]
        mdot_f_per_engine = thrust_per_engine * tsfc
        fuel_per_engine = mdot_f_per_engine * seg["duration_minutes"] * 60

        h_est = atmosphere.get_altitude_from_pressure(current_params["ps_0"])
        ei_nox = ei_nox_dallara(results_dict.get('pt_3', nan), results_dict.get('tt_3', nan), h_est)
        
        emissions_per_engine = emissions(mdot_f_per_engine, ei_nox, dt=seg["duration_minutes"] * 60)
        
        total_fuel += fuel_per_engine * num_engines
        for key in total_emissions:
            if not isnan(emissions_per_engine[key]):
                total_emissions[key] += emissions_per_engine[key] * num_engines
            else:
                total_emissions[key] = nan

        # *** NEW PRINT STATEMENTS ADDED HERE ***
        print(f"    Thrust: {thrust_per_engine:.0f} N/eng, TSFC: {tsfc*1e6:.2f} mg/Ns, EI NOx: {ei_nox*1000:.2f} g/kg")
        print(f"    Fuel burnt (per engine): {fuel_per_engine:.2f} kg")
        if num_engines > 1:
            print(f"    Fuel burnt (total for segment): {fuel_per_engine * num_engines:.2f} kg")
        # **************************************

    print(f"\n--- TOTALS for {aircraft_name.upper()} ({num_engines} engines) ---")
    if not all_segments_valid: print("  WARNING: Some segments failed, totals are incomplete.")
    print(f"  Total Fuel: {total_fuel:.2f} kg")
    print(f"  Total NOx: {total_emissions['m_nox']:.2f} kg")
    print(f"  Total CO2: {total_emissions['m_co2']:.2f} kg")
    print("="*50 + "\n")

if __name__ == '__main__':
    T_TAKEOFF_ORIGINAL_PER_ENGINE = 7535
    
    aircraft_configs = {
        "AERIS": {
            "num_engines": 1, 
            "baseline_engine_config": { "bpr": 3.3, "pr_fan": 1.9, "pr_lpc": 1.5, "pr_hpc": 5.65, "tt_4": 1400., "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1450, "pr_fan": 2.0, "pr_hpc": 6.0}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.65, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1350}},
                {"name": "Cruise", "duration_minutes": 120, "target_thrust_N": 0.30 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.80, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1250}},
            ]
        },
        "HALO": {
            "num_engines": 2, 
            "baseline_engine_config": { "bpr": 4.2, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 24.0, "tt_4": 1500., "eta_fan": 0.92, "eta_lpc": 0.91, "eta_hpc": 0.90, "eta_hpt": 0.93, "eta_lpt": 0.94, "lhv": 43.e6, "cooling_h": 0.05, "cooling_l": 0.03 },
            "mission_segments": [
                { "name": "Take-off HALO", "duration_minutes": 5, "target_thrust_N": 26220, "flight_conditions": {"mach_0": 0.25, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1550}},
                { "name": "Climb HALO", "duration_minutes": 20, "target_thrust_N": 22287, "flight_conditions": {"mach_0": 0.70, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1450}},
                { "name": "Cruise HALO", "duration_minutes": 400, "target_thrust_N": 7866.15, "flight_conditions": {"mach_0": 0.82, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1300}},
            ]
        },
        "PH_LAB": {
            "num_engines": 2, 
            "baseline_engine_config": { "bpr": 2.6, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 7, "tt_4": 1200, "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                { "name": "Take-off PH_LAB", "duration_minutes": 5, "target_thrust_N": 9711.9, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1650}},
                { "name": "Climb PH_LAB", "duration_minutes": 20, "target_thrust_N": 8255.115, "flight_conditions": {"mach_0": 0.4, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1500}},
                { "name": "Cruise PH-LAB", "duration_minutes": 120, "target_thrust_N": 2913.57, "flight_conditions": {"mach_0": 0.7, "ts_0": 230.0, "ps_0": 35000.0}, "engine_params_override": {"tt_4": 1200}},
            ]
        }
    }

    for name, config in aircraft_configs.items():
        run_mission_simulation(name, config)