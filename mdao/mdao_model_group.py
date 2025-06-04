# your_aircraft_project/mdao_framework/aircraft_model_v2.py
import openmdao.api as om
from .components_v2 import (WingGeom, FuselageGeom, EmpennageGeom, PropulsionSys,
                            AeroCoeffs, WeightBuildUp, MissionPerformance, CruisePerformance,
                            TakeOffLandingPerformance)
# Constants
N_PER_KG = 9.80665

class AircraftModel(om.Group):
    """Assembles aircraft components based on user's DesignParameters structure."""

    def initialize(self):
        # Declare options that can be passed when instantiating AircraftModel
        # These are typically fixed parameters for a given optimization run.
        self.options.declare('target_range_m', default=3500e3, types=float, units='m')
        self.options.declare('cruise_mach_target', default=0.78, types=float)
        self.options.declare('cruise_altitude_m', default=11000.0, types=float, units='m')
        self.options.declare('max_payload_N', default=58840.0, types=float, units='N') # e.g. 6000 kg * g
        self.options.declare('crew_weight_N', default=1600.0, types=float, units='N') # e.g. 2 crew * 80kg * g
        self.options.declare('num_engines', default=2, types=int)
        self.options.declare('oswald_efficiency', default=0.8, types=float)
        self.options.declare('CL_max_clean', default=1.6, types=float)
        self.options.declare('CL_max_TO', default=1.9, types=float)
        self.options.declare('CL_max_LAND', default=2.2, types=float)
        self.options.declare('engine_cruise_tsfc_kg_Ns', default=1.6e-5, types=float, units='kg/(N*s)')
        self.options.declare('max_load_factor', default=3.5, types=float)
        self.options.declare('rho_SL_kg_m3', default=1.225, types=float, units='kg/m**3')
        # For reserve fuel calculation
        self.options.declare('diversion_range_m', default=200 * 1852.0, types=float, units='m') # 200 nm
        self.options.declare('loiter_time_s', default=30 * 60.0, types=float, units='s') # 30 min
        self.options.declare('L_D_loiter_reserve', default=17.0, types=float) # L/D for reserve loiter


    def setup(self):
        # --- Independent Variables (Design Variables will be added by the driver) ---
        # We can use an IndepVarComp to hold DVs and other fixed inputs if not promoted directly.
        # For now, DVs will be added to the model directly in the run script.
        # Fixed inputs that are passed as options to components:
        
        # Get cruise air density and speed of sound from altitude and Mach
        # This could be a component itself (Atmosphere model)
        # Simplified: use ISA model for density at cruise_altitude_m
        # T = T0 - L*h; p = p0 * (T/T0)^(-g0/(L*R)); rho = p/(R*T)
        # T0 = 288.15 K, p0 = 101325 Pa, L = 0.0065 K/m, R=287.05 J/kgK, g0=9.80665
        h_cruise = self.options['cruise_altitude_m']
        if h_cruise <= 11000.0: # Troposphere
            T_cruise = 288.15 - 0.0065 * h_cruise
            rho_cruise = 1.225 * (T_cruise / 288.15)**(N_PER_KG / (287.05 * 0.0065) - 1.0)
        else: # Lower Stratosphere (isothermal up to 20km)
            T_cruise = 216.65 # -56.5 C
            rho_cruise = 0.36391 * math.exp(- (N_PER_KG / (287.05 * T_cruise)) * (h_cruise - 11000.0))
        
        speed_of_sound_cruise = math.sqrt(1.4 * 287.05 * T_cruise) # gamma=1.4, R=287.05
        cruise_speed_mps_calc = self.options['cruise_mach_target'] * speed_of_sound_cruise

        # --- Add Subsystems (Components) ---
        # Promote inputs that are common DVs or top-level parameters for clarity
        # The DVs (W_S, A_w, T_W, Lambda_025c_w, l_f) will be connected from the top level.
        
        self.add_subsystem('winggeom', WingGeom(),
                           promotes_inputs=['weight_W_TO', 'weight_W_S', 'wing_A_w', 
                                            'wing_lambda_w', 'wing_Lambda_025c_w', 'fuselage_l_f'])
        
        self.add_subsystem('fusegeom', FuselageGeom(),
                           promotes_inputs=['fuselage_l_f'])

        self.add_subsystem('empgeom', EmpennageGeom(),
                           promotes_inputs=['fuselage_l_f', 'emp_V_h', 'emp_A_h', 'emp_V_v', 'emp_A_v'])
        
        self.add_subsystem('propsys', PropulsionSys(engine_N_engines=self.options['num_engines']),
                           promotes_inputs=['weight_W_TO', 'weight_T_W', 
                                            'engine_diameter_per', 'engine_length_per'])
        
        self.add_subsystem('aerocoeffs', AeroCoeffs(cruise_mach=self.options['cruise_mach_target'],
                                                    perf_e_oswald=self.options['oswald_efficiency'],
                                                    perf_CL_max_clean=self.options['CL_max_clean']))
        
        self.add_subsystem('weightest', WeightBuildUp(max_load_factor=self.options['max_load_factor'],
                                                      cruise_mach=self.options['cruise_mach_target'],
                                                      weight_W_PL=self.options['max_payload_N'],
                                                      weight_W_crew=self.options['crew_weight_N'],
                                                      engine_N_engines=self.options['num_engines']))
                                                      # W_TO_guess will be connected from W_TO (implicit loop)

        # MissionPerformance calculates W_TO needed for the mission.
        # This W_TO is the primary objective or a key variable in an outer loop/solver.
        # For now, we'll connect the 'calculated_W_TO' from MissionPerformance
        # back to 'weight_W_TO' for other components. This creates an algebraic loop
        # that OpenMDAO's NewtonSolver can handle.
        self.add_subsystem('missionperf', MissionPerformance(target_range_m=self.options['target_range_m'],
                                                             cruise_speed_mps=cruise_speed_mps_calc,
                                                             engine_cruise_tsfc_kg_Ns=self.options['engine_cruise_tsfc_kg_Ns'],
                                                             diversion_range_m=self.options['diversion_range_m'],
                                                             loiter_time_s=self.options['loiter_time_s'],
                                                             aero_L_D_loiter=self.options['L_D_loiter_reserve'],
                                                             weight_W_PL=self.options['max_payload_N']))

        self.add_subsystem('cruiseperf', CruisePerformance(cruise_density_kg_m3=rho_cruise,
                                                           cruise_speed_mps=cruise_speed_mps_calc,
                                                           cruise_altitude_m=self.options['cruise_altitude_m']))
        
        self.add_subsystem('toflperf', TakeOffLandingPerformance(perf_CL_max_TO=self.options['CL_max_TO'],
                                                                 perf_CL_max_LAND=self.options['CL_max_LAND'],
                                                                 rho_SL_kg_m3=self.options['rho_SL_kg_m3']))

        # --- Connections ---
        # Wing Geometry outputs
        self.connect('winggeom.wing_S_w', ['empgeom.wing_S_w', 'aerocoeffs.wing_S_w', 
                                           'weightest.wing_S_w', 'cruiseperf.wing_S_w', 'toflperf.wing_S_w'])
        self.connect('winggeom.wing_b_w', ['empgeom.wing_b_w', 'weightest.wing_b_w'])
        self.connect('winggeom.wing_mac_w', 'empgeom.wing_mac_w')
        self.connect('winggeom.wing_A_w', ['aerocoeffs.wing_A_w', 'weightest.wing_A_w']) # A_w is also a DV input to winggeom
        self.connect('winggeom.wing_Lambda_025c_w', ['aerocoeffs.wing_Lambda_025c_w', 'weightest.wing_Lambda_025c_w']) # Also a DV

        # Fuselage Geometry outputs
        self.connect('fusegeom.fuselage_wetted_area', 'aerocoeffs.fuselage_wetted_area')
        self.connect('fusegeom.fuselage_fineness_ratio', 'aerocoeffs.fuselage_fineness_ratio')
        self.connect('fusegeom.fuselage_max_diameter', 'weightest.fuselage_max_diameter')
        # fuselage_l_f is a DV, connected directly to weightest.fuselage_l_f if needed

        # Empennage Geometry outputs
        self.connect('empgeom.emp_S_h', 'weightest.emp_S_h')
        self.connect('empgeom.emp_S_v', 'weightest.emp_S_v')
        self.connect('empgeom.emp_wetted_area_h', 'aerocoeffs.emp_wetted_area_h')
        self.connect('empgeom.emp_wetted_area_v', 'aerocoeffs.emp_wetted_area_v')

        # Propulsion System outputs
        self.connect('propsys.engine_T_TO_total', ['cruiseperf.engine_T_TO_total', 'toflperf.engine_T_TO_total'])
        self.connect('propsys.engine_T_TO_per_engine', 'weightest.engine_T_TO_per_engine')
        self.connect('propsys.engine_nacelle_wetted_area_total', 'aerocoeffs.engine_nacelle_wetted_area_total')

        # AeroCoeffs outputs
        self.connect('aerocoeffs.aero_CD0', 'cruiseperf.aero_CD0')
        self.connect('aerocoeffs.aero_K_drag', 'cruiseperf.aero_K_drag')
        self.connect('aerocoeffs.aero_L_D_max', 'missionperf.aero_L_D_cruise') # Use L/D_max for cruise L/D estimate

        # WeightBuildUp outputs
        self.connect('weightest.weight_W_OE_calc', 'missionperf.weight_W_OE_calc')
        # W_TO is tricky: MissionPerformance calculates a W_TO required for the mission.
        # This calculated W_TO should ideally match the W_TO used for component sizing.
        # This forms an algebraic loop.
        self.connect('missionperf.calculated_W_TO', ['weight_W_TO', # Promoted input for winggeom, propsys
                                                     'weightest.weight_W_TO_guess', # For empirical weight equations
                                                     'cruiseperf.calculated_W_TO',
                                                     'toflperf.weight_W_TO'])
        
        # MissionPerformance outputs for cruise
        self.connect('missionperf.weight_W_F_used_mission', 'cruiseperf.weight_W_F_used_mission')

        # Promote key objective and constraint variables
        self.promotes('missionperf', outputs=['calculated_W_TO', 'range_constraint', 'achieved_range_m'])
        self.promotes('cruiseperf', outputs=['lift_equals_weight_constraint', 'thrust_equals_drag_constraint', 
                                             'cruise_CL', 'cruise_L_D'])
        self.promotes('toflperf', outputs=['take_off_distance_calc_m', 'landing_distance_calc_m', 
                                           'stall_speed_TO_mps', 'stall_speed_LAND_mps'])
        
        # Setup a non-linear solver for the implicit W_TO loop
        self.nonlinear_solver = om.NewtonSolver(solve_subsystems=True, maxiter=20, iprint=0, atol=1e-5, rtol=1e-5)
        self.linear_solver = om.DirectSolver() # Can use om.PETScKrylov() for larger problems

        # If W_TO is an explicit DV, then missionperf.calculated_W_TO would be a constraint (e.g., calculated_W_TO - DV_W_TO = 0)
        # Or, W_TO is an output of a BalanceComp that drives W_F_capacity to meet range.
        # The current setup sizes W_TO for the mission.
