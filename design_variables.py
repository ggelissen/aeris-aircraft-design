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
        self.take_off_distance = None
        self.landing_distance = None
        self.diversion_distance = None
        self.loiter_time = None
        self.max_eq_velocity = None
        self.max_load_factor = None 
        self.crit_mach = None
        

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
        self.take_off_distance = config.get('takeoff_distance')
        self.landing_distance = config.get('landing_distance')
        self.diversion_distance = config.get('diversion_distance')
        self.loiter_time = config.get('loiter_time')
        self.max_eq_velocity = config.get('max_eq_velocity') 
        self.max_load_factor = config.get('max_load_factor')
        self.crit_mach = config.get('crit_mach')

        # Load subsystem parameters
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
        self.W_OE = 11973.3                         # Operational Empty Weight (OEW) in N
        self.W_F = 12930.5                          # Total Fuel weight in N
        self.W_PL = 5884                            # Maximum Payload weight in N
        self.W_S = 2563                             # Wing Loading in N/m^2
        self.T_W = 0.369                            # Thrust-to-Weight ratio in N/N
        self.M_ff = 0.5793                        # Maximum Fuel Fraction

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
        self.S_w = W_TO / W_S                       # Wing Area in m^2
        self.A_w = 9.0                             # Aspect Ratio
        if self.S_w is not None and self.A_w is not None:
            self.b_w = m.sqrt(self.A_w * self.S_w)  # Wing Span in m
        self.mac = 1.2824                            # Mean Aerodynamic Chord in m
        self.y_LEMAC = 2.1016                       # y-position of Leading Edge of MAC in m
        self.lambda_w = 0.2703                        # Wing Taper Ratio
        self.Lambda_w = None                        # Wing Sweep Angle in degrees
        self.Lambda_w_quarter = 0.6487 # 37.1673 degrees        # Wing quarter-Chord Sweep Angle in radians
        self.max_t_c_w = 0.1438
        self.t_c_w_r = 0.12        #PLACEHOLDER                 # Wing Thickness-to-Chord Ratio at Root
        self.t_c_w_t = 0.12        #PLACEHOLDER             # Wing Thickness-to-Chord Ratio at Tip
        if self.t_c_w_r is not None and self.t_c_w_t is not None:
            self.tau_w = self.t_c_w_t / self.t_c_w_r    # Wing Thickness-to-Chord Ratio Gradient
        self.airfoil_w = None                       # Wing Airfoil Type
        self.i_w = None                             # Wing Incidence Angle in degrees
        self.epsilon_t = None                       # Wing Twist Angle in degrees
        self.Gamma_w = 0.0175                         # Wing Dihedral Angle in radians
        self.root_chord = 1.819  # Wing Root Chord in m
        self.tip_chord = 0.4916  # Wing Tip Chord in m
        self.t_r = self.t_c_w_r * self.root_chord                           # Wing Root Thickness in m

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

        self.CL_max_TO = None                       # Maximum Lift Coefficient at Take-Off
        self.CL_max_L = None                        # Maximum Lift Coefficient at Landing
        self.CL_max_cruise = None                   # Maximum Lift Coefficient at Cruise

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
        self.D_f = 1.5 #placeholder                             # Fuselage Diameter in m
        self.l_f = 10 #PLACEHOLDER!!!!!                             # Fuselage Length in m
        if self.D_f is not None and self.l_f is not None:
            self.lf_df = self.l_f / self.D_f        # Fuselage Length-to-Diameter Ratio
        self.l_n = 2 #placeholder                             # Nose Length in m

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
        self.N_engines = 1                          # Number of Engines
        self.T_TO = T_W * W_TO                      # Thrust at Take-Off in N
        self.cruise_thrust_setting = None           # Thrust setting for cruise
        self.engine_weight =   None                 # Engine Weight in N
        self.engine_max_thrust = None               # Engine Maximum Thrust in N
        self.engine_length = None                   # Engine Length in m
        self.engine_diameter = None                 # Engine Diameter in m
        self.cruise_tsfc = None                     # Thrust Specific Fuel Consumption at Cruise in kg/N/h
        self.take_off_tsfc = None                   # Thrust Specific Fuel Consumption at Take-Off in kg/N/h

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
        self.S_h =    1.39                          # Horizontal Stabilizer Area in m^2
        self.S_v =   2.16                          # Vertical Stabilizer Area in m^2
        self.S_t = None                             # Total Stabilizer Area in m^2
        if self.S_h is not None and self.S_v is not None:
            self.Gamma_h = np.arctan2(self.S_v, self.S_h) # Butterfly Angle in radians
        self.x_t = None                             # V-Tail Position in m
        self.V_h = 0.7 #estimation                             # V-Tail Volume Coefficient
        self.V_v = 0.05 #estimation                             # Horizontal Stabilizer Volume Coefficient
        self.i_t = None                             # V-Tail Incidence Angle in degrees
        self.A_t = None                             # V-Tail Aspect Ratio
        self.Lambda_t_025c = None                   # V-Tail Quarter-Chord Sweep Angle in degrees
        self.lambda_t = None                        # V-Tail Taper Ratio
        self.t_c_t = None                           # V-Tail Thickness-to-Chord Ratio
        self.airfoil_t = None                       # V-Tail Airfoil Type
        self.vtail_dihedral = 110 #placeholder                  # V-Tail Dihedral Angle in radians
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
        self.S_a = 2 #placeholder!!                             # Control Surface Area in m^2
        self.x_a = None                             # Control Surface Position in m
        self.delta_a = None                         # Control Surface Deflection Angle in degrees
        self.C_m_a = None                           # Control Surface Moment Coefficient

    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

class CGParameters:
    """
    Class to hold center of gravity (CG) related parameters for the aircraft design.
    Append more parameters as needed.
    """
    def __init__(self):
        self.x_cg_wing = 5                       # CG Position of the Wing in m
        self.x_cg_fuselage = 4                   # CG Position of the Fuselage in m
        self.x_cg_landing_gear = 5               # CG Position of the Landing Gear in m
        self.x_cg_empennage = 9                  # CG Position of the Empennage in m
        self.x_cg_fixed_equipment = 3            # CG Position of the Fixed Equipment in m
        self.x_cg_propulsion = 7                 # CG Position of the Propulsion System in m
        self.x_cg_payload = 3                    # CG Position of the Payload in m
        self.x_cg_fuel = 5                       # CG Position of the Fuel in m


    def load_from_dict(self, param_dict):
        for key, value in param_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
