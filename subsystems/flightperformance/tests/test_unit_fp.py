import unittest
import numpy as np
import matplotlib.pyplot as plt

from subsystems.flightperformance.FlightSim import FlightSim
from subsystems.flightperformance.take_off_requirement import calculate_Cm
from subsystems.flightperformance.utils_flight import __ISA__
from subsystems.flightperformance.ControlStability import Control
from subsystems.flightperformance.flightperformance import FlightPerformance


class TestGroundRun(unittest.TestCase):

    def setUp(self):
        FS = FlightSim()
        self.T1 = FS.ground_run2(7000, 5000, 12, 0.017, 10, 0.9, 14, 1, 1800)
        self.T2 = FS.ground_run2(7000, 4000, 12, 0.017, 10, 0.9, 14, 1, 1800)
        self.Cm1 = calculate_Cm(1, 4000, 12, 4, 6, 1, 7, 6, 1,  1, 1, 2, 0.017, 10, 0.9, 14, 1, 1800)
        self.Cm2 = calculate_Cm(1, 4000, 12, 4, 6, 1, 7, 6, 1, -1, 1, 2, 0.017, 10, 0.9, 14, 1, 1800)
        self.Cm3 = calculate_Cm(1, 5000, 12, 4, 6, 1, 7, 6, 1,  1, 1, 2, 0.017, 10, 0.9, 14, 1, 1800)

    def test_groundrun(self):
        self.assertGreater(self.T1[0], self.T2[0]) # larger weight should require larger thrust to take-off

    def test_Cm(self):
        self.assertLess(self.Cm1[0], self.Cm2[0]) # deflecting elevator up should increase Cm
        self.assertLess(self.Cm3[0], self.Cm1[0]) # Higher thrust (bc of higher weight) should decrease Cm

class TestISA(unittest.TestCase):
    def setUp(self):
        self.results0 = __ISA__(0)
        self.results1 = __ISA__(-1000)
        self.results2 = __ISA__(1000)
        self.results3 = __ISA__(20000)

    def test_ISA(self):
        self.assertEqual(self.results0[0], 15.00+273.15)
        self.assertAlmostEqual(self.results0[1]/100, 10.13*10**4/100, 0)
        self.assertAlmostEqual(self.results0[2], 1.225,2)
        self.assertAlmostEqual(self.results0[3], (1.4*287.05*(15+273.15))**0.5, 0)
        self.assertEqual(self.results1[0], 15.00+273.15)
        self.assertAlmostEqual(self.results1[1]/100, 10.13*10**4/100, 0)
        self.assertAlmostEqual(self.results1[2], 1.225,2)
        self.assertAlmostEqual(self.results1[3], (1.4*287.05*(15+273.15))**0.5, 0)
        self.assertEqual(self.results2[0], 8.5+273.15)
        self.assertAlmostEqual(self.results2[1]/100, 8.988*10**4/100, 0)
        self.assertAlmostEqual(self.results2[2], 1.112, 2)
        self.assertAlmostEqual(self.results2[3], (1.4*287.05*(8.5+273.15))**0.5, 0)
        self.assertEqual(self.results3[0], -56.5+273.15)
        self.assertAlmostEqual(self.results3[1]/1000, 0.5529*10**4/1000, 0)
        self.assertAlmostEqual(self.results3[2], 0.08891, 2)
        self.assertAlmostEqual(self.results3[3], (1.4*287.05*(-56.5+273.15))**0.5, 0)

class TestStability(unittest.TestCase):
    def setUp(self):
        control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, mac=2, Vh_V=1, CLh=-2, CLA_h=0.6, C_m_ac=-0.5, x_lemac=6, l_fus=12)
        control2 = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, mac=2, Vh_V=1, CLh=-2, CLA_h=0.7, C_m_ac=-0.5, x_lemac=6, l_fus=12)
        control3 = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, mac=2, Vh_V=1, CLh=-2, CLA_h=0.6, C_m_ac=-0.5, x_lemac=6, l_fus=15)
        self.ShS_stable = control.__stability_curve__(0.5)
        self.ShS_control = control.__control_curve__(0.5)
        self.xcg = control.__calculate_X_stability__(0.2)
        self.xcg_oew = control.xcg_OEW_estimation(1000, 0.5, 1000, 0.5)
        self.cg_min, self.cg_max = control.cg_range(2500, 0.65, [100, 500], [0.8, 0.1], [800, 200], [0.65, 0.8])
        self.cg_range1 = control.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[3], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=7)
        self.cg_range2 = control2.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[3], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=7)
        self.cg_range3 = control3.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[3], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=7)
        self.cg_range4 = control.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[7], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=7)
        plt.close('all')
        
    def testcontrol(self):
        self.assertAlmostEqual(self.ShS_control, 0.063636363)

    def teststability(self):
        self.assertAlmostEqual(self.ShS_stable, 0.12121212)

    def test_cg_mac(self):
        self.assertAlmostEqual(self.xcg, 0.695)

    def test_cg_oew(self):
        self.assertEqual(self.xcg_oew, 1/2)

    def test_cg_range(self):
        self.assertAlmostEqual(self.cg_min, 0.5471666667)
        self.assertAlmostEqual(self.cg_max, 0.6688846154)
    
    def test_cg_range2(self):
        self.assertGreater(self.cg_range1["cg_range"], self.cg_range2["cg_range"])
        self.assertGreater(self.cg_range1["Sh/S"], self.cg_range3["Sh/S"])
        self.assertLess(self.cg_range1["x_lemac/lfus"], self.cg_range4["x_lemac/lfus"])

