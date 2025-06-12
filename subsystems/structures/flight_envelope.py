

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

    # def compute_gust_loads(self, V_range, Ude):
    #     """
    #     Compute gust load factors over a range of velocities.
        
    #     Args:
    #         params: DesignParameters object containing aircraft specs.
    #         V_range: Numpy array of velocities [m/s].
    #         Ude: Design gust velocity [m/s].
        
    #     Returns:
    #         Tuple of (n_gust_positive, n_gust_negative) arrays.
    #     """
    #     rho = self.density_at_altitude['cruise']
    #     mac = self.chord
    #     Cl_alpha = self.CL_alpha
    #     W_S = self.weight_configuration['OEW_Payload_Fuselage_Fuel']/ self.S  # Wing loading in N/m²
        

    #     mu_g = W_S / (0.5 * rho * mac * Cl_alpha * 9.80665)
    #     K_g = (0.88 * mu_g) / (5.3 + mu_g)
        
    #     n_gust_positive = 1 + (K_g * rho * V_range * Ude * Cl_alpha) / (2 * W_S) 
    #     n_gust_negative = 1 - (K_g * rho * V_range * Ude * Cl_alpha) / (2 * W_S) 
        
        
    #     return n_gust_positive, n_gust_negative

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

    # def calc_gust_loads(self, velocity_aixs, U_gust, weight_N, density, chord):
    #     a = 2*np.pi # to be confirmed
    #     # wing loading
    #     W_S = weight_N / self.S  # in N/m²
    #     # aeroplane mass ratio
    #     ug = 2 * W_S / (density * chord * a * self.S * 9.80665)
    #     # gust alleviation factor
    #     kg = 0.88 * ug / (5.3 + ug)

    #     # EAS 
    #     #velocity_aixs_EAS
    #     n_gust_pos = 1 + kg * 1.225 * U_gust * velocity_aixs / (2 * W_S)
    #     n_gust_neg = 1 - kg * 1.225 * U_gust * velocity_aixs / (2 * W_S)
        

    #     #n_gust_pos = 1 + (density * CL_alpha * S * velocity_aixs * U_gust) / (2 * weight_N)
    #     #n_gust_neg = 1 - (density * CL_alpha * S * velocity_aixs * U_gust) / (2 * weight_N)

    #     return n_gust_pos, n_gust_neg

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

    def plot_vn_diagram(self, velocity_aixs, n_pos_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust):

        plt.figure(figsize=(10, 6))

        # Maneuver limits
        plt.plot(velocity_aixs, n_maneuver_pos, label='Positive Maneuver Limit', color='blue')
        plt.plot(velocity_aixs, n_maneuver_neg, label='Negative Maneuver Limit', color='blue')

        # Gust loads
        # plt.plot(velocity_aixs, n_gust_pos, '--', label='Positive Gust Load', color='orange')
        # plt.plot(velocity_aixs, n_gust_neg, '--', label='Negative Gust Load', color='orange')
        V_gust = np.array(velocities_eas_gust)
        plt.plot(V_gust, n_gust_pos, label="Gust Load", linestyle='--', color='orange')
        plt.plot(V_gust, n_gust_neg, label="Gust Load", linestyle='--', color='orange')

        # Key speeds
        # Compute VA as the speed at which the parabola hits the flat limit
        VA_index = np.argmax(n_maneuver_pos >= n_pos_limit)
        VA = velocity_aixs[VA_index] # VA Equivalent Airspeed (EAS) [m/s]
        VA_TAS = equivalent_to_true_air_speed(VA, self.density_at_altitude[altitude_level], self.density_at_altitude['sea_level'])  # Convert EAS to TAS [m/s]
        print(f"VA (EAS): {VA} m/s, VA (TAS): {VA_TAS} m/s")
        

        # Custom color map for specific speeds
        speed_labels = ['VS', 'VA', 'VC', 'VD']
        speed_values = [VS, VA, VC, VD]
        color_map = {
            'VS': 'blue',
            'VA': 'gray',
            'VC': 'orange',
            'VD': 'red'
        }

        for v, label in zip(speed_values, speed_labels):
            plt.axvline(x=v, color=color_map[label], linestyle=':', label=label)

        # Labels and aesthetics
        plt.title(f'V-n Diagram (Flight Envelope)\nWeight: {weight_config}, Altitude: {altitude_level}, CL config: {ac_configuration}')
        plt.xlabel('Equivalent Airspeed (m/s)')
        plt.ylabel('Load Factor (n)')
        plt.grid(True)
        plt.legend(loc='upper right')
        plt.ylim(-4, 5)
        plt.xlim(0, VD + 10)
        plt.tight_layout()
        plt.show()

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
        # 2. Calculate speeds
        VS, VD, velocity_aixs = self.calc_diagram_speed(weight_N, density, CL_max, self.VC)
        # 3. Calculate gust velocity
        #U_gust = self.calc_gust_velocity(altitude, velocity_aixs, self.VC, VD) 
        # 4. Calculate gust loads
        #n_gust_pos, n_gust_neg = self.calc_gust_loads(velocity_aixs, U_gust, weight_N, density, self.chord)
        #n_gust_pos, n_gust_neg = self.compute_gust_loads(velocity_aixs, U_gust)
        n_gust_pos, n_gust_neg, velocities_eas_gust = self.calc_gust()
        # 5. Calculate maneuver loads
        n_maneuver_pos, n_maneuver_neg = self.calc_maneuver_loads(velocity_aixs, n_pos_limit, n_neg_limit, VS, VD)
        # 6. Plot the V-n diagram
        self.plot_vn_diagram(velocity_aixs, n_pos_limit, n_gust_pos, n_gust_neg, n_maneuver_pos, n_maneuver_neg, VS, self.VC, VD, weight_config, altitude_level, ac_configuration, velocities_eas_gust)

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
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    fe = FlightEnvelope(params)
    fe.generate_flight_envelope("OEW_Payload_Fuselage_Fuel", "cruise", "CLEAN")
    #fe.run_all_configurations()


