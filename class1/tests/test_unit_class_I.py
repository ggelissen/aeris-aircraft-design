import unittest
import math
import sys
import os
import copy


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from class1.initial_weight_estimations import *
from class1.thrust_wing_loading import *
from class1.preliminary_sizing.prelim_sizing_wing import *

class TestClassI(unittest.TestCase):
    def test_get_drag_polar_params(self):
        self.assertEqual(get_drag_polar_params('uav'), (0.02, 0.8))
        self.assertEqual(get_drag_polar_params("business_jet"), (0.017, 0.8))
        self.assertEqual(get_drag_polar_params("helicopter"), (0.025, 0.8))

    def test_calculate_L_D_cruise_jet(self):
        self.assertAlmostEqual(calculate_L_D_cruise_jet(0, 10, 0.9), float('inf'))
        self.assertAlmostEqual(calculate_L_D_cruise_jet(0.04, 10, 0.9), 11.51, places=2)
        self.assertEqual(calculate_L_D_cruise_jet(-0.02, 10, 0.9), float('inf'))


    def test_calculate_L_D_loiter(self):
        self.assertAlmostEqual(calculate_L_D_loiter(0, 10, 0.9), float('inf'))
        self.assertAlmostEqual(calculate_L_D_loiter(0.04, 10, 0.9), 13.29, places=2)
        self.assertEqual(calculate_L_D_loiter(-0.02, 10, 0.9), float('inf'))

    def test_get_statistical_fuel_fractions(self):
        self.assertEqual(get_statistical_fuel_fractions('uav', 'M4_climb1'), 0.980)
        self.assertEqual(get_statistical_fuel_fractions('business_jet', 'climb'), 0.980)
        self.assertEqual(get_statistical_fuel_fractions('uav', 'descent'), 0.990)
        self.assertEqual(get_statistical_fuel_fractions('business_jet', 'unknown'), 1.0)
        self.assertEqual(get_statistical_fuel_fractions('helicopter', 'climb'), 1.0)
    
    def test_calculate_cruise_fuel_fraction(self):
        self.assertAlmostEqual(calculate_cruise_fuel_fraction_jet(3000000, 240, 16, 0.00017), 0.272, places=3)
        self.assertEqual(calculate_cruise_fuel_fraction_jet(3000000, 0, 20, 0.00015), 0)
        self.assertEqual(calculate_cruise_fuel_fraction_jet(3000000, 240, 0, 0.00017), 0)

    def test_calculate_loiter_fuel_fraction(self):
        self.assertAlmostEqual(calculate_loiter_fuel_fraction_jet(2700, 18, 0.00017), 0.779, places=3)
        self.assertEqual(calculate_loiter_fuel_fraction_jet(2700, 0, 0.00017), 0)

    def test_get_empty_weight_coeffs(self):
        self.assertEqual(get_empty_weight_coeffs('uav'), (0.3765, 227.795))
        self.assertEqual(get_empty_weight_coeffs('business_jet'), (0.5417, 579.96))
        self.assertEqual(get_empty_weight_coeffs('helicopter'), (0.5, 1000))

    def setUp(self):
        self.uav_aircraft_params = {
            "type": "uav",
            "A": 9,
            "M_tfo": 0.05, 
            "c_j_kg_Ns": lb_hr_lbf_to_kg_Ns(0.685),
            "type_for_coeffs": "uav"
        }
        self.uav_mission_params = {
            "W_PL_N": 5000,
            "W_crew_N": 0.0,
            "R_cruise1_m": 3000000,
            "V_cruise_ms": 250
        }
        self.uav_reserve_params = {
            "type": "mission_extension",
            "R_cruise2_m": 460000,
            "E_loiter_s": 7200
        }

    def test_class1_weight_estimation(self):
        results = class1_weight_estimation(self.uav_aircraft_params, 
                                           self.uav_mission_params, 
                                           self.uav_reserve_params, 
                                           verbose=False)
        print(results)
        self.assertIsNotNone(results)
        
        sum_of_components = (results["W_E"] + 
                             results["W_F"] + 
                             results["W_PL"] + 
                             results["W_crew"] 
                             +results["W_tfo"])
        self.assertAlmostEqual( results["W_TO"], sum_of_components,places=1)
        self.assertGreater(results["W_TO"], 0)
        self.assertGreater(results["W_TO"], results["W_E"])
        self.assertGreater(results["W_TO"], results["W_F"])
        self.assertLess(results["M_ff"], 1.0)
        self.assertGreater(results["M_ff"], 0.0)

        longer_range_mission_params = copy.deepcopy(self.uav_mission_params)
        longer_range_mission_params["R_cruise1_m"] = 5000000
        longer_range_results = class1_weight_estimation(self.uav_aircraft_params, 
                                                        longer_range_mission_params, 
                                                        self.uav_reserve_params, 
                                                        verbose=False)
        self.assertGreater(longer_range_results["W_TO"], results["W_TO"])
    
    

    def setUpPayloadRange(self):
        self.design_results = {
            "W_TO_N": 70000,
            "W_OE_N": 40000,
            "W_PL_N": 5000,
            "L_D_cruise1": 16.0,
            "mission_segments_detailed_ff": [
                ("M1_eng_start_warmup", 0.990), ("M2_taxi_out", 0.995),
                ("M3_take_off", 0.995), ("M4_climb1", 0.980),
                ("M6_descent1", 0.990), ("M7_climb2_reserve", 0.990),
                ("M8_cruise2_reserve", 0.985), ("M9_loiter_reserve", 0.970),
                ("M10_descent2_reserve", 0.990), ("M11_land_taxi_shutdown", 0.995),
            ]
        }
        self.aircraft_params_pr = {
            "type": "uav",
            "c_j_kg_Ns": lb_hr_lbf_to_kg_Ns(0.685),
        }
        self.mission_config_pr = {
            "V_cruise_ms": 250,
            "R_cruise1_m": 5000000
        }
        self.W_P_max_structural_N = 12000
        self.W_F_max_capacity_N = 25000

    def test_calculate_payload_range_points(self):
        self.setUpPayloadRange()
        pr_data = calculate_payload_range_points(
            self.design_results,
            self.aircraft_params_pr,
            self.mission_config_pr,
            self.W_P_max_structural_N,
            self.W_F_max_capacity_N
        )

        self.assertIsInstance(pr_data, list)
        self.assertEqual(len(pr_data), 6, "Function should return 6 data points")
        for point in pr_data:
            self.assertIsInstance(point, dict)
            self.assertIn("W_P_kg", point)
            self.assertIn("R_km", point)
            self.assertIn("Segment", point)

        payloads_kg = [p['W_P_kg'] for p in pr_data]
        self.assertEqual(payloads_kg, sorted(payloads_kg, reverse=True), "Data must be sorted by payload descending")

        max_payload_point = pr_data[0]
        design_point = pr_data[1]
        ferry_point = pr_data[-1]

        self.assertEqual(max_payload_point["Segment"], "Max Payload")
        self.assertAlmostEqual(max_payload_point["W_P_kg"], N_to_kg(self.W_P_max_structural_N), places=1)
        
        self.assertEqual(design_point["Segment"], "Design Point")
        self.assertAlmostEqual(design_point["W_P_kg"], N_to_kg(self.design_results["W_PL_N"]), places=1)

        self.assertEqual(ferry_point["Segment"], "Ferry Range")
        self.assertAlmostEqual(ferry_point["W_P_kg"], 0, places=1)

        ranges_km = [p['R_km'] for p in pr_data]
        for i in range(len(ranges_km) - 1):
            self.assertGreaterEqual(ranges_km[i+1], ranges_km[i],
                                    f"Range must not decrease as payload decreases. Failed at index {i}.")

        self.assertEqual(ferry_point["R_km"], max(ranges_km))
        
