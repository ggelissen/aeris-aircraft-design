import numpy as np
import math

# --- Assumed imports from your project structure ---
# You will need to ensure these modules/functions are correctly implemented
# and provide the necessary parameters from design_variables.py
# from DSEGroup17.design_variables import AircraftParameters, PropulsionParameters, WeightParameters
# from DSEGroup17.class1.initial_weight_estimations import initial_mtow_estimation # Example
# from DSEGroup17.class2.component_weights import calculate_wing_struct_weight_fraction # Example from Ch11
# from DSEGroup17.subsystems.propulsion.main_prop import get_propulsion_function # Example for F_prop
# from DSEGroup17.subsystems.flightperformance.field_performance import check_tofl_constraint, check_lfl_constraint # Example

# --- Constants (Many of these will come from design_variables.py or need calibration) ---
# <<< USER ATTENTION REQUIRED: Calibrate all constants based on Torenbeek and your specific aircraft class >>>

# Example values, replace with actuals or imports from design_variables.py
H_g = 4350e3  # Calorific value of fuel / g (m) (Torenbeek, p.44, 245, though units vary, ensure consistency)
rho_sl = 1.225  # Sea level air density (kg/m^3)
g = 9.80665    # Gravitational acceleration (m/s^2)
gamma_air = 1.4 # Ratio of specific heats for air

# Aerodynamic technology factor for supercritical sections (Torenbeek, Eq. 10.47)
M_prime = 0.935
# Default drag divergence margin (Torenbeek, Eq. 10.41)
delta_M_dd = 0.03 # Example, can be 0 to 0.05

# Skin friction and form factor related (Torenbeek, Eq. 10.39)
r_t_wing = 2.8 # Example typical value for r_t (thickness form factor for wing)
Cf_cruise = 0.003 # Example typical skin friction coefficient at cruise Reynolds number
d_w_h_factor = 1.25 # Factor for (CDp S)h / (CDp S)w, (e.g., 1 + 0.25), (Torenbeek, Eq. 10.38)

# Oswald efficiency factor for wing-due-to-lift drag (Torenbeek, Section 10.3.1)
e_prime_wing = 0.90 # Example for a well-designed wing with camber/twist

# Compressibility drag target in cruise (Torenbeek, Section 10.6.2)
C_Dc_cruise_target = 0.0008 # Example

# Fuel tank volumetric efficiency (Torenbeek, Eq. 10.30)
eta_tank_wing = 0.55

# Weight calculation coefficients (Torenbeek, Chapter 10, based on Chapter 8 & 11)
# These are critical and need careful derivation/calibration based on your aircraft type and materials
# Gamma_2 represents fixed area-dependent secondary wing structure weight (Eq. 10.13 / 8.1)
# Gamma_3 represents primary wing structure weight scaling (Eq. 10.35)
# For Gamma_3: n_ult, eta_cp_wing, b_ref_wing will be needed.
# r_h is (horizontal tail weight / wing weight)

# Example (Placeholder - MUST BE REFINED)
Gamma_2_coeff = 0.025 # Placeholder for (1+rh)*Psi_S / q_hat (from Eq. 10.13 and 8.1)
Gamma_3_coeff_factor = 0.0002 # Placeholder for 0.0013*(1+rh)*eta_cp*n_ult / b_ref (from Eq. 10.35)
mu_resf = 0.045 # Reserve fuel fraction (Torenbeek, p. 250, 388)
mu_lg = 0.040   # Landing gear weight fraction (Torenbeek, p. 250)

# --- Helper Functions (examples, to be expanded) ---

def calculate_dynamic_pressure(rho, V):
    return 0.5 * rho * V**2

def get_isa_conditions(altitude_m):
    # Placeholder: Implement ISA model from Torenbeek Appendix B or a standard library
    # Returns rho, p, T, a at the given altitude
    if altitude_m < 11000:
        T = 288.15 - 0.0065 * altitude_m
        p = 101325 * (T / 288.15)**(g / (0.0065 * 287.05))
        rho = p / (287.05 * T)
    else: # Isothermal layer
        T = 216.65
        p = 22632 * math.exp(-g * (altitude_m - 11000) / (287.05 * T))
        rho = p / (287.05 * T)
    a = math.sqrt(gamma_air * 287.05 * T)
    return rho, p, T, a

