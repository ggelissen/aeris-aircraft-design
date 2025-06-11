import unittest
import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from class1.initial_weight_estimations import *


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
            "A": 12.0,
            "M_tfo": 0.001, 
            "c_j_kg_Ns": 0.00017,
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
