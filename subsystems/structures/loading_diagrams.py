# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import integrate
from vspfunctions import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *


# ==== Loading Diagrams for UAV Wing Structure ===
#
#
# This code generates loading diagrams for a UAV wing structure based on distributed loads along the span.
# Inputs: 
# - Lift distribution (1D np.array of lift force per unit span)
# - Drag distribution (1D np.array of drag force per unit span)
# - Moment distribution (1D np.array of moment per unit span)
# - Weight distribution (1D np.array of weight per unit span)
# Outputs:          
# - Wing loading diagrams (lift, drag, moment)
# - Internal load distributions (shear force, bending moment, torsion)
# - Total wing weight
#
# Axis System Convention:
# - X-axis: Longitudinal axis (nose to tail; postive backwards)
# - Y-axis: Lateral axis (wingtip to wingtip; positive to right wingtip)
# - Z-axis: Vertical axis (positive upwards)
# =================================================================

class WingLoadingDiagrams:
    def __init__(self, params: DesignParameters):
        self.params = params
        self.SetUp()

    def SetUp(self):
        """
        Set up the loading diagrams parameters and configurations.
        This method initializes the necessary parameters for the loading diagrams calculations.
        """     

        # ==== Generate spanwise mesh (half-span) ====
        self.span = self.params.wing.b_w # Full wingspan = 40 m
        self.y = np.linspace(0, self.span / 2, 1000)  # Half-span from root to tip

        # ==== Initialize arrays for distributed loads ====
        #
        self.V_critical = self.params.performance.V_A
       
        self.lift = []
        self.drag = []
        self.moment_aero = []
        inputspace = np.linspace(0, self.span / 2, 1000)
        for i, (cl, sparwise_poss) in enumerate(zip(self.params.wing.CL_distribution, inputspace)):
            chord = cross_section(self.params, sparwise_poss, False)[1]
            self.lift.append(self.params.wing.CL_distribution[i] * 0.5 * self.params.cruise_density * (self.V_critical ** 2) * chord)
        for i, (cd, sparwise_poss) in enumerate(zip(self.params.wing.CD_distribution, inputspace)):
            chord = cross_section(self.params, sparwise_poss, False)[1]
            self.drag.append(self.params.wing.CD_distribution[i] * 0.5 * self.params.cruise_density * (self.V_critical ** 2) * chord)
        for i, (cm, sparwise_poss) in enumerate(zip(self.params.wing.CM_distribution, inputspace)):
            chord = cross_section(self.params, sparwise_poss, False)[1]
            self.moment_aero.append(self.params.wing.CM_distribution[i] * 0.5 * self.params.cruise_density * (self.V_critical ** 2) * chord ** 2)
        # TODO: fix weight distribution
        self.weight = 9.80665 * np.array([ 28.17669986, 120.5630069 , 120.37993347, 120.19691115,
       120.01393996, 119.83101988, 119.64815091, 119.46533307,
       119.28256635, 119.09985074, 118.91718625, 118.73457288,
       118.55201062, 118.36949949, 118.18703947, 118.00463057,
       117.82227278, 117.63996612, 117.45771057, 117.27550614,
       117.09335283, 116.91125064, 116.72919956, 116.54719961,
       116.36525077, 116.18335305, 116.00150644, 115.81971096,
       115.63796659, 115.45627334, 115.27463121, 115.09304019,
       114.9115003 , 114.73001152, 114.54857386, 114.36718732,
       114.18585189, 114.00456758, 113.8233344 , 113.64215232,
       113.46102137, 113.27994154, 113.09891282, 112.91793522,
       112.73700874, 112.55613337, 112.37530913, 112.194536  ,
       112.01381399, 111.8331431 , 111.65252333, 111.47195467,
       111.29143713, 111.11097071, 110.93055541, 110.75019122,
       110.56987816, 110.38961621, 110.20940538, 110.02924566,
       109.84913715, 109.66908077, 109.4890755 , 109.30912135,
       109.12921831, 108.94936639, 108.76956559, 108.58981591,
       108.41011734, 108.23046989, 108.05087356, 107.87132835,
       107.69183425, 107.51239127, 107.33299941, 107.15365866,
       106.97436904, 106.79513053, 106.61594313, 106.43680686,
       106.2577217 , 106.07868766, 105.89970473, 105.72077292,
       105.54189224, 105.36306266, 105.18428421, 105.00555687,
       104.82688065, 104.64825555, 104.46968156, 104.29115869,
       104.11268694, 103.93426631, 103.75589679, 103.57757839,
       103.39931111, 103.22109494, 103.0429299 , 102.86481597,
       102.68675315, 102.50874146, 102.33078088, 102.15287142,
       101.97501307, 101.79720585, 101.61944974, 101.44174474,
       101.26409087, 101.08648811, 100.90893647, 100.73143595,
       100.55398654, 100.37658825, 100.19924108, 100.02194503,
        99.84470009,  99.66750627,  99.49036357,  99.31327199,
        99.13623144,  98.95924157,  98.78230283,  98.6054152 ,
        98.42857869,  98.25179329,  98.07505901,  97.89837586,
        97.72174381,  97.54516289,  97.36863308,  97.19215439,
        97.01572682,  96.83935037,  96.66302503,  96.48675081,
        96.31052771,  96.13435573,  95.95823486,  95.78216512,
        95.60614649,  95.43017897,  95.25426258,  95.0783973 ,
        94.90258314,  94.7268201 ,  94.55110817,  94.37544736,
        94.19983767,  94.0242791 ,  93.84877165,  93.67331531,
        93.49791009,  93.32255599,  93.147253  ,  92.97200114,
        92.79680039,  92.62165076,  92.44655224,  92.27150485,
        92.09650857,  91.9215634 ,  91.74666936,  91.57182644,
        91.39703463,  91.22229394,  91.04760436,  90.87296591,
        90.69837857,  90.52384235,  90.34935724,  90.17492326,
        90.00054039,  89.82620864,  89.65192801,  89.47769849,
        89.3035201 ,  89.12939282,  88.95531665,  88.78129161,
        88.60731755,  88.43339419,  88.25952195,  88.08570083,
        87.91193082,  87.73821194,  87.56454417,  87.39092751,
        87.21736198,  87.04384756,  86.87038427,  86.69697209,
        86.52361102,  86.35030108,  86.17704225,  86.00383454,
        85.83067795,  85.65757248,  85.48451813,  85.31151489,
        85.13856277,  84.96566177,  84.79281189,  84.62001312,
        84.44726548,  84.27456895,  84.10192353,  83.92932924,
        83.75678607,  83.58429401,  83.41185307,  83.23946325,
        83.06712454,  82.89483696,  82.72260049,  82.55041514,
        82.37828091,  82.20619779,  82.0341658 ,  81.86218492,
        81.69025516,  81.51837651,  81.34654899,  81.17477258,
        81.00304729,  80.83137312,  80.65975007,  80.48817814,
        80.31665732,  80.14518762,  79.97376904,  79.80240157,
        79.63108523,  79.45982   ,  79.28860589,  79.1174429 ,
        78.94633103,  78.77527027,  78.60426063,  78.43330211,
        78.26239471,  78.09153843,  77.92073327,  77.74997922,
        77.57927629,  77.40862448,  77.23802379,  77.06747421,
        76.89697575,  76.72652842,  76.55613219,  76.38578709,
        76.21549311,  76.04525024,  75.87505849,  75.70491786,
        75.53482835,  75.36478995,  75.19480267,  75.02486651,
        74.85498147,  74.68514755,  74.51536474,  74.34563305,
        74.17595248,  74.00632303,  73.8367447 ,  73.66721748,
        73.49774138,  73.3283164 ,  73.15894254,  72.9896198 ,
        72.82034817,  72.65112766,  72.48195827,  72.31284   ,
        72.14377284,  71.97475681,  71.80579189,  71.63687809,
        71.4680154 ,  71.29920384,  71.13044339,  70.96173406,
        70.79307585,  70.62446876,  70.45591278,  70.28740793,
        70.11895419,  69.95055157,  69.78220006,  69.61389968,
        69.44565041,  69.27745226,  69.10930523,  68.94120932,
        68.77316452,  68.60517084,  68.43722828,  68.26933684,
        68.15769314,  68.1339413 ,  68.11019049,  68.0864407 ,
        68.06269193,  68.03894419,  68.01519747,  67.99145177,
        67.9677071 ,  67.94396345,  67.92022083,  67.89647923,
        67.87273865,  67.8489991 ,  67.82526057,  67.80152307,
        67.77778659,  67.75405113,  67.7303167 ,  67.70658329,
        67.6828509 ,  67.65911954,  67.6353892 ,  67.61165989,
        67.5879316 ,  67.56420433,  67.54047809,  67.51675287,
        67.49302868,  67.46930551,  67.44558336,  67.42186223,
        67.39814214,  67.37442306,  67.35070501,  67.32698798,
        67.30327198,  67.279557  ,  67.25584304,  67.23213011,
        67.2084182 ,  67.18470731,  67.16099745,  67.13728861,
        67.1135808 ,  67.08987401,  67.06616825,  67.0424635 ,
        67.01875979,  66.99505709,  68.17135542,  68.14765478,
        68.12395515,  68.10025655,  68.07655898,  68.05286243,
        68.0291669 ,  68.0054724 ,  67.98177892,  67.95808646,
        67.93439503,  67.91070462,  67.88701524,  67.86332688,
        67.83963954,  67.81595323,  67.79226794,  67.76858367,
        67.74490043,  67.72121821,  67.69753702,  67.67385685,
        67.65017771,  67.62649958,  67.60282249,  67.57914641,
        67.55547136,  67.53179733,  67.50812433,  67.48445235,
        67.4607814 ,  67.43711147,  67.41344256,  67.38977467,
        67.36610781,  67.34244198,  67.31877717,  67.29511338,
        67.27145061,  67.24778887,  67.22412816,  67.20046846,
        67.17680979,  67.15315215,  67.12949553,  67.10583993,
        67.08218536,  67.05853181,  67.03487928,  67.01122778,
        66.9875773 ,  66.96392785,  66.94027941,  66.91663201,
        66.89298562,  66.86934027,  66.84569593,  66.82205262,
        66.79841033,  66.77476907,  66.75112883,  66.72748961,
        66.70385142,  66.68021425,  66.65657811,  66.63294298,
        66.60930889,  66.58567581,  66.56204377,  66.53841274,
        66.51478274,  66.49115376,  66.46752581,  66.44389888,
        66.42027297,  66.39664809,  66.37302423,  66.34940139,
        66.32577958,  66.3021588 ,  66.27853903,  66.25492029,
        66.23130258,  66.20768589,  66.18407022,  66.16045557,
        66.13684195,  66.11322936,  66.08961779,  66.06600724,
        66.04239795,  66.01878991,  65.9951829 ,  65.97157691,
        65.94797195,  65.92436801,  65.90076509,  65.8771632 ,
        65.85356233,  65.82996248,  65.80636366,  65.78276586,
        65.75916909,  65.73557334,  65.71197861,  65.68838491,
        65.66479223,  65.64120057,  65.61760994,  65.59402033,
        65.57043175,  65.54684419,  65.52325765,  65.49967214,
        65.47608765,  65.45250419,  65.42892175,  65.40534033,
        65.38175994,  65.35818057,  65.33460222,  65.3110249 ,
        65.2874486 ,  65.26387333,  65.24029908,  65.21672585,
        65.19315365,  65.16958247,  65.14601231,  65.12244318,
        65.09887507,  65.07530799,  65.05174193,  65.02817689,
        65.00461288,  64.98104989,  64.95748792,  64.93392698,
        64.91036706,  64.88680817,  64.8632503 ,  64.83969346,
        64.81613763,  64.79258283,  64.76902906,  64.74547631,
        64.72192458,  64.69837388,  64.6748242 ,  64.65127554,
        64.62772791,  64.6041813 ,  64.58063572,  64.55709116,
        64.53354762,  64.51000511,  64.48646362,  64.46292315,
        64.43938371,  64.41584529,  64.3923079 ,  64.36877153,
        64.34523618,  64.32170186,  64.29816856,  64.27463629,
        64.25110504,  64.22757481,  64.20404561,  64.18051743,
        64.15699027,  64.13346414,  64.10993903,  64.08641495,
        64.06289188,  64.03936985,  64.01584883,  63.99232885,
        63.96880988,  63.94529194,  63.92177502,  63.89825913,
        63.87474426,  63.85123041,  63.82771759,  63.80420579,
        63.78069501,  63.75718526,  63.73367653,  63.71016883,
        63.68666215,  63.66315649,  63.63965186,  63.61614825,
        63.59264567,  63.56914411,  63.54564357,  63.52214406,
        63.49864557,  63.4751481 ,  63.45165166,  63.42815624,
        63.40466185,  63.38116848,  63.35767613,  63.33418481,
        63.31069451,  63.28720523,  63.26371698,  63.24022975,
        63.21674355,  63.19325837,  63.16977421,  63.14629108,
        63.12280897,  63.09932788,  63.07584782,  63.05236879,
        63.02889077,  63.00541378,  62.98193782,  62.95846287,
        62.93498896,  62.91151606,  62.88804419,  62.86457334,
        62.84110352,  62.81763472,  62.79416694,  62.77070019,
        62.74723417,  62.72376901,  62.70030486,  62.67684175,
        62.65337965,  62.62991858,  62.60645854,  62.58299951,
        62.55954151,  62.53608454,  62.51262859,  62.48917366,
        62.46571976,  62.44226688,  62.41881502,  62.39536419,
        62.37191438,  62.3484656 ,  62.32501784,  62.3015711 ,
        62.27812539,  62.2546807 ,  62.23123703,  62.20779439,
        62.18435277,  62.16091218,  62.13747261,  62.11403406,
        62.09059654,  62.06716004,  62.04372457,  62.02029012,
        61.99685669,  61.97342429,  61.94999291,  61.92656255,
        61.90313322,  61.87970492,  61.85627763,  61.83285137,
        61.80942614,  61.78600192,  61.76257874,  61.73915657,
        61.71573543,  61.69231531,  61.66889622,  61.64547815,
        61.62206111,  61.59864508,  61.57523009,  61.55181611,
        61.52840316,  61.50499124,  61.48158033,  61.45817046,
        61.4347616 ,  61.41135377,  61.38794696,  61.36454118,
        61.34113642,  61.31773269,  61.29432997,  61.27092829,
        61.24752762,  61.22412798,  61.20072937,  61.17733177,
        61.15393521,  61.13053966,  61.10714514,  61.08375164,
        61.06035917,  61.03696772,  61.01357729,  60.99018789,
        60.96679951,  60.94341216,  60.92002583,  60.89664052,
        60.87325624,  60.84987298,  60.82649075,  60.80310954,
        60.77972935,  60.75635019,  60.73297205,  60.70959493,
        60.68621884,  60.66284377,  60.63946973,  60.61609671,
        60.59272471,  60.56935374,  60.54598379,  60.52261487,
        60.49924696,  60.47588009,  60.45251423,  60.4291494 ,
        60.4057856 ,  60.38242282,  60.35906106,  60.33570032,
        60.31234061,  60.28898193,  60.26562426,  60.24226763,
        60.21891201,  60.19555742,  60.17220385,  60.14885131,
        60.12549979,  60.10214929,  60.07879982,  60.05545137,
        60.03210395,  60.00875755,  59.98541217,  59.96206782,
        59.93872449,  59.91538219,  59.8920409 ,  59.86870065,
        59.84536141,  59.8220232 ,  59.79868602,  59.77534986,
        59.75201472,  59.7286806 ,  59.70534751,  59.68201545,
        59.6586844 ,  59.63535438,  59.61202539,  59.58869742,
        59.56537047,  59.54204455,  59.51871965,  59.49539577,
        59.47207294,  59.44875114,  59.42543037,  59.40211062,
        59.37879189,  59.35547419,  59.33215751,  59.30884186,
        59.28552723,  59.26221362,  59.23890104,  59.21558948,
        59.19227894,  59.16896943,  59.14566095,  59.12235348,
        59.09904704,  59.07574163,  59.05243723,  59.02913386,
        59.00583152,  58.9825302 ,  58.9592299 ,  58.93593063,
        58.91263238,  58.88933515,  58.86603895,  58.84274377,
        58.81944962,  58.79615649,  57.57286438,  57.5495733 ,
        57.52628324,  57.50299421,  57.4797062 ,  57.45641921,
        57.43313325,  57.40984831,  57.38656439,  57.3632815 ,
        57.33999963,  57.31671879,  57.29343897,  57.27016017,
        57.2468824 ,  57.22360565,  57.20032993,  57.17705522,
        57.15378155,  57.13050889,  57.10723726,  57.08396666,
        57.06069708,  57.03742852,  57.01416098,  56.99089447,
        56.96762899,  56.94436452,  56.92110109,  56.89783867,
        56.87457728,  56.85131691,  56.82805757,  56.80479925,
        56.78154195,  56.75828568,  56.73503043,  56.71177621,
        56.68852301,  56.66527083,  56.64201968,  56.61876955,
        56.59552044,  56.57227236,  56.54902531,  56.52577927,
        56.50253426,  56.47929028,  56.45604731,  56.43280538,
        56.40956446,  56.38632457,  56.3630857 ,  56.33984786,
        56.31661104,  56.29337525,  56.27014047,  56.24690673,
        56.223674  ,  56.2004423 ,  56.17721163,  56.15398198,
        56.13075335,  56.10752574,  56.08429916,  56.0610736 ,
        56.03784907,  56.01462556,  55.99140308,  55.96818161,
        55.94496118,  55.92174176,  55.89852337,  55.87530601,
        55.85208966,  55.82887435,  55.80566005,  55.78244678,
        55.75923453,  55.73602331,  55.71281311,  55.68960394,
        55.66639578,  55.64318866,  55.61998255,  55.59677747,
        55.57357342,  55.55037038,  55.52716837,  55.50396739,
        55.48076743,  55.45756849,  55.43437058,  55.41117369,
        55.38797782,  55.36478298,  55.34158916,  55.31839637,
        55.2952046 ,  55.27201385,  55.24882413,  55.22563543,
        55.20244776,  55.1792611 ,  55.15607548,  55.13289087,
        55.10970729,  55.08652474,  55.06334321,  55.0401627 ,
        55.01698319,  54.99380469,  54.97062723,  54.94745078,
        54.92427536,  54.90110096,  54.87792759,  54.85475524,
        54.83158392,  54.80841361,  54.78524434,  54.76207608,
        54.73890885,  54.71574265,  54.69257747,  54.66941331,
        54.64625017,  54.62308806,  54.59992698,  54.57676691,
        54.55360787,  54.53044986,  54.50729287,  54.4841369 ,
        54.46098196,  54.43782804,  54.41467514,  54.39152327,
        54.36837242,  54.34522259,  54.32207379,  54.29892602,
        54.27577926,  54.25263353,  54.22948883,  54.20634515,
        54.18320249,  54.16006086,  54.13692025,  54.11378066,
        54.0906421 ,  54.06750456,  54.04436804,  54.02123255,
        53.99809809,  53.97496464,  53.95183222,  53.92870083,
        53.90557046,  53.88244111,  53.85931278,  53.83618548,
        53.81305921,  53.78993396,  53.76680973,  53.74368652,
        53.72056434,  53.69744318,  53.67432305,  53.65120394,
        53.62808586,  53.60496879,  53.58185276,  53.55873774,
        53.53562375,  53.51251079,  53.48939884,  53.46628792,
        53.44317803,  53.42006916,  53.39696131,  53.37385449,
        53.35074869,  53.32764391,  53.30454016,  53.28143743,
        53.25833573,  53.23523505,  53.21213539,  53.18903676,
        53.16593915,  53.14284257,  53.119747  ,  53.09665247,
        53.07355895,  53.05046646,  53.027375  ,  53.00428456,
        52.98119514,  52.95810674,  52.93501937,  52.91193303,
        52.8888477 ,  52.86576341,  52.84268013,  52.81959788,
        52.79651665,  52.77343645,  52.75035727,  52.72727911,
        52.70420198,  52.68112587,  52.65805079,  52.63497673,
        52.61190369,  52.58883168,  52.56576069,  52.54269072,
        52.51962178,  52.49655387,  52.47348697,  52.4504211 ,
        52.42735626,  52.40429243,  52.38122964,  52.35816786,
        52.33510711,  52.31204738,  52.28898868,  52.265931  ,
        52.24287435,  52.21981872,  52.19676411,  52.17371052,
        52.15065796,  52.12760643,  52.10455592,  52.08150643,
        52.05845796,  52.03541052,  52.01236411,  51.98931871,
        51.96627434,  51.943231  ,  51.92018868,  51.89714738,
        51.87410711,  51.85106786,  51.82802963,  19.81265874])
        #self.params.weight.W_wing * (1 - (2 * self.y / self.span)**2)
        self.lift = np.array(self.lift)
        self.drag = np.array(self.drag)
        self.moment_aero = np.array(self.moment_aero)

        self.load_max = self.params.max_load_factor
        self.lift = self.lift * self.load_max * 1.5       # Scale lift by ultimate load factor (SF = 1.5)

    def compute_resultant_loads(self, lift, drag, moment_aero, weight):
        """
        Compute net vertical load and torque along the span.
        Inputs:
            - lift: 1D np.array of lift force per unit span (N/m)
            - drag: 1D np.array of drag force per unit span (N/m)
            - moment_aero: 1D np.array of aerodynamic moment per unit span (Nm/m)
            - weight: 1D np.array of weight per unit span (N/m)
        Outputs:
            - force_z: net distributed vertical load in z-direction (N)
            - force_x: net distributed load in x-direction (N)
            - torque_y: distributed torque about y-axis (Nm/m)
        """
        # Net Distributes Loads
        force_z = + lift - weight  # net distributed vertical load in z (positive downwards)
        force_x = + drag  # net distributed horizontal load in negative x-direction (positive towards nose)

        # For Torque: Aerod. Moment + Induced Torque (from Vertical/Horizontal Forces)
        x_distance_SC_AC = 0.01  # X-axis distance from reference load point to shear center (m)
        z_distance_SC_AC = 0.01  # Z-axis distance from reference load point to shear center (m)
        moment_aerodynamic_to_shear_center = - (force_x * z_distance_SC_AC + force_z * x_distance_SC_AC)  # induced torque from forces about y-axis

        # Total torque about y-axis
        torque_y = moment_aero + moment_aerodynamic_to_shear_center # distributed torque about y-axis (postice Right-handed system)
        

        return force_z, force_x, torque_y

    def compute_internal_distributions(self, y, force_z, force_x, torque_y):
        """
        Compute internal loads from distributed loading along y-axis (spanwise).
        Inputs:
            - qz: net vertical distributed load (lift - weight), N/m
            - torque_dist: distributed pitching moment + drag-induced torque (Nm/m)
        Output:
            - Vz: shear in z-direction (N)
            - Mx: bending moment about x-axis (Nm)
            - Tx: torsion about x-axis (Nm)
        """

        y_tip_root = np.flip(y)  # Reverse y for integration from tip to root

        # Integrate from tip (right) to root (left)
    
        # Distributed Load in z-direction
        Vz_tip_to_root = - integrate.cumulative_trapezoid(force_z[::-1], y_tip_root, initial=0)  # Shear force in z-direction
        # Note: The bending moment about x-axis is due to the shear force in z-direction
        Mx_tip_to_root = - integrate.cumulative_trapezoid(Vz_tip_to_root, y_tip_root, initial=0)   # Bending moment about x-axis

        # Distributed Load in x-direction
        Vx_tip_to_root = - integrate.cumulative_trapezoid(force_x[::-1], y_tip_root, initial=0)  # Shear force in x-direction
        # Note: The bending moment about z-axis is due to the shear force in x-direction
        Mz_tip_to_root = - integrate.cumulative_trapezoid(Vx_tip_to_root, y_tip_root, initial=0)  # Bending moment about z-axis

        # Torsion about y-axis
        Ty_tip_to_root = - integrate.cumulative_trapezoid(torque_y[::-1], y_tip_root, initial=0)  # Torsion about y-axis

        # Flip back -> root to tip
        shear_z = Vz_tip_to_root[::-1]
        bend_moment_x = Mx_tip_to_root[::-1]
        shear_x = Vx_tip_to_root[::-1]
        bend_moment_z = Mz_tip_to_root[::-1]
        torsion_y = Ty_tip_to_root[::-1]

        num_points = len(shear_z)  # Assuming all arrays have the same length

        internal_loads_list = [
        {
            'shear_z': shear_z[i],
            'moment_x': bend_moment_x[i],
            'torsion_y': torsion_y[i],
            'shear_x': shear_x[i],
            'moment_z': bend_moment_z[i]
        }
        for i in range(num_points)
        ]
        
        internal_loads = {
            'shear_z': shear_z,
            'moment_x': bend_moment_x,
            'torsion_y': torsion_y,
            'shear_x': shear_x,
            'moment_z': bend_moment_z
        }

        return internal_loads_list, internal_loads

 
        return internal_loads

    def plot_internal_loads(self, y, Vz, Mx, Ty, Vx, Mz, title_prefix=""):
        """
        Plot internal load distributions along the wing half-span.

        Parameters:
        - y: spanwise positions (m)
        - Vz: shear force in z-direction (N)
        - Mx: bending moment about x-axis (Nm)
        - Ty: torsion about y-axis (Nm)
        - Vx: (optional) shear force in x-direction (N)
        - Mz: (optional) bending moment about z-axis (Nm)
        - title_prefix: string to prepend to plot titles
        """
        components = [
            (Vz, "Shear Force $V_z$", "Shear $V_z$ (N)"),
            (Mx, "Bending Moment $M_x$", "Moment $M_x$ (Nm)"),
            (Ty, "Torque $T_y$", "Torque $T_y$ (Nm)"),
            (Vx, "Shear Force $V_x$", "Shear $V_x$ (N)"),
            (Mz, "Bending Moment $M_z$", "Moment $M_z$ (Nm)")
        ]

    
        num_plots = len(components)
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.5 * num_plots), sharex=True)

        for ax, (data, title, ylabel) in zip(axes, components):
            ax.plot(y, data)
            ax.set_title(f"{title_prefix}{title}")
            ax.set_ylabel(ylabel)
            ax.grid(True)

        axes[-1].set_xlabel("Spanwise Location y (m)")
        plt.tight_layout()
        plt.show()

    def plot_wing_aerodynamic_loading(self, lift_dist, drag_dist, moment_dist):
        """
        Plot wing loading diagrams given the lift, drag, and moment distributions.
        
        Parameters:
        - lift_dist: 1D np.array of lift force per unit span (length 200)
        - drag_dist: 1D np.array of drag force per unit span (length 200)
        - moment_dist: 1D np.array of moment per unit span (length 200)
        """
        # Spanwise locations: from -1 (left tip) to 1 (right tip), 200 points total
        y = np.linspace(-1, 1, 200)

        # Plotting
        plt.figure(figsize=(15, 8))

        plt.subplot(3, 1, 1)
        plt.plot(y, lift_dist)
        plt.title("Lift Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Lift (N/m)")
        plt.grid(True)

        plt.subplot(3, 1, 2)
        plt.plot(y, drag_dist)
        plt.title("Drag Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Drag (N/m)")
        plt.grid(True)

        plt.subplot(3, 1, 3)
        plt.plot(y, moment_dist)
        plt.title("Moment Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Moment (Nm/m)")
        plt.grid(True)

        plt.tight_layout()
        plt.show()

    def plot_wing_weight(weight_dist):
        """
        Plot wing weight distribution along the span and compute total weight.
        
        Parameters:
        - weight_dist: 1D np.array of weight per unit span (N/m), length 200
        """
        y = np.linspace(-1, 1, 200)

        # Total weight via trapezoidal integration
        total_weight = np.trapz(weight_dist, y)

        # Plotting
        plt.figure(figsize=(8, 4))
        plt.plot(y, weight_dist, label='Weight Distribution')
        plt.title("Wing Weight Distribution")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Weight (N/m)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        print(f"Total Wing Weight: {total_weight:.2f} N")

    def run_analysis(self, PLOT):
        """
        Run the loading analysis for a given load case and plot results.
        Parameters:
        - y: spanwise locations (1D np.array)
        - lift: lift distribution (1D np.array)
        - drag: drag distribution (1D np.array)
        - moment: aerodynamic moment distribution (1D np.array)
        - weight: weight distribution (1D np.array)
        - label: optional label for the load case
        - PLOT: boolean to control plotting
        """

        force_z, force_x, torque_y = self.compute_resultant_loads(self.lift, self.drag, self.moment_aero, self.weight)
        internal_loads_list, internal_loads = self.compute_internal_distributions(self.y, force_z, force_x, torque_y)
        shear_z = internal_loads['shear_z']
        bend_moment_x = internal_loads['moment_x']
        torsion_y = internal_loads['torsion_y']
        shear_x = internal_loads['shear_x']
        bend_moment_z = internal_loads['moment_z']
        # Plotting the internal loads if PLOT is True
        if PLOT:
            self.plot_internal_loads(self.y, shear_z, bend_moment_x, torsion_y, shear_x, bend_moment_z, title_prefix="")
        return internal_loads_list





if __name__ == "__main__":
    # Initialize the loading diagrams class
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    internal_loads_list = WingLoadingDiagrams(params).run_analysis(PLOT=True)







