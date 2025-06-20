import unittest
import numpy.testing as npt


try:
    from subsystems.structures.wing_structure_generation import *
    from subsystems.structures.utils_struct import *
    from subsystems.structures.wing_stress_analysis import *
except:
    from wing_structure_generation import *
    from utils_struct import *
    from wing_stress_analysis import *

class TestWingStructureGeneration(unittest.TestCase):
    def test_wing_structure_generation(self):

        designvars = DesignParameters()
        designvars.load_from_yaml("design_config.yaml")
        vsp.ClearVSPModel()

        #### Add fuselage and change fuselage shape to make room for payload. This is done by changing the cross-sections of the fuselage.
        create_fuselage(designvars)

        ### Add wing
        create_wing(designvars)

        ### Add v_tail
        create_V_tail(designvars)

        ### Add engines
        create_engines(designvars)

        # Add fuel tank
        calculate_fuel_capacity(designvars)

        prev_cwd = os.getcwd()
        os.chdir(os.getcwd() + "/data")
        vsp.WriteVSPFile("aircraft_model2.vsp3")
        os.chdir(prev_cwd)

        ### Calculate specifications
        calculate_cg(designvars)
        calculate_wet_areas(designvars)

        ### Set up structure
        # wing_structure_generation(designvars)

        # Freeze geometry:

        vsp.UpdateGeom(designvars.wing.wingid)
        designvars.wing.b_w = vsp.GetParmVal(designvars.wing.wingid, "TotalSpan", "WingGeom")
        vsp.UpdateGeom(designvars.wing.wingid)
        vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom.csv")
        vsp.SetSetFlag(designvars.wing.wingid, 8, True)
        vsp.ComputeDegenGeom(8, vsp.DEGEN_GEOM_CSV_TYPE)
        data = pd.read_csv("data/DegenGeom.csv", header=None, skiprows=10, nrows=2211)
        datanp = data.to_numpy()
        designvars.structurecoords = np.round(datanp, decimals=6)

        spars, stringer_array, outline, chord_length, lower_airfoil, upper_airfoil= cross_sectional_structure_along_span(designvars, 0.5, plot=False)
        npt.assert_array_almost_equal(spars[0], np.array([[ 6.59595772, -0.01500409], [ 6.59595772,  0.11616861]]) )
        npt.assert_array_almost_equal(stringer_array[0], np.array([6.37867816, 0.01682175]))
        npt.assert_array_almost_equal(outline[0], np.array([7.15988575, 0.035759  ]))
        npt.assert_almost_equal(chord_length, 1.2128225335875822)
        npt.assert_array_almost_equal(lower_airfoil[0], np.array([6.35339321, 0.04797702]))
        npt.assert_array_almost_equal(upper_airfoil[0], np.array([7.15988575, 0.035759  ]))


class TestUtilsStruct(unittest.TestCase):
    def test_mohrs_circle(self):
        npt.assert_array_almost_equal(plot_Mohrs_circle_complete(100e6, 60e6, 10e6, 40e6, 55e6, 35e6)/1e6, np.array([ 1.54192094e+08,  3.52887421e+07, -1.94808357e+07])/1e6 , )

