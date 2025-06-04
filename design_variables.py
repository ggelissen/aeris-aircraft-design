import math as m
import numpy as np
import yaml


class DesignParameters:
    def __init__(self, initial_config_path=None):
        """
        Initialize the design parameters for the aircraft.
        If an initial configuration file is provided, load the parameters from it.
        """
        # Top-level Parameters
        self.range = None
        self.cruise_speed = None
        self.cruise_mach = None
        self.stall_speed_clean = None
        self.stall_speed_land = None
        self.cruise_altitude = None
        self.cruise_density = None
        self.take_off_distance = None
        self.landing_distance = None
        self.diversion_distance = None
        self.loiter_time = None
        self.max_eq_velocity = None
        self.max_load_factor = None
        self.crit_mach = None
        self.inertia_matrix = None



        # Subsystem Parameters
        self.cg = CGParameters()  # Center of Gravity Parameters
        self.weight = WeightParameters()
        self.wing = WingParameters(W_TO=self.weight.W_TO, W_S=self.weight.W_S)
        self.performance = PerformanceParameters()
        self.fuselage = FuselageParameters()
        self.engine = EngineParameters(W_TO=self.weight.W_TO, T_W=self.weight.T_W)
        self.empennage = EmpennageParameters(l_f=self.fuselage.l_f)
        self.landing_gear = LandingGearParameters()
        self.control_surface = ControlSurfaceParameters()
        self.stability_aero = StabilityAerodynamicParameters()
        self.inertia = IntertiaParameters()

        # Loads Initial Configuration from YAML File (design_config.yaml)
        self.initial_config_path = initial_config_path
        if self.initial_config_path:
            self.load_from_yaml(self.initial_config_path)

    def load_from_yaml(self, file_path):
        """
        Load design parameters from a YAML file.
        :param file_path: Path to the YAML configuration file.
        """
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)

        # Load top-level parameters
        self.range = config.get('range')
        self.cruise_speed = config.get('cruise_speed')
        self.cruise_mach = config.get('cruise_mach')
        self.stall_speed_clean = config.get('stall_speed_clean')
        self.stall_speed_land = config.get('stall_speed_land')
        self.max_eq_velocity = config.get('max_eq_velocity')
        self.cruise_altitude = config.get('cruise_altitude')
        self.cruise_density = config.get('cruise_density')
        self.take_off_distance = config.get('takeoff_distance')
        self.landing_distance = config.get('landing_distance')
        self.diversion_distance = config.get('diversion_distance')
        self.loiter_time = config.get('loiter_time')
        self.max_eq_velocity = config.get('max_eq_velocity') 
        self.max_load_factor = config.get('max_load_factor')
        self.crit_mach = config.get('crit_mach')

        # Load subsystem parameters
        # if 'cg' in config:
        #     self.cg.load_from_dict(config.get('cg', {}))
        if 'wing'in config:
            self.wing.load_from_dict(config.get('wing', {}))
        if 'performance' in config:
            self.performance.load_from_dict(config.get('performance', {}))
        if 'fuselage' in config:
            self.fuselage.load_from_dict(config.get('fuselage', {}))
        if 'engine' in config:
            self.engine.load_from_dict(config.get('engine', {}))
        if 'empennage' in config:
            self.empennage.load_from_dict(config.get('empennage', {}))
        if 'landing_gear' in config:
            self.landing_gear.load_from_dict(config.get('landing_gear', {}))
        if 'control_surface' in config:
            self.control_surface.load_from_dict(config.get('control_surface', {}))
        if 'cg' in config:
            self.cg.load_from_dict(config.get('cg', {}))
        if 'stability_aero' in config:
            self.stability_aero.load_from_dict(config.get('stability_aero', {}))

    def update_parameter(self, parameter_name, value):
        """
        Update a specific design parameter.
        :param parameter_name: Name of the parameter to update.
        :param value: New value for the parameter.
        """
        keys = parameter_name.split('.')
        current = self
        for key in keys[:-1]:
            current = getattr(current, key, None)
            if current is None:
                raise AttributeError(f"Parameter '{parameter_name}' not found.")
        setattr(current, keys[-1], value)
        print(f"Updated {parameter_name} to {value}")

    def get_parameter(self, parameter_name):
        """
        Get the value of a specific design parameter.
        :param parameter_name: Name of the parameter to retrieve.
        :return: Value of the specified parameter.
        """
        keys = parameter_name.split('.')
        current = self
        for key in keys:
            current = getattr(current, key, None)
            if current is None:
                raise AttributeError(f"Parameter '{parameter_name}' not found.")
        return current   