class AircraftDesignIteration:
    def __init__(self, design_config):
        # Load parameters from design_config (which should source from design_variables.py)
        self.M_des = design_config['cruise_mach']
        self.altitude_cruise_m = design_config['cruise_altitude_m']
        self.payload_kg = design_config['payload_kg']
        self.design_range_m = design_config['design_range_m']
        # ... other aircraft, propulsion, weight parameters
        self.eta_o_cruise = design_config.get('propulsion_eta_o_cruise', 0.35) # Example
        self.mu_T_propulsion = design_config.get('propulsion_mu_T', 0.26) # Example (W_pp / T_TO)
        self.tau_cruise_propulsion = design_config.get('propulsion_tau_cruise', 0.8) # Example (T_cruise_corrected / T_TO)
        self.Cd_fixed_fuselage_vt_nacelles_m2 = design_config.get('Cd_fixed_area', 1.5) # Example (CDpS)fix

        self.rho_cruise, self.p_cruise, self.T_cruise, self.a_cruise = get_isa_conditions(self.altitude_cruise_m)
        self.V_cruise = self.M_des * self.a_cruise
        self.q_hat_cruise = calculate_dynamic_pressure(self.rho_cruise, self.V_cruise)

        # For Gamma_3 calculation
        self.n_ult = design_config.get('n_ult', 3.75)
        self.eta_cp_wing = design_config.get('eta_cp_wing', 0.4) # Center of pressure, wing
        self.b_ref_wing = design_config.get('b_ref_wing', 100) # Reference span for wing weight
        self.r_h_tail_wing_weight_ratio = design_config.get('r_h_tail_wing_weight_ratio', 0.10)

        # Initial MTOW guess
        self.W_MTO_N_current = design_config.get('initial_mtow_guess_N', 50000 * g) # Example 50 tons
        self.W_MZF_N_current = self.W_MTO_N_current * 0.7 # Rough initial guess for MZFW

    def calculate_propulsion_function(self):
        # Based on Torenbeek Eq. 10.9 and components from Eq. 10.7, 10.8
        # R_eq_cruise = self.design_range_m + R_lost_m (R_lost from Eq. 12.63)
        # This needs a proper calculation based on mission profile (Chapter 12)
        # <<< USER ATTENTION REQUIRED: Implement R_eq_cruise properly >>>
        R_lost_m_example = 300e3 # Example
        R_eq_cruise = self.design_range_m + R_lost_m_example

        term_fuel = R_eq_cruise / (self.eta_o_cruise * H_g)
        term_powerplant = self.mu_T_propulsion / (self.tau_cruise_propulsion * (self.p_cruise / 101325.0))
        self.F_prop = term_fuel + term_powerplant
        return self.F_prop

    def calculate_gamma_coeffs(self):
        # Eq 10.13 / 8.1 for Gamma_2
        # Example Psi_S_wing from Eq 8.1 ( Ww = ... + Psi_S * Sw )
        Psi_S_wing_example = 210 # N/m^2, example from Torenbeek p.236
        self.Gamma_2 = (1 + self.r_h_tail_wing_weight_ratio) * Psi_S_wing_example / self.q_hat_cruise

        # Eq 10.35 for Gamma_3
        # <<< USER ATTENTION REQUIRED: W_MZF_N_current is part of an outer iteration loop >>>
        sqrt_W_MZF_q_hat = math.sqrt(self.W_MZF_N_current / self.q_hat_cruise)
        self.Gamma_3 = Gamma_3_coeff_factor * (1 + self.r_h_tail_wing_weight_ratio) * \
                         self.eta_cp_wing * self.n_ult * sqrt_W_MZF_q_hat / self.b_ref_wing
        return self.Gamma_2, self.Gamma_3


    def evaluate_wing_design(self, C_L_hat, A_w, Lambda_w_deg):
        """
        Evaluates a wing design point based on Chapter 10 of Torenbeek.
        """
        Lambda_w_rad = math.radians(Lambda_w_deg)
        R_lost_m_example = 300e3  # Example value for range lost (meters)

        # Step 2: Determine Wing Thickness Ratio / Sweep Angle
        M_dd = self.M_des + delta_M_dd # Target drag divergence Mach number
        # Using Eq. 10.49 to find (t/c)_w (cos Lambda_w)^2
        # (t/c)_w * (cos Lambda_w)^2 = (cos Lambda_w)^3 * (M' - M_dd * cos Lambda_w) - 0.115 * C_L_hat^1.5
        term1 = (math.cos(Lambda_w_rad)**3) * (M_prime - M_dd * math.cos(Lambda_w_rad))
        term2 = 0.115 * C_L_hat**1.5
        tc_cos2_Lambda = term1 - term2

        if tc_cos2_Lambda <= 0: # Not feasible or formula breakdown
            return float('inf'), float('inf'), {} # Indicate infeasible design

        # (t/c)_w can be derived if Lambda_w is fixed, or an optimal Lambda_w can be sought (Eq. 10.50)
        # For now, assume Lambda_w is a selection variable, and tc_cos2_Lambda is determined.
        # Effective (t/c)_w for weight calc is tc_cos2_Lambda / (cos Lambda_w)^2
        # Effective (t/c)_w for profile drag is also related to this.

        # <<< USER ATTENTION REQUIRED: Outer iteration loop for MTOW convergence starts here >>>
        # Initial guess for MTOW might be needed for the first pass
        # For S_w calculation (Eq. 10.1, $S_w = W_{MTO} / (\hat{q} \hat{C}_L)$)
        # And for W_MZF in Gamma_3 calculation

        # Step 3: Calculate Wing Aerodynamic Characteristics
        # S_w depends on W_MTO_N_current which will be updated.
        S_w = self.W_MTO_N_current / (self.q_hat_cruise * C_L_hat)

        # Wing Profile Drag (Eq. 10.39)
        # (CDp)_wing+h.tail = 2 * d_w+h_factor * (1 + r_t_wing * tc_cos2_Lambda) * Cf_cruise
        # Note: tc_cos2_Lambda implicitly contains (t/c)_w and cos(Lambda_w)
        CDp_wing_htail_coeff = 2 * d_w_h_factor * (1 + r_t_wing * tc_cos2_Lambda) * Cf_cruise

        # Drag due to Lift (Eq. 10.40)
        CDL_wing_coeff = C_L_hat**2 / (math.pi * A_w * e_prime_wing)

        # Total airframe drag coefficient at design C_L_hat
        # (CD0S)_airframe = (CDp_wing_htail_coeff * S_w) + self.Cd_fixed_fuselage_vt_nacelles_m2
        # CD_hat_airframe = (CD0S)_airframe / S_w + CDL_wing_coeff + C_Dc_cruise_target
        CD_hat_airframe = (CDp_wing_htail_coeff) + (self.Cd_fixed_fuselage_vt_nacelles_m2 / S_w) + \
                            CDL_wing_coeff + C_Dc_cruise_target

        # Step 4: Calculate Wing and Tail Structure Weight Fraction
        self.calculate_gamma_coeffs() # Recalculate Gamma_2, Gamma_3 with current W_MZF
        # mu_w_h = Gamma_3 * A_w * sqrt(A_w/C_L_hat) / ((t/c)_w * cos^2 Lambda_w) + Gamma_2 / C_L_hat
        # Substitute tc_cos2_Lambda for (t/c)_w * cos^2 Lambda_w
        mu_w_h = (self.Gamma_3 * A_w * math.sqrt(A_w / C_L_hat) / tc_cos2_Lambda) + (self.Gamma_2 / C_L_hat)

        # Step 5: Calculate Wing Penalty Function (WPF)
        # F_wp = mu_w_h + F_prop * ( ( (CDp)_wing+h.tail + C_Dc ) / C_L_hat + C_L_hat / (pi * A_w * e_prime) )
        self.calculate_propulsion_function()
        F_wp = mu_w_h + self.F_prop * ( (CDp_wing_htail_coeff + C_Dc_cruise_target) / C_L_hat + \
                                      C_L_hat / (math.pi * A_w * e_prime_wing) )

        # Step 6: Calculate MTOW (Eq. 10.15)
        # W_pay + Sigma_W_fix_fuselage_systems_etc
        # Sigma_W_fix needs to be estimated based on fuselage size, systems, ops items (Chapter 8)
        # <<< USER ATTENTION REQUIRED: Implement W_payload_N and W_fix_total_N properly >>>
        W_payload_N = self.payload_kg * g
        # Example breakdown for W_fix_total_N (fuselage, vert tail, systems, furnishings, ops items)
        # This should be derived from more detailed Class II methods (Torenbeek Chapter 8.3)
        W_fix_fuselage_example_N = 0.15 * self.W_MTO_N_current # Highly simplified placeholder
        W_fix_systems_example_N = 0.10 * self.W_MTO_N_current  # Highly simplified placeholder
        W_fix_total_N = W_fix_fuselage_example_N + W_fix_systems_example_N # Sum of all fixed weights NOT in WPF num.

        numerator_mtow = W_payload_N + W_fix_total_N + \
                           self.F_prop * self.q_hat_cruise * self.Cd_fixed_fuselage_vt_nacelles_m2
        denominator_mtow = 1 - (mu_resf + mu_lg + F_wp)

        if denominator_mtow <= 0: # Not a feasible design
             return float('inf'), float('inf'), {}

        W_MTO_N_calculated = numerator_mtow / denominator_mtow

        # Update W_MZF_N for Gamma_3 in next iteration (OEW fixed part + payload)
        # OEW_fixed_part = W_fix_total_N + W_lg_N + W_resf_fuel_system_N_etc
        # W_OEW_N = (some_fixed_base_weight) + (factor * W_MTO_N_calculated) # From detailed Class II methods
        # For simplicity, assume OEW is a fraction of MTOW for this outer loop example
        # <<< USER ATTENTION REQUIRED: Implement a proper OEW calculation for W_MZF update >>>
        OEW_fraction_example = 0.55 # Highly simplified
        W_OEW_N_calculated = OEW_fraction_example * W_MTO_N_calculated
        self.W_MZF_N_current = W_OEW_N_calculated + W_payload_N


        # Step 7: Calculate Mission Fuel (using total airframe CD_hat_airframe)
        W_misf_N = W_MTO_N_calculated * (self.design_range_m + R_lost_m_example) / \
                     (self.eta_o_cruise * H_g * (C_L_hat / CD_hat_airframe))
        # Simplified approach from Eq 10.7 for total mission fuel. Note: The P_i in Eq 12.60 or 12.64
        # would be (eta_o * C_L_hat / CD_hat_airframe). R_eq already contains R_lost.

        # Store results
        results = {
            "S_w_m2": S_w,
            "tc_cos2_Lambda": tc_cos2_Lambda,
            "t_over_c_eff": tc_cos2_Lambda / (math.cos(Lambda_w_rad)**2 if math.cos(Lambda_w_rad) !=0 else float('inf')),
            "CDp_wing_htail_coeff": CDp_wing_htail_coeff,
            "CDL_wing_coeff": CDL_wing_coeff,
            "CD_hat_airframe": CD_hat_airframe,
            "mu_w_h": mu_w_h,
            "F_wp": F_wp,
            "W_MTO_N": W_MTO_N_calculated,
            "W_misf_N": W_misf_N
        }
        return W_MTO_N_calculated, W_misf_N, results

    def check_constraints(self, C_L_hat, A_w, Lambda_w_deg, S_w, W_MTO_N, W_L_N, tc_eff):
        """
        Checks constraints from Step 8.
        Returns True if all constraints met, False otherwise.
        """
        # <<< USER ATTENTION REQUIRED: Implement all constraint checks thoroughly >>>
        # Example: Fuel Tank Volume (Eq. 10.30)
        V_tank_m3 = 0.90 * eta_tank_wing * tc_eff * S_w**1.5 * A_w**-0.5
        # Required fuel volume (example: mission fuel + reserve fuel)
        # (Wf)_max needs calculation from mission + reserves
        # W_total_fuel_N = self.W_misf_N_current + mu_resf * W_MTO_N # simplified
        # rho_fuel_kg_m3 = 800 # example
        # V_f_req_m3 = W_total_fuel_N / (rho_fuel_kg_m3 * g)
        # if V_tank_m3 < V_f_req_m3:
        #     print("Constraint failed: Fuel tank volume")
        #     return False

        # Example: Buffet Onset (Section 10.7.2, Figure 10.14)
        # C_L_buffet_limit = get_buffet_limit(self.M_des, tc_eff, Lambda_w_deg) # Needs implementation
        # if C_L_hat > C_L_buffet_limit:
        #     print("Constraint failed: Buffet onset")
        #     return False

        # Example: Pitch-up / Max Aspect Ratio
        # if Lambda_w_deg == 30 and A_w > 10: # Simplified
        #     print("Constraint failed: Max Aspect Ratio / Pitch-up")
        #     return False

        # Example: TOFL Constraint (Chapter 9) - needs T_TO, W_MTO/S_w, b_w
        # b_w = math.sqrt(A_w * S_w)
        # T_TO_N = W_MTO_N * (self.T_TO_over_W_MTO_guess) # Needs thrust calculation
        # if not check_tofl_constraint(W_MTO_N, S_w, b_w, T_TO_N, self.config['max_tofl_m']):
        #     print("Constraint failed: TOFL")
        #     return False

        # Example: LFL Constraint (Chapter 9)
        # CL_max_land = self.config['CL_max_landing']
        # if not check_lfl_constraint(W_L_N, S_w, CL_max_land, self.config['max_lfl_m']):
        #     print("Constraint failed: LFL")
        #     return False

        return True # If all checks pass