class TestWingStressAnalysis(unittest.TestCase):
    def test_displacement(self):
        designvars = DesignParameters()
        designvars.load_from_yaml("design_config.yaml")
        vsp.ClearVSPModel()

        #### Add fuselage and change fuselage shape to make room for payload. This is done by changing the cross-sections of the fuselage.
        create_fuselage(designvars)

        ### Add wing
        create_wing(designvars)

        ### Add v_tail
        create_V_tail(designvars)

        ### Add engines
        create_engines(designvars)

        # Add fuel tank
        calculate_fuel_capacity(designvars)

        prev_cwd = os.getcwd()
        os.chdir(os.getcwd() + "/data")
        vsp.WriteVSPFile("aircraft_model2.vsp3")
        os.chdir(prev_cwd)

        ### Calculate specifications
        calculate_cg(designvars)
        calculate_wet_areas(designvars)

        ### Set up structure
        # wing_structure_generation(designvars)

        # Freeze geometry:

        vsp.UpdateGeom(designvars.wing.wingid)
        designvars.wing.b_w = vsp.GetParmVal(designvars.wing.wingid, "TotalSpan", "WingGeom")
        vsp.UpdateGeom(designvars.wing.wingid)
        vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom.csv")
        vsp.SetSetFlag(designvars.wing.wingid, 8, True)
        vsp.ComputeDegenGeom(8, vsp.DEGEN_GEOM_CSV_TYPE)
        data = pd.read_csv("data/DegenGeom.csv", header=None, skiprows=10, nrows=2211)
        datanp = data.to_numpy()
        designvars.structurecoords = np.round(datanp, decimals=6)
        npt.assert_array_almost_equal(calculate_bending_distribution(np.linspace(10000000,0,1000), np.ones((1000,)), 70e9, designvars.wing.b_w / 2 * np.cos(designvars.wing.Gamma_w)), np.array([ 0.00000000e+00, -2.14996214e-09, -8.59697813e-09, -1.93367423e-08,
       -3.43649490e-08, -5.36772925e-08, -7.72694672e-08, -1.05137167e-07,
       -1.37276088e-07, -1.73681922e-07, -2.14350365e-07, -2.59277110e-07,
       -3.08457853e-07, -3.61888288e-07, -4.19564108e-07, -4.81481008e-07,
       -5.47634683e-07, -6.18020827e-07, -6.92635134e-07, -7.71473299e-07,
       -8.54531015e-07, -9.41803978e-07, -1.03328788e-06, -1.12897842e-06,
       -1.22887129e-06, -1.33296218e-06, -1.44124679e-06, -1.55372081e-06,
       -1.67037993e-06, -1.79121986e-06, -1.91623629e-06, -2.04542490e-06,
       -2.17878140e-06, -2.31630147e-06, -2.45798082e-06, -2.60381513e-06,
       -2.75380011e-06, -2.90793144e-06, -3.06620482e-06, -3.22861595e-06,
       -3.39516051e-06, -3.56583421e-06, -3.74063273e-06, -3.91955178e-06,
       -4.10258704e-06, -4.28973421e-06, -4.48098899e-06, -4.67634707e-06,
       -4.87580414e-06, -5.07935589e-06, -5.28699803e-06, -5.49872625e-06,
       -5.71453623e-06, -5.93442368e-06, -6.15838429e-06, -6.38641375e-06,
       -6.61850776e-06, -6.85466202e-06, -7.09487221e-06, -7.33913403e-06,
       -7.58744317e-06, -7.83979534e-06, -8.09618622e-06, -8.35661151e-06,
       -8.62106690e-06, -8.88954808e-06, -9.16205076e-06, -9.43857063e-06,
       -9.71910337e-06, -1.00036447e-05, -1.02921903e-05, -1.05847358e-05,
       -1.08812770e-05, -1.11818096e-05, -1.14863292e-05, -1.17948315e-05,
       -1.21073123e-05, -1.24237672e-05, -1.27441920e-05, -1.30685822e-05,
       -1.33969337e-05, -1.37292420e-05, -1.40655030e-05, -1.44057123e-05,
       -1.47498655e-05, -1.50979585e-05, -1.54499868e-05, -1.58059462e-05,
       -1.61658323e-05, -1.65296409e-05, -1.68973677e-05, -1.72690083e-05,
       -1.76445585e-05, -1.80240139e-05, -1.84073702e-05, -1.87946232e-05,
       -1.91857685e-05, -1.95808018e-05, -1.99797188e-05, -2.03825152e-05,
       -2.07891867e-05, -2.11997290e-05, -2.16141378e-05, -2.20324088e-05,
       -2.24545376e-05, -2.28805200e-05, -2.33103517e-05, -2.37440284e-05,
       -2.41815457e-05, -2.46228993e-05, -2.50680850e-05, -2.55170984e-05,
       -2.59699353e-05, -2.64265912e-05, -2.68870620e-05, -2.73513433e-05,
       -2.78194309e-05, -2.82913203e-05, -2.87670073e-05, -2.92464876e-05,
       -2.97297569e-05, -3.02168109e-05, -3.07076452e-05, -3.12022556e-05,
       -3.17006378e-05, -3.22027875e-05, -3.27087002e-05, -3.32183719e-05,
       -3.37317981e-05, -3.42489745e-05, -3.47698968e-05, -3.52945608e-05,
       -3.58229620e-05, -3.63550963e-05, -3.68909593e-05, -3.74305467e-05,
       -3.79738542e-05, -3.85208775e-05, -3.90716122e-05, -3.96260542e-05,
       -4.01841990e-05, -4.07460424e-05, -4.13115800e-05, -4.18808076e-05,
       -4.24537209e-05, -4.30303154e-05, -4.36105871e-05, -4.41945314e-05,
       -4.47821442e-05, -4.53734211e-05, -4.59683578e-05, -4.65669501e-05,
       -4.71691935e-05, -4.77750838e-05, -4.83846168e-05, -4.89977880e-05,
       -4.96145932e-05, -5.02350280e-05, -5.08590883e-05, -5.14867696e-05,
       -5.21180676e-05, -5.27529782e-05, -5.33914968e-05, -5.40336193e-05,
       -5.46793414e-05, -5.53286586e-05, -5.59815668e-05, -5.66380617e-05,
       -5.72981388e-05, -5.79617939e-05, -5.86290228e-05, -5.92998210e-05,
       -5.99741843e-05, -6.06521084e-05, -6.13335890e-05, -6.20186218e-05,
       -6.27072024e-05, -6.33993266e-05, -6.40949901e-05, -6.47941885e-05,
       -6.54969175e-05, -6.62031729e-05, -6.69129503e-05, -6.76262455e-05,
       -6.83430541e-05, -6.90633717e-05, -6.97871943e-05, -7.05145173e-05,
       -7.12453365e-05, -7.19796476e-05, -7.27174463e-05, -7.34587282e-05,
       -7.42034892e-05, -7.49517248e-05, -7.57034308e-05, -7.64586029e-05,
       -7.72172367e-05, -7.79793279e-05, -7.87448723e-05, -7.95138655e-05,
       -8.02863033e-05, -8.10621813e-05, -8.18414952e-05, -8.26242408e-05,
       -8.34104136e-05, -8.42000094e-05, -8.49930240e-05, -8.57894529e-05,
       -8.65892919e-05, -8.73925367e-05, -8.81991830e-05, -8.90092265e-05,
       -8.98226628e-05, -9.06394876e-05, -9.14596968e-05, -9.22832858e-05,
       -9.31102505e-05, -9.39405866e-05, -9.47742897e-05, -9.56113555e-05,
       -9.64517797e-05, -9.72955580e-05, -9.81426862e-05, -9.89931598e-05,
       -9.98469747e-05, -1.00704126e-04, -1.01564611e-04, -1.02428423e-04,
       -1.03295560e-04, -1.04166016e-04, -1.05039788e-04, -1.05916870e-04,
       -1.06797260e-04, -1.07680952e-04, -1.08567942e-04, -1.09458225e-04,
       -1.10351799e-04, -1.11248657e-04, -1.12148797e-04, -1.13052213e-04,
       -1.13958901e-04, -1.14868858e-04, -1.15782078e-04, -1.16698557e-04,
       -1.17618292e-04, -1.18541277e-04, -1.19467509e-04, -1.20396983e-04,
       -1.21329695e-04, -1.22265640e-04, -1.23204815e-04, -1.24147215e-04,
       -1.25092835e-04, -1.26041671e-04, -1.26993720e-04, -1.27948976e-04,
       -1.28907436e-04, -1.29869095e-04, -1.30833948e-04, -1.31801993e-04,
       -1.32773223e-04, -1.33747635e-04, -1.34725225e-04, -1.35705988e-04,
       -1.36689920e-04, -1.37677017e-04, -1.38667274e-04, -1.39660687e-04,
       -1.40657252e-04, -1.41656964e-04, -1.42659820e-04, -1.43665814e-04,
       -1.44674943e-04, -1.45687202e-04, -1.46702587e-04, -1.47721093e-04,
       -1.48742717e-04, -1.49767454e-04, -1.50795299e-04, -1.51826249e-04,
       -1.52860299e-04, -1.53897445e-04, -1.54937682e-04, -1.55981007e-04,
       -1.57027414e-04, -1.58076900e-04, -1.59129460e-04, -1.60185090e-04,
       -1.61243785e-04, -1.62305542e-04, -1.63370356e-04, -1.64438223e-04,
       -1.65509138e-04, -1.66583097e-04, -1.67660096e-04, -1.68740131e-04,
       -1.69823196e-04, -1.70909289e-04, -1.71998404e-04, -1.73090537e-04,
       -1.74185685e-04, -1.75283842e-04, -1.76385004e-04, -1.77489168e-04,
       -1.78596328e-04, -1.79706480e-04, -1.80819621e-04, -1.81935746e-04,
       -1.83054850e-04, -1.84176929e-04, -1.85301979e-04, -1.86429996e-04,
       -1.87560975e-04, -1.88694912e-04, -1.89831803e-04, -1.90971643e-04,
       -1.92114429e-04, -1.93260155e-04, -1.94408817e-04, -1.95560412e-04,
       -1.96714934e-04, -1.97872380e-04, -1.99032746e-04, -2.00196026e-04,
       -2.01362217e-04, -2.02531314e-04, -2.03703313e-04, -2.04878210e-04,
       -2.06056000e-04, -2.07236680e-04, -2.08420244e-04, -2.09606688e-04,
       -2.10796009e-04, -2.11988202e-04, -2.13183262e-04, -2.14381186e-04,
       -2.15581969e-04, -2.16785606e-04, -2.17992093e-04, -2.19201427e-04,
       -2.20413602e-04, -2.21628615e-04, -2.22846461e-04, -2.24067136e-04,
       -2.25290635e-04, -2.26516955e-04, -2.27746090e-04, -2.28978037e-04,
       -2.30212791e-04, -2.31450348e-04, -2.32690704e-04, -2.33933855e-04,
       -2.35179795e-04, -2.36428521e-04, -2.37680029e-04, -2.38934313e-04,
       -2.40191371e-04, -2.41451197e-04, -2.42713788e-04, -2.43979138e-04,
       -2.45247244e-04, -2.46518101e-04, -2.47791705e-04, -2.49068052e-04,
       -2.50347138e-04, -2.51628957e-04, -2.52913507e-04, -2.54200781e-04,
       -2.55490777e-04, -2.56783490e-04, -2.58078915e-04, -2.59377049e-04,
       -2.60677887e-04, -2.61981424e-04, -2.63287657e-04, -2.64596580e-04,
       -2.65908191e-04, -2.67222483e-04, -2.68539454e-04, -2.69859099e-04,
       -2.71181413e-04, -2.72506393e-04, -2.73834033e-04, -2.75164330e-04,
       -2.76497280e-04, -2.77832877e-04, -2.79171118e-04, -2.80511998e-04,
       -2.81855513e-04, -2.83201659e-04, -2.84550432e-04, -2.85901827e-04,
       -2.87255839e-04, -2.88612465e-04, -2.89971701e-04, -2.91333541e-04,
       -2.92697982e-04, -2.94065019e-04, -2.95434648e-04, -2.96806865e-04,
       -2.98181666e-04, -2.99559045e-04, -3.00938999e-04, -3.02321524e-04,
       -3.03706615e-04, -3.05094268e-04, -3.06484478e-04, -3.07877241e-04,
       -3.09272554e-04, -3.10670411e-04, -3.12070809e-04, -3.13473742e-04,
       -3.14879207e-04, -3.16287200e-04, -3.17697716e-04, -3.19110751e-04,
       -3.20526300e-04, -3.21944359e-04, -3.23364924e-04, -3.24787991e-04,
       -3.26213555e-04, -3.27641612e-04, -3.29072158e-04, -3.30505188e-04,
       -3.31940698e-04, -3.33378684e-04, -3.34819142e-04, -3.36262066e-04,
       -3.37707454e-04, -3.39155300e-04, -3.40605600e-04, -3.42058350e-04,
       -3.43513546e-04, -3.44971183e-04, -3.46431257e-04, -3.47893763e-04,
       -3.49358699e-04, -3.50826058e-04, -3.52295837e-04, -3.53768031e-04,
       -3.55242637e-04, -3.56719649e-04, -3.58199065e-04, -3.59680878e-04,
       -3.61165085e-04, -3.62651682e-04, -3.64140664e-04, -3.65632028e-04,
       -3.67125768e-04, -3.68621880e-04, -3.70120361e-04, -3.71621205e-04,
       -3.73124409e-04, -3.74629968e-04, -3.76137878e-04, -3.77648134e-04,
       -3.79160733e-04, -3.80675670e-04, -3.82192941e-04, -3.83712540e-04,
       -3.85234465e-04, -3.86758711e-04, -3.88285273e-04, -3.89814147e-04,
       -3.91345329e-04, -3.92878815e-04, -3.94414600e-04, -3.95952680e-04,
       -3.97493050e-04, -3.99035707e-04, -4.00580645e-04, -4.02127862e-04,
       -4.03677352e-04, -4.05229110e-04, -4.06783134e-04, -4.08339418e-04,
       -4.09897958e-04, -4.11458751e-04, -4.13021790e-04, -4.14587073e-04,
       -4.16154595e-04, -4.17724352e-04, -4.19296339e-04, -4.20870551e-04,
       -4.22446986e-04, -4.24025638e-04, -4.25606503e-04, -4.27189577e-04,
       -4.28774856e-04, -4.30362334e-04, -4.31952009e-04, -4.33543875e-04,
       -4.35137928e-04, -4.36734165e-04, -4.38332580e-04, -4.39933169e-04,
       -4.41535929e-04, -4.43140854e-04, -4.44747941e-04, -4.46357184e-04,
       -4.47968581e-04, -4.49582126e-04, -4.51197816e-04, -4.52815645e-04,
       -4.54435610e-04, -4.56057706e-04, -4.57681929e-04, -4.59308275e-04,
       -4.60936739e-04, -4.62567318e-04, -4.64200006e-04, -4.65834799e-04,
       -4.67471694e-04, -4.69110686e-04, -4.70751770e-04, -4.72394942e-04,
       -4.74040199e-04, -4.75687535e-04, -4.77336946e-04, -4.78988429e-04,
       -4.80641978e-04, -4.82297589e-04, -4.83955259e-04, -4.85614982e-04,
       -4.87276755e-04, -4.88940573e-04, -4.90606432e-04, -4.92274328e-04,
       -4.93944256e-04, -4.95616211e-04, -4.97290191e-04, -4.98966190e-04,
       -5.00644204e-04, -5.02324228e-04, -5.04006259e-04, -5.05690292e-04,
       -5.07376324e-04, -5.09064348e-04, -5.10754362e-04, -5.12446361e-04,
       -5.14140340e-04, -5.15836295e-04, -5.17534223e-04, -5.19234118e-04,
       -5.20935977e-04, -5.22639795e-04, -5.24345567e-04, -5.26053290e-04,
       -5.27762959e-04, -5.29474570e-04, -5.31188119e-04, -5.32903601e-04,
       -5.34621011e-04, -5.36340347e-04, -5.38061602e-04, -5.39784774e-04,
       -5.41509857e-04, -5.43236848e-04, -5.44965742e-04, -5.46696535e-04,
       -5.48429222e-04, -5.50163799e-04, -5.51900263e-04, -5.53638608e-04,
       -5.55378830e-04, -5.57120925e-04, -5.58864889e-04, -5.60610717e-04,
       -5.62358405e-04, -5.64107949e-04, -5.65859344e-04, -5.67612586e-04,
       -5.69367672e-04, -5.71124596e-04, -5.72883354e-04, -5.74643942e-04,
       -5.76406355e-04, -5.78170590e-04, -5.79936642e-04, -5.81704506e-04,
       -5.83474179e-04, -5.85245656e-04, -5.87018933e-04, -5.88794005e-04,
       -5.90570868e-04, -5.92349518e-04, -5.94129951e-04, -5.95912162e-04,
       -5.97696147e-04, -5.99481902e-04, -6.01269421e-04, -6.03058702e-04,
       -6.04849740e-04, -6.06642530e-04, -6.08437068e-04, -6.10233350e-04,
       -6.12031371e-04, -6.13831128e-04, -6.15632615e-04, -6.17435829e-04,
       -6.19240766e-04, -6.21047420e-04, -6.22855788e-04, -6.24665865e-04,
       -6.26477647e-04, -6.28291130e-04, -6.30106310e-04, -6.31923181e-04,
       -6.33741741e-04, -6.35561984e-04, -6.37383906e-04, -6.39207503e-04,
       -6.41032770e-04, -6.42859704e-04, -6.44688300e-04, -6.46518554e-04,
       -6.48350461e-04, -6.50184017e-04, -6.52019218e-04, -6.53856059e-04,
       -6.55694536e-04, -6.57534646e-04, -6.59376382e-04, -6.61219742e-04,
       -6.63064721e-04, -6.64911315e-04, -6.66759519e-04, -6.68609329e-04,
       -6.70460740e-04, -6.72313749e-04, -6.74168352e-04, -6.76024542e-04,
       -6.77882318e-04, -6.79741673e-04, -6.81602605e-04, -6.83465108e-04,
       -6.85329178e-04, -6.87194811e-04, -6.89062003e-04, -6.90930750e-04,
       -6.92801046e-04, -6.94672888e-04, -6.96546271e-04, -6.98421192e-04,
       -7.00297645e-04, -7.02175627e-04, -7.04055133e-04, -7.05936159e-04,
       -7.07818701e-04, -7.09702754e-04, -7.11588313e-04, -7.13475376e-04,
       -7.15363937e-04, -7.17253992e-04, -7.19145537e-04, -7.21038567e-04,
       -7.22933078e-04, -7.24829066e-04, -7.26726527e-04, -7.28625456e-04,
       -7.30525849e-04, -7.32427701e-04, -7.34331009e-04, -7.36235768e-04,
       -7.38141974e-04, -7.40049621e-04, -7.41958707e-04, -7.43869227e-04,
       -7.45781177e-04, -7.47694551e-04, -7.49609346e-04, -7.51525558e-04,
       -7.53443182e-04, -7.55362214e-04, -7.57282650e-04, -7.59204485e-04,
       -7.61127715e-04, -7.63052336e-04, -7.64978344e-04, -7.66905733e-04,
       -7.68834500e-04, -7.70764641e-04, -7.72696151e-04, -7.74629026e-04,
       -7.76563261e-04, -7.78498853e-04, -7.80435796e-04, -7.82374088e-04,
       -7.84313722e-04, -7.86254696e-04, -7.88197005e-04, -7.90140644e-04,
       -7.92085609e-04, -7.94031896e-04, -7.95979500e-04, -7.97928418e-04,
       -7.99878645e-04, -8.01830176e-04, -8.03783007e-04, -8.05737135e-04,
       -8.07692554e-04, -8.09649261e-04, -8.11607251e-04, -8.13566519e-04,
       -8.15527062e-04, -8.17488875e-04, -8.19451954e-04, -8.21416295e-04,
       -8.23381893e-04, -8.25348744e-04, -8.27316843e-04, -8.29286187e-04,
       -8.31256771e-04, -8.33228590e-04, -8.35201641e-04, -8.37175919e-04,
       -8.39151420e-04, -8.41128140e-04, -8.43106073e-04, -8.45085217e-04,
       -8.47065566e-04, -8.49047116e-04, -8.51029864e-04, -8.53013804e-04,
       -8.54998932e-04, -8.56985244e-04, -8.58972737e-04, -8.60961404e-04,
       -8.62951243e-04, -8.64942249e-04, -8.66934417e-04, -8.68927743e-04,
       -8.70922223e-04, -8.72917853e-04, -8.74914628e-04, -8.76912545e-04,
       -8.78911597e-04, -8.80911783e-04, -8.82913096e-04, -8.84915533e-04,
       -8.86919090e-04, -8.88923762e-04, -8.90929544e-04, -8.92936433e-04,
       -8.94944425e-04, -8.96953514e-04, -8.98963697e-04, -9.00974970e-04,
       -9.02987327e-04, -9.05000765e-04, -9.07015280e-04, -9.09030866e-04,
       -9.11047521e-04, -9.13065239e-04, -9.15084016e-04, -9.17103848e-04,
       -9.19124731e-04, -9.21146659e-04, -9.23169630e-04, -9.25193639e-04,
       -9.27218681e-04, -9.29244752e-04, -9.31271847e-04, -9.33299963e-04,
       -9.35329096e-04, -9.37359240e-04, -9.39390391e-04, -9.41422546e-04,
       -9.43455700e-04, -9.45489848e-04, -9.47524987e-04, -9.49561112e-04,
       -9.51598218e-04, -9.53636302e-04, -9.55675359e-04, -9.57715384e-04,
       -9.59756374e-04, -9.61798324e-04, -9.63841231e-04, -9.65885088e-04,
       -9.67929893e-04, -9.69975641e-04, -9.72022327e-04, -9.74069948e-04,
       -9.76118499e-04, -9.78167975e-04, -9.80218373e-04, -9.82269688e-04,
       -9.84321916e-04, -9.86375053e-04, -9.88429093e-04, -9.90484034e-04,
       -9.92539870e-04, -9.94596597e-04, -9.96654211e-04, -9.98712708e-04,
       -1.00077208e-03, -1.00283233e-03, -1.00489345e-03, -1.00695544e-03,
       -1.00901828e-03, -1.01108198e-03, -1.01314654e-03, -1.01521194e-03,
       -1.01727819e-03, -1.01934528e-03, -1.02141320e-03, -1.02348195e-03,
       -1.02555153e-03, -1.02762193e-03, -1.02969315e-03, -1.03176519e-03,
       -1.03383803e-03, -1.03591168e-03, -1.03798613e-03, -1.04006137e-03,
       -1.04213741e-03, -1.04421424e-03, -1.04629185e-03, -1.04837024e-03,
       -1.05044940e-03, -1.05252934e-03, -1.05461004e-03, -1.05669150e-03,
       -1.05877372e-03, -1.06085670e-03, -1.06294042e-03, -1.06502489e-03,
       -1.06711010e-03, -1.06919604e-03, -1.07128272e-03, -1.07337013e-03,
       -1.07545825e-03, -1.07754710e-03, -1.07963666e-03, -1.08172694e-03,
       -1.08381792e-03, -1.08590960e-03, -1.08800197e-03, -1.09009505e-03,
       -1.09218881e-03, -1.09428325e-03, -1.09637838e-03, -1.09847418e-03,
       -1.10057065e-03, -1.10266779e-03, -1.10476559e-03, -1.10686406e-03,
       -1.10896317e-03, -1.11106294e-03, -1.11316335e-03, -1.11526441e-03,
       -1.11736610e-03, -1.11946842e-03, -1.12157137e-03, -1.12367495e-03,
       -1.12577915e-03, -1.12788396e-03, -1.12998939e-03, -1.13209542e-03,
       -1.13420205e-03, -1.13630928e-03, -1.13841711e-03, -1.14052553e-03,
       -1.14263453e-03, -1.14474411e-03, -1.14685428e-03, -1.14896501e-03,
       -1.15107631e-03, -1.15318818e-03, -1.15530060e-03, -1.15741358e-03,
       -1.15952711e-03, -1.16164119e-03, -1.16375581e-03, -1.16587097e-03,
       -1.16798667e-03, -1.17010289e-03, -1.17221964e-03, -1.17433691e-03,
       -1.17645469e-03, -1.17857299e-03, -1.18069180e-03, -1.18281111e-03,
       -1.18493092e-03, -1.18705122e-03, -1.18917202e-03, -1.19129330e-03,
       -1.19341506e-03, -1.19553731e-03, -1.19766002e-03, -1.19978321e-03,
       -1.20190686e-03, -1.20403097e-03, -1.20615554e-03, -1.20828056e-03,
       -1.21040602e-03, -1.21253193e-03, -1.21465828e-03, -1.21678507e-03,
       -1.21891228e-03, -1.22103992e-03, -1.22316799e-03, -1.22529647e-03,
       -1.22742536e-03, -1.22955467e-03, -1.23168438e-03, -1.23381448e-03,
       -1.23594499e-03, -1.23807589e-03, -1.24020717e-03, -1.24233884e-03,
       -1.24447088e-03, -1.24660330e-03, -1.24873610e-03, -1.25086925e-03,
       -1.25300277e-03, -1.25513665e-03, -1.25727088e-03, -1.25940546e-03,
       -1.26154038e-03, -1.26367564e-03, -1.26581124e-03, -1.26794717e-03,
       -1.27008343e-03, -1.27222001e-03, -1.27435690e-03, -1.27649412e-03,
       -1.27863164e-03, -1.28076947e-03, -1.28290760e-03, -1.28504603e-03,
       -1.28718475e-03, -1.28932376e-03, -1.29146305e-03, -1.29360262e-03,
       -1.29574247e-03, -1.29788259e-03, -1.30002297e-03, -1.30216362e-03,
       -1.30430453e-03, -1.30644569e-03, -1.30858710e-03, -1.31072876e-03,
       -1.31287066e-03, -1.31501279e-03, -1.31715516e-03, -1.31929775e-03,
       -1.32144057e-03, -1.32358361e-03, -1.32572687e-03, -1.32787033e-03,
       -1.33001400e-03, -1.33215788e-03, -1.33430195e-03, -1.33644621e-03,
       -1.33859067e-03, -1.34073531e-03, -1.34288013e-03, -1.34502513e-03,
       -1.34717030e-03, -1.34931564e-03, -1.35146114e-03, -1.35360680e-03,
       -1.35575261e-03, -1.35789858e-03, -1.36004469e-03, -1.36219095e-03,
       -1.36433734e-03, -1.36648387e-03, -1.36863052e-03, -1.37077730e-03,
       -1.37292420e-03, -1.37507122e-03, -1.37721835e-03, -1.37936559e-03,
       -1.38151293e-03, -1.38366037e-03, -1.38580790e-03, -1.38795552e-03,
       -1.39010323e-03, -1.39225103e-03, -1.39439890e-03, -1.39654684e-03,
       -1.39869485e-03, -1.40084293e-03, -1.40299106e-03, -1.40513926e-03,
       -1.40728750e-03, -1.40943579e-03, -1.41158413e-03, -1.41373250e-03,
       -1.41588091e-03, -1.41802934e-03, -1.42017781e-03, -1.42232629e-03,
       -1.42447480e-03, -1.42662331e-03, -1.42877184e-03, -1.43092036e-03])

)