class WeightParameters:
    """
    Class to hold weight-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.W_TO = 30787.8                         # Maximum Take-Off Weight (MTOW) in N
        self.W_E = None                             # Empty Weight in N
        self.W_OE = 11973.3                         # Operational Empty Weight (OEW) in N
        self.W_F = 12930.5                          # Total Fuel weight in N
        self.W_PL = 5884                            # Maximum Payload weight in N
        self.W_crew = 0.0                           # Crew Weight in N
        self.W_S = 2563                             # Wing Loading in N/m^2
        self.T_W = 0.369                            # Thrust-to-Weight ratio in N/N
        self.M_ff = 0.5793                          # Maximum Fuel Fraction
        self.Fuel_Fuselage_Fraction = 0.5           # Fraction of fuel in fuselage
        self.M_tfo = 0.05                           # Maximum Trapped Fuel and Oil Fraction
        self.W_tfo = None                           # Trapped Fuel and Oil Fraction
        self.W_F_used = None                        # Used Fuel Weight in N
        self.W_F_res = None                         # Reserve Fuel Weight in N
        self.M_TO = self.W_TO / 9.80665                # Maximum Take-Off Mass in kg

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class WingParameters:
    """
    Class to hold wing-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, W_TO: float = None, W_S: float = None):
        self.wetted_area = None                         # Wing Wetted Area in m^2, to be calculated by subsystems.structures.vspfunctions.calculate_wet_areas(), taking into account part of wing inside fuselage
        self.S_w = W_TO / W_S                       # Wing Area in m^2
        self.A_w_target = 9.0                             # Aspect Ratio (INITIAL)
        self.A_w_actual = None                      # Because addition of yehudi and winglets change aspect ratio. During iteration, optimise such that target=actual
        if self.S_w is not None and self.A_w_target is not None:
            self.b_w = m.sqrt(self.A_w_target * self.S_w)  # Wing Span in m
        self.mac = 1.2824                            # Mean Aerodynamic Chord in m
        self.y_LEMAC = None                       # y-position of Leading Edge of MAC in m, recalculated by the programme
        self.x_LEMAC = 5.0                            # Position of Leading Edge of MAC in m
        self.xpos = None                                # calculated in the code in m. relative to the root
        self.z_LEMAC = 0.0
        self.lambda_w = 0.2703                        # Wing Taper Ratio
        self.Lambda_w = None                        # Wing Sweep Angle in degrees
        self.Lambda_025c_w = 32 * np.pi / 180               # Wing quarter-Chord Sweep Angle in radians
        self.Lambda_0_w = None                          # Will be calculated in the code in rad
        self.t_c_w_max = None
        self.t_c_w_r = 0.12                    # Wing Thickness-to-Chord Ratio at Root
        self.t_c_w_t = 0.12                     # Wing Thickness-to-Chord Ratio at Tip
        self.airfoil_w = "Supercritical airfoil, based on Class-Shape Transformation parametrisation for airfoils"
        # Airfoil parameters for CST-parametrised supercritical airfoil. For now, root and tip airfoil are the same.
        self.CST_uppersurf = [0.23723,   0.08150,   0.32028,     0.04044,       0.31712,     0.18393,    0.29198,     0.30933] # First 7 coefficients for NACA SC(2)-7014 Supercritical Airfoil. These coefficients can be optimised.
        self.CST_lowersurf = [0.23723,    -0.05508,   -0.31490,   -0.01788,   -0.26995,   -0.19510,     0.13560,     0.27263] # First 7 coefficients for NACA SC(2)-7014 Supercritical Airfoil. These coefficients can be optimised.
        self.x_c_m = 0.37                           # Location along chord of max thickness
        if self.t_c_w_r is not None and self.t_c_w_t is not None:
            self.tau_w = self.t_c_w_t / self.t_c_w_r    # Wing Thickness-to-Chord Ratio Gradient
        self.i_w = 0.0                             # Wing Incidence Angle in degrees
        self.epsilon_t_quarter_chord = 0.0                       # Wing Twist Angle in radians
        self.Gamma_w = 0.0175                         # Wing Dihedral Angle in radians
        self.root_chord = 1.819  # Wing Root Chord in m
        self.tip_chord = 0.4916  # Wing Tip Chord in m
        self.t_r = self.t_c_w_r * self.root_chord   # Wing Root Thickness in m
        self.planform_points = None  # 2D Numpy array with points forming the planform, is calculated by create_wing()
        self.threeDpoints = None # 3D Numpy array with points forming the wing, is calculated by create_wing()
        self.threeDairfoil1 = None
        self.threeDairfoil2 = None
        self.threeDairfoil3 = None
        self.wingid = None # Will contain the object ID of the wing in VSP, is set by create_wing()
        self.wingsection = WingSectionPars()  # Wing section parameters, such as spars, are stored here
        self.wingribs = Wingribs()  # Wing ribs parameters, such as thickness, are stored here
        self.yehudi = True
        self.yehudi_pos_frac = 0.3 # Yehudi Position Fraction, where 0 is the root and 1 is the tip
        self.yehudi_area = 6.0 # Yehudi area m2
        self.yehudi_flaps = FlapGroup(spanwise_pos_frac_inbound=0.11, spanwise_pos_frac_outbound=0.3, flapwidth=0.4)
        self.main_flaps = FlapGroup(spanwise_pos_frac_inbound=0.35, spanwise_pos_frac_outbound=0.7, flapwidth=0.4)
        self.flapgroups = [self.yehudi_flaps, self.main_flaps]

        

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class PerformanceParameters:
    """
    Class to hold performance-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.climb_rate = None                      # Climb Rate in m/s
        self.climb_rate_alt = None                  # Climb Rate Altitude in m
        self.climb_gradient_AEO = None              # Climb Gradient AEO
        self.climb_gradient_OEI = None              # Climb Gradient OEI
        self.climb_gradient_AEO_alt = None          # Climb Gradient AEO Altitude in ft
        self.climb_gradient_OEI_alt = None          # Climb Gradient OEI Altitude in ft
        self.delta_CD0_OEI = None                   # Zero-Lift Drag Coefficient Differential AEO

        self.CL_max_TO = 1.3                        # Maximum Lift Coefficient at Take-Off
        self.CL_max_LAND = 1.6                      # Maximum Lift Coefficient at Landing
        self.CL_max_cruise = 1.8                    # Maximum Lift Coefficient at Cruise

        self.CL_alpha = 5.0                  # Lift Curve Slope in 1/rad

        self.L_D_cruise = None                      # Lift-to-Drag Ratio at Cruise
        self.L_D_loiter = None                      # Lift-to-Drag Ratio at Loiter

        self.CL_cruise = None                  # Lift Coefficient at Cruise	

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class FuselageParameters:
    """
    Class to hold fuselage-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.l_f = 10                           # Fuselage Length in m

        # Fuselage Cross Sections:
        self.crosssections = {
            "fuselagetip1": {"Tan_Angles": {"top": 21.32, "right": 45, "bottom": 21.32, "left": 45}},
            "crosssection_1": {"Tan_Angles": {"top": 7.11, "right": 0, "bottom": 7.11, "left": 0},
                               "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                 "Dimensions": {"Width": 1.12, "Height": 0.9, "Keystone": 0.57143,
                                                 "RadiusSymmetryType": 1.0, "Radius": 0.35, "RadiusBR": 0.09}},
            "crosssection_2": {"Tan_Angles": {"top": 0, "right": 0, "bottom": 0, "left": 0},
                                 "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                    "Dimensions": {"Width": 1.25, "Height": 1.05, "Keystone": 0.58929,
                                                     "RadiusSymmetryType": 3.0, "Radius": 0.38}},
            "crosssection_3": {"Tan_Angles": {"top": 0, "right": 0, "bottom": 0, "left": 0},
                                    "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                        "Dimensions": {"Width": 1.25, "Height": 0.98, "Keystone": 0.60357,
                                                        "RadiusSymmetryType": 3.0, "Radius": 0.38}},
            "fuselagetip2": {"Tan_Angles": {"top": -26.05, "right": -45, "bottom": -26.05, "left": -45}}
        }


        self.D_f = np.max(np.array([self.crosssections[f"crosssection_{i+1}"]['Dimensions']['Width'] for i in range(len(self.crosssections)-2)]))    #  Maximum Fuselage Diameter in m
        if self.D_f is not None and self.l_f is not None:
            self.lf_df = self.l_f / self.D_f        # Fuselage Length-to-Diameter Ratio
        self.l_n = 2.0                              # Nose Length in m
        self.fuseid = None # Will contain the object ID of the wing in VSP, is set by create_fuselage()


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class EngineParameters:
    """
    Class to hold engine-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, W_TO: float = None, T_W: float = None):
        # TODO: Add separate variables for the nacelle
        self.N_engines = 1                          # Number of Engines
        self.T_TO = T_W * W_TO                      # Thrust at Take-Off in N
        self.cruise_thrust_setting = None           # Thrust setting for cruise
        self.engine_weight =   None                 # Engine Weight in N
        self.engine_max_thrust = None               # Engine Maximum Thrust in N
        self.engine_length = None                   # Engine Length in m
        self.engine_diameter = None                 # Engine Diameter in m
        self.nacelle_diameter = None
        self.nacelle_length = None
        self.cruise_tsfc = None                     # Thrust Specific Fuel Consumption at Cruise in kg/N/h
        self.take_off_tsfc = None                   # Thrust Specific Fuel Consumption at Take-Off in kg/N/h
        self.nacelle_blend_par = -0.4               # Parameter specifying the blend of the nacelle with the fuselage
        self.nacelle_inlet_tan_angles = np.deg2rad(np.array([20., 20., 20., 20.]))  # Nacelle Inlet Tangent Angles in radians
        self.nacelle_outlet_tan_angles = np.deg2rad(np.array([-15., -20., -15., -20.]))  # Nacelle Exhaust Tangent Angles in radians
        self.engine_x_pos = -6.5                    # Engine X-Position in m
        self.engine_y_pos = 0.0                     # Engine Y-Position in m
        self.engine_z_pos = -0.9                    # Engine Z-Position in m


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class EmpennageParameters:
    """
    Class to hold empennage-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, l_f: float = None):
        # TODO: Change to V-Tail, remove horizontal and vertical stabilizer parameters, which are still used in some part of the code
        self.S_h =    1.39                          # Horizontal Stabilizer Area in m^2
        self.S_v =   2.16                          # Vertical Stabilizer Area in m^2
        self.V_h = 0.7 #estimation                             # V-Tail Volume Coefficient
        self.V_v = 0.05 #estimation                             # Horizontal Stabilizer Volume Coefficient
        self.S_t = None                             # Total Stabilizer Area in m^2
        if self.S_h is not None and self.S_v is not None:
            self.Gamma_h = np.arctan2(self.S_v, self.S_h)  # Butterfly Angle in radians
        self.type = 'fixed'

        # V_Tail:
        self.b_v = 3.0                            # V_Tail Span in m
        self.c_t = 1.0                             # V-Tail Tip Chord in m
        self.c_r = 1.5                             # V-Tail Root Chord in m
        self.wetted_area = None                         # V-Tail Wetted Area in m^2, to be calculated by the OpenVSP CompGeom function, taking into account part of stabilizer inside fuselage
        self.x_t = 8.0                             # V-Tail Position in m
        self.z_t = -0.2                        # V-Tail position in m
        self.V_t = None                             # V-Tail Volume Coefficient
        self.i_t = None                             # V-Tail Incidence Angle in degrees
        self.A_t = 9                             # V-Tail Aspect Ratio
        self.Lambda_t_025c = None                   # V-Tail Quarter-Chord Sweep Angle in degrees
        self.lambda_t = None                        # V-Tail Taper Ratio
        self.t_c_t = None                           # V-Tail Thickness-to-Chord Ratio
        self.airfoil_t = None                       # V-Tail Airfoil Type
        self.vtail_dihedral = np.deg2rad((110 - 180)/-2) #placeholder                  # V-Tail Dihedral Angle in radians
        self.L_v = 0.45* l_f                         #Moment arm vertical stabilizer
        self.L_h = 0.45* l_f                        #Moment arm horizontal stabilizer

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class LandingGearParameters:
    """
    Class to hold landing gear-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.n_mlg = 2                              # Number of Main Landing Gear Units
        self.n_nlg = 1                              # Number of Nose Landing Gear Units
        self.D_mlg = None                           # Main Landing Gear Diameter in m
        self.D_nlg = None                           # Nose Landing Gear Diameter in m
        self.b_mlg = None                           # Main Landing Gear Track in m
        self.b_nlg = None                           # Nose Landing Gear Track in m
        self.l_mlg = None                           # Main Landing Gear Length in m
        self.l_nlg = None                           # Nose Landing Gear Length in m
        self.psi_mlg = None                         # Main Landing Gear Pressure in psi
        self.psi_nlg = None                         # Nose Landing Gear Pressure in psi
        self.LCN = 11                               # Load Classification Number
        self.scrape_angle  = 15                 # Scrape Angle in degrees, used for the nose wheel  
        self.tipback_angle = 15                 # Tipback Angle in degrees, used for the nose wheel
        self.lat_tipover_angle = 7                # Lateral Tipover Angle in degrees, used for the nose wheel
        self.overturn_angle = 55
        self.static_frac_nlg = 0.08                     # Static Load Fraction on Nose Landing Gear
        self.static_frac_mlg = 1 - self.static_frac_nlg      # Static Load Fraction on Main Landing Gear


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class ControlSurfaceParameters:
    """
    Class to hold control surface-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.x_a_inboard = 3.6                             # Control Surface Position in m
        self.x_a_outboard = 4.5
        self.aileron_width = 0.17                        # Aileron Width in m
        self.S_a = (self.x_a_outboard-self.x_a_inboard)*self.aileron_width                          # Control Surface Area in m^2
        self.delta_a = None                         # Control Surface Deflection Angle in degrees
        self.C_m_a = None                           # Control Surface Moment Coefficient

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class CGParameters:
    """
    Class to hold center of gravity (CG) related parameters for the aircraft design.
    Append more parameters as needed. subsystems.structures.vspfunctions.calculate_cg() can also automatically
    calculate CG from the 3D model, but for this more precise weights and geometries of the aircraft need to be known.
    """
    def __init__(self):
        self.x_cg_wing = 5                       # CG Position of the Wing in m
        self.x_cg_fuselage = 4                   # CG Position of the Fuselage in m
        self.x_cg_landing_gear = 4.7               # CG Position of the Landing Gear in m
        self.x_cg_empennage = 9                  # CG Position of the Empennage in m
        self.x_cg_fixed_equipment = 3            # CG Position of the Fixed Equipment in m
        self.x_cg_propulsion = 7                 # CG Position of the Propulsion System in m
        self.x_cg_payload = 3                    # CG Position of the Payload in m
        self.x_cg_fuel = 5                       # CG Position of the Fuel in m
        self.cg_vector_from_3Dmodel = None       # calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity
        self.total_mass_from_3Dmodel = None      # calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity
        self.z_cg = 1.5                          # CG Height in m, can be calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class WingSectionPars:
    def __init__(self):
        self.spars = {
            "Spar1": {"x_pos_frac": 0.2, "t_flange_1_mm": 3, "t_flange_2_mm": 3, "t_web_mm": 2, "flange_width_mm": 50},
            "Spar2": {"x_pos_frac": 0.7, "t_flange_1_mm": 3, "t_flange_2_mm": 3, "t_web_mm": 2, "flange_width_mm": 50},
        }
        self.num_spars = len(self.spars)
        self.stringers = {
            "Stringer1": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.02, "crosssectionalarea_mm2": 200 },
            "Stringer2": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.1, "crosssectionalarea_mm2": 200 },
            "Stringer3": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.25, "crosssectionalarea_mm2": 200 },
            "Stringer4": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.4, "crosssectionalarea_mm2": 200 },
            "Stringer5": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.5, "crosssectionalarea_mm2": 200},
            "Stringer6": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.6, "crosssectionalarea_mm2": 200},
            "Stringer7": {"top_or_bottom_side": "top", "pos_along_airfoil_side": 0.8, "crosssectionalarea_mm2": 200},
            "Stringer8": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.02, "crosssectionalarea_mm2": 200},
            "Stringer9": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.1, "crosssectionalarea_mm2": 200},
            "Stringer10": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.25, "crosssectionalarea_mm2": 200},
            "Stringer11": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.4, "crosssectionalarea_mm2": 200},
            "Stringer12": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.5, "crosssectionalarea_mm2": 200},
            "Stringer13": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.6, "crosssectionalarea_mm2": 200},
            "Stringer14": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.8, "crosssectionalarea_mm2": 200},
        }
        self.num_stringers = len(self.stringers)