# --- Main Optimization Loop ---
def run_transonic_wing_optimization(design_config, fom_choice="MTOW"):
    # <<< USER ATTENTION REQUIRED: This is a highly simplified optimization loop structure.
    # A robust optimization algorithm (e.g., SLSQP, Genetic Algorithm) is needed.
    # Proper handling of constraints within the optimizer is crucial.
    # Iterative convergence for MTOW (and its components like W_MZF, Gamma_3) is vital. >>>

    aircraft_iter = AircraftDesignIteration(design_config)

    # Define ranges for selection variables
    C_L_hat_range = np.linspace(0.3, 0.7, 5)  # Example
    A_w_range = np.linspace(6, 12, 5)        # Example
    Lambda_w_deg_range = np.linspace(25, 35, 3) # Example

    best_fom_value = float('inf')
    best_design_params = {}
    best_results = {}

    print("Starting Transonic Wing Optimization...")
    print(f"Target FOM: Minimize {fom_choice}")

    for C_L_hat_val in C_L_hat_range:
        for A_w_val in A_w_range:
            for Lambda_w_deg_val in Lambda_w_deg_range:
                print(f"\nEvaluating: CL_hat={C_L_hat_val:.2f}, Aw={A_w_val:.1f}, Lambda_w={Lambda_w_deg_val:.1f}")

                # --- MTOW Iteration Loop ---
                # <<< USER ATTENTION REQUIRED: Implement a robust convergence loop for MTOW >>>
                mtow_iteration_limit = 10
                mtow_tolerance = 0.001 * g # 0.1% of 1N
                W_MTO_N_previous = aircraft_iter.W_MTO_N_current
                converged = False
                for i in range(mtow_iteration_limit):
                    W_MTO_N_calc, W_misf_N_calc, results_current = aircraft_iter.evaluate_wing_design(
                        C_L_hat_val, A_w_val, Lambda_w_deg_val
                    )
                    if W_MTO_N_calc == float('inf'): # Infeasible based on tc_cos2_Lambda
                        print("  Design infeasible (tc_cos2_Lambda).")
                        break

                    print(f"  Iter {i+1}: MTOW_calc={W_MTO_N_calc/g:.0f} kg, MZF_curr={aircraft_iter.W_MZF_N_current/g:.0f} kg")
                    if abs(W_MTO_N_calc - W_MTO_N_previous) < mtow_tolerance:
                        aircraft_iter.W_MTO_N_current = W_MTO_N_calc # Final converged value
                        aircraft_iter.W_misf_N_current = W_misf_N_calc
                        converged = True
                        print(f"  MTOW Converged to {W_MTO_N_calc/g:.0f} kg.")
                        break
                    W_MTO_N_previous = W_MTO_N_calc
                    aircraft_iter.W_MTO_N_current = W_MTO_N_calc # Update for next Gamma_3, S_w calc
                
                if not converged and W_MTO_N_calc != float('inf'):
                    print("  MTOW did not converge.")
                    continue
                elif W_MTO_N_calc == float('inf'):
                    continue


                # --- Constraint Checking ---
                # S_w_final = results_current.get("S_w_m2", 0)
                # W_L_N_example = W_MTO_N_calc * 0.85 # Simplified landing weight
                # tc_eff_final = results_current.get("tc_eff",0)
                # if not aircraft_iter.check_constraints(C_L_hat_val, A_w_val, Lambda_w_deg_val, S_w_final, W_MTO_N_calc, W_L_N_example, tc_eff_final):
                #     print("  Design failed constraints.")
                #     continue
                # For this prototype, we'll assume constraints are checked elsewhere or simplify

                # --- Evaluate FOM ---
                current_fom_value = float('inf')
                if fom_choice == "MTOW":
                    current_fom_value = W_MTO_N_calc
                elif fom_choice == "MissionFuel":
                    current_fom_value = W_misf_N_calc
                
                print(f"  Calculated FOM ({fom_choice}): {current_fom_value/g if current_fom_value != float('inf') else 'inf'} kg")

                if current_fom_value < best_fom_value:
                    best_fom_value = current_fom_value
                    best_design_params = {
                        "C_L_hat": C_L_hat_val,
                        "A_w": A_w_val,
                        "Lambda_w_deg": Lambda_w_deg_val
                    }
                    best_results = results_current
                    print(f"  *** New best design found! ***")

    print("\n--- Optimization Finished ---")
    if best_fom_value != float('inf'):
        print(f"Best Design Parameters for minimizing {fom_choice}: {best_design_params}")
        print(f"Best FOM Value: {best_fom_value/g:.2f} kg")
        print("Associated Results:")
        for key, value in best_results.items():
            if isinstance(value, float) and "coeff" not in key and "mu" not in key and "F_wp" not in key:
                print(f"  {key}: {value/g if 'N' in key else value:.4f}")
            else:
                print(f"  {key}: {value:.4f}")

    else:
        print("No feasible design found.")

    return best_design_params, best_fom_value, best_results