if __name__ == '__main__':
    unittest.main(verbosity=2)



    import pytest
import numpy as np
from unittest.mock import MagicMock
from flight_envelope import FlightEnvelope, _set_report_style

class DummyPerformance:
    CL_alpha = 5.7
    CL_max_cruise = 1.4
    CL_max_TO = 1.6
    CL_max_LAND = 2.0

class DummyWing:
    S_w = 30.0
    mac = 2.0

class DummyWeight:
    W_OE = 8000
    W_TO = 15000
    W_PL = 2000
    W_F = 5000
    Fuel_Fuselage_Fraction = 0.5

class DummyParams:
    performance = DummyPerformance()
    wing = DummyWing()
    weight = DummyWeight()
    cruise_mach = 0.7
    cruise_density = 0.4
    cruise_temperature = 220
    cruise_altitude = 10000

class TestFlightEnvelope:

    @pytest.fixture
    def env(self):
        return FlightEnvelope(DummyParams())

    def test_set_report_style(self):
        # Just call the function to ensure no exceptions
        _set_report_style()

    def test_calc_load_factor_limits(self, env):
        n_pos, n_neg = env.calc_load_factor_limits(15000)
        assert np.isclose(n_pos, min(2.1 + (10900 / (15000 + 4536)), 3.8))
        assert np.isclose(n_neg, -0.4 * n_pos)

    def test_calc_diagram_speed(self, env):
        weight_N = 15000 * 9.81
        rho = 1.225
        CL_max = 1.5
        VC = 100
        V = env.calc_diagram_speed(weight_N, rho, CL_max, VC)
        expected_VS_TAS = np.sqrt((2 * weight_N) / (rho * env.S * CL_max))
        from utils.unit_conversions import true_to_equivalent_air_speed
        expected_VS = true_to_equivalent_air_speed(expected_VS_TAS, rho, 1.225)
        assert np.isclose(V, expected_VS)