class Wingribs:
    def __init__(self):
        self.ribs = {
            "Rib1": {"x_pos_frac": 0.2, "t_mm": 2},
            "Rib2": {"x_pos_frac": 0.4, "t_mm": 2},
            "Rib3": {"x_pos_frac": 0.6, "t_mm": 2},
            "Rib4": {"x_pos_frac": 0.8, "t_mm": 2},
        }
        self.num_ribs = len(self.ribs)
class Control:
    def __init__(self, x_mlg, x_cg):
        self.CLah = None
        self.CLaA_h = None
        self.de_da = 0.1                    # Control Surface Effectiveness
        self.lh = abs(x_mlg - x_cg)
        self.Vh_V = 1
        self.x_ac = None
        self.CLh = None
        self.CLA_h = None
        self.C_m_ac = None
        self.X = np.arange(0,1,0.01)

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class IntertiaParameters:
    def __init__(self, W_TO :float = None, g :float = None):
        self.I_xx = None     # Moment of inertia about x-axis (kg*m^2)
        self.I_yy = None     # Moment of inertia about y-axis (kg*m^2)
        self.I_zz = None     # Moment of inertia about z-axis (kg*m^2)
        self.I_xz = None     # Product of inertia xz-plane (kg*m^2)

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class StabilityAerodynamicParameters:
    def __init__(self):
        self.CL0 = None       # Lift coefficient at alpha=0 (or CZ0 in body axes)
        self.CD0 = None       # Zero-lift drag coefficient (or CX0 in body axes)
        self.CLa = None       # Lift curve slope (dCL/dalpha or dCZ/dalpha)
        self.Cma = None       # Pitching moment coefficient slope (dCm/dalpha)
        self.alpha0_rad = None # Initial angle of attack (radians) for the reference flight condition
        self.theta0_rad = None # Initial pitch angle (radians) for the reference flight condition

        # Longitudinal Derivatives
        self.CX0 = None       
        self.CZ0 = None       
        self.CXu = None
        self.CZu = None
        self.Cmu = None
        self.CXa = None # Often dCX/dalpha
        self.CZa = None         # = CLa (if using stability axes and thrust effects on Z are small)
        self.CXq = None
        self.CZq = None
        self.Cmq = None
        self.CXadot = None
        self.CZadot = None
        self.Cmadot = None
        self.Cmde = None      # Pitch control effectiveness (elevator)

        # Lateral-Directional Derivatives
        self.CYb = None       # Side force due to sideslip
        self.Clb = None       # Rolling moment due to sideslip (dihedral effect)
        self.Cnb = None       # Yawing moment due to sideslip (weathercock stability)
        self.CYp = None
        self.Clp = None       # Rolling moment due to roll rate (roll damping)
        self.Cnp = None       # Yawing moment due to roll rate
        self.CYr = None
        self.Clr = None       # Rolling moment due to yaw rate
        self.Cnr = None       # Yawing moment due to yaw rate (yaw damping)
        
        # Lateral-Directional Control Derivatives (optional for basic stability, needed for control response)
        self.CYda = None
        self.Clda = None      # Aileron effectiveness
        self.Cnda = None
        self.CYdr = None
        self.Cldr = None
        self.Cndr = None      # Rudder effectiveness

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class FlapGroup:
    def __init__(self, spanwise_pos_frac_inbound: float = None, spanwise_pos_frac_outbound: float = None,
                 flapwidth: float = None):

        self.spanwise_pos_frac_inbound = spanwise_pos_frac_inbound
        self.spanwise_pos_frac_outbound = spanwise_pos_frac_outbound
        self.flapwidth = flapwidth # meter