# PLEASE PLEASE do never ever under any circumstances change / remove existing variables! unless you are sure no one else is using them
import math as m
import numpy as np
import yaml
import toml
import json


class DesignParameters:
    def __init__(self, initial_config_path=None):
        """
        Initialize the design parameters for the aircraft.
        If an initial configuration file is provided, load the parameters from it.
        """
        # Top-level Parameters
        self.landing_mach = 0.2 # TODO Alejandro Added this so that the preliminary_stability code can run
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
        self.structurecoords = None
        self.fueltank = FuelTank()
        self.cruise_aoa = None

        # Subsystem Parameters
        self.cg = CGParameters()  # Center of Gravity Parameters
        self.materials = MaterialsParameters()
        self.weight = WeightParameters()
        self.performance = PerformanceParameters()
        self.wing = WingParameters(self, W_TO=self.weight.W_TO, W_S=self.weight.W_S)
        self.fuselage = FuselageParameters()
        self.engine = EngineParameters(W_TO=self.weight.W_TO, T_W=self.weight.T_W)
        self.empennage = EmpennageParameters(l_f=self.fuselage.l_f)
        self.landing_gear = LandingGearParameters()
        self.control_surface = ControlSurfaceParameters()
        self.stability_aero = StabilityAerodynamicParameters()
        self.inertia = IntertiaParameters()
        self.structure_results = StructuresResults(self)


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
        self.cruise_aoa = config.get('cruise_aoa')
        self.cruise_viscosity = config.get('cruise_viscosity')

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
        if 'materials' in config:
            self.materials = config.get('materials', {})

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
    
    def __repr__(self):
        """
        Provides a developer-friendly string representation of the object.
        """
        # Create a dictionary from the object's attributes
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        
        # Use json.dumps for a nicely formatted, indented string
        return json.dumps(attrs, indent=4, default=lambda o: o.__dict__)