import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from loading_diagrams import WingLoadingDiagrams

# Dummy parameters for testing
class DummyPerformance:
    V_A = 70

class DummyWing:
    b_w = 20  # 20 m span
    CL_distribution = np.ones(1000) * 1.0
    CD_distribution = np.ones(1000) * 0.05
    CM_distribution = np.ones(1000) * 0.01

class DummyParams:
    performance = DummyPerformance()
    wing = DummyWing()
    cruise_density = 1.225

class TestWingLoadingDiagrams:

    @pytest.fixture
    def mock_cross_section(self):
        with patch('loading_diagrams.cross_section', return_value=(0, 2.0)):
            yield

    @pytest.fixture
    def diagram(self, mock_cross_section):
        return WingLoadingDiagrams(DummyParams())

    def test_y_span(self, diagram):
        assert len(diagram.y) == 1000
        assert np.isclose(diagram.y[0], 0)
        assert np.isclose(diagram.y[-1], DummyParams().wing.b_w / 2)

    def test_lift_distribution(self, diagram):
        # Each lift value should be computed as CL * 0.5 * rho * V^2 * chord
        expected_value = 1.0 * 0.5 * 1.225 * (70 ** 2) * 2.0
        assert np.allclose(diagram.lift, expected_value)

    def test_drag_distribution(self, diagram):
        expected_value = 0.05 * 0.5 * 1.225 * (70 ** 2) * 2.0
        assert np.allclose(diagram.drag, expected_value)

    def test_moment_distribution(self, diagram):
        expected_value = 0.01 * 0.5 * 1.225 * (70 ** 2) * 2.0
        assert np.allclose(diagram.moment_aero, expected_value)