# --- Example Usage ---
if __name__ == "__main__":
    # <<< USER ATTENTION REQUIRED: Populate design_config with actual values from design_variables.py >>>
    # This would typically be loaded from your DSEGroup17/design_config.yaml
    # and DSEGroup17/design_variables.py
    example_design_config = {
        "cruise_mach": 0.82,
        "cruise_altitude_m": 11000,
        "payload_kg": 20000,
        "design_range_m": 5500e3, # 5500 km
        "initial_mtow_guess_N": 120000 * g, # Initial MTOW guess in Newtons
        "propulsion_eta_o_cruise": 0.33,
        "propulsion_mu_T": 0.25, # W_pp / T_TO
        "propulsion_tau_cruise": 0.8, # T_cruise_corrected / T_TO
        "Cd_fixed_area": 1.8, # (CDpS)_fix_fuselage_etc in m^2
        "n_ult": 3.75,
        "eta_cp_wing": 0.42,
        "b_ref_wing": 100,
        "r_h_tail_wing_weight_ratio": 0.10
        # Add other necessary parameters here
    }

    # Choose FOM: "MTOW" or "MissionFuel"
    # chosen_fom = "MTOW"
    chosen_fom = "MissionFuel"

    best_params, best_fom, full_results = run_transonic_wing_optimization(example_design_config, fom_choice=chosen_fom)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.cm as cm

# # --- Constants and Assumptions (Values are illustrative and based on typical transonic transports) ---
# # Aerodynamic Parameters
# M_DES = 0.82  # Design cruise Mach number
# Q_CRUISE_PA = 20000  # Dynamic pressure at cruise (Pa), e.g., at 11km altitude, M 0.82 -> q approx 20-25 kPa
# RHO_CRUISE = 0.364 # Air density at cruise altitude (kg/m^3) e.g. 11km
# V_CRUISE = M_DES * np.sqrt(1.4 * 287 * 216.65) # Cruise speed (m/s) for q calculation if needed
# GAMMA_AIR = 1.4 # Ratio of specific heats
# P_STATIC_CRUISE = 22632 # Static pressure at 11km (Pa)
# # Q_CRUISE_PA = 0.5 * GAMMA_AIR * P_STATIC_CRUISE * M_DES**2 # More accurate q

# M_PRIME = 0.935  # Aerodynamic technology factor for Korn's equation (e.g., 0.935 for supercritical)
# DELTA_M_DD = 0.03 # Margin for M_dd over M_des (M_dd = M_des + DELTA_M_DD)
# M_DD_TARGET = M_DES + DELTA_M_DD

# C_F_SKIN = 0.0028  # Skin friction coefficient (turbulent, representative)
# D_W_H_FACTOR = 1.25  # Factor for horizontal tail profile drag relative to wing
# R_T_FACTOR = 3.0  # Shape factor for thickness drag
# OSWALD_EFF_MODIFIED = 0.92  # Modified Oswald efficiency factor (e_tilde) for wing design
# CD_COMPRESSIBILITY_TARGET = 0.0008  # Target compressibility drag at M_des

