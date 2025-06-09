import unittest

from subsystems.flightperformance.FlightSim import FlightSim
from subsystems.flightperformance.take_off_requirement import calculate_Cm

class TestGroundRun(unittest.TestCase):
    
    def setUp(self):
        FS = FlightSim()
        self.T1 = FS.ground_run2(7000, 5000)
        self.T2 = FS.ground_run2(7000, 4000)
        self.Cm1 = calculate_Cm(1, 4000, 12, 4, 6, 1, 7, 6, 1, 1, 1, 1, 2)
        self.Cm2 = calculate_Cm(1, 4000, 12, 4, 6, 1, 7, 6, 1, 1, -1, 1, 2)
    
    def test_groundrun(self):
        self.assertGreater(self.T1[0], self.T2[0]) # larger weight should require larger thrust to take-off
    
    def test_Cm(self):
        self.assertLess(self.Cm1[0], self.Cm2[0]) # deflecting elevator up should increase Cm