class TestThrustWingLoading(unittest.TestCase):
    def test_get_isa_conditions_pd(self):
        T, P, rho, sig, delta, theta = get_isa_conditions_pd(0)
        #sea level
        self.assertAlmostEqual(T, 288.15, places=1)
        self.assertAlmostEqual(P, 101325, places=1)
        self.assertAlmostEqual(rho, 1.225, places=1)
        self.assertAlmostEqual(sig, 1.0, places=1)
        self.assertAlmostEqual(delta, 1.0, places=1)
        self.assertAlmostEqual(theta, 1.0, places=1)

        # tropopause
        T, P, rho, sig, delta, theta = get_isa_conditions_pd(11000)
        self.assertAlmostEqual(T, 216.65, places=1)
        self.assertAlmostEqual(P, 22632, places=0)
        self.assertAlmostEqual(rho, 0.36391, places=1)
        self.assertAlmostEqual(sig, 0.297, places=1)
        self.assertAlmostEqual(delta, 0.226, places=1)
        self.assertAlmostEqual(theta, 0.75, places=1)
        # above tropopause
        T, _, _, _, _, _ = get_isa_conditions_pd(20000)
        self.assertAlmostEqual(T, T, places=1)

        # for LAPSE RATE ISA ==0


    def test_get_aircraft_config_aerodynamics(self):
        C_D0, e, C_Lmax, A  = get_aircraft_config_aerodynamics_pd('uav', "clean_config_P12", 9.0)
        self.assertEqual(C_D0, 0.0145)
        self.assertEqual(e, 0.85)
        self.assertEqual(C_Lmax, 0.8)
        # Test an undefined configuration, should return default clean values
        C_D0_def, e_def, C_Lmax_def, _ = get_aircraft_config_aerodynamics_pd("uav", "non_existent_config", 9)
        self.assertEqual(C_D0_def, 0.0145)
        self.assertEqual(e_def, 0.85)
        self.assertEqual(C_Lmax_def, 1.8)

        C_D0, e, C_Lmax, A = get_aircraft_config_aerodynamics_pd('uav', "take_off_gear_down_P12", 9.0)
        self.assertEqual(C_D0, 0.042)
        self.assertEqual(e, 0.9)
        self.assertEqual(C_Lmax, 1.9)

        C_D0, e, C_Lmax, A = get_aircraft_config_aerodynamics_pd('uav', "generic_landing_flaps_gear_down", 9.0)
        self.assertEqual(C_D0, 0.0145 + 0.02 + 0.065)
        self.assertEqual(e, 0.85+0.1)
        self.assertEqual(C_Lmax, 2.6)


    def test_get_C_L_at_CL32_CD_max_pd(self):
        self.assertEqual(get_C_L_at_CL32_CD_max_pd(0, 0, 0), 0)

    def test_get_CD_at_CL_pd(self):
        self.assertEqual(get_CD_at_CL_pd(0, 0, 0, 0), float('inf'))

    def test_constraint_stall_speed_pd(self):
        self.assertAlmostEqual(constraint_stall_speed_pd(None, 1.225, 50, 1.8), 2756.25, places=2)
        self.assertIsNone(constraint_stall_speed_pd(None, 1.225, 50, 0))

    def test_constraint_takeoff_distance_uav_pd(self):   
        self.assertAlmostEqual(constraint_take_off_distance_uav_pd(3500, 1219.2, 1.9, 1, "uav_2_engine"), 0.345, places=3)

    def test_constraint_landing_distance_uav_pd(self):
        W_S_TO = constraint_landing_distance_pd(None, 1200, 2.4, 0.9, 1.225, "CS25")
        self.assertAlmostEqual(W_S_TO, 3352.146, places=1)
        self.assertIsNone(constraint_landing_distance_pd(None,- 1200, -0, -0.9, -1.225), None)

    def test_constraint_cruise_speed_uav_pd(self):
        V_cruise_ms = 240.0
        alt_cruise_m = 10000
        C_D0_clean = 0.0145
        e_clean = 0.85
        A_clean = 9.0
        with self.subTest(msg="Core calculation with valid inputs"):
            wing_loading = np.array([4000.0]) 
            result_T_W = constraint_cruise_speed_uav_pd(wing_loading, V_cruise_ms, alt_cruise_m, C_D0_clean, e_clean, A_clean)
            self.assertAlmostEqual(result_T_W[0], 0.131, places=2)
      
        with self.subTest(msg="Handles zero wing loading"):
            wing_loading_invalid = np.array([0.0])
            result_invalid = constraint_cruise_speed_uav_pd(
                wing_loading_invalid, V_cruise_ms, alt_cruise_m, C_D0_clean, e_clean, A_clean)
            self.assertTrue(np.isnan(result_invalid[0]))        

    def test_interpolate_TOP_pd(self):
        """ Tests the Take-Off Parameter interpolation from the chart. """
        expected_top_npm2 = psf_to_Npm2(152.5)
        self.assertAlmostEqual(interpolate_TOP_pd(4500, "uav_2_engine"), expected_top_npm2, places=1)
        
        expected_low_npm2 = psf_to_Npm2(60)
        self.assertAlmostEqual(interpolate_TOP_pd(1000, "uav_2_engine"), expected_low_npm2, places=1)

        expected_high_npm2 = psf_to_Npm2(320)
        self.assertAlmostEqual(interpolate_TOP_pd(12000, "uav_2_engine"), expected_high_npm2, places=1)

       

    def test_constraint_climb_rate_uav_pd(self):
        """ Tests the climb rate constraint calculation. """
        wing_loading = np.array([4000.0]) # N/m^2
        roc_ms = 5.0 # m/s
        alt_climb_m = 3000 # m
        C_D0_climb, e_climb, A_climb = 0.02, 0.8, 9.0
        
        # Expected value calculated manually based on the formulas
        # This checks the entire chain: ISA calc -> CL_opt -> V_climb -> T/W
        expected_tw = 0.158
        result_tw = constraint_climb_rate_uav_pd(
            wing_loading, roc_ms, alt_climb_m, C_D0_climb, e_climb, A_climb
        )
        self.assertAlmostEqual(result_tw[0], expected_tw, places=3)
        
    def test_constraint_climb_gradient_uav_pd(self):
        """ Tests the climb gradient constraint for both AEO and OEI cases. """
        wing_loading = np.array([3000.0])
        alt_grad_m = ft_to_m(5000)
        C_D0_grad, e_grad, A_grad = 0.027, 0.9, 9.0
        
        with self.subTest("AEO (All Engines Operative)"):
            grad_req_aeo = 0.024 # 2.4% gradient
            result_tw_aeo = constraint_climb_gradient_uav_pd(
                wing_loading, grad_req_aeo, alt_grad_m, 
                C_D0_grad, e_grad, A_grad, is_OEI=False
            )
            # Expected value calculated manually
            self.assertAlmostEqual(result_tw_aeo[0], 0.098, places=2)

        with self.subTest("OEI (One Engine Inoperative)"):
            grad_req_oei = 0.012 # 1.2% gradient for 2-engine aircraft
            delta_CD0_OEI = 0.005
            result_tw_oei = constraint_climb_gradient_uav_pd(
                wing_loading, grad_req_oei, alt_grad_m, 
                C_D0_grad, e_grad, A_grad, 
                is_OEI=True, num_engines=2, delta_CD0_OEI=delta_CD0_OEI
            )
            # Expected value calculated manually (should be significantly higher)
            self.assertAlmostEqual(result_tw_oei[0], 0.183, places=2)