# # Propulsion Parameters
# R_EQ_KM = 6000  # Equivalent range (km)
# ETA_O_ENGINE = 0.35  # Overall engine efficiency
# H_G_FUEL_KM = 4350  # Fuel specific energy (km)
# MU_T_PROP_WEIGHT = 0.28  # Power plant weight per unit take-off thrust (kg/N or dimensionless if TTO in N)
# TAU_THRUST_LAPSE = 0.25  # Cruise thrust / Take-off thrust at cruise altitude
# DELTA_PRESSURE_RATIO = P_STATIC_CRUISE / 101325 # Pressure ratio at cruise altitude

# # Structural Parameters (Illustrative - these are complex to derive)
# # From Eq 10.35 for Lambda_3
# R_H_TAIL_WEIGHT = 0.10 # Horizontal tail weight as fraction of wing weight
# ETA_CP_WING = 0.45    # Spanwise center of pressure
# N_ULT_LOAD_FACTOR = 3.75 # Ultimate load factor
# W_MZF_GUESS_KG = 100000 * 9.81 # Max Zero Fuel Weight (N) - initial guess
# B_REF_STRUCT_M = 100 # Reference span for wing weight (m)
# LAMBDA_3_BASE = 0.0013 * (1 + R_H_TAIL_WEIGHT) * ETA_CP_WING * N_ULT_LOAD_FACTOR * np.sqrt(W_MZF_GUESS_KG / Q_CRUISE_PA) / B_REF_STRUCT_M

# # From Eq 10.13 for Lambda_2
# SIGMA_S_SECONDARY_STRUCT_PA = 2100 # Secondary structure specific weight (N/m^2 or Pa)
# LAMBDA_2_BASE = (1 + R_H_TAIL_WEIGHT) * SIGMA_S_SECONDARY_STRUCT_PA / Q_CRUISE_PA

# # Weight Parameters for MTOW (Illustrative)
# W_PAY_N = 25000 * 9.81  # Payload weight (N)
# DELTA_W_FIX_N = 60000 * 9.81  # Fixed weight components (N) (fuselage, systems etc.)
# CD_FIXED_DRAG_AREA_M2 = 2.0  # Fixed parasite drag area (m^2) (fuselage, vert tail)
# MU_RESF = 0.045  # Reserve fuel fraction of MTOW
# MU_LG = 0.04  # Landing gear weight fraction of MTOW

# # Constraint Parameters
# ETA_TANK_VOL = 0.55 # Volumetric efficiency of wing tank
# R_M_FUEL_KM = R_EQ_KM + 1500 # Max mission range for fuel tank sizing (km)
# C_RESF_FUEL_FRAC = 0.15 # Reserve fuel as fraction of mission fuel for tank sizing
# RHO_FUEL_KGM3 = 800 # Fuel density (kg/m^3)
# CL_BUFFET_LIMIT = 0.75 # Buffet onset CL at M_des
# A_W_PITCH_UP_LIMIT = 11.0 # Max aspect ratio for pitch-up for given sweep
# TOFL_PROXY_SPAN_LOADING_LIMIT_NM2 = 5000 # Max W_MTO/b_w^2 (N/m^2) as a proxy for TOFL

# # Fixed Design Variables for 2D plots
# LAMBDA_W_DEG = 30.0  # Wing sweep angle (degrees)
# LAMBDA_W_RAD = np.deg2rad(LAMBDA_W_DEG)

# # --- Helper Functions ---
# def calculate_geometry(CL_design, W_MTO_estimate_N, q_cruise_Pa, A_w):
#     """Calculates wing area and span."""
#     if q_cruise_Pa <= 0 or CL_design <= 0:
#         return np.nan, np.nan
#     S_w_m2 = W_MTO_estimate_N / (q_cruise_Pa * CL_design)
#     if S_w_m2 <= 0 or A_w <=0:
#         return np.nan, np.nan
#     b_w_m = np.sqrt(A_w * S_w_m2)
#     return S_w_m2, b_w_m

# def calculate_tc_w_from_Mdd_constraint(M_dd_target, CL_design, Lambda_w_rad, M_prime_tech):
#     """
#     Calculates (t/c)_w based on M_dd constraint (rearranged from Eq. 10.49).
#     (t/c)_w * (cos Lambda_w_rad)^2 = (cos Lambda_w_rad)^3 * (M_prime - M_dd_target * cos Lambda_w_rad) - 0.115 * CL_design^1.5
#     """
#     cos_L = np.cos(Lambda_w_rad)
#     if cos_L == 0: return np.nan
    
#     term1 = (cos_L**3) * (M_prime_tech - M_dd_target * cos_L)
#     term2 = 0.115 * CL_design**1.5
    
#     tc_cos2_lambda = term1 - term2
#     if tc_cos2_lambda <= 0 or cos_L**2 == 0: # t/c must be positive
#         return np.nan 
#     tc_w = tc_cos2_lambda / (cos_L**2)
#     return tc_w

# def calculate_profile_drag_coeff_wing(tc_w, Lambda_w_rad, C_f_skin, d_w_h_factor, r_t_factor):
#     """Calculates wing profile drag coefficient (Eq. 10.39)."""
#     if np.isnan(tc_w): return np.nan
#     cos_L_sq = np.cos(Lambda_w_rad)**2
#     # (C_tilde_Dp)_w from Eq 10.37
#     C_tilde_Dp_w_val = 2 * d_w_h_factor * (1 + r_t_factor * tc_w * cos_L_sq) * C_f_skin
#     return C_tilde_Dp_w_val

# def calculate_induced_drag_coeff(CL_design, A_w, oswald_eff_modified):
#     """Calculates induced drag coefficient (Part of Eq. 10.40)."""
#     if A_w <= 0 or oswald_eff_modified <=0: return np.nan
#     return CL_design**2 / (np.pi * A_w * oswald_eff_modified)

# def calculate_total_airframe_drag_coeff(C_profile_Dp_w, CL_design, C_induced_DL, CD_compressibility_target, S_w_m2, CD_fixed_drag_area_m2):
#     """Calculates total airframe drag coefficient and L/D."""
#     if np.isnan(C_profile_Dp_w) or np.isnan(C_induced_DL) or S_w_m2 <= 0:
#         return np.nan, np.nan
    