class TestFlightPerformance(unittest.TestCase):
    def setUp(self):
        self.fp = FlightPerformance()
        self.D, self.D0, self.Di = self.fp.__drag__(0.02, 1.225, 100, 20, 5000, 10, 0.9)
        self.range = self.fp.__range__(20*(10**-6), 50000, 30000, 10, 0.9, 0.01, 0.3108, 12)
        self.payload_range_min, self.payload_range_max = self.fp.payload_range(20*(10**-6), 10, 0.9, 0.01, 50000, 20000, 20000, 0.3108, 12)
        self.ROC1 = self.fp.ROC(0.017, 1.225, np.arange(1, 500, 1), 20, 50000, 10, 0.9, 7000)
        self.ROC2 = self.fp.ROC(0.017, 1.225, np.arange(1, 500, 1), 20, 50000, 10, 0.9, 4000)
        self.ROC3 = self.fp.ROC(0.017, 0.5, np.arange(1, 500, 1), 20, 50000, 10, 0.9, 7000*(0.5/1.225))
        self.stall_speed = self.fp.stall_speed(560000*9.81, 845, 1.225, 2)
        self.endurance = self.fp.endurance(20000, 50000, 0.02, 10, 0.88, 14*(10**-6))
        self.hmax1, self.vmax1 = self.fp.performance_limit(50000, 15, 1.1, 7000, 0.02, 10, 0.88)
        self.hmax2, self.vmax2 = self.fp.performance_limit(35000, 15, 1.1, 7000, 0.02, 10, 0.88)
        self.hmax3, self.vmax3 = self.fp.performance_limit(50000, 15, 1.1, 10000, 0.02, 10, 0.88)

    def testDrag1(self):
        self.assertAlmostEqual(self.D,2457.217911, 5)
    def testDrag2(self):
        self.assertAlmostEqual(self.D0,2450)
    def testDrag3(self):
        self.assertAlmostEqual(self.Di,7.217911251, 5)

    def testRange(self):
        self.assertAlmostEqual(self.range, 15634.688, places=1)
    
    def test_range_vel(self):
        self.assertAlmostEqual(self.range[1], 84.394, places=1)
    
    def test_max_payload_range(self):
        self.assertAlmostEqual(self.payload_range_max, self.fp.__range__(20*(10**-6), 40000, 20000, 10, 0.9, 0.01, 0.3108, 12),0)
    
    def test_min_payload_range(self):
        self.assertAlmostEqual(self.payload_range_min, self.fp.__range__(20*(10**-6), 50000, 30000, 10, 0.9, 0.01, 0.3108, 12),0)

    def test_ROC_less_thrust1(self):
        self.assertGreater(self.ROC1[0], self.ROC2[0])
    def test_ROC_less_thrust2(self):
        self.assertEqual(self.ROC1[1], self.ROC2[1])
    def test_ROC_less_thrust3(self):
        self.assertGreater(self.ROC1[2], self.ROC2[2])
    def test_ROC_less_thrust4(self):
        self.assertGreater(self.ROC1[3], self.ROC2[3])
        
    def test_ROC_higher_alt1(self):
        self.assertGreater(self.ROC1[0], self.ROC3[0])
    def test_ROC_higher_alt2(self):
        self.assertLess(self.ROC1[1], self.ROC3[1])
    def test_ROC_higher_alt3(self):
        self.assertGreater(self.ROC1[2], self.ROC3[2])
    def test_ROC_higher_alt4(self):
        self.assertLess(self.ROC1[3], self.ROC3[3])
        
    def test_stall_speed(self):
        self.assertAlmostEqual(self.stall_speed, 72.8504298)
        
    def test_endurance(self):
        self.assertAlmostEqual(self.endurance, 69142.79158, 4)
    
    def test_limit_low_weight(self):
        self.assertGreater(self.hmax2, self.hmax1)
        self.assertGreater(self.vmax2, self.vmax1)
        
    def test_limit_high_thrust(self):
        self.assertGreater(self.hmax3, self.hmax1)
        self.assertGreater(self.vmax3, self.vmax1)