class TestPrelimWingSizing(unittest.TestCase):
    def test_calculate_sweep_angle_025c_rad(self):
        self.assertEqual(calculate_sweep_angle_025c_rad(0.5, 0.935), 0)
        self.assertAlmostEqual(calculate_sweep_angle_025c_rad(0.8, 0.935), 0.564, places=3)

    def test_calculate_taper_ratio(self):
        self.assertAlmostEqual(calculate_taper_ratio(0.5), 0.3)

    def test_calculate_chord_lengths(self):
        # self.assertTupleEqual(calculate_chord_lengths(5, 2, 0.5), (3.3, 1.6))
        self.assertAlmostEqual(calculate_chord_lengths(5, 2, 0.5)[0], 3.33, places=1)
        self.assertAlmostEqual(calculate_chord_lengths(5, 2, 0.5)[1], 1.67, places=1)

    def test_calculate_MAC_and_y_LEMAC(self):
        c_root, c_tip, b = 3.33, 1.67, 2
        self.assertAlmostEqual(calculate_MAC_and_y_LEMAC(c_root, c_tip, b)[0], 2.59, places=2)
        self.assertAlmostEqual(calculate_MAC_and_y_LEMAC(c_root, c_tip, b)[1], 0.44, places=2)

    def test_calculate_thickness_ratio(self):
        self.assertGreater(calculate_thickness_ratio(12000, 0.5, 50000, 10, 0.3, 0.935), calculate_thickness_ratio(12000, 0.75, 50000, 10, 0.3, 0.935))
        self.assertGreater(calculate_thickness_ratio(10000, 0.5, 50000, 10, 0.3, 0.935), calculate_thickness_ratio(10000, 0.75, 50000, 10, 0.4, 0.935))

    def calculate_dihedral_angle_rad(self):
        self.assertAlmostEqual(calculate_dihedral_angle_rad(0.598), np.deg2rad(2.0), places=3)
        self.assertAlmostEqual(calculate_dihedral_angle_rad(0.0), np.deg2rad(5.0), places=3)

    def calculate_sweep_angle_LE(self):
        self.assertAlmostEqual(calculate_sweep_angle_LE(0.598, 3.33, 2, 0.5), 0.0, places=3)
        self.assertAlmostEqual(calculate_sweep_angle_LE(0.598, 3.33, 2, 0.3), 0.1, places=3)
        self.assertGreater(calculate_sweep_angle_LE(0.8, 3.33, 2, 0.5), calculate_sweep_angle_LE(0.5, 3.33, 2, 0.5))

    def calculate_sweep_angle_x_c(self):
        self.assertAlmostEqual(calculate_sweep_angle_x_c(0.0, 3.33, 2, 0.25, 0.5), 0.0, places=3)
        self.assertAlmostEqual(calculate_sweep_angle_x_c(0.1, 3.33, 2, 0.25, 0.5), 0.1, places=3)
        self.assertGreater(calculate_sweep_angle_x_c(0.8, 3.33, 2, 0.25, 0.5), calculate_sweep_angle_x_c(0.5, 3.33, 2, 0.25, 0.5))

 

if __name__ == '__main__':
    unittest.main(verbosity=2)