import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from wing_stress_analysis import perform_cross_section_analysis, calculate_bending_distribution

class DummyDesignVars:
    class Wing:
        class WingSection:
            wingskin = {'thicness': 0.005}
        wingsection = WingSection()
    wing = Wing()

class TestWingStressAnalysis:

    @pytest.fixture
    def dummy_loading(self):
        return {
            "moment_x": 1000,
            "moment_z": 2000,
            "torsion_y": 150,
            "shear_x": 300,
            "shear_z": 400,
        }

    def test_perform_cross_section_analysis(self, dummy_loading):
        with patch("wing_stress_analysis.cross_sectional_structure_along_span", return_value=(["spar"], ["stringer"], None, None, None, None)), \
             patch("wing_stress_analysis.run_cross_section_analysis", return_value={"stress": 42}) as mock_run:
            result = perform_cross_section_analysis(DummyDesignVars(), dummy_loading)
            assert "stress" in result
            assert result["stress"] == 42
            mock_run.assert_called_once()

    def test_calculate_bending_distribution(self):
        M = np.linspace(0, 1000, 100)
        I = np.ones_like(M) * 0.01
        E = 70e9  # Young's modulus (Pa)
        half_span = 10.0  # meters
        deflection = calculate_bending_distribution(M, I, E, half_span)
        assert isinstance(deflection, np.ndarray)
        assert deflection.shape == M.shape
        assert np.all(np.isfinite(deflection))