#     # CD0 based on Eq 8.16: CD0_airframe = C_profile_Dp_w + CD_fixed_drag_area_m2 / S_w_m2
#     # This C_profile_Dp_w is (C_tilde_Dp)w from Eq 10.39, which is CD0 for the wing+tail part
#     CD0_airframe = C_profile_Dp_w + (CD_fixed_drag_area_m2 / S_w_m2 if S_w_m2 > 0 else np.inf)

#     C_D_total = CD0_airframe + C_induced_DL + CD_compressibility_target
    
#     L_D_ratio = CL_design / C_D_total if C_D_total > 0 else np.nan
#     return C_D_total, L_D_ratio

# def calculate_propulsion_function(R_eq_km, eta_o_engine, H_g_fuel_km, mu_T_prop_weight, tau_thrust_lapse, delta_pressure_ratio):
#     """Calculates the propulsion function F_prop (Eq. 10.9 related)."""
#     if eta_o_engine <= 0 or H_g_fuel_km <=0 or tau_thrust_lapse <=0 or delta_pressure_ratio <=0:
#         return np.nan
#     term_fuel = R_eq_km / (eta_o_engine * H_g_fuel_km)
#     term_engine_weight = mu_T_prop_weight / (tau_thrust_lapse * delta_pressure_ratio)
#     return term_fuel + term_engine_weight

# def calculate_wing_struct_weight_params(Lambda_3_base_val, tc_w, Lambda_w_rad, Lambda_2_base_val):
#     """Calculates Lambda_1_eff and Lambda_2_eff for WPF formula, adapting Lambda_1 for t/c and sweep."""
#     # Adapting Lambda_3 from Eq 10.35 to match structure of Lambda_1 in Eq 10.12 for WPF formula
#     # Lambda_1_eff = Lambda_3_base / (tc_w * (np.cos(Lambda_w_rad))**2)
#     # Lambda_2_eff = Lambda_2_base
#     # The WPF formula (Eq 10.43) uses Lambda_3 directly with tc_w and cos(Lambda_w) in the denominator
#     return Lambda_3_base_val, Lambda_2_base_val


# def calculate_wpf(Lambda_3_eff, A_w, CL_design, tc_w, Lambda_w_rad, Lambda_2_eff, F_prop,
#                   C_profile_Dp_w, CD_compressibility_target, oswald_eff_modified):
#     """Calculates Wing Penalty Function (Eq. 10.43)."""
#     if np.isnan(tc_w) or tc_w <=0 or CL_design <=0 or A_w <=0 or oswald_eff_modified <=0: return np.nan
    
#     term_struct_primary = Lambda_3_eff * A_w * np.sqrt(A_w / CL_design) / (tc_w * (np.cos(Lambda_w_rad))**2)
#     term_struct_secondary = Lambda_2_eff / CL_design
    
#     term_prop_profile = F_prop * (C_profile_Dp_w + CD_compressibility_target) / CL_design
#     term_prop_induced = F_prop * CL_design / (np.pi * A_w * oswald_eff_modified)
    
#     wpf_val = term_struct_primary + term_struct_secondary + term_prop_profile + term_prop_induced
#     return wpf_val

# def calculate_mtow_N(W_pay_N, delta_W_fix_N, F_prop, q_cruise_Pa, CD_fixed_drag_area_m2,
#                      mu_resf, mu_lg, wpf):
#     """Calculates Maximum Take-Off Weight (N) (Eq. 10.15)."""
#     if np.isnan(wpf): return np.nan
    
#     numerator = W_pay_N + delta_W_fix_N + F_prop * q_cruise_Pa * CD_fixed_drag_area_m2
#     denominator = 1 - (mu_resf + mu_lg + wpf)
    
#     if denominator <= 0: # Avoid division by zero or negative (unphysical)
#         return np.nan
#     return numerator / denominator

# # --- Main Visualization Logic ---
# CL_design_range = np.linspace(0.3, 0.7, 21)  # Range for Design Lift Coefficient
# A_w_range = np.linspace(6, 14, 21)      # Range for Aspect Ratio

# WPF_results = np.zeros((len(A_w_range), len(CL_design_range)))
# MTOW_results_N = np.zeros((len(A_w_range), len(CL_design_range)))
# TC_W_results = np.zeros((len(A_w_range), len(CL_design_range)))
# S_W_results = np.zeros((len(A_w_range), len(CL_design_range)))
# B_W_results = np.zeros((len(A_w_range), len(CL_design_range)))

# # Constraint satisfaction matrices
# fuel_vol_ok = np.zeros_like(WPF_results, dtype=bool)
# buffet_ok = np.zeros_like(WPF_results, dtype=bool)
# aspect_ratio_ok = np.zeros_like(WPF_results, dtype=bool)
# span_loading_ok = np.zeros_like(WPF_results, dtype=bool)
# tc_w_valid = np.zeros_like(WPF_results, dtype=bool)


# # Iterative MTOW calculation (simple fixed-point iteration)
# W_MTO_current_N = 150000 * 9.81 # Initial guess for MTOW (N)

# # Pre-calculate F_prop as it's constant for fixed engine/mission params
# F_prop_val = calculate_propulsion_function(R_EQ_KM, ETA_O_ENGINE, H_G_FUEL_KM, MU_T_PROP_WEIGHT, TAU_THRUST_LAPSE, DELTA_PRESSURE_RATIO)

# for i, A_w_val in enumerate(A_w_range):
#     for j, CL_val in enumerate(CL_design_range):
#         # Step 1 (Implicit): W_MTO_current_N is the iterated MTOW
#         # Step 2: Geometry (depends on W_MTO)
#         S_w_val, b_w_val = calculate_geometry(CL_val, W_MTO_current_N, Q_CRUISE_PA, A_w_val)
#         S_W_results[i,j] = S_w_val
#         B_W_results[i,j] = b_w_val

#         # Step 3.1: Thickness ratio from Mdd constraint
#         tc_w_val = calculate_tc_w_from_Mdd_constraint(M_DD_TARGET, CL_val, LAMBDA_W_RAD, M_PRIME)
#         TC_W_results[i,j] = tc_w_val
#         tc_w_valid[i,j] = not np.isnan(tc_w_val) and 0.06 < tc_w_val < 0.18 # Practical limits

#         if not tc_w_valid[i,j]:
#             WPF_results[i, j] = np.nan
#             MTOW_results_N[i, j] = np.nan
#             continue

