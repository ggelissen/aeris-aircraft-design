import unittest

from subsystems.flightperformance.FlightSim import FlightSim

class TestGroundRun(unittest.TestCase):
    
    def setUp(self):
        FS = FlightSim()
        self.T1 = FS.ground_run2(7000, 5000)
        self.T2 = FS.ground_run2(7000, 4000)
    
    def test_groundrun(self):
        self.assertGreater(self.T1[0], self.T2[0]) # larger weight should require larger thrust to take-off