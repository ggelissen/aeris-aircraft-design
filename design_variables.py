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
        self.stall_speed_clean = None
        self.stall_speed_land = None
        self.cruise_altitude = None
        self.take_off_distance = None
        self.landing_distance = None

        # Subsystem Parameters
        self.performance = PerformanceParameters()
        self.wing = WingParameters()
        self.fuselage = FuselageParameters()
        self.engine = EngineParameters()
        self.empennage = EmpennageParameters()
        self.landing_gear = LandingGearParameters()

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
        self.stall_speed_clean = config.get('stall_speed_clean')
        self.stall_speed_land = config.get('stall_speed_land')
        self.cruise_altitude = config.get('cruise_altitude')
        self.take_off_distance = config.get('take_off_distance')
        self.landing_distance = config.get('landing_distance')

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
        print(f"Updated {parameter_name} to {value}")]

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
    

class WingParameters:
    def __init__(self):
        self.



class AERIS:
    """
    Class that contains all design parameters for the AERIS aircraft.
    """
    def __init__(self):

        # Mission Parameters
        self.R = 6500e3                             # Range in m
        self.V_cruise = 240                         # Cruise Speed in m/s
        self.V_s_clean = 100                        # Stall Speed in kts
        self.V_s_land = 85                          # Landing Speed in kts
        self.h_cruise = 12100                       # Cruise Altitude in m
        self.S_TO = 1500                            # Take-Off Distance in m
        self.S_L = 1200                             # Landing Distance in m


        # Performance Parameters
        self.c = 20                                 # Climb Rate in m/s
        self.c_alt = 0                              # Climb Rate Altitude in m

        self.c_V_AEO = 0.2                          # Climb Gradient AEO
        self.c_V_OEI = 0.024                        # Climb Gradient OEI
        self.c_V_AEO_alt = 0                        # Climb Gradient AEO Altitude in ft
        self.c_V_OEI_alt = 35                       # Climb Gradient OEI Altitude in ft
        self.delta_CD0_OEI = 0.005                  # Zero-Lift Drag Coefficient Differential AEO


        # Parameters obtained from preliminary sizing
        self.W_TO = 30787.8                         # Maximum Take-Off Weight (MTOW) in N
        self.W_OE = 11973.3                         # Operational Empty Weight (OEW) in N
        self.W_F = 12930.5                          # Total Fuel weight in N
        self.W_PL = 5884                            # Maximum Payload weight in N
        self.W_S = 2563                             # Wing Loading in N/m^2
        self.T_W = 0.369                            # Thrust-to-Weight ratio in N/N
        self.C_L_max = ... # TODO                   # Maximum Lift Coefficient at Cruise
        self.C_L_max_TO = 1.6                       # Maximum Lift Coefficient at Take-Off  
        self.C_L_max_L = 1.8                        # Maximum Lift Coefficient at Landing


        # Wing Parameters
        self.S_w = self.W_TO / self.W_S               # Wing Area in m^2
        self.A_w = 9.0                                # Aspect Ratio
        self.b_w = m.sqrt(self.A * self.S)            # Wing Span in m
        self.mac = self.S / self.b                  # Mean Aerodynamic Chord in m
        self.lambda_w = ... # TODO                  # Wing Taper Ratio
        self.Lambda_w = ... # TODO                  # Wing Sweep Angle in degrees
        self.t_c_w_r = ...    # TODO                # Wing Thickness-to-Chord Ratio at Root
        self.t_c_w_t = ...    # TODO                # Wing Thickness-to-Chord Ratio at Tip
        self.tau_w = self.t_c_w_t / self.t_c_w_r    # Wing Thickness-to-Chord Ratio Gradient
        self.airfoil_w = 'NACA 0012' # TODO         # Wing Airfoil Type
        self.i_w = ... # TODO                       # Wing Incidence Angle in degrees
        self.epsilon_t = ... # TODO                 # Wing Twist Angle in degrees
        self.Gamma_w = ... # TODO                   # Wing Dihedral Angle in degrees


        # Propulsion Parameters
        self.N_engines = 1                          # Number of Engines
        self.T_TO = self.T_W * self.W_TO            # Thrust at Take-Off in N
        self.cruise_thrust_setting = 0.9            # Thrust setting for cruise


        # Fuselage Parameters
        self.D_f = ... # TODO                       # Fuselage Diameter in m
        self.l_f = ... # TODO                       # Fuselage Length in m
        self.lf_df = self.l_f / self.D_f            # Fuselage Length-to-Diameter Ratio
        self.l_n = ... # TODO                       # Nose Length in m


        # Engine Parameters
        self.engine_weight = 234.1 * 9.81           # Engine Weight in N
        self.engine_max_thrust = 13.34e3            # Engine Maximum Thrust in N
        self.engine_length = 1.58                   # Engine Length in m
        self.engine_diameter = 0.80                 # Engine Diameter in m


        # Empennage Parameters
        self.S_h = ... # TODO                       # Horizontal Stabilizer Area in m^2
        self.S_v = ... # TODO                       # Vertical Stabilizer Area in m^2
        self.S_t = ... # TODO                       # Total Stabilizer Area in m^2
        self.Gamma_h = np.arctan2(self.S_v, self.S_h) # Butterfly Angle in radians
        self.x_t = ... # TODO                       # V-Tail Position in m
        self.V_t = ... # TODO                       # V-Tail Volume Coefficient
        self.i_t = ... # TODO                       # V-Tail Incidence Angle in degrees
        self.A_t = ... # TODO                       # V-Tail Aspect Ratio
        self.Lambda_t_025c = ... # TODO             # V-Tail Quarter-Chord Sweep Angle in degrees
        self.lambda_t = ... # TODO                  # V-Tail Taper Ratio
        self.t_c_t = ... # TODO                     # V-Tail Thickness-to-Chord Ratio
        self.airfoil_t = 'NACA 0012' # TODO         # V-Tail Airfoil Type

        
        # Landing Gear Parameters
        self.n_mlg = 2                              # Number of Main Landing Gear Units
        self.n_nlg = 1                              # Number of Nose Landing Gear Units
        self.D_mlg = ... # TODO                     # Main Landing Gear Diameter in m
        self.D_nlg = ... # TODO                     # Nose Landing Gear Diameter in m
        self.b_mlg = ... # TODO                     # Main Landing Gear Track in m
        self.b_nlg = ... # TODO                     # Nose Landing Gear Track in m
        self.l_mlg = ... # TODO                     # Main Landing Gear Length in m
        self.l_nlg = ... # TODO                     # Nose Landing Gear Length in m
        self.psi_mlg = ... # TODO                   # Main Landing Gear Pressure in psi
        self.psi_nlg = ... # TODO                   # Nose Landing Gear Pressure in psi


    def calculate_wing_fuel_volume(self):
        """
        Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
        Calculate the wing fuel volume based on the wing planform dimensions and thickness-to-chord ratio. (accuracy: +/- 10%)
        """
        V_WF = 0.54 * (self.S**2 / self.b) * self.t_c_w_r * ((1 + self.lambda_w * self.tau_w**0.5 + self.lambda_w**2 * self.tau_w) / (1 + self.lambda_w**2))
        return V_WF
    
    def calculate_landing_gear_loading(self):
        """
        Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
        Calculate the landing gear loading based on the maximum take-off weight and the number of landing gear units.
        """
        P_nlg = (self.W_TO * self.l_mlg) / (self.n_nlg * (self.l_mlg + self.l_nlg))
        P_mlg = (self.W_TO * self.l_nlg) / (self.n_mlg * (self.l_mlg + self.l_nlg))
        return P_nlg, P_mlg

    def calculate_total_wetted_area(self):
        """
        Source: Roskam - Airplane Design Part II: Preliminary Configuration Design and Integration of the Propulsion System, 2003.
        Calculate the total wetted area based on the wing area, fuselage area, and empennage area.
        """
        S_exp_w = self.S_w - (self.c_w_r * self.D_f)

        S_wet_w = 2 * S_exp_w * (1 + 0.25 * self.t_c_w_r * (1 + self.tau_w * self.lambda_w) / (1 + self.lamda_w))
        S_wet_t = 2 * self.S_t * (1 + 0.25 * self.t_c_t * (1 + self.lambda_t) / (1 + self.lambda_t))
        S_wet_fus = np.pi * self.D_f * self.l_f * (0.5 + 0.135 * self.l_n / self.l_f)**(2/3) * (1.015 + 0.3 / (self.lf_df**1.5))
        S_wet_nac = ... # TODO

        return S_wet_w + S_wet_t + S_wet_fus + S_wet_nac