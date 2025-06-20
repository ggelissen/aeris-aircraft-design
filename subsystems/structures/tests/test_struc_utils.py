import unittest
import subsystems.structures.utils_struct as utils

class StrucUtilsTest(unittest.TestCase):
    def test_calculate_normal_strains(self):
        result = utils.calculate_normal_strains(23*10**6, 5*10**6, 110*10**6, 35, 70*10**9, 0.34, 0.003)
        self.assertAlmostEqual(result['x'], 0.10477)
        self.assertAlmostEqual(result['y'], 0.104425, 3)
        self.assertAlmostEqual(result['z'], 0.1064354, 3)
    
    def test_calculate_axial_deformation(self):
        result = utils.calculate_axial_deformation(12345, 69, 420*10**8, 42)
        self.assertAlmostEqual(result, 4.82882*10**-7, 3)
    
    def test_calculate_axial_stress(self):
        result = utils.calculate_axial_stress(69420, 42)
        self.assertAlmostEqual(result, 1652.8571, 3)

    def test_calculate_bending_stress(self):
        result = utils.calculate_bending_stress(69420, 100, 2020)
        self.assertAlmostEqual(result, 3436.6336633, 3)

    def test_calculate_Mohrs_circle_stress(self):
        result = utils.calculate_Mohrs_circle_stress(200*10**6, 69*10**6, 7*10**6)
        self.assertAlmostEqual(result[0], 200.37298, 3)
        self.assertAlmostEqual(result[1], 68.62701, 3)
        self.assertAlmostEqual(result[2], 65.87298, 3)

    def test_calculate_shear_strains(self):
        result = utils.calculate_shear_strains(1*10**6, 2*10**6, 3*10**6, 360*10**8)
        self.assertAlmostEqual(result['xy'], 2.77777*10**-5)
        self.assertAlmostEqual(result['xz'], 5.55555*10**-5)
        self.assertAlmostEqual(result['yz'], 8.333333*10**-5)

    def test_calculate_transverse_shear_stress(self):
        result = utils.calculate_transverse_shear_stress(6969, 10*(10**-3), 10101010, 2)
        self.assertAlmostEqual(result, 3.44965*10**-6)        

    def test_calculate_torsional_deformation_circ(self):
        result = utils.calculate_torsional_deformation_circ(69696, 6.9, 69*10**9, 69)
        self.assertAlmostEqual(result, 1.0100869*10**-7)

    def test_calculate_torsional_stress_circ(self):
        result = utils.calculate_torsional_stress_circ(69696, 50, 3.60)
        self.assertAlmostEqual(result, 5018.112)

    def test_calculate_torsional_stress_thin(self):
        result = utils.calculate_torsional_stress_thin(69696, 5, 47)
        self.assertAlmostEqual(result, 148.2893617, 3)

    def test_equivalent_to_true_air_speed(self):
        result = utils.equivalent_to_true_air_speed(300, 0.3108, 1.225)
        self.assertAlmostEqual(result, 595.591915, 3)

    def test_Pa_to_lbf_ft2(self):
        result = utils.Pa_to_lbf_ft2(30*10**6)
        self.assertAlmostEqual(result, 7518756.3382, 2)

    def test_N_to_lbf(self):
        result = utils.N_to_lbf(696969)
        self.assertAlmostEqual(result, 156684.9211, 2)

    def test_true_to_equivalent_air_speed(self):
        result = utils.true_to_equivalent_air_speed(123, 0.3108, 1.225)
        self.assertAlmostEqual(result, 61.95517273)

    def test_psf_to_Npm2(self):
        result = utils.psf_to_Npm2(420420)
        self.assertAlmostEqual(result, 20129835.726, 0)

    def test_Pa_to_lbf_ft2(self):
        result = utils.Pa_to_lbf_ft2(360*10**6)
        self.assertAlmostEqual(result, 7518756.3382, 2)

    def test_N_to_kg(self):
        result = utils.N_to_kg(696969)
        self.assertAlmostEqual(result, 71071.0589, 2)

    def test_ms_to_kts(self):
        result = utils.ms_to_kts(222)
        self.assertAlmostEqual(result, 431.53385, 3)

    def test_min_to_s(self):
        result = utils.min_to_s(11)
        self.assertAlmostEqual(result, 660)

    def test_m_to_km(self):
        result = utils.m_to_km(6969)
        self.assertAlmostEqual(result, 6.969)

    def test_m_to_ft(self):
        result = utils.m_to_ft(4321)
        self.assertAlmostEqual(result, 14176.509186, 3)

    def test_m2_to_ft2(self):
        result = utils.m2_to_ft2(1234)
        self.assertAlmostEqual(result, 13282.6526)

    def test_lbf_to_N(self):
        result = utils.lbf_to_N(420420)
        self.assertAlmostEqual(result, 1870120.6524)

    def test_lb_hr_lbf_to_kg_Ns(self):
        result = utils.lb_hr_lbf_to_kg_Ns(0.591)
        self.assertAlmostEqual(result, 1.67403335866*10**-5)

    def test_lb_hr_hp_to_kg_J(self):
        result = utils.lb_hr_hp_to_kg_J(0.420360)
        self.assertAlmostEqual(result, 7.10264528*10**-8)

    def test_ft_to_m(self):
        result = utils.ft_to_m(3.601)
        self.assertAlmostEqual(result, 1.0975848)

    def test_ms_to_kmh(self):
        result = utils.ms_to_kmh(3.6)
        self.assertAlmostEqual(result, 12.96)

    def test_kts_to_ms(self):
        result = utils.kts_to_ms(2.102)
        self.assertAlmostEqual(result, 1.08136128)