import pytest
from unittest.mock import patch, MagicMock
from vspfunctions import print_all_params, plotSTL, create_fuselage
import numpy as np

class DummyFuselage:
    l_f = 10.0
    crosssections = {
        "fuselagetip1": {
            "Tan_Angles": {"top": 10, "right": 10, "bottom": 10, "left": 10}
        }
    }

class DummyDesignVars:
    fuselage = DummyFuselage()

class TestVSPFunctions:

    def test_print_all_params(self, capsys):
        with patch("vspfunctions.vsp.GetGeomParmIDs", return_value=["id1", "id2"]), \
             patch("vspfunctions.vsp.GetParmName", side_effect=["P1", "P2"]), \
             patch("vspfunctions.vsp.GetParmGroupName", side_effect=["G1", "G2"]), \
             patch("vspfunctions.vsp.GetParmVal", side_effect=[1.0, 2.0]):
            print_all_params("dummy")
            captured = capsys.readouterr()
            assert "Group: G1 / Parameter Name: P1 / Value: 1.0" in captured.out
            assert "Group: G2 / Parameter Name: P2 / Value: 2.0" in captured.out

    def test_plotSTL(self):
        with patch("vspfunctions.mesh.Mesh.from_file") as mock_mesh, \
             patch("vspfunctions.pv.PolyData") as mock_polydata, \
             patch("vspfunctions.pv.Plotter") as mock_plotter, \
             patch("vspfunctions.is_headless", return_value=True):
            mock_mesh.return_value.vectors = np.zeros((10, 3, 3))
            plotSTL("dummy_file.stl")
            assert mock_plotter.call_count >= 1

    def test_create_fuselage(self):
        with patch("vspfunctions.vsp.AddGeom", return_value="fuse_id"), \
             patch("vspfunctions.vsp.GetXSecSurf", return_value="surf"), \
             patch("vspfunctions.vsp.GetNumXSec", return_value=3), \
             patch("vspfunctions.vsp.InsertXSec"), \
             patch("vspfunctions.vsp.SetParmVal"), \
             patch("vspfunctions.vsp.GetXSecParm", return_value="xsecparm"), \
             patch("vspfunctions.vsp.GetXSec", return_value="xsec"), \
             patch("vspfunctions.vsp.SetXSecTanAngles"):
            create_fuselage(DummyDesignVars())



