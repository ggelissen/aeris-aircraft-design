

# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *
from class2.master_design_loop import master_design_process


# ==== Flight Envelope for UAV ====
#
#
# This code generates a V-n diagram (Flight Envelope) for a UAV based on the STANAG 4671 and EASA CS-23 standards.
# Inputs:
# - Weight configuration (e.g., MTOW, MZFW)
# - Altitude level (e.g., sea level, cruise altitude)
# - Aircraft configuration (e.g., clean, take-off, landing)
# Outputs:
# - V-n diagram showing velocity vs. load factor limits
# - Gust loads and maneuver loads
# - Gust velocity calculations based on altitude
#

# THE INTRUCTIONS FOR THIS CODE ARE IN THE BOTTOM OF THE FILE
# =================================================================


class FlightEnvelope:
    def __init__(self, params: DesignParameters):
        self.params = params
        self.SetUp(params)
    
    def SetUp(self, params: DesignParameters):
        """
        Set up the flight envelope parameters and configurations.
        This method initializes the necessary parameters for the flight envelope calculations.
        """

        # 1 - UAV Paramenters

        #   -> Aerodynamic Constants
        self.CL_alpha =  params.performance.CL_alpha # Lift curve slope (1/rad)
        self.CL_max_values = {
            "CLEAN": params.performance.CL_max_cruise,  # Clean configuration
            "TAKE-OFF":  params.performance.CL_max_TO,  # Take-off configuration
            "LAND":  params.performance.CL_max_LAND  # Landing configuration
        }

        #   -> Atmospheric densities 
        self.density_at_altitude = {
            "sea_level": 1.225,
            "cruise":  params.cruise_density # cruise (design) using ISA standard atmosphere values
            } 
        
        #   -> Aircraft Geometry
        self.S = params.wing.S_w  # wing area (m²)
        self.chord = params.wing.mac # Mean Aerodynamic Chord (MAC) in m

        #   -> Cruise Speed TAS 
        VC_TAS = params.cruise_speed # TAS in m/s
        self.VC = true_to_equivalent_air_speed(VC_TAS, self.density_at_altitude['cruise'], 
                                               self.density_at_altitude['sea_level'])  # Convert TAS to EAS [m/s]
        
        #   -> Flight Altitude 
        self.flight_altitude = {
            "sea_level": 0, # m
            "cruise":  params.cruise_altitude # m
            }
        
        #   -> Weight Configuration Scenarios
        self.weight_configuration = {
            "OEW": params.weight.W_OE,  # Operational Empty Weight (OEW) [N] 
            "MTOW": params.weight.W_TO,  # Maximum Take-Off Weight (MTOW) [N] 
            "OEW_Payload_Fuselage_Fuel": params.weight.W_OE + params.weight.W_PL + 
                                            params.weight.W_F * params.weight.Fuel_Fuselage_Fraction # OEW + Payload + Fuselage_Fuel [N] 

        }

    def calc_load_factor_limits(self, MTOW_kg):
        """
        Calculate the positive and negative load factor limits based on MTOW.
        The limits are based on the NATO SATNAG 4671.

        :param MTOW_kg: Maximum Take-Off Weight in kg

        :return: Tuple of positive and negative load factor limits
        """
        n_pos_limit = min(2.1 + (10900 / (MTOW_kg + 4536)), 3.8)
        n_neg_limit = -0.4 * n_pos_limit
        return n_pos_limit, n_neg_limit

    def calc_diagram_speed(self, weight_N, density_altitude, CL_max, VC):
        """
        Calculate the stall speed (VS), dive speed (VD), and velocity axis for the V-n diagram.

        :param weight_N: Weight in Newtons
        :param density: Air density at the given altitude in kg/m³
        :param CL_max: Maximum lift coefficient for the aircraft configuration
        :param VC: Cruise speed in m/s

        :return: Tuple of stall speed (VS), dive speed (VD), and velocity axis (velocity_aixs)
        """
        # Stall speed (VS)
        VS_TAS = np.sqrt((2 * weight_N) / (density_altitude * self.S * CL_max)) # Stall speed in TAS [m/s]
        print(f"Stall speed (TAS): {VS_TAS} m/s")
        VS = true_to_equivalent_air_speed(VS_TAS, density_altitude, self.density_at_altitude['sea_level'])  # Convert TAS to EAS [m/s]
        # Dive speed (VD)
        VD = 1.25 * VC   # Dive speed (VD) EAS [m/s]
        # Velocity axis for the V-n diagram (EAS) [m/s]
        velocity_aixs = np.linspace(0, VD, 1000) 

        return VS, VD, velocity_aixs


    def calc_gust(self):

        rho = 1.225
        rho_cruise = self.density_at_altitude['cruise']  # Air density at cruise altitude in kg/m³
        VB = 70  # EAS  in m/s 
        VC = self.VC # Cruise speed EAS in m/s
        VD = VD = 1.25 * VC   # Dive speed (VD) EAS [m/s]
        
        mac = self.chord
        Cl_alpha = self.CL_alpha
        W_S = self.weight_configuration['OEW_Payload_Fuselage_Fuel'] / self.S  # Wing loading in N/m²
        print(f"W_S: {W_S} N/m²")

        mu_g = (W_S) / (9.80665*0.5 * rho_cruise * mac * Cl_alpha)
        K_g = (0.88 * mu_g) / (5.3 + mu_g)
        

        V_values_var = [VB, VC, VD]  # Airspeeds EAS in m/s
        # Gust Velocities for at Cruise Altitude
        u_values_var = [15.2, 10.21, 10.21/2]  # Gust intensities in m/s STANAG 4671
        
        
        # Compute total load factor n
        n_values_positive_revised = [1 + (rho * V * self.CL_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_values_var, u_values_var)]
        n_values_negative_revised = [1 - (rho * V * Cl_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_values_var, u_values_var)]
        print(f"n_values_positive_revised: {n_values_positive_revised}")
        V_values_extended = [0] + V_values_var
        n_values_positive_extended = [1] + n_values_positive_revised
        n_values_negative_extended = [1] + n_values_negative_revised
        velocities_eas_gust = V_values_extended


        # # Compute gust velocity as a function of V
        # U_gust = np.piecewise(velocity_aixs,
        #     [velocity_aixs <= VC, velocity_aixs > VC],
        #     [U_VC,
        #     lambda V: U_VC - ((U_VC - U_VD) / (VD - VC)) * (V - VC)]
        # )  
        # print(f"Gust velocity at altitude {altitude_m} m: U_VC = {U_VC} m/s, U_VD = {U_VD} m/s")
        return n_values_positive_extended, n_values_negative_extended, velocities_eas_gust


    def calc_maneuver_loads(self, velocity_aixs, n_pos_limit, n_neg_limit, VS, VD):
        """
        Calculate the maneuver load factors for positive and negative loads.

        :param velocity_aixs: Array of velocities for the V-n diagram
        :param n_pos_limit: Positive load factor limit
        :param n_neg_limit: Negative load factor limit
        :param VS: Stall speed in m/s
        :param VD: Dive speed in m/s

        :return: Tuple of positive and negative maneuver load factors
        """

        # I. Compute positive maneuver load factor
        n_parabola = (velocity_aixs / VS) ** 2              # CLmax limit (stall speed parabola)
        n_flat = np.full_like(velocity_aixs, n_pos_limit)   # Maximum positive load factor (flat line)

        n_maneuver_pos = np.minimum(n_parabola, n_flat)     # --> Postive maneuver load factor (minimum of parabola and flat line)

        # II. Compute negative maneuver load factor
        V_break = VS * np.sqrt(abs(n_neg_limit))

        n_maneuver_neg = np.piecewise(          # --> Negative maneuver load factor
            velocity_aixs,
            [velocity_aixs <= V_break,
            (velocity_aixs > V_break) & (velocity_aixs <= self.VC),
            (velocity_aixs > self.VC)],
            [
                lambda V: -((V / VS) ** 2),                         # Parabola (until it hits n_neg_limit)
                lambda V: n_neg_limit,                              # Flat line (from V_break to VC)
                lambda V: n_neg_limit * (VD - V) / (VD - self.VC)        # Linearly back to 0
            ]
        )

        return n_maneuver_pos, n_maneuver_neg

    def plot_vn_diagram(self, velocity_aixs, n_pos_limit, n_neg_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust):

        plt.figure(figsize=(10, 6))

        # Plot maneuver limits
        plt.plot(velocity_aixs, n_maneuver_pos, color='blue')
        plt.plot(velocity_aixs, n_maneuver_neg, color='blue')

        # Plot gust loads
        V_gust = np.array(velocities_eas_gust)
        plt.plot(V_gust, n_gust_pos, linestyle='--', color='orange')
        plt.plot(V_gust, n_gust_neg, linestyle='--', color='orange')

        # Compute VA
        VA_index = np.argmax(n_maneuver_pos >= n_pos_limit)
        VA = velocity_aixs[VA_index]
        print(f"VA (EAS): {VA} m/s")

        # Compute VA′ (negative)
        VA_prime_index = np.argmax(n_maneuver_neg <= n_neg_limit)
        VA_prime = velocity_aixs[VA_prime_index]
        print(f"VA′ (EAS): {VA_prime} m/s")

        # Plot vertical lines for VS, VA, VC, VD, VA'
        speeds = [VS, VA, VC, VD, VA_prime]
        labels = [r'$V_{S}$', r'$V_{A}$', r'$V_{C}$', r'$V_{D}$', r'$V_{A}^{*}$']
        colors = ['black'] * 5

        for v, label, color in zip(speeds, labels, colors):
            plt.axvline(x=v, color=color, linestyle=':')
            plt.text(v + 2, 0.1, label, fontsize=13, ha='left', va='bottom', color=color)

        # Overlay blue segment of VD
        plt.vlines(x=VD, ymin=0, ymax=n_pos_limit, colors='blue', linestyles='-', linewidth=2.5)

        # Highlight VA and VA′ points on the curve
        plt.plot(VA, n_pos_limit, 'ko')
        plt.text(VA + 2, n_pos_limit + 0.2, r'$n =$' + f'{n_pos_limit:.1f}', fontsize=13, color='black')

        plt.plot(VA_prime, n_neg_limit, 'ko')
        plt.text(VA_prime + 2, n_neg_limit - 0.4, r'n =' + f'{n_neg_limit:.1f}', fontsize=13, color='black')

        # Draw horizontal axis at n = 0
        plt.axhline(y=0, color='black', linewidth=1)

        # Aesthetics
        plt.xlabel(r'$V_{EAS}$ [m/s]', fontsize=14, labelpad=0, loc='right')
        plt.ylabel(r'$n$ [-]', fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='y')
        
        # plt.legend(
        #     [n_maneuver_pos, n_gust_pos],
        #     ['Maneuver Envelope', 'Gust Envelope'],
        #     loc='upper right', fontsize=14
        # )

        # Move x-axis label to n = 0 line
        ax = plt.gca()
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_position(('outward', 0))

        plt.legend(loc='upper right', fontsize=14)
        plt.ylim(-4, 5)
        plt.xlim(0, VD + 10)
        plt.tight_layout()
        plt.savefig(f"Figures/VN_diagram")


    def lift_coeff(self, n_pos_limit, n_neg_limit, load_case):
        """
        Calculate the lift coefficient based on the load factor limits and load case.
        :param n_pos_limit: Positive load factor limit
        :param n_neg_limit: Negative load factor limit
        :param load_case: Load case type, either "POSITIVE" or "NEGATIVE"
        :return: Lift coefficient
        """

        if load_case == "POSITIVE":
            n_ult =  n_pos_limit
            V = 162.348
            lift = n_ult * self.weight_configuration['OEW_Payload_Fuselage_Fuel']
        elif load_case == "NEGATIVE":
            n_ult = n_neg_limit
            V = 126.376
            lift = n_ult * self.weight_configuration['MTOW']

        lift = self.weight_configuration['MTOW']
        V = 209
        lift_coefficient = lift / (0.5 * self.density_at_altitude['cruise'] * V**2 * self.S)  # Lift coefficient

        return lift_coefficient




    def generate_flight_envelope(self, weight_config: str, altitude_level: str, ac_configuration: str):
        """
        Generates a V-n diagram based on selected weight and altitude.

        Parameters:
            weight_config: str, e.g., 'MTOW', 'MLW', 'OEW'
            altitude_level: str, e.g., 'sea_level', 'cruise'
        """
        weight_N = self.weight_configuration[weight_config]
        MTOW_kg = N_to_kg(self.weight_configuration['MTOW'])  # Convert weight from N to kg
        density = self.density_at_altitude[altitude_level]  # Get density based on altitude level
        altitude = self.flight_altitude[altitude_level]
        CL_max = self.CL_max_values[ac_configuration]  # Get CL_max based on aircraft configuration

        # 1. Calculate load factor limits
        n_pos_limit, n_neg_limit = self.calc_load_factor_limits(MTOW_kg)
  
        # 2. Calculate stall speed (VS), dive speed (VD), and velocity axis
        VS, VD, velocity_aixs = self.calc_diagram_speed(weight_N, density, CL_max, self.VC)
 
        # 3. Calculate Gust loads
        n_gust_pos, n_gust_neg, velocities_eas_gust = self.calc_gust()

        # 4. Calculate maneuver loads
        n_maneuver_pos, n_maneuver_neg = self.calc_maneuver_loads(velocity_aixs, n_pos_limit, n_neg_limit, VS, VD)

        # 6. Plot the V-n diagram
        self.plot_vn_diagram(velocity_aixs, n_pos_limit, n_neg_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, self.VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust)

        # 7. Calculate and print the lift coefficient limits
        load_case = "NEGATIVE" ########## CHANGE THIS TO "NEGATIVE" FOR NEGATIVE LOAD CASE
        cl = self.lift_coeff(n_pos_limit, n_neg_limit, load_case)
        print(f"Angle of attack limit for {weight_config} at {altitude_level} in {ac_configuration} configuration: {cl:.4f}")



    def run_all_configurations(self):
        """
        Runs the flight envelope generation for all valid combinations of
        weight configuration, altitude level, and aircraft configuration.
        Skips incompatible configurations (e.g., landing config at cruise altitude).
        """
        for weight_key in self.weight_configuration.keys():
            for altitude_key in self.density_at_altitude.keys():
                for ac_config_key in self.CL_max_values.keys():

                    # === Skip incompatible scenarios ===
                    if altitude_key == 'cruise' and ac_config_key == 'LAND':
                        continue  # Skip landing config at cruise altitude
                    if altitude_key == 'cruise' and ac_config_key == 'TAKE-OFF':
                        continue  # Clean config usually not relevant on ground

                    print(f"\nRunning: Weight = {weight_key}, Altitude = {altitude_key}, Config = {ac_config_key}")
                    self.generate_flight_envelope(weight_key, altitude_key, ac_config_key)




if __name__ == "__main__":

    params, _, _ = master_design_process("design_config.yaml")

    fe = FlightEnvelope(params)
    fe.generate_flight_envelope("MTOW", "cruise", "CLEAN")
    #fe.run_all_configurations()





# TO RUN THE FILE:

# 1. SELECT THE WEIGHT CONFIGURATION, ALTITUDE LEVEL,   
#    AND AIRCRAFT CONFIGURATION when calling the function generate_flight_envelope

# 2. FOR CL CALCULATION, SELECT THE LOAD CASE
#    (POSITIVE OR NEGATIVE) (inside the class FlightEnvelope -> item 7 of generate_flight_envelope)



