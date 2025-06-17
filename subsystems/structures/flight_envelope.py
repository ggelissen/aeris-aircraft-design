# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import math as m

# --- Setup Project Paths ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *
from class2.master_design_loop import master_design_process


# --- Plotting Style and Formatting ---

def _set_report_style():
    """Sets a professional plot style suitable for reports."""
    try:
        plt.rcParams['font.family'] = 'Arial'
    except RuntimeError:
        print("Arial font not found, falling back to default sans-serif.")
        plt.rcParams['font.family'] = 'sans-serif'
    
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['lines.markersize'] = 6

COLOR_PALETTE = {
    'blue': '#0d3b66',
    'orange': '#ee964b',
    'grey': '#4F4F4F',
    'red': '#D7263D' # A distinct red for critical points
}


# ==== Flight Envelope for UAV ====

class FlightEnvelope:
    def __init__(self, params: DesignParameters):
        self.params = params
        self.SetUp(params)
    
    # ... (SetUp and other calculation methods remain the same) ...
    def SetUp(self, params: DesignParameters):
        self.CL_alpha = params.performance.CL_alpha
        self.CL_max_values = {"CLEAN": params.performance.CL_max_cruise, "TAKE-OFF": params.performance.CL_max_TO, "LAND": params.performance.CL_max_LAND}
        self.density_at_altitude = {"sea_level": 1.225, "cruise": params.cruise_density}
        self.S = params.wing.S_w
        self.chord = params.wing.mac
        VC_TAS = params.cruise_mach * m.sqrt(1.4 * 287.05 * params.cruise_temperature)
        self.VC = true_to_equivalent_air_speed(VC_TAS, params.cruise_density, self.density_at_altitude['sea_level'])
        self.flight_altitude = {"sea_level": 0, "cruise": params.cruise_altitude}
        self.weight_configuration = {"OEW": params.weight.W_OE, "MTOW": params.weight.W_TO, "OEW_Payload_Fuselage_Fuel": params.weight.W_OE + params.weight.W_PL + params.weight.W_F * params.weight.Fuel_Fuselage_Fraction}

    def calc_load_factor_limits(self, MTOW_kg):
        n_pos_limit = min(2.1 + (10900 / (MTOW_kg + 4536)), 3.8)
        n_neg_limit = -0.4 * n_pos_limit
        return n_pos_limit, n_neg_limit

    def calc_diagram_speed(self, weight_N, density_altitude, CL_max, VC):
        VS_TAS = np.sqrt((2 * weight_N) / (density_altitude * self.S * CL_max))
        VS = true_to_equivalent_air_speed(VS_TAS, density_altitude, self.density_at_altitude['sea_level'])
        VD = 1.25 * VC
        velocity_axis = np.linspace(0, VD, 1000)
        return VS, VD, velocity_axis

    def calc_gust(self):
        rho = 1.225
        rho_cruise = self.density_at_altitude['cruise']
        VB = 70
        VC = self.VC
        VD = 1.25 * VC
        mac = self.chord
        Cl_alpha = self.CL_alpha
        W_S = self.weight_configuration['OEW_Payload_Fuselage_Fuel'] / self.S
        mu_g = W_S / (9.80665 * 0.5 * rho_cruise * mac * Cl_alpha)
        K_g = (0.88 * mu_g) / (5.3 + mu_g)
        V_values_var = [VB, VC, VD]
        u_values_var = [15.2, 10.21, 10.21 / 2]
        n_values_positive_revised = [1 + (rho * V * self.CL_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_values_var, u_values_var)]
        n_values_negative_revised = [1 - (rho * V * Cl_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_values_var, u_values_var)]
        velocities_eas_gust = [0] + V_values_var
        n_values_positive_extended = [1] + n_values_positive_revised
        n_values_negative_extended = [1] + n_values_negative_revised
        return n_values_positive_extended, n_values_negative_extended, velocities_eas_gust

    def calc_maneuver_loads(self, velocity_aixs, n_pos_limit, n_neg_limit, VS, VD):
        n_parabola = (velocity_aixs / VS) ** 2
        n_flat = np.full_like(velocity_aixs, n_pos_limit)
        n_maneuver_pos = np.minimum(n_parabola, n_flat)
        V_break = VS * np.sqrt(abs(n_neg_limit))
        n_maneuver_neg = np.piecewise(velocity_aixs,
            [velocity_aixs <= V_break, (velocity_aixs > V_break) & (velocity_aixs <= self.VC), (velocity_aixs > self.VC)],
            [lambda V: -((V / VS) ** 2), lambda V: n_neg_limit, lambda V: n_neg_limit * (VD - V) / (VD - self.VC)])
        return n_maneuver_pos, n_maneuver_neg

    def plot_vn_diagram(self, velocity_aixs, n_pos_limit, n_neg_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust):
        _set_report_style()
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.fill_between(velocity_aixs, n_maneuver_pos, n_maneuver_neg, color=COLOR_PALETTE['blue'], alpha=0.1)
        ax.plot(velocity_aixs, n_maneuver_pos, color=COLOR_PALETTE['blue'])
        ax.plot(velocity_aixs, n_maneuver_neg, color=COLOR_PALETTE['blue'])
        
        V_gust = np.array(velocities_eas_gust)
        ax.plot(V_gust, n_gust_pos, linestyle='--', color=COLOR_PALETTE['orange'])
        ax.plot(V_gust, n_gust_neg, linestyle='--', color=COLOR_PALETTE['orange'])
        
        # --- Calculate and Annotate Key Speeds and Points ---
        VA = VS * np.sqrt(n_pos_limit)
        VA_prime = VS * np.sqrt(-n_neg_limit)
        
        # Add VA* back to the speeds dictionary
        speeds = {'$V_S$': VS, '$V_A$': VA, '$V_A^*$': VA_prime, '$V_C$': VC, '$V_D$': VD}
        
        for label, v in speeds.items():
            ax.axvline(x=v, color=COLOR_PALETTE['grey'], linestyle=':', linewidth=1)
            ax.text(v + 4, ax.get_ylim()[0] * 0.9 - 0.3, label, fontsize=11, ha='center', va='bottom', color=COLOR_PALETTE['grey'])

        # --- Add Critical Load Case points ---
        critical_points_plot, = ax.plot([VA, VA_prime], [n_pos_limit, n_neg_limit], 
                                        marker='*', color=COLOR_PALETTE['red'], 
                                        linestyle='None', markersize=12, label='Critical Load Cases')
        
        # --- Aesthetics and Axis Configuration ---
        ax.set_ylabel('$n$ [-]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        
        ax.spines['bottom'].set_position('zero')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # --- Position the X-label manually to align with annotations ---
        ax.set_xlabel('') # Clear the default label
        ax.text(ax.get_xlim()[1] - 3, ax.get_ylim()[0] * 0.9 + 1.75, '$V_{EAS}$ [m/s]', ha='left', va='center', color='black', fontsize=14)
        
        ax.axhline(y=n_pos_limit, color=COLOR_PALETTE['grey'], linestyle=':', linewidth=1)
        ax.text(ax.get_xlim()[1], n_pos_limit, f' $n={n_pos_limit:.2f}$', ha='left', va='center', color=COLOR_PALETTE['grey'])
        ax.axhline(y=n_neg_limit, color=COLOR_PALETTE['grey'], linestyle=':', linewidth=1)
        ax.text(ax.get_xlim()[1], n_neg_limit, f' $n={n_neg_limit:.2f}$', ha='left', va='center', color=COLOR_PALETTE['grey'])
        ax.vlines(x=VD, ymin=0, ymax=n_pos_limit, color=COLOR_PALETTE['grey'])

        # --- Create and Style Legend ---
        maneuver_patch = mpatches.Patch(color=COLOR_PALETTE['blue'], alpha=0.2, label='Maneuver Envelope')
        gust_line = plt.Line2D([0], [0], color=COLOR_PALETTE['orange'], linestyle='--', label='Gust Envelope')
        
        # Add the new critical points handle to the legend
        handles = [maneuver_patch, gust_line, critical_points_plot]
        
        legend = ax.legend(handles=handles, loc='upper left', frameon=True)
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
        frame.set_facecolor('white')
        frame.set_edgecolor('black')
        frame.set_alpha(0.8)
        frame.set_linewidth(0.5)
        legend.set_zorder(10)

        ax.set_ylim(n_neg_limit - 1.5, n_pos_limit + 1)
        ax.set_xlim(0, VD * 1.05)
        
        plt.tight_layout()
        plt.savefig(f"Figures/VN_diagram_{weight_config}_{altitude_level}.png", transparent=False, dpi=300)
        print(f"Saved plot: Figures/VN_diagram_{weight_config}_{altitude_level}.png")
        plt.close(fig)

    def generate_flight_envelope(self, weight_config: str, altitude_level: str, ac_configuration: str):
        weight_N = self.weight_configuration[weight_config]
        MTOW_kg = N_to_kg(self.weight_configuration['MTOW'])
        density = self.density_at_altitude[altitude_level]
        altitude = self.flight_altitude[altitude_level]
        CL_max = self.CL_max_values[ac_configuration]
        n_pos_limit, n_neg_limit = self.calc_load_factor_limits(MTOW_kg)
        VS, VD, velocity_aixs = self.calc_diagram_speed(weight_N, density, CL_max, self.VC)
        n_gust_pos, n_gust_neg, velocities_eas_gust = self.calc_gust()
        n_maneuver_pos, n_maneuver_neg = self.calc_maneuver_loads(velocity_aixs, n_pos_limit, n_neg_limit, VS, VD)
        self.plot_vn_diagram(velocity_aixs, n_pos_limit, n_neg_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, self.VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust)

    def run_all_configurations(self):
        for weight_key in self.weight_configuration.keys():
            for altitude_key in self.density_at_altitude.keys():
                for ac_config_key in self.CL_max_values.keys():
                    if altitude_key == 'cruise' and ac_config_key in ['LAND', 'TAKE-OFF']:
                        continue
                    print(f"\nRunning: Weight = {weight_key}, Altitude = {altitude_key}, Config = {ac_config_key}")
                    self.generate_flight_envelope(weight_key, altitude_key, ac_config_key)

if __name__ == "__main__":
    params, _, _ = master_design_process(config_file="design_config.yaml")
    fe = FlightEnvelope(params)
    fe.generate_flight_envelope("MTOW", "cruise", "CLEAN")