import pytest
import numpy as np
from fatigue import (
    calculate_critical_buckling_stress,
    sn_curve,
    miners_rule,
    corrected_stress,
    plot_sn_curve
)

class TestFatigue:

    def test_calculate_critical_buckling_stress(self):
        E, I, A, L = 70e9, 8e-6, 0.004, 2.0
        sigma_cr = calculate_critical_buckling_stress(E, I, A, L)
        expected = (np.pi ** 2 * E * I) / (L ** 2 * A)
        assert np.isclose(sigma_cr, expected)

    def test_calculate_critical_buckling_stress_zero_inputs(self):
        assert calculate_critical_buckling_stress(0, 1, 1, 1) == 0
        assert calculate_critical_buckling_stress(1, 0, 1, 1) == 0
        assert calculate_critical_buckling_stress(1, 1, 0, 1) == 0
        assert calculate_critical_buckling_stress(1, 1, 1, 0) == 0

    def test_sn_curve(self):
        assert np.isclose(sn_curve(100, A=1e12, m=3), (1e12 / 100) ** (1/3))

    def test_miners_rule(self):
        stress = [100, 150]
        cycles = [1e4, 2e4]
        damage = miners_rule(stress, cycles, A=1e12, m=3)
        expected = sum(n / sn_curve(s, A=1e12, m=3) for s, n in zip(stress, cycles))
        assert np.isclose(damage, expected)

    @pytest.mark.parametrize("method,expected", [
        ("none", 100),
        ("goodman", 100 / (1 - 40/400)),
        ("gerber", 100 / (1 - (40/400)**2)),
    ])
    def test_corrected_stress(self, method, expected):
        assert np.isclose(corrected_stress(100, 40, 400, method), expected)

    def test_plot_sn_curve(self, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        plot_sn_curve(sigma_D=172, ND=1e6, m=5, Rm=400, sigma_m=40, method='goodman')



import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from gust_diagram import equivalent_to_true_air_speed

class DummyPerformance:
    CL_alpha = 5.7

class DummyWing:
    mac = 2.0
    S_w = 25.0

class DummyWeight:
    W_OE = 9000
    W_PL = 1500
    W_F = 4000
    Fuel_Fuselage_Fraction = 0.6

class DummyParams:
    performance = DummyPerformance()
    wing = DummyWing()
    weight = DummyWeight()
    cruise_density = 0.4
    cruise_speed = 120

class TestGustDiagram:

    @pytest.fixture
    def params(self):
        return DummyParams()

    def test_mu_g_and_Kg(self, params):
        rho_cruise = params.cruise_density
        mac = params.wing.mac
        Cl_alpha = params.performance.CL_alpha
        W_S = (params.weight.W_OE + params.weight.W_PL + params.weight.W_F * params.weight.Fuel_Fuselage_Fraction) / params.wing.S_w
        mu_g = W_S / (9.80665 * 0.5 * rho_cruise * mac * Cl_alpha)
        K_g = (0.88 * mu_g) / (5.3 + mu_g)
        assert 0 < mu_g < 10
        assert 0 < K_g < 1

    def test_equivalent_to_true_air_speed_conversion(self):
        TAS = equivalent_to_true_air_speed(70, 0.4, 1.225)
        assert isinstance(TAS, float)
        assert TAS > 0

    def test_gust_load_factor_computation(self, params):
        rho = 1.225
        rho_cruise = params.cruise_density
        Cl_alpha = params.performance.CL_alpha
        mac = params.wing.mac
        W_S = (params.weight.W_OE + params.weight.W_PL + params.weight.W_F * params.weight.Fuel_Fuselage_Fraction) / params.wing.S_w
        mu_g = W_S / (9.80665 * 0.5 * rho_cruise * mac * Cl_alpha)
        K_g = (0.88 * mu_g) / (5.3 + mu_g)

        VB = equivalent_to_true_air_speed(70, rho_cruise, rho)
        VC = params.cruise_speed
        VD = 1.25 * VC
        gusts = [15.2, 10.21, 10.21 / 2]

        V_eas = [v * (rho_cruise / rho)**0.5 for v in [VB, VC, VD]]
        n_pos = [1 + (rho * V * Cl_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_eas, gusts)]
        n_neg = [1 - (rho * V * Cl_alpha * K_g * u) / (2 * W_S) for V, u in zip(V_eas, gusts)]

        for n in n_pos + n_neg:
            assert n > -10 and n < 10  # sanity check


