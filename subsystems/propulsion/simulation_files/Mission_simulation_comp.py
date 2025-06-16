#!/usr/bin/python
# -*- coding: utf-8 -*-
import pprint
from math import sqrt, nan, isnan, log
import sys 
import os 
import numpy as np
import matplotlib.pyplot as plt

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
def run_mission_simulation_comparison():
    """
    Runs a mission simulation for multiple aircraft with their specific engine
    configurations and missions to compare performance.
    """
    print("Starting Aircraft Mission Comparison Simulation with specific engine models...\n")

    # --- Thrust Parameters as specified ---
    T_TO = 7535          # N for AERIS
    T_TOHALO = 121478.211     # N for HALO (MTOW* 0.3)
    T_TOPH_LAB = 19423    # N for PH-LAB (MTOW * 0.3)
    T_cruise = 1800  # N for AERIS cruise thrust
    # --- Aircraft Configurations with Specific Engine Params and Missions ---
    aircraft_configs = {
        "AERIS": {
            "num_engines": 1,
            "baseline_engine_config": { "bpr": 3.3, "pr_fan": 1.9, "pr_lpc": 1.5, "pr_hpc": 5.65, "tt_4": 1400., "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TO, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TO, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TO, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1400}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TO, "flight_conditions": {"mach_0": 0.55, "ts_0": 242.7, "ps_0": 46560}, "engine_params_override": {"tt_4": 1300}},
                {"name": "Cruise", "duration_minutes": 120, "target_thrust_N": T_cruise, "flight_conditions": {"mach_0": 0.7, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1200}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TO, "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 900}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TO, "flight_conditions": {"mach_0": 0.30, "ts_0": 282.65, "ps_0": 95970}, "engine_params_override": {"tt_4": 950}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TO, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1000}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TO, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
            ]
        },
        "HALO": {
            "num_engines": 2,
            "baseline_engine_config": { "bpr": 4.2, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 24.0, "tt_4": 1500., "eta_fan": 0.92, "eta_lpc": 0.91, "eta_hpc": 0.90, "eta_hpt": 0.93, "eta_lpt": 0.94, "lhv": 43.e6, "cooling_h": 0.05, "cooling_l": 0.03 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TOHALO, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TOHALO, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 950}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TOHALO, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1600}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.90 * T_TOHALO, "flight_conditions": {"mach_0": 0.65, "ts_0": 235.2, "ps_0": 34567}, "engine_params_override": {"tt_4": 1500}},
                {"name": "Cruise", "duration_minutes": 400, "target_thrust_N": 0.3*T_TOHALO, "flight_conditions": {"mach_0": 0.85, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1400}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TOHALO, "flight_conditions": {"mach_0": 0.55, "ts_0": 242.7, "ps_0": 55720}, "engine_params_override": {"tt_4": 1000}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TOHALO, "flight_conditions": {"mach_0": 0.35, "ts_0": 268.65, "ps_0": 75271}, "engine_params_override": {"tt_4": 980}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TOHALO, "flight_conditions": {"mach_0": 0.28, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1100}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TOHALO, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}},
            ]
        },
        "PH-LAB (Citation II)": {
            "num_engines": 2,
            "baseline_engine_config": { "bpr": 2.6, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 7, "tt_4": 1200, "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9, "eta_hpt": 0.93, "eta_lpt": 0.93, "lhv": 43.e6 },
            "mission_segments": [
                {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 800}},
                {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}},
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TOPH_LAB, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1300}},
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.60, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1200}},
                {"name": "Cruise", "duration_minutes": 120, "target_thrust_N": 0.3*T_TOPH_LAB, "flight_conditions": {"mach_0": 0.7, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1100}},
                {"name": "Descent", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 900}},
                {"name": "Loiter", "duration_minutes": 35, "target_thrust_N": 0.15 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.28, "ts_0": 285.2, "ps_0": 95970}, "engine_params_override": {"tt_4": 880}},
                {"name": "Landing", "duration_minutes": 5, "target_thrust_N": 0.30 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 950}},
                {"name": "Taxi & Shutdown", "duration_minutes": 15, "target_thrust_N": 0.07 * T_TOPH_LAB, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 800}},
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

            # Start with the specific baseline config for the aircraft
            current_engine_params = config["baseline_engine_config"].copy()
            # Add general efficiencies/parameters if not in the specific config
            current_engine_params.setdefault("eta_com", 0.99)
            current_engine_params.setdefault("eta_mech_l", 0.99)
            current_engine_params.setdefault("eta_mech_h", 0.99)
            current_engine_params.setdefault("pr_com", 0.95)
            current_engine_params.setdefault("pr_inl", 0.98)
            current_engine_params.setdefault("bleed_to", 0.0)
            current_engine_params.setdefault("power_tol", 0.0)
            current_engine_params.setdefault("power_toh", 0.0)
            current_engine_params.setdefault("cooling_l", 0.0)
            current_engine_params.setdefault("cooling_h", 0.0)
            current_engine_params.setdefault("full_output", True)
            
            # Update with flight conditions and segment-specific overrides
            current_engine_params.update(segment["flight_conditions"])
            if "engine_params_override" in segment:
                current_engine_params.update(segment["engine_params_override"])

            analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
            
            try:
                tf_results = turbofan_parametric_analysis(
                    mach_0=current_engine_params["mach_0"],
                    ts_0=current_engine_params["ts_0"],
                    ps_0=current_engine_params["ps_0"],
                    **analysis_params
                )
                tsfc = tf_results[1]
                
                if isnan(tsfc) or tsfc <= 0:
                    print(f"  Warning: Invalid TSFC ({tsfc}) for {segment['name']}. Skipping segment.")
                    continue

                # TSFC is per Newton, so total fuel flow is just TSFC * total thrust
                mdot_f_total_aircraft = segment["target_thrust_N"] * tsfc
                segment_fuel_kg = mdot_f_total_aircraft * dt_seconds
                total_fuel_kg += segment_fuel_kg

                output_dict = tf_results[5]
                tt_3 = output_dict.get('tt_3', 600)
                pt_3 = output_dict.get('pt_3', 10e5)
                ei_nox = (2 + 28.5 * ((pt_3 / 1000) / 3100)**0.5 * np.exp((tt_3 - 825) / 250)) / 1000
                
                segment_emissions_data = emissions(mdot_f_total_aircraft, ei_nox, dt=dt_seconds)
                for key in total_emissions:
                    if not isnan(segment_emissions_data.get(key, nan)):
                        total_emissions[key] += segment_emissions_data[key]

                print(f"  Thrust: {segment['target_thrust_N']:.0f} N, TSFC: {tsfc:.4e}, Fuel: {segment_fuel_kg:.2f} kg")

            except Exception as e:
                print(f"  ERROR during analysis for segment {segment['name']}: {e}")

        results_per_aircraft[aircraft_name] = {
            "Total Fuel (kg)": total_fuel_kg,
            "Total Emissions (kg)": total_emissions
        }
        print(f"\n--- Total for {aircraft_name} ---")
        print(f"  Total Fuel Used: {total_fuel_kg:.2f} kg")
        for species, mass in total_emissions.items():
            print(f"  Total {species.replace('m_', '').upper()}: {mass:.2f} kg")

    # # --- Emissions Comparison Calculation and Printout ---
    # print("\n\n" + "="*50)
    # print("===== Emissions Reduction Comparison vs. AERIS =====")
    # print("="*50 + "\n")

    # aeris_emissions = results_per_aircraft.get("AERIS", {}).get("Total Emissions (kg)")

    # if aeris_emissions:
    #     for aircraft_name, results in results_per_aircraft.items():
    #         if aircraft_name == "AERIS":
    #             continue

    #         print(f"--- Comparison: AERIS vs. {aircraft_name} ---")
    #         other_emissions = results.get("Total Emissions (kg)")
    #         if not other_emissions:
    #             print("  Could not retrieve emissions data for comparison.")
    #             continue

    #         # Compare Fuel
    #         aeris_fuel = results_per_aircraft["AERIS"]["Total Fuel (kg)"]
    #         other_fuel = results["Total Fuel (kg)"]
    #         if other_fuel > 0:
    #             fuel_reduction = ((other_fuel - aeris_fuel) / other_fuel) * 100
    #             print(f"  Fuel Consumption: {fuel_reduction:.2f}% lower")


    #         # Compare Emissions
    #         for species, aeris_mass in aeris_emissions.items():
    #             other_mass = other_emissions.get(species)
    #             if other_mass is not None and other_mass > 0:
    #                 percentage_diff = ((other_mass - aeris_mass) / other_mass) * 100
    #                 species_name = species.replace('m_', '').upper()
    #                 print(f"  {species_name} Emissions: {percentage_diff:.2f}% lower")
    #         print("-" * 20)

    return results_per_aircraft


if __name__ == '__main__':
    run_mission_simulation_comparison()