#         # Step 3.2 - 3.5: Drag components
#         C_profile_Dp_w_val = calculate_profile_drag_coeff_wing(tc_w_val, LAMBDA_W_RAD, C_F_SKIN, D_W_H_FACTOR, R_T_FACTOR)
#         C_induced_DL_val = calculate_induced_drag_coeff(CL_val, A_w_val, OSWALD_EFF_MODIFIED)
#         # CD_total_val, L_D_val = calculate_total_airframe_drag_coeff(C_profile_Dp_w_val, CL_val, C_induced_DL_val, CD_COMPRESSIBILITY_TARGET, S_w_val, CD_FIXED_DRAG_AREA_M2)
#         # Step 4: Propulsion Function (already calculated as F_prop_val)

#         # Step 5: Wing Structural Weight Parameters
#         Lambda_3_eff_val, Lambda_2_eff_val = calculate_wing_struct_weight_params(LAMBDA_3_BASE, tc_w_val, LAMBDA_W_RAD, LAMBDA_2_BASE)
        
#         # Step 6: Wing Penalty Function
#         wpf_calc = calculate_wpf(Lambda_3_eff_val, A_w_val, CL_val, tc_w_val, LAMBDA_W_RAD, Lambda_2_eff_val, F_prop_val,
#                                  C_profile_Dp_w_val, CD_COMPRESSIBILITY_TARGET, OSWALD_EFF_MODIFIED)
#         WPF_results[i, j] = wpf_calc
        
#         # Step 7: MTOW Calculation
#         # Simple iteration for MTOW convergence
#         mtow_iter_N = W_MTO_current_N
#         for _ in range(5): # Iterate a few times
#              # Recalculate S_w with new MTOW estimate for WPF parameters if they depend on MTOW (Lambda_3 does via W_MZF)
#              # For this visualization, assume Lambda_3_base is fixed based on an initial W_MZF_GUESS
#              # This simplifies, otherwise WPF itself becomes dependent on the MTOW iteration.
#             mtow_new_N = calculate_mtow_N(W_PAY_N, DELTA_W_FIX_N, F_prop_val, Q_CRUISE_PA, CD_FIXED_DRAG_AREA_M2,
#                                         MU_RESF, MU_LG, wpf_calc if not np.isnan(wpf_calc) else 1.0) # Use 1.0 if wpf is nan to avoid error
#             if np.isnan(mtow_new_N) or abs(mtow_new_N - mtow_iter_N) < 1000: # Converged if change < 1kN
#                 break
#             mtow_iter_N = mtow_new_N
#         MTOW_results_N[i, j] = mtow_iter_N
        
#         # Update S_w and b_w with the converged MTOW for constraint checks
#         S_w_final, b_w_final = calculate_geometry(CL_val, mtow_iter_N, Q_CRUISE_PA, A_w_val)

#         # Step 8: Evaluate Constraints (using final MTOW and geometry)
#         if np.isnan(mtow_iter_N) or np.isnan(S_w_final) or np.isnan(b_w_final) or np.isnan(tc_w_val):
#             continue

#         # Fuel Tank Volume (Eq. 10.30, 10.31)
#         V_tank_m3 = 0.90 * ETA_TANK_VOL * tc_w_val * S_w_final**1.5 * A_w_val**-0.5
        
#         # Simplified W_misf_for_tank_sizing (based on R_M_FUEL_KM)
#         # Recalculate CD_total for R_M_FUEL_KM (using CL_val, which might not be optimal for max range but is a simplification)
#         CD_total_for_RM, _ = calculate_total_airframe_drag_coeff(C_profile_Dp_w_val, CL_val, C_induced_DL_val, CD_COMPRESSIBILITY_TARGET, S_w_final, CD_FIXED_DRAG_AREA_M2)
#         W_misf_for_tank_N = (R_M_FUEL_KM / (ETA_O_ENGINE * H_G_FUEL_KM * (CL_val / CD_total_for_RM if CD_total_for_RM > 0 else np.inf))) * mtow_iter_N if not np.isnan(CD_total_for_RM) else np.inf

#         W_fuel_total_req_N = W_misf_for_tank_N * (1 + C_RESF_FUEL_FRAC)
#         V_fuel_total_req_m3 = W_fuel_total_req_N / (RHO_FUEL_KGM3 * 9.81)
#         fuel_vol_ok[i, j] = V_tank_m3 >= V_fuel_total_req_m3 if not np.isnan(V_tank_m3) and not np.isnan(V_fuel_total_req_m3) else False

#         # Buffet Onset
#         buffet_ok[i, j] = CL_val <= CL_BUFFET_LIMIT

#         # Aspect Ratio Limit (Pitch-up)
#         aspect_ratio_ok[i, j] = A_w_val <= A_W_PITCH_UP_LIMIT
        
#         # Span Loading (TOFL proxy)
#         span_loading_N_m2 = mtow_iter_N / (b_w_final**2) if b_w_final > 0 else np.inf
#         span_loading_ok[i,j] = span_loading_N_m2 <= TOFL_PROXY_SPAN_LOADING_LIMIT_NM2 if not np.isnan(span_loading_N_m2) else False


# # --- Plotting Results ---
# X, Y = np.meshgrid(CL_design_range, A_w_range)

# fig, ax = plt.subplots(figsize=(12, 10))

# # Plot WPF contours
# contour_wpf = ax.contourf(X, Y, WPF_results, levels=np.linspace(np.nanmin(WPF_results), np.nanmin(WPF_results) + 0.1, 20), extend='both', cmap='viridis_r')
# plt.colorbar(contour_wpf, label='Wing Penalty Function (WPF)')
# contour_lines_wpf = ax.contour(X, Y, WPF_results, levels=np.linspace(np.nanmin(WPF_results), np.nanmin(WPF_results) + 0.1, 10), colors='black', linewidths=0.5)
# ax.clabel(contour_lines_wpf, inline=True, fontsize=8, fmt='%1.3f')

# # Plot MTOW contours (as an alternative FOM)
# # contour_mtow = ax.contour(X, Y, MTOW_results_N / 9.81 / 1000, levels=10, colors='grey', linestyles='--', linewidths=1.0) # MTOW in tonnes
# # ax.clabel(contour_mtow, inline=True, fontsize=8, fmt='%1.0f t')


# # Overlay Constraint Boundaries
# # Valid t/c range (implicitly handled by nan, but could be plotted)
# # ax.contour(X, Y, tc_w_valid.astype(int), levels=[0.5], colors='pink', linestyles=':', linewidths=2, label='Invalid t/c')