class WeightParameters:
    """
    Class to hold weight-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.W_TO = 25750                       # Maximum Take-Off Weight (MTOW) in N
        self.W_E = None                             # Empty Weight in N
        self.W_OE = 11277                         # Operational Empty Weight (OEW) in N
        self.W_F = 8589                 # Total Fuel weight in N
        self.W_PL = 5884                            # Maximum Payload weight in N
        self.W_crew = 0.0                           # Crew Weight in N
        self.W_S = 3218.59                             # Wing Loading in N/m^2, can be updated by class II 
        self.W_S_max = 3218.59                      # Maximum Wing Loading in N/m^2, set by class I analysis
        self.T_W = 0.305                           # Thrust-to-Weight ratio in N/N
        self.M_ff = 0.588                         # Maximum Fuel Fraction 
        self.Fuel_Fuselage_Fraction = 0             # Fraction of fuel in fuselage
        self.M_tfo = 0.05                           # 0.001 on the initial sizing script!! Maximum Trapped Fuel and Oil Fraction TODO, why is this here? Does it need to be accounted? Though it is just part of OEW? This is not contingency fuel, value yes, but not the description
        self.W_tfo = 1890.384                           # Trapped Fuel and Oil Fraction
        self.W_F_used = 10103.319            # Used Fuel Weight in N
        self.W_F_res = 1379.7765        # Reserve Fuel Weight in N
        self.M_TO = self.W_TO / 9.80665             # Maximum Take-Off Mass in kg
        self.W_fus = None                           # Fuselage weight in N
        self.W_wing = 1665.24                         # Wing weight in N


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WeightParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))


class WingParameters:
    """
    Class to hold wing-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, parent, W_TO: float = None, W_S: float = None):
        self.wetted_area = None                         # Wing Wetted Area in m^2, to be calculated by subsystems.structures.vspfunctions.calculate_wet_areas(), taking into account part of wing inside fuselage
        self.S_w = W_TO / W_S                       # Wing Area in m^2
        self.S_ref = self.S_w
        self.A_w_target =12.0                              # Aspect Ratio (INITIAL)
        self.A_w_actual = None                      # Because addition of yehudi and winglets change aspect ratio. During iteration, optimise such that target=actual
        if self.S_w is not None and self.A_w_target is not None:
            self.b_w = m.sqrt(self.A_w_target * self.S_w)  # Wing Span in m
        self.mac = 0.924                           # Mean Aerodynamic Chord in m
        self.y_LEMAC = None                       # y-position of Leading Edge of MAC in m, recalculated by the programme
        self.x_LEMAC = 5.0                            # Position of Leading Edge of MAC in m
        self.xpos = None                                # calculated in the code in m. relative to the root
        self.z_LEMAC = 0.0
        self.lambda_w = 0.2703                        # Wing Taper Ratio
        self.Lambda_w = None                        # Wing Sweep Angle in degrees
        self.Lambda_025c_w = 26.6 * np.pi / 180               # Wing quarter-Chord Sweep Angle in radians
        self.Lambda_05_w = 0.607                           # Wind half-chord sweep angle in rad
        self.Lambda_0_w =None                       # Wing leading edge sweep angle in rad
        self.t_c_w_max = None
        self.de_da = 0.246616                         # Downwash effect on the lift coefficient.
        self.t_c_w_r = 0.12                    # Wing Thickness-to-Chord Ratio at Root
        self.t_c_w_t = 0.12                     # Wing Thickness-to-Chord Ratio at Tip
        self.t_c_w = 0.12                     # Wing Thickness-to-Chord Ratio, average of root and tip
        self.CL = 0.304                          # Design CL of aircraft during cruise
        self.eta = 0.95                  # wing efficiency
        self.cm_025c =-0.6              # moment coeff at quarter chord
        self.airfoil_w = "Supercritical airfoil, based on Class-Shape Transformation parametrisation for airfoils"
        # Airfoil parameters for CST-parametrised supercritical airfoil. For now, root and tip airfoil are the same.
        self.list_of_airfoils = {
            "airfoil1": {
                "Name": "NACA SC(2)-0714 Supercritical Airfoil",
                "tcratio": 0.14,
                'designcl': 0.7,
                "CST_uppersurf": [0.23723,   0.08150,   0.32028,     0.04044,       0.31712,     0.18393,    0.29198,     0.30933],
                "CST_lowersurf": [0.23723,    -0.05508,   -0.31490,   -0.01788,   -0.26995,   -0.19510,     0.13560,     0.27263],
                "simulation_parms": {
                    'Transition_location_for_effective_aoa_0.03_upper_surface': 0.10, # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_upper_surface': 0.01, # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_0.03_lower_surface': 0.1, # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_lower_surface': 0.01, # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_upper_surface': 0.08, # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface': 0.01, # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_lower_surface': 0.1, # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface': 0.01, # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                }
            },
            "airfoil2": {
                "Name": "NACA SC(2)-0612 Supercritical Airfoil",
                'tcratio': 0.12,
                'designcl': 0.6,
                "CST_uppersurf": [0.20037, 0.07330, 0.27432,0.02640, 0.27780, 0.16726, 0.21760, 0.25335],
                "CST_lowersurf": [  -0.20037, -0.06944, -0.21812, -0.11350, -0.11873,  -0.24495,   0.10684,  0.21754],
                "simulation_parms": {
                    'Transition_location_for_effective_aoa_0.03_upper_surface': 0.10,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_0.03_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_upper_surface': 0.08,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                }
            },
            "airfoil3": {
                "Name": "NACA SC(2)-0412 Supercritical Airfoil",
                "tcratio": 0.12,
                'designcl': 0.4,
                "CST_uppersurf": [0.20026, 0.06946, 0.26357, 0.01485, 0.27227,   0.14107,   0.17255,   0.17255],
                "CST_lowersurf": [-0.20026,  -0.08105,  -0.21756,  -0.12698, -0.14338,  -0.24577,   0.04569,   0.16772],
                "simulation_parms": {
                    'Transition_location_for_effective_aoa_0.03_upper_surface': 0.10,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_0.03_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_upper_surface': 0.08,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                }
            },
            "airfoil4": {
                "Name": "NACA SC(2)-0410 Supercritical Airfoil",
                "tcratio": 0.10,
                'designcl': 0.4,
                "CST_uppersurf": [  0.16386,   0.05367,   0.22778,   0.00233,   0.22977,     0.11922,     0.14088,   0.18320],
                "CST_lowersurf": [-  0.16386,   -0.06313,   -0.19743,  -0.07145,  -0.15608,   -0.18852,     0.02047,    0.15824],
                "simulation_parms": {
                    'Transition_location_for_effective_aoa_0.03_upper_surface': 0.10,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_0.03_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_upper_surface': 0.08,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                }
            },
            "airfoil5": {
                "Name": "NACA SC(2)-0610 Supercritical Airfoil",
                "tcratio": 0.10,
                'designcl': 0.6,
                "CST_uppersurf": [    0.16404,     0.05956,    0.23113,     0.02687,    0.21458,      0.16472,      0.17881,    0.24337],
                "CST_lowersurf": [-   0.16404,    -0.04884,   -0.21140,   -0.03327,   -0.16024,   -0.17440,    0.07773,     0.21854],
                "simulation_parms": {
                    'Transition_location_for_effective_aoa_0.03_upper_surface': 0.10,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_0.03_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_0.03_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_upper_surface': 0.08,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                    'Transition_location_for_effective_aoa_-1.655_lower_surface': 0.1,
                    # source: https://ntrs.nasa.gov/api/citations/19890008197/downloads/19890008197.pdf # TODO: Check validity for M=0.85
                    'momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface': 0.01,
                    # Better estimate needed TODO: Mrugank read ESDU documenation for DELTHU
                }
            },
        }

        closest_key = None
        min_distance = float('inf')

        for key, data in self.list_of_airfoils.items():
            tcratio = data.get('tcratio')
            designcl = data.get('designcl')
            if tcratio is None or designcl is None:
                continue  # Skip if either value is missing

            # Euclidean distance in (tcratio, designcl) space
            distance = ((tcratio -  self.t_c_w) ** 2 + (designcl - parent.performance.C_L_hat) ** 2) ** 0.5 # TODO. No definition for this.

            if distance < min_distance:
                min_distance = distance
                closest_key = key
        self.chosenairfoil = closest_key
        self.simulation_parms = self.list_of_airfoils[closest_key]['simulation_parms'] # Simulation parameters for the airfoil, such as transition location and momentum thickness jump
        self.CST_uppersurf = self.list_of_airfoils[closest_key]['CST_uppersurf'] # First 7 coefficients for NACA SC(2)-0714 Supercritical Airfoil. These coefficients can be optimised.
        self.CST_lowersurf = self.list_of_airfoils[closest_key]['CST_lowersurf'] # First 7 coefficients for NACA SC(2)-0714 Supercritical Airfoil. These coefficients can be optimised.
        self.x_c_m = 0.37                           # Location along chord of max thickness
        if self.t_c_w_r is not None and self.t_c_w_t is not None:
            self.tau_w = self.t_c_w_t / self.t_c_w_r    # Wing Thickness-to-Chord Ratio Gradient
        self.i_w = 0.0                             # Wing Incidence Angle in degrees
        self.epsilon_t_quarter_chord = 0.0                       # Wing Twist Angle in radians
        self.Gamma_w = 0.0175                         # Wing Dihedral Angle in radians
        self.root_chord = 1.819  # Wing Root Chord in m
        self.tip_chord = 0.4916  # Wing Tip Chord in m
        self.C_m_ac = None       # Wing moment coefficient at aerodynamic center
        self.t_r = self.t_c_w_r * self.root_chord   # Wing Root Thickness in m
        self.planform_points = None  # 2D Numpy array with points forming the planform, is calculated by create_wing()
        self.threeDpoints = None # 3D Numpy array with points forming the wing, is calculated by create_wing()
        self.threeDairfoil1 = None
        self.threeDairfoil2 = None
        self.threeDairfoil3 = None
        self.wingid = None # Will contain the object ID of the wing in VSP, is set by create_wing()
        self.wingsection = WingSectionParameters(parent)  # Wing section parameters, such as spars, are stored here
        self.wingribs = Wingribs(parent)  # Wing ribs parameters, such as thickness, are stored here
        self.yehudi = True
        self.yehudi_pos_frac = 0.3 # Yehudi Position Fraction, where 0 is the root and 1 is the tip
        self.yehudi_area = 4.0 # Yehudi area m2
        self.yehudi_flaps = FlapGroup(spanwise_pos_frac_inbound=0.18, spanwise_pos_frac_outbound=0.3, flapwidth=0.2) # First two span, second one chord
        self.main_flaps = FlapGroup(spanwise_pos_frac_inbound=0.35, spanwise_pos_frac_outbound=0.75, flapwidth=0.04)
        self.flapgroups = [self.yehudi_flaps, self.main_flaps]
        self.airfoil_clalpha = 1.5
        self.airfoil_cd0 = 0.06
        self.C_D0 = 0.017196 
        self.e = 0.9         #oswald efficiency factor
        self.k2 = 1 / (np.pi * self.A_w_target * self.e)
        self.Mach_cross = 0.935
        self.epsilon_t = 0         # Wing twist angle [degrees]
        self.weight_distribution = None
        self.max_allowed_x_displacement = 1.0 # m
        self.max_allowed_z_displacement = 0.10
        self.max_allowed_twist_angle = np.pi / 20 # rad


        # Aerodynamics Loads Distribution
        self.CL_distribution = None  # Lift Coefficient Distribution along the span
        self.CD_distribution = None  # Drag Coefficient Distribution along the span
        self.CM_distribution = None  # Moment Coefficient Distribution along the span

        
    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))


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
        self.CL_max_cruise = 1.6                    # Maximum Lift Coefficient at Cruise

        self.CL_alpha = 5.0                  # Lift Curve Slope in 1/rad

        self.L_D_cruise = 14.562                      # Lift-to-Drag Ratio at Cruise
        self.L_D_loiter = 16.815                      # Lift-to-Drag Ratio at Loiter

        self.stall_angle_cruise = 15 * np.pi/180    # stall angle from CL-alpha curve airfoil

        self.CL_cruise = 0.4                  # Lift Coefficient at Cruise
        self.C_L_hat = 0.6                      # Design Lift Coefficient, to be updated by alejandro's code

        self.V_A = 162.35                       # Maneuvering Speed in m/s (USE this for Aerodynamic Loads)


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class FuselageParameters:
    """
    Class to hold fuselage-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.l_f = 10                           # Fuselage Length in m
        self.lh = None                          # Dist from wing to hor. stabilizer
        self.C_m_ac = -0.3584513                       # Moment coefficient at the aerodynamic center.
        self.x_ac = None                        # Aerodynamic center of the aircraft.
        self.x_payload = None                   # x-coordinate of Center of gravity of payload
        self.x_fuselage = None                  # x-coordinate of Center of gravity of fuselage

        # Fuselage Cross Sections:
        self.crosssections = {
            "fuselagetip1": {"Tan_Angles": {"top": 21.32, "right": 45, "bottom": 21.32, "left": 45}},
            "crosssection_1": {"Tan_Angles": {"top": 7.11, "right": 0, "bottom": 7.11, "left": 0},
                               "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                 "Dimensions": {"Width": 1.2, "Height": 1.2, "Keystone": 0.57143,
                                                 "RadiusSymmetryType": 1.0, "Radius": 0.35, "RadiusBR": 0.09}},
            "crosssection_2": {"Tan_Angles": {"top": 0, "right": 0, "bottom": 0, "left": 0},
                                 "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                    "Dimensions": {"Width": 1.6, "Height": 1.4, "Keystone": 0.58929,
                                                     "RadiusSymmetryType": 3.0, "Radius": 0.38}},
            "crosssection_3": {"Tan_Angles": {"top": 0, "right": 0, "bottom": 0, "left": 0},
                                    "Type": "vsp.XS_ROUNDED_RECTANGLE",
                                        "Dimensions": {"Width": 1.6, "Height": 1.2, "Keystone": 0.60357,
                                                        "RadiusSymmetryType": 3.0, "Radius": 0.38}},
            "fuselagetip2": {"Tan_Angles": {"top": -26.05, "right": -45, "bottom": -26.05, "left": -45}}
        }


        self.D_f = 1.7
        #self.D_f = np.max(np.array([self.crosssections[f"crosssection_{i+1}"]['Dimensions']['Width'] for i in range(len(self.crosssections)-2)]))    #  Maximum Fuselage Diameter in m
        if self.D_f is not None and self.l_f is not None:
            self.lf_df = self.l_f / self.D_f        # Fuselage Length-to-Diameter Ratio
        self.l_n = 2.0                              # Nose Length in m
        self.fuseid = None # Will contain the object ID of the wing in VSP, is set by create_fuselage()
        self.coordinates_have_been_loaded = False
        self.fuselage_coords = None


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class EngineParameters:
    """
    Class to hold engine-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, W_TO: float = None, T_W: float = None):
        # TODO: Add separate variables for the nacelle
        self.N_engines = 1                          # Number of Engines
        # self.T_TO = T_W * W_TO                      # Thrust at Take-Off in N
        self.T_TO = 8135                     # Thrust at Take-Off in N
        self.cruise_thrust_setting = None           # Thrust setting for cruise
        self.engine_weight =   234.05                 # Engine Weight in N
        self.engine_max_thrust = 9340               # Engine Maximum Thrust in N
        self.engine_length = None                   # Engine Length in m
        self.engine_diameter = None                 # Engine Diameter in m
        self.nacelle_diameter = 0.918
        self.nacelle_length = 1.9
        self.fuel_density = None                    # Fuel density depending on fuel type (A1, SAF, etc)
        self.cruise_tsfc = 68                     # Thrust Specific Fuel Consumption at Cruise in kg/N/h # TODO, it is now in lb/hr, all code did this
        self.take_off_tsfc = None                   # Thrust Specific Fuel Consumption at Take-Off in kg/N/h
        self.nacelle_blend_par = -0.4               # Parameter specifying the blend of the nacelle with the fuselage
        self.nacelle_inlet_tan_angles = np.deg2rad(np.array([20., 20., 20., 20.]))  # Nacelle Inlet Tangent Angles in radians
        self.nacelle_outlet_tan_angles = np.deg2rad(np.array([-15., -20., -15., -20.]))  # Nacelle Exhaust Tangent Angles in radians
        self.engine_x_pos = -6.5                    # Engine X-Position in m
        self.engine_y_pos = 0.0                     # Engine Y-Position in m
        self.engine_z_pos = -1.1                    # Engine Z-Position in m
        self.Bpr = 3.3                            # Bypass Ratio, used for engine sizing
        self.eta_nozz = 0.97                   # Nozzle Efficiency, used for engine sizing
        self.eta_fanturb = 0.75  
        self.tt4to = 1400 #tt4 temp at takeoff   
        self.prfan = 1.9           
        self.prlpc = 1.5
        self.prhpc = 5.65 
        self.tt4start = 850
        self.tt4taxi = 900
        self.tt4climb = 1300
        self.tt4cruise = 1200
        self.tt4descent = 900
        self.tt4landing = 1000
        self.lhv = 43.e6
        self.etafan = 0.915
        self.etalpc = 0.9
        self.etahpc = 0.9
        self.etahpt = 0.93
        self.etalpt = 0.93
        self.etacom = 0.99
        self.etamechl = 0.99
        self.etamechh = 0.99
        self.prcom = 0.99
        self.prinlet = 0.98
        self.bleedto = 0. 
        self.power_tol = 0.
        self.power_toh = 0.
        self.cooling_l = 0.
        self.cooling_h = 0.
        self.cruise_thrust = 1324 #N


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class EmpennageParameters:
    """
    Class to hold empennage-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self, l_f: float = None):
        # TODO: Change to V-Tail, remove horizontal and vertical stabilizer parameters, which are still used in some part of the code
        # ^^ no right? V-tail is combination of hor. tail and vert. tail size?
        self.S_h =    1.23                          # Horizontal Stabilizer Area in m^2
        self.S_v =   0.97                         # Vertical Stabilizer Area in m^2
        self.V_h = 0.64 #estimation                             # V-Tail Volume Coefficient
        self.V_v = 0.07 #estimation                             # Horizontal Stabilizer Volume Coefficient
        self.Cl_alpha = 6.341572                          # Hor. Stabilizer cl alpha curve during cruise
        self.CL_h = -1.06717                              # Design CL of hor. stabilizer. during cruise
        self.S_t = 1.57                           # Total Stabilizer Area in m^2
        if self.S_h is not None and self.S_v is not None:
            self.Gamma_h = np.arctan2(self.S_v, self.S_h)  # Butterfly Angle in radians
        self.type = 'fixed'
        self.Vh_v = 0.95                             # Ratio of (hor.) tail speed to free stream speed.

        # V_Tail:
        self.b_v = 3.76                            # V_Tail Span in m TODO, computed in preliminary_sizing_tail.py, shouldnt be a magic number
        self.b_v_h = self.b_v * np.cos(self.Gamma_h) * 2 # hor tail span
        self.c_t = 1.0                             # V-Tail Tip Chord in m
        self.c_r = 1.5                             # V-Tail Root Chord in m
        self.wetted_area = None                         # V-Tail Wetted Area in m^2, to be calculated by the OpenVSP CompGeom function, taking into account part of stabilizer inside fuselage
        self.x_t = 8.0                             # V-Tail Position in m
        self.z_t = -0.2                             # V-Tail position in m
        self.V_t = None                             # V-Tail Volume Coefficient
        self.i_t = None                             # V-Tail Incidence Angle in degrees
        self.A_t = self.b_v**2/self.S_v             # V-Tail Aspect Ratio
        self.A_t_h = self.b_v_h**2/self.S_h             # hor tail Aspect Ratio
        self.Lambda_t_025c = None                   # V-Tail Quarter-Chord Sweep Angle in degrees
        self.lambda_t = 0.25                        # V-Tail Taper Ratio
        self.t_c_t = 0.14                           # V-Tail Thickness-to-Chord Ratio
        self.airfoil_t = None                       # V-Tail Airfoil Type
        self.vtail_dihedral = np.deg2rad((110 - 180)/-2) #placeholder                  # V-Tail Dihedral Angle in radians
        self.L_v = 0.45* l_f                         #Moment arm vertical stabilizer
        self.L_h = 0.45* l_f                        #Moment arm horizontal stabilizer
        self.z_v = 0.5*self.b_v #TODO this is a placeholder for distance between tail a/c and cg vertically
        self.tailid = None

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))


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
        self.scrape_angle  = 15  * np.pi/180               # Scrape Angle in radians, used for the nose wheel  
        self.tipback_angle = 15  * np.pi/180               # Tipback Angle in radians, used for the nose wheel
        self.lat_tipover_angle = 7 * np.pi/180                # Lateral Tipover Angle in radians, used for the nose wheel
        self.overturn_angle = 55 * np.pi/180  # Overturn Angle in radians, used for the main wheel
        self.static_frac_nlg = 0.08                     # Static Load Fraction on Nose Landing Gear
        self.static_frac_mlg = 1 - self.static_frac_nlg      # Static Load Fraction on Main Landing Gear


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class ControlSurfaceParameters:
    """
    Class to hold control surface-related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.x_a_inboard = 3.7                             # Control Surface Position in m
        self.x_a_outboard = 4.7
        self.aileron_width = 0.14                        # Aileron Width in m
        self.S_a = (self.x_a_outboard-self.x_a_inboard)*self.aileron_width                          # Control Surface Area in m^2
        self.delta_a = None                         # Control Surface Deflection Angle in degrees
        self.C_m_a = None                           # Control Surface Moment Coefficient
        self.vtailid = None

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class CGParameters:
    """
    Class to hold center of gravity (CG) related parameters for the aircraft design.
    Append more parameters as needed. subsystems.structures.vspfunctions.calculate_cg() can also automatically
    calculate CG from the 3D model, but for this more precise weights and geometries of the aircraft need to be known.
    """
    def __init__(self):
        self.x_cg_wing = 3.78                       # CG Position of the Wing in m
        self.x_cg_fuselage = 4                   # CG Position of the Fuselage in m
        self.x_cg_landing_gear = 4.7               # CG Position of the Landing Gear in m
        self.x_cg_empennage = 9                  # CG Position of the Empennage in m
        self.x_cg_fixed_equipment = 3            # CG Position of the Fixed Equipment in m
        self.x_cg_propulsion = 7                 # CG Position of the Propulsion System in m
        self.x_cg_payload = 3                    # CG Position of the Payload in m
        self.x_cg_fuel = 5                       # CG Position of the Fuel in m
        self.x_ac_w = 3.781                      # wing aerodynamic center
        self.cg_vector_from_3Dmodel = None       # calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity
        self.total_mass_from_3Dmodel = None      # calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity
        self.z_cg = 1.5                          # CG Height in m, can be calculated by subsystems.structures.vspfunctions.calculate_cg() from the 3D model, if 3D model has enough fidelity
        self.z_cg_propulsion = None              # Z CG pos of the propulsion system in m
        
    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
            """
            Provides a developer-friendly string representation of the WingParameters object.
            """
            attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
            return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class WingSectionParameters:
    def __init__(self, parent):
        self.spars = {
            "Spar1": {"x_pos_frac": 0.2, "t_flange_1_mm": 8, "t_flange_2_mm": 8, "t_web_mm": 30, "flange_width_mm": 70, 'material_density_kgm3': parent.materials.material_density},
            "Spar2": {"x_pos_frac": 0.7, "t_flange_1_mm": 8, "t_flange_2_mm": 8, "t_web_mm": 30, "flange_width_mm": 70, 'material_density_kgm3': parent.materials.material_density},
        }
        self.num_spars = len(self.spars)
        self.stringers = {
            "Stringer1": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.02, "crosssectionalarea_mm2": 1150 , 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer2": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.1, "crosssectionalarea_mm2": 1150 , 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer3": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.25, "crosssectionalarea_mm2": 1150 , 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer4": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.4, "crosssectionalarea_mm2": 1150 , 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer5": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.5, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer6": {"top_or_bottom_side": "top" , "pos_along_airfoil_side": 0.6, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer7": {"top_or_bottom_side": "top", "pos_along_airfoil_side": 0.8, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer8": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.02, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer9": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.1, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer10": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.25, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer11": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.4, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer12": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.5, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer13": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.6, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
            "Stringer14": {"top_or_bottom_side": "bottom", "pos_along_airfoil_side": 0.8, "crosssectionalarea_mm2": 1150, 'material_density_kgm3': parent.materials.material_density, 'area_moment_of_inertia_m4': 5e-9*8, 'K': 1.0},
        }
        self.num_stringers = len(self.stringers)
        self.wingskin = {
            'thicness': 1, # mm
            'material_density_kgm3': parent.materials.material_density # kg/m^3
        }


class Wingribs:
    def __init__(self, parent):
        self.ribs = {
            "Rib1": {"y_pos_frac": 0.2, "t_mm": 2, 'material_density_kgm3': parent.materials.material_density},
            "Rib2": {"y_pos_frac": 0.4, "t_mm": 2, 'material_density_kgm3': parent.materials.material_density},
            "Rib3": {"y_pos_frac": 0.6, "t_mm": 2, 'material_density_kgm3': parent.materials.material_density},
            "Rib4": {"y_pos_frac": 0.8, "t_mm": 2, 'material_density_kgm3': parent.materials.material_density},
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

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class IntertiaParameters:
    def __init__(self, W_TO :float = None, g :float = None):
        self.I_xx = 1212.66     # Moment of inertia about x-axis (kg*m^2)
        self.I_yy = 8466.62     # Moment of inertia about y-axis (kg*m^2)
        self.I_zz = 9219.268     # Moment of inertia about z-axis (kg*m^2)
        self.I_xz = 382.99     # Product of inertia xz-plane (kg*m^2)

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
        self.CXu = None #from cd-mach curve from alejandro
        self.CZu = None 
        self.Cmu = None
        self.CXa = None         # Often dCX/dalpha
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
        
        # # Lateral-Directional Control Derivatives (optional for basic stability, needed for control response)
        # self.CYda = None
        # self.Clda = None      # Aileron effectiveness
        # self.Cnda = None
        # self.CYdr = None
        # self.Cldr = None
        # self.Cndr = None      # Rudder effectiveness

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class FlapGroup:
    def __init__(self, spanwise_pos_frac_inbound: float = None, spanwise_pos_frac_outbound: float = None,
                 flapwidth: float = None):

        self.spanwise_pos_frac_inbound = spanwise_pos_frac_inbound
        self.spanwise_pos_frac_outbound = spanwise_pos_frac_outbound
        self.flapwidth = flapwidth # meter
        self.density_kgm2 = 30 # kg/m^2, density of the flap per square meter of flap area

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class FuelTank:
    def __init__(self):
        self.dist_from_wingskin = 0.15
        self.frac_pos_chord_min = 0.2537 # 0 = LE + dist_from_wingskin, 1 = TE - dist_from_wingskin
        self.frac_pos_chord_max = 0.85 # See above
        self.frac_pos_along_span_inboard = 0.1753
        self.frac_pos_along_span_outboard = 0.7802
        self.fuel_tank_wing_volume = None # calculated by subsystems.structures.vspfunctions.calculate_fuel_capacity()
        self.t = None
        self.density_kgm3 = 800 # kg/m^3, density of Jet A1 fuel

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))
    

class MaterialsParameters():
    def __init__(self):
        # Open VSP materials library is used to get the material properties
        file_path =  "materials_library.toml"
        with open(file_path, 'r') as f:
            data = toml.load(f)
        
        # Load materials data from the TOML file
        materials_data = data["materials"]

        # Set the material name to DESIRED material
        self.material_name = "Aluminium_7075_T6_wrought"

        for mat_id, mat in materials_data.items():
            if mat["name"].lower() == self.material_name.lower():
                self.material = mat

        # Get material properties
        self.material_code = self.material["code"]                                  # Material code
        self.material_density = self.material["density"]                            # Density in kg/m^3
        self.material_E = self.material["E"]                                        # Young's Modulus in GPa
        self.material_G = self.material["G"]                                        # Shear Modulus in GPa
        self.material_price_kg = self.material["price_per_kg"]                      # Price per kg in EUR 
        self.material_sigma_yield = self.material["sigma_yield"]                    # Yield Strenght MPa
        self.material_sigma_ult = self.material["sigma_ult"]                        # Ultimate Strenght MPa
        self.material_tau_max = self.material["tau_max"]                            # Shear Strenght MPa
        self.material_max_service_temp = self.material["max_service_temp"]          # Celsius degrees
        self.material_min_service_temp = self.material["min_service_temp"]          # Celsius degrees
        self.material_fracture_tough = self.material["fracture_tough"]              # MPa*m^0.5
        self.material_thermal_shock_resist = self.material["thermal_shock_resist"]  # Celsius degrees
        self.material_recycle = self.material["recycle"]                            # 1->yes 0->no
        self.material_co2_eq = self.material["co2_eq"]                                    # kg/kg

    def __repr__(self):
        """
        Provides a developer-friendly string representation of the WingParameters object.
        """
        attrs = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(attrs, indent=4, default=lambda o: str(o))

class StructuresResults():
    def __init__(self, parent):
        self.parent = parent
        self.W_Wing = parent.weight.W_wing
        self.x_bending_distribution = None
        self.z_bending_distribution = None
        self.twist_distribution = None
        self.max_displacement_x = None
        self.max_displacement_z = None
        self.max_twist_angle = None
        self.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround = []
        self.should_increase_sparcap_thickness_by_30_percent_in_nextround = False
        self.should_increase_sparweb_thickness_by_30_percent_in_nextround = False
        self.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround = []
        self.should_increase_sparcap_thickness_by_10_percent_in_nextround = False
        self.should_increase_sparweb_thickness_by_10_percent_in_nextround = False
        self.should_increase_wingskin_thickness_by_10_percent_in_nextround = False

    def update_wing_structure(self):
        for stringer in self.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround:
            self.parent.wing.wingsection.stringers[stringer]["crosssectionalarea_mm2"] *= 1.14
            self.parent.wing.wingsection.stringers[stringer]['area_moment_of_inertia_m4'] *= 1.14
            if stringer in self.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround:
                self.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround.remove(stringer)
        for stringer in self.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround:
            self.parent.wing.wingsection.stringers[stringer]["crosssectionalarea_mm2"] *= 1.05
            self.parent.wing.wingsection.stringers[stringer]['area_moment_of_inertia_m4'] *= 1.05
        if self.should_increase_sparcap_thickness_by_30_percent_in_nextround:
            self.parent.wing.wingsection.spars['Spar1']['t_flange_1_mm'] *= 1.3
            self.parent.wing.wingsection.spars['Spar1']['t_flange_2_mm'] *= 1.3
            self.parent.wing.wingsection.spars['Spar2']['t_flange_1_mm'] *= 1.3
            self.parent.wing.wingsection.spars['Spar2']['t_flange_2_mm'] *= 1.3
        elif self.should_increase_sparcap_thickness_by_10_percent_in_nextround:
            self.parent.wing.wingsection.spars['Spar1']['t_flange_1_mm'] *= 1.1
            self.parent.wing.wingsection.spars['Spar1']['t_flange_2_mm'] *= 1.1
            self.parent.wing.wingsection.spars['Spar2']['t_flange_1_mm'] *= 1.1
            self.parent.wing.wingsection.spars['Spar2']['t_flange_2_mm'] *= 1.1
        if self.should_increase_sparweb_thickness_by_30_percent_in_nextround:
            self.parent.wing.wingsection.spars['Spar1']['t_web_mm'] *= 1.3
            self.parent.wing.wingsection.spars['Spar2']['t_web_mm'] *= 1.3
        elif self.should_increase_sparweb_thickness_by_10_percent_in_nextround:
            self.parent.wing.wingsection.spars['Spar1']['t_web_mm'] *= 1.1
            self.parent.wing.wingsection.spars['Spar2']['t_web_mm'] *= 1.1
        if  self.should_increase_wingskin_thickness_by_10_percent_in_nextround:
            self.parent.wing.wingsection.wingskin['thicness'] * 1.1

        self.this_stringer_should_increase_stringer_AtimesI_by_30_percent_in_nextround = []
        self.should_increase_sparcap_thickness_by_30_percent_in_nextround = False
        self.should_increase_sparweb_thickness_by_30_percent_in_nextround = False
        self.this_stringer_should_increase_stringer_AtimesI_by_10_percent_in_nextround = []
        self.should_increase_sparcap_thickness_by_10_percent_in_nextround = False
        self.should_increase_sparweb_thickness_by_10_percent_in_nextround = False
        self.should_increase_wingskin_thickness_by_10_percent_in_nextround = False

class VSPparameters():
    def __init (self):
        self.x_cg_vsp = 5.567
        self.y_cg_vsp = 0
        self.z_cg_vsp = 0.111
    
    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