# # Fuel Volume Constraint (where fuel_vol_ok becomes False)
# # Need to find the boundary. For simplicity, plot where it's NOT ok.
# fuel_constraint_plot = np.ma.masked_where(fuel_vol_ok, np.ones_like(fuel_vol_ok))
# #ax.pcolormesh(X, Y, fuel_constraint_plot, cmap='Reds_r', alpha=0.2, shading='auto', vmin=0, vmax=1)
# ax.contour(X, Y, fuel_vol_ok.astype(int), levels=[0.5], colors='red', linestyles='-.', linewidths=2, label='Fuel Volume Limit')

# # Buffet Constraint
# buffet_constraint_plot = np.ma.masked_where(buffet_ok, np.ones_like(buffet_ok))
# #ax.pcolormesh(X, Y, buffet_constraint_plot, cmap='Oranges_r', alpha=0.2, shading='auto', vmin=0, vmax=1)
# ax.contour(X, Y, buffet_ok.astype(int), levels=[0.5], colors='orange', linestyles='--', linewidths=2, label='Buffet Limit')

# # Aspect Ratio Limit
# aspect_ratio_constraint_plot = np.ma.masked_where(aspect_ratio_ok, np.ones_like(aspect_ratio_ok))
# #ax.pcolormesh(X, Y, aspect_ratio_constraint_plot, cmap='Purples_r', alpha=0.2, shading='auto', vmin=0, vmax=1)
# ax.contour(X, Y, aspect_ratio_ok.astype(int), levels=[0.5], colors='purple', linestyles=':', linewidths=2, label='Aspect Ratio Limit')

# # Span Loading Limit (TOFL proxy)
# span_loading_constraint_plot = np.ma.masked_where(span_loading_ok, np.ones_like(span_loading_ok))
# #ax.pcolormesh(X, Y, span_loading_constraint_plot, cmap='Greens_r', alpha=0.2, shading='auto', vmin=0, vmax=1)
# ax.contour(X, Y, span_loading_ok.astype(int), levels=[0.5], colors='green', linestyles='-', linewidths=2, label='TOFL (Span Loading) Limit')


# # Identify feasible region
# feasible_region = tc_w_valid & fuel_vol_ok & buffet_ok & aspect_ratio_ok & span_loading_ok
# ax.contourf(X, Y, feasible_region.astype(float), levels=[0.5, 1.5], colors=['none', 'lightgray'], alpha=0.3)
# ax.contour(X, Y, feasible_region.astype(float), levels=[0.5], colors='black', linewidths=2.5, label='Feasible Region Boundary')


# # Find and plot the minimum WPF in the feasible region
# if np.any(feasible_region):
#     wpf_feasible = np.where(feasible_region, WPF_results, np.inf)
#     min_wpf_idx = np.unravel_index(np.argmin(wpf_feasible), wpf_feasible.shape)
#     min_CL = CL_design_range[min_wpf_idx[1]]
#     min_Aw = A_w_range[min_wpf_idx[0]]
#     min_WPF_val = WPF_results[min_wpf_idx]
#     ax.plot(min_CL, min_Aw, 'ko', markersize=10, label=f'Min WPF ({min_WPF_val:.3f}) at CL={min_CL:.2f}, Aw={min_Aw:.1f}')
    
#     # Also print the MTOW at this point
#     mtow_at_min_wpf_tonnes = MTOW_results_N[min_wpf_idx] / 9.81 / 1000
#     print(f"Optimal Point (Min WPF): CL={min_CL:.2f}, Aw={min_Aw:.1f}, WPF={min_WPF_val:.4f}")
#     print(f"  Corresponding (t/c)_w: {TC_W_results[min_wpf_idx]:.4f}")
#     print(f"  Corresponding MTOW: {mtow_at_min_wpf_tonnes:.1f} tonnes")
#     print(f"  Corresponding Wing Area: {S_W_results[min_wpf_idx]:.1f} m^2")
#     print(f"  Corresponding Wing Span: {B_W_results[min_wpf_idx]:.1f} m")


# ax.set_xlabel('Design Lift Coefficient ($C_L$)')
# ax.set_ylabel('Aspect Ratio ($A_w$)')
# ax.set_title(f'Transonic Wing Design Space (WPF Contours) for $\Lambda_w = {LAMBDA_W_DEG}°$')

# # Create a legend for constraint lines
# handles, labels = [], []
# if np.any(~fuel_vol_ok): handles.append(plt.Line2D([0], [0], color='red', lw=2, linestyle='-.')) ; labels.append('Fuel Vol. Limit')
# if np.any(~buffet_ok): handles.append(plt.Line2D([0], [0], color='orange', lw=2, linestyle='--')); labels.append('Buffet Limit')
# if np.any(~aspect_ratio_ok): handles.append(plt.Line2D([0], [0], color='purple', lw=2, linestyle=':')); labels.append('Aspect Ratio Limit')
# if np.any(~span_loading_ok): handles.append(plt.Line2D([0], [0], color='green', lw=2, linestyle='-')); labels.append('TOFL Proxy Limit')
# if np.any(feasible_region):
#     handles.append(plt.Line2D([0], [0], color='black', lw=2.5)); labels.append('Feasible Region')
#     if 'Min WPF' in ax.get_legend_handles_labels()[1]: # Check if min_wpf_plot exists
#          h_opt, l_opt = ax.get_legend_handles_labels()
#          handles.append(h_opt[l_opt.index(f'Min WPF ({min_WPF_val:.3f}) at CL={min_CL:.2f}, Aw={min_Aw:.1f}')]) # Add existinglabel
#          labels.append(f'Min WPF ({min_WPF_val:.3f})')


# ax.legend(handles, labels, loc='upper right', fontsize='small')
# ax.grid(True, linestyle=':', alpha=0.7)
# plt.tight_layout()
# plt.show()

# print("\nNote: This script provides a visualization of the algorithm's sensitivity.")
# print("The 'optimal' point is based on the discretized grid and assumed constants.")
# print("It uses simplified formulas from Chapter 10 of Torenbeek's 'Advanced Aircraft Design'.")
# print(f"Assumed fixed sweep angle: {LAMBDA_W_DEG} degrees.")
# print(f"Assumed design cruise Mach number: {M_DES}.")
# print(f"Assumed (t/c)_w is calculated to meet M_dd = {M_DD_TARGET} using a Korn-like equation.")

