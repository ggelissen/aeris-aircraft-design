import numpy as np
import openmdao.api as om
import math

# Conversion constant
N_PER_KG = 9.80665  # Standard gravity

# --- Geometry Related Components ---
class WingGeom(om.ExplicitComponent):
    """Calculates basic wing geometry based on W_TO, W_S, A_w, taper, sweep."""
    def setup(self):
        self.add_input('weight_W_TO', val=30787.8, units='N', desc='Max Takeoff Weight')
        self.add_input('weight_W_S', val=2563.0, units='N/m**2', desc='Wing Loading')
        self.add_input('wing_A_w', val=9.0, desc='Wing Aspect Ratio')
        self.add_input('wing_lambda_w', val=0.35, desc='Wing Taper Ratio (c_tip/c_root)')
        self.add_input('wing_Lambda_025c_w', val=math.radians(25.0), units='rad', desc='Wing Quarter-Chord Sweep')
        self.add_input('fuselage_l_f', val=12.0, units='m', desc='Fuselage length, for x_LEMAC estimate')


        self.add_output('wing_S_w', val=12.0, units='m**2', desc='Wing Reference Area')
        self.add_output('wing_b_w', val=10.0, units='m', desc='Wing Span')
        self.add_output('wing_mac_w', val=1.3, units='m', desc='Wing Mean Aerodynamic Chord')
        self.add_output('wing_root_chord_w', val=1.8, units='m', desc='Wing Root Chord')
        self.add_output('wing_tip_chord_w', val=0.5, units='m', desc='Wing Tip Chord')
        self.add_output('wing_x_LEMAC_w', val=4.8, units='m', desc='x-location of Wing LEMAC')
        self.add_output('wing_y_LEMAC_w', val=2.0, units='m', desc='y-location of Wing LEMAC')
        self.add_output('wing_Lambda_LE_w', val=math.radians(28.0), units='rad', desc='Wing Leading Edge Sweep')


    def compute(self, inputs, outputs):
        W_TO = inputs['weight_W_TO']
        W_S = inputs['weight_W_S']
        A_w = inputs['wing_A_w']
        lambda_w = inputs['wing_lambda_w']
        Lambda_025c_w = inputs['wing_Lambda_025c_w']
        l_f = inputs['fuselage_l_f']

        if W_S > 1e-6:
            S_w = W_TO / W_S
        else:
            S_w = 0.0
        outputs['wing_S_w'] = S_w

        if S_w > 0 and A_w > 1e-6:
            b_w = math.sqrt(A_w * S_w)
        else:
            b_w = 0.0
        outputs['wing_b_w'] = b_w

        if b_w > 1e-6 and (1 + lambda_w) > 1e-6:
            c_r = (2 * S_w) / (b_w * (1 + lambda_w))
            c_t = lambda_w * c_r
        else:
            c_r = 0.0
            c_t = 0.0
        outputs['wing_root_chord_w'] = c_r
        outputs['wing_tip_chord_w'] = c_t

        if c_r > 0 and (1 + lambda_w) > 1e-6 : # Ensure c_r is positive for MAC calculation
            mac_w = (2.0/3.0) * c_r * (1 + lambda_w + lambda_w**2) / (1 + lambda_w)
            y_LEMAC = (b_w / 6.0) * (1 + 2*lambda_w) / (1 + lambda_w)
        else:
            mac_w = 0.0
            y_LEMAC = 0.0
        outputs['wing_mac_w'] = mac_w
        outputs['wing_y_LEMAC_w'] = y_LEMAC
        
        # Estimate x_LEMAC as a fraction of fuselage length (can be refined or made a DV)
        outputs['wing_x_LEMAC_w'] = 0.40 * l_f 

        # Estimate LE sweep from 0.25c sweep
        if A_w > 1e-6 and (1 + lambda_w) > 1e-6:
            # tan(Lambda_LE) = tan(Lambda_qc) + (c_r / b_w) * ( (1-lambda_w)/(1+lambda_w) ) * (0.25 * 4 / A_w)
            # Simplified: term = (1-lambda_w) / (A_w * (1+lambda_w))
            # tan(Lambda_LE) = tan(Lambda_025c) + (1/A_w) * ( (c_r * (1-lambda_w)) / (b_w * (1+lambda_w)) ) * (4*0.25)
            # tan(Lambda_LE) = tan(Lambda_025c) + ( (root_chord * (1-lambda_w)) / ( A_w * b_w * (1+lambda_w) ) ) # This is not quite right
            # Using a common approximation related to sweep points:
            # tan(Lambda_LE) = tan(Lambda_0.25c) + (0.25 * c_r * (1-lambda_w)) / (b_w/2 * (1+lambda_w)) ... this is also complex
            # A simpler geometric relationship for straight tapered wings:
            # x_offset_tip_le_from_root_le = (b_w/2) * tan(Lambda_LE_w)
            # x_offset_tip_qc_from_root_qc = (b_w/2) * tan(Lambda_025c_w)
            # x_offset_tip_le_from_root_le = x_offset_tip_qc_from_root_qc - 0.25*c_t + 0.25*c_r
            # (b_w/2) * tan(Lambda_LE_w) = (b_w/2) * tan(Lambda_025c_w) + 0.25*(c_r - c_t)
            if b_w > 1e-6:
                 tan_Lambda_LE = math.tan(Lambda_025c_w) + (0.25 * (c_r - c_t)) / (b_w / 2.0)
                 outputs['wing_Lambda_LE_w'] = math.atan(tan_Lambda_LE)
            else:
                 outputs['wing_Lambda_LE_w'] = Lambda_025c_w
        else:
            outputs['wing_Lambda_LE_w'] = Lambda_025c_w


class FuselageGeom(om.ExplicitComponent):
    """Calculates basic fuselage geometry."""
    def setup(self):
        self.add_input('fuselage_l_f', val=12.0, units='m', desc='Fuselage Length')
        # More inputs could be max_diameter_to_length_ratio, cabin_length_frac, etc.
        self.add_output('fuselage_max_diameter', val=1.8, units='m', desc='Fuselage Max Diameter')
        self.add_output('fuselage_wetted_area', val=60.0, units='m**2', desc='Fuselage Wetted Area (Placeholder)')
        self.add_output('fuselage_fineness_ratio', val=6.67, desc='l_f / D_f')

    def compute(self, inputs, outputs):
        l_f = inputs['fuselage_l_f']
        # Placeholder calculations for diameter and wetted area
        # Max diameter could be a DV or related to l_f
        max_D = l_f / 6.5 # Example fineness ratio target
        outputs['fuselage_max_diameter'] = max_D
        # Wetted area approximation for a Sears-Haack body or similar
        outputs['fuselage_wetted_area'] = math.pi * max_D * l_f * 0.85 # Highly simplified
        if max_D > 1e-6:
            outputs['fuselage_fineness_ratio'] = l_f / max_D
        else:
            outputs['fuselage_fineness_ratio'] = 0


class EmpennageGeom(om.ExplicitComponent):
    """Sizes empennage surfaces based on volume coefficients."""
    def setup(self):
        self.add_input('fuselage_l_f', val=12.0, units='m', desc='Fuselage Length (for moment arm est.)')
        self.add_input('wing_S_w', val=12.0, units='m**2', desc='Wing Area')
        self.add_input('wing_mac_w', val=1.3, units='m', desc='Wing MAC')
        self.add_input('wing_b_w', val=10.0, units='m', desc='Wing Span')
        self.add_input('emp_V_h', val=0.8, desc='Horizontal Tail Volume Coefficient')
        self.add_input('emp_A_h', val=4.0, desc='HTP Aspect Ratio')
        self.add_input('emp_V_v', val=0.07, desc='Vertical Tail Volume Coefficient')
        self.add_input('emp_A_v', val=1.8, desc='VTP Aspect Ratio')
        # Add taper, sweep for HTP and VTP as inputs if they are DVs

        self.add_output('emp_S_h', val=2.5, units='m**2', desc='HTP Area')
        self.add_output('emp_l_h', val=5.0, units='m', desc='HTP Moment Arm (estimate)')
        self.add_output('emp_S_v', val=1.0, units='m**2', desc='VTP Area')
        self.add_output('emp_l_v', val=5.0, units='m', desc='VTP Moment Arm (estimate)')
        self.add_output('emp_wetted_area_h', val=5.0, units='m**2', desc='HTP Wetted Area (Placeholder)')
        self.add_output('emp_wetted_area_v', val=2.0, units='m**2', desc='VTP Wetted Area (Placeholder)')

    def compute(self, inputs, outputs):
        l_f = inputs['fuselage_l_f']
        S_w = inputs['wing_S_w']
        mac_w = inputs['wing_mac_w']
        b_w = inputs['wing_b_w']
        V_h = inputs['emp_V_h']
        A_h = inputs['emp_A_h'] # Used for wetted area est.
        V_v = inputs['emp_V_v']
        A_v = inputs['emp_A_v'] # Used for wetted area est.

        # Estimate moment arms (distance from aircraft CG to tail AC)
        # This is a major simplification; true l_h, l_v depend on aircraft CG.
        # For initial sizing, often taken as ~0.45-0.55 * l_f
        l_h_est = 0.5 * l_f
        l_v_est = 0.5 * l_f
        outputs['emp_l_h'] = l_h_est
        outputs['emp_l_v'] = l_v_est

        if S_w > 0 and mac_w > 0 and l_h_est > 1e-6:
            S_h = (V_h * S_w * mac_w) / l_h_est
        else:
            S_h = 0
        outputs['emp_S_h'] = S_h

        if S_w > 0 and b_w > 0 and l_v_est > 1e-6:
            S_v = (V_v * S_w * b_w) / l_v_est
        else:
            S_v = 0
        outputs['emp_S_v'] = S_v
        
        # Placeholder wetted area (approx 2*exposed area, but depends on thickness)
        outputs['emp_wetted_area_h'] = S_h * 2.05 
        outputs['emp_wetted_area_v'] = S_v * 2.05


# --- Propulsion System ---
class PropulsionSys(om.ExplicitComponent):
    """Calculates engine thrust and estimates nacelle drag."""
    def setup(self):
        self.add_input('weight_W_TO', val=30787.8, units='N', desc='Max Takeoff Weight')
        self.add_input('weight_T_W', val=0.369, desc='Thrust-to-Weight Ratio')
        self.add_input('engine_N_engines', val=1, desc='Number of Engines')
        self.add_input('engine_diameter_per', val=0.8, units='m', desc='Diameter per engine nacelle')
        self.add_input('engine_length_per', val=1.5, units='m', desc='Length per engine nacelle')

        self.add_output('engine_T_TO_total', val=11360.0, units='N', desc='Total Takeoff Thrust')
        self.add_output('engine_T_TO_per_engine', val=11360.0, units='N', desc='Takeoff Thrust per Engine')
        self.add_output('engine_nacelle_wetted_area_total', val=7.5, units='m**2', desc='Total Nacelle Wetted Area')
        # SFC will be an input for performance calculations later
        # self.add_output('engine_cruise_tsfc_kg_Ns', val=1.6e-5, units='kg/(N*s)')

    def compute(self, inputs, outputs):
        W_TO = inputs['weight_W_TO']
        T_W = inputs['weight_T_W']
        N_engines = inputs['engine_N_engines'] if inputs['engine_N_engines'] > 0 else 1
        dia_nac = inputs['engine_diameter_per']
        len_nac = inputs['engine_length_per']

        T_TO_total = W_TO * T_W
        outputs['engine_T_TO_total'] = T_TO_total
        outputs['engine_T_TO_per_engine'] = T_TO_total / N_engines
        
        # Nacelle wetted area (cylinder + cone approximations or more detailed)
        # S_nac_cyl = pi * D * L_cyl
        # S_nac_inlet_cone approx pi * D * L_inlet_cone_slant
        # S_nac_nozzle_cone approx pi * D_exit * L_nozzle_cone_slant
        # Simplified: assume it's like a cylinder for wetted area
        outputs['engine_nacelle_wetted_area_total'] = N_engines * (math.pi * dia_nac * len_nac) * 1.1 # Factor for complexity


# --- Aerodynamics ---
class AeroCoeffs(om.ExplicitComponent):
    """Estimates key aerodynamic coefficients."""
    def setup(self):
        # Inputs from geometry
        self.add_input('wing_S_w', val=12.0, units='m**2')
        self.add_input('wing_A_w', val=9.0)
        self.add_input('wing_Lambda_025c_w', val=math.radians(25.0), units='rad')
        self.add_input('wing_t_c_w_r', val=0.14, desc='Wing root t/c') # Used for wave drag est.
        self.add_input('fuselage_wetted_area', val=60.0, units='m**2')
        self.add_input('fuselage_fineness_ratio', val=6.67)
        self.add_input('emp_wetted_area_h', val=5.0, units='m**2')
        self.add_input('emp_wetted_area_v', val=2.0, units='m**2')
        self.add_input('engine_nacelle_wetted_area_total', val=7.5, units='m**2')
        # Inputs for cruise conditions
        self.add_input('cruise_mach', val=0.78)
        self.add_input('perf_e_oswald', val=0.8, desc='Oswald efficiency factor')
        self.add_input('perf_CL_max_clean', val=1.6, desc='Max lift coeff, clean config')


        self.add_output('aero_CL_alpha_3D', val=math.radians(5.0), units='1/rad', desc='Wing 3D Lift Curve Slope')
        self.add_output('aero_CD0', val=0.025, desc='Zero-Lift Drag Coefficient')
        self.add_output('aero_K_drag', val=0.04, desc='Induced Drag Factor (1/pi*A*e)')
        self.add_output('aero_L_D_max', val=15.0, desc='Max Lift-to-Drag Ratio')

    def compute(self, inputs, outputs):
        S_w = inputs['wing_S_w']
        A_w = inputs['wing_A_w']
        Lambda_025c_w_rad = inputs['wing_Lambda_025c_w']
        # M_cruise = inputs['cruise_mach']
        e_oswald = inputs['perf_e_oswald']

        # 3D Lift curve slope (Helmbold-Prandtl approximation)
        # CL_alpha_2D approx 2*pi for thin airfoils at low Mach
        cl_alpha_2d = 2 * math.pi / (1 + ( ( (2*math.pi * math.tan(Lambda_025c_w_rad)**2 ) / (A_w * math.sqrt(1-min(inputs['cruise_mach'],0.95)**2)) if (1-min(inputs['cruise_mach'],0.95)**2)>0 else float('inf') ) if A_w >0 else float('inf') ) ) # Simplified
        # Using a simpler approximation for CL_alpha_3D for now
        # Effective aspect ratio for sweep: Ae = A_w / cos(Lambda_eff)^2
        # CL_alpha_3D = cl_alpha_2d * A_w / (A_w + 2 * (1 + tau_factor) / cos(Lambda_eff))
        # DATCOM method or similar would be more accurate.
        # Simplified:
        if A_w > 0:
            beta_mach_sq = 1.0 - min(inputs['cruise_mach'], 0.98)**2 # Avoid M=1 issues
            beta_mach = math.sqrt(beta_mach_sq) if beta_mach_sq > 0 else 0.1
            CL_alpha_3D = (2 * math.pi * A_w) / (A_w + 2 * math.cos(Lambda_025c_w_rad) / beta_mach ) # Modified from Anderson
            # Ensure it's not excessively high or low
            CL_alpha_3D = min(max(CL_alpha_3D, 3.0), 6.0) # Heuristic bounds
        else:
            CL_alpha_3D = 0.0
        outputs['aero_CL_alpha_3D'] = CL_alpha_3D


        # CD0 estimation (Component buildup method - very simplified)
        # Cf = skin friction coefficient, depends on Reynolds number and Mach
        # Re_fus = rho * V * l_f / mu
        # For M=0.78 at 11km, Re ~ 30-50 million for a 10-20m aircraft
        Cf_turbulent = 0.003 # Typical for turbulent flow on smooth surface at high Re

        cd0_wing = Cf_turbulent * (inputs['wing_S_w'] * 2.05) / S_w # Assuming S_wet_wing ~ 2.05 * S_ref
        cd0_fuse = Cf_turbulent * inputs['fuselage_wetted_area'] / S_w
        cd0_emp_h = Cf_turbulent * inputs['emp_wetted_area_h'] / S_w
        cd0_emp_v = Cf_turbulent * inputs['emp_wetted_area_v'] / S_w
        cd0_nac = Cf_turbulent * inputs['engine_nacelle_wetted_area_total'] / S_w
        cd0_misc = 0.002 # For interference, leakage, protuberances, landing gear (if not fully clean)

        CD0 = cd0_wing + cd0_fuse + cd0_emp_h + cd0_emp_v + cd0_nac + cd0_misc
        # Add wave drag estimate if transonic (simplified)
        # if M_cruise > 0.7:
        #    CD_wave = 0.001 + 0.005 * (M_cruise - 0.7)**2 # Very rough
        #    CD0 += CD_wave
        outputs['aero_CD0'] = max(CD0, 0.015) # Ensure a minimum sensible CD0

        # Induced drag factor
        if A_w > 0 and e_oswald > 0:
            K_drag = 1.0 / (math.pi * A_w * e_oswald)
        else:
            K_drag = 0.1 # Penalty if A_w or e is zero
        outputs['aero_K_drag'] = K_drag
        
        if CD0 > 0 and K_drag > 0:
             # CL for max L/D = sqrt(CD0/K)
             CL_at_LDmax = math.sqrt(CD0 / K_drag)
             if CL_at_LDmax < inputs['perf_CL_max_clean']: # Ensure it's achievable
                 CD_at_LDmax = CD0 + K_drag * CL_at_LDmax**2
                 outputs['aero_L_D_max'] = CL_at_LDmax / CD_at_LDmax if CD_at_LDmax > 0 else 0.0
             else: # If CL for L/D max is too high, cap L/D at CL_max_clean
                 CD_at_CLmax_clean = CD0 + K_drag * inputs['perf_CL_max_clean']**2
                 outputs['aero_L_D_max'] = inputs['perf_CL_max_clean'] / CD_at_CLmax_clean if CD_at_CLmax_clean > 0 else 0.0
        else:
            outputs['aero_L_D_max'] = 0.0


# --- Weight Buildup ---
class WeightBuildUp(om.ExplicitComponent):
    """Estimates component weights and aggregates them."""
    def setup(self):
        # Inputs from geometry and systems
        self.add_input('wing_S_w', val=12.0, units='m**2')
        self.add_input('wing_b_w', val=10.0, units='m')
        self.add_input('wing_A_w', val=9.0)
        self.add_input('wing_t_c_w_r', val=0.14) # Root t/c
        self.add_input('wing_Lambda_025c_w', val=math.radians(25.0), units='rad')
        self.add_input('fuselage_l_f', val=12.0, units='m')
        self.add_input('fuselage_max_diameter', val=1.8, units='m')
        self.add_input('emp_S_h', val=2.5, units='m**2')
        self.add_input('emp_S_v', val=1.0, units='m**2')
        self.add_input('engine_T_TO_per_engine', val=11360.0, units='N')
        self.add_input('engine_N_engines', val=1)
        self.add_input('weight_W_TO_guess', val=30787.8, units='N', desc="Initial W_TO, used for some empirical weight equations")
        self.add_input('max_load_factor', val=3.5, desc="Ultimate load factor for structural sizing")
        self.add_input('cruise_mach', val=0.78)

        # Fixed weights (can be made inputs or options)
        self.add_input('weight_W_PL', val=5884.0, units='N', desc='Max Payload Weight')
        self.add_input('weight_W_crew', val=1600.0, units='N', desc='Crew Weight')
        
        # Outputs
        self.add_output('weight_W_wing', val=3000.0, units='N', desc='Wing Weight')
        self.add_output('weight_W_fuselage', val=4000.0, units='N', desc='Fuselage Weight')
        self.add_output('weight_W_empennage', val=500.0, units='N', desc='Empennage Weight (H+V)')
        self.add_output('weight_W_engine_sys', val=2000.0, units='N', desc='Engine System Weight (incl. nacelles)')
        self.add_output('weight_W_lg', val=1500.0, units='N', desc='Landing Gear Weight')
        self.add_output('weight_W_systems', val=3000.0, units='N', desc='Fixed Systems (avionics, etc.)')
        self.add_output('weight_W_OE_calc', val=14000.0, units='N', desc='Calculated Operational Empty Weight')
        # W_F (max fuel capacity) and W_TO will be handled by a solver or optimizer loop

    def compute(self, inputs, outputs):
        # Using simplified empirical weight equations (e.g., from Raymer, Torenbeek, Gudmundsson)
        # These are placeholders and should be replaced by detailed structural analysis or better statistical models.
        N_ult = inputs['max_load_factor'] # Ultimate load factor
        W_TO_guess_kg = inputs['weight_W_TO_guess'] / N_PER_KG
        S_w_m2 = inputs['wing_S_w']
        b_w_m = inputs['wing_b_w']
        A_w = inputs['wing_A_w']
        lambda_w = 0.35 # Assuming, not an input yet for this component
        Lambda_rad = inputs['wing_Lambda_025c_w']
        t_c_root = inputs['wing_t_c_w_r']
        
        # Wing Weight (Raymer simplified)
        # W_wing_lbs = 0.036 * S_w_ft^0.758 * W_zf_lbs^0.0035 * (A / cos(Lambda_qc)^2)^0.6 * q_psi^0.006 * lambda^0.04 * (100*tc_root)^-0.3 * (N_ult * W_dg_lbs)^0.49
        # Highly simplified for N:
        W_wing = 0.0050 * S_w_m2**0.7 * (W_TO_guess_kg * N_ult)**0.55 * A_w**0.65 * (b_w / (t_c_root * (S_w_m2/b_w_m)))**0.3 # Very rough
        W_wing_N = W_wing * N_PER_KG * 25 # Fudge factor
        outputs['weight_W_wing'] = max(W_wing_N, 0.10 * inputs['weight_W_TO_guess']) # Ensure sensible min

        # Fuselage Weight
        S_fuse_wet_m2 = inputs['fuselage_l_f'] * inputs['fuselage_max_diameter'] * math.pi * 0.8 # approx
        W_fuse_N = 0.025 * (S_fuse_wet_m2**1.2) * (inputs['fuselage_l_f']/inputs['fuselage_max_diameter'])**0.5 * N_ult**0.2 * N_PER_KG * 10
        outputs['weight_W_fuselage'] = max(W_fuse_N, 0.12 * inputs['weight_W_TO_guess'])

        # Empennage Weight
        W_emp_N = 0.018 * (N_ult * W_TO_guess_kg)**0.4 * (inputs['emp_S_h'] + inputs['emp_S_v'])**0.8 * N_PER_KG * 10
        outputs['weight_W_empennage'] = max(W_emp_N, 0.02 * inputs['weight_W_TO_guess'])

        # Engine System Weight (Torenbeek for turbofans, very simplified)
        # W_eng_single_lbs = 0.5 * T_TO_lbs^0.9
        W_eng_sys_N = inputs['engine_N_engines'] * (0.03 * inputs['engine_T_TO_per_engine']**0.95 + 500) * 2.5 # Incl nacelle, systems
        outputs['weight_W_engine_sys'] = max(W_eng_sys_N, 0.05 * inputs['weight_W_TO_guess'])

        # Landing Gear Weight (typically 3-6% of W_TO)
        W_lg_N = 0.045 * inputs['weight_W_TO_guess']
        outputs['weight_W_lg'] = W_lg_N

        # Fixed Systems (avionics, furnishings, electrical, hydraulics etc.)
        # Can be a % of W_OE or W_TO, or a more detailed buildup
        W_systems_N = 0.08 * inputs['weight_W_TO_guess'] + 2000 # Base for small aircraft
        outputs['weight_W_systems'] = W_systems_N

        # Operational Empty Weight (OEW) = Sum of structural, engine, LG, systems + Crew
        W_OE_calc = (outputs['weight_W_wing'] + outputs['weight_W_fuselage'] +
                     outputs['weight_W_empennage'] + outputs['weight_W_engine_sys'] +
                     outputs['weight_W_lg'] + outputs['weight_W_systems'] +
                     inputs['weight_W_crew'])
        outputs['weight_W_OE_calc'] = W_OE_calc


# --- Performance Calculations ---
class MissionPerformance(om.ExplicitComponent):
    """Calculates mission fuel and range."""
    def setup(self):
        self.add_input('weight_W_OE_calc', val=14000.0, units='N', desc='Operational Empty Weight')
        self.add_input('weight_W_PL', val=5884.0, units='N', desc='Payload Weight')
        self.add_input('weight_W_F_capacity', val=12930.5, units='N', desc='Max Fuel Capacity') # This is W_F from user file
        
        self.add_input('aero_L_D_cruise', val=15.0, desc='Cruise L/D')
        self.add_input('engine_cruise_tsfc_kg_Ns', val=1.6e-5, units='kg/(N*s)')
        self.add_input('target_range_m', val=3000e3, units='m', desc='Target design range')
        self.add_input('cruise_speed_mps', val=230.0, units='m/s') # Mach * speed_of_sound

        # Reserve fuel policy (e.g., diversion + loiter)
        self.add_input('diversion_range_m', val=370e3, units='m', desc='Diversion distance (e.g., 200 nm)')
        self.add_input('loiter_time_s', val=1800.0, units='s', desc='Loiter time (e.g., 30 min)')
        self.add_input('aero_L_D_loiter', val=17.0, desc='Loiter L/D (typically higher than cruise L/D)')

        # Outputs
        self.add_output('calculated_W_TO', val=30000.0, units='N', desc='Calculated MTOW for the mission')
        self.add_output('weight_W_F_used_mission', val=10000.0, units='N', desc='Fuel used for main mission legs')
        self.add_output('weight_W_F_reserve', val=2000.0, units='N', desc='Reserve fuel')
        self.add_output('weight_M_ff_mission', val=0.3, desc='Mission fuel fraction W_F_used / W_TO')
        self.add_output('achieved_range_m', val=3000e3, units='m', desc='Range achieved with W_F_used')
        self.add_output('range_constraint', val=0.0, units='m', desc='target_range - achieved_range (should be <=0)')


    def compute(self, inputs, outputs):
        W_OE = inputs['weight_W_OE_calc']
        W_PL = inputs['weight_W_PL']
        W_F_cap = inputs['weight_W_F_capacity']

        L_D_cruise = inputs['aero_L_D_cruise'] if inputs['aero_L_D_cruise'] > 1e-6 else 1.0
        TSFC_cruise_kgNs = inputs['engine_cruise_tsfc_kg_Ns'] if inputs['engine_cruise_tsfc_kg_Ns'] > 1e-9 else 1e-9
        TSFC_cruise_NsN = TSFC_cruise_kgNs * N_PER_KG # Convert to N_fuel / (N_thrust * s)
        
        R_target_m = inputs['target_range_m']
        V_cruise_mps = inputs['cruise_speed_mps']

        # Landing weight (OEW + Payload + Reserve Fuel)
        # Estimate reserve fuel first (simplified Breguet for diversion and endurance for loiter)
        L_D_loiter = inputs['aero_L_D_loiter'] if inputs['aero_L_D_loiter'] > 1e-6 else 1.0
        R_div_m = inputs['diversion_range_m']
        T_loiter_s = inputs['loiter_time_s']

        # Iteratively solve for W_TO and W_F_used, or use Breguet range equation rearranged
        # W_TO = W_OE + W_PL + W_F_mission + W_F_reserve
        # W_F_mission = W_TO * (1 - exp(-R * g * TSFC / (V * L/D)))
        # This requires solving for W_TO.
        # For now, let's assume a fuel fraction and calculate range, then a constraint.

        # Simplified: Calculate fuel needed for target range, then add reserves.
        # This is an iterative process in reality.
        # W_L = W_OE + W_PL (Landing weight before reserve fuel for main mission calc)
        
        # Estimate W_TO by assuming a fuel fraction initially, then iterate.
        # Or, more directly for constraint checking:
        # Given a W_TO (e.g. from optimizer), calculate W_F_available for mission.
        # W_F_available_for_mission_and_reserves = W_TO_current - W_OE - W_PL
        # This W_TO_current would be an implicit variable solved by OpenMDAO's Newton solver
        # or an input if W_TO is a DV.
        # For an ExplicitComponent, we need to calculate outputs from inputs.

        # Let's calculate fuel required for target range + reserves, and this defines W_TO.
        # This is a sizing approach.
        
        # Fuel for reserves:
        # W_0_for_res_calc = W_OE + W_PL # Approx weight at start of reserve segment
        # For simplicity, assume reserve L/D and TSFC are similar to loiter/cruise
        # W_F_diversion = W_0_for_res_calc * (math.exp(R_div_m * TSFC_cruise_NsN / (V_cruise_mps * L_D_loiter)) - 1) # Incorrect, this is for W_final = W_0 * exp(...)
        # W_F_diversion needs W_final after diversion.
        # Let W_res_start = W_OE + W_PL.
        # W_div_end = W_res_start / math.exp(R_div_m * TSFC_cruise_NsN / (V_cruise_mps * L_D_loiter))
        # W_F_div = W_res_start - W_div_end
        
        # W_loiter_end = W_div_end / math.exp(T_loiter_s * TSFC_cruise_NsN / L_D_loiter) # Endurance formula
        # W_F_loiter = W_div_end - W_loiter_end
        # W_F_reserve_calc = W_F_div + W_F_loiter
        
        # Simplified reserve fuel: typically 5-10% of total fuel or mission fuel.
        # Or based on fixed diversion + loiter. Let's use a percentage of W_OE + W_PL for now.
        W_F_reserve_calc = 0.05 * (W_OE + W_PL) + \
                           (T_loiter_s * TSFC_cruise_NsN / L_D_loiter) * (W_OE + W_PL) # Very rough loiter fuel
        outputs['weight_W_F_reserve'] = W_F_reserve_calc

        # Fuel for main mission:
        # W_TO_approx = (W_OE + W_PL + W_F_reserve_calc) / (1 - Mff_target_for_range)
        # Mff_target_for_range = 1 - math.exp(-R_target_m * TSFC_cruise_NsN / (V_cruise_mps * L_D_cruise))
        # W_F_mission_calc = W_TO_approx * Mff_target_for_range
        
        # Iterative approach to find W_F_mission and W_TO consistently:
        W_land_after_mission = W_OE + W_PL + W_F_reserve_calc
        exp_factor = math.exp(R_target_m * TSFC_cruise_NsN / (V_cruise_mps * L_D_cruise))
        if exp_factor < 1.0001 : exp_factor = 1.0001 # Avoid issues if factor is ~1 or less

        W_TO_calc = W_land_after_mission * exp_factor
        W_F_mission_calc = W_TO_calc - W_land_after_mission
        
        outputs['calculated_W_TO'] = W_TO_calc
        outputs['weight_W_F_used_mission'] = W_F_mission_calc

        if W_TO_calc > 1e-6:
            outputs['weight_M_ff_mission'] = W_F_mission_calc / W_TO_calc
        else:
            outputs['weight_M_ff_mission'] = 0

        # Achieved range with W_F_cap (if W_F_mission_calc > W_F_cap)
        # Or, for constraint, check if W_F_mission_calc <= W_F_cap
        # Here, we are sizing W_TO for the mission.
        # The 'achieved_range_m' is effectively the target_range_m because we sized fuel for it.
        outputs['achieved_range_m'] = R_target_m 
        outputs['range_constraint'] = R_target_m - outputs['achieved_range_m'] # Should be zero by this formulation

        # A different formulation for achieved_range if W_TO is fixed and W_F_used is W_F_cap - W_F_reserve:
        # W_F_for_range_max_cap = W_F_cap - W_F_reserve_calc
        # if W_F_for_range_max_cap > 0:
        #     W_TO_at_cap = W_OE + W_PL + W_F_cap
        #     mass_ratio_at_cap = W_TO_at_cap / (W_TO_at_cap - W_F_for_range_max_cap)
        #     achieved_range_at_cap = (V_cruise_mps * L_D_cruise / TSFC_cruise_NsN) * math.log(mass_ratio_at_cap)
        #     outputs['achieved_range_m'] = achieved_range_at_cap
        #     outputs['range_constraint'] = R_target_m - achieved_range_at_cap
        # else:
        #     outputs['achieved_range_m'] = 0
        #     outputs['range_constraint'] = R_target_m


class CruisePerformance(om.ExplicitComponent):
    """Calculates cruise lift, drag, and checks constraints."""
    def setup(self):
        self.add_input('calculated_W_TO', val=30000.0, units='N') # Current aircraft weight for cruise segment
        self.add_input('weight_W_F_used_mission', val=10000.0, units='N') # To estimate avg cruise weight
        self.add_input('wing_S_w', val=12.0, units='m**2')
        self.add_input('cruise_density_kg_m3', val=0.36, units='kg/m**3') # At cruise altitude
        self.add_input('cruise_speed_mps', val=230.0, units='m/s')
        self.add_input('aero_CD0', val=0.025)
        self.add_input('aero_K_drag', val=0.04)
        self.add_input('engine_T_TO_total', val=11360.0, units='N') # For thrust lapse
        self.add_input('cruise_altitude_m', val=11000, units='m')


        self.add_output('cruise_CL', val=0.5, desc='Cruise Lift Coefficient')
        self.add_output('cruise_CD', val=0.03, desc='Cruise Drag Coefficient')
        self.add_output('cruise_Drag_N', val=5000.0, units='N', desc='Cruise Drag Force')
        self.add_output('cruise_Thrust_required_N', val=5000.0, units='N', desc='Thrust required for cruise')
        self.add_output('cruise_Thrust_available_N', val=6000.0, units='N', desc='Thrust available at cruise')
        self.add_output('cruise_L_D', val=16.0, desc='Actual L/D at cruise conditions')
        self.add_output('lift_equals_weight_constraint', val=0.0, units='N', desc='L - W (should be >=0)')
        self.add_output('thrust_equals_drag_constraint', val=0.0, units='N', desc='T_avail - D_req (should be >=0)')

    def compute(self, inputs, outputs):
        # Average cruise weight (W_TO - 0.5 * W_F_used_mission)
        W_cruise_avg = inputs['calculated_W_TO'] - 0.5 * inputs['weight_W_F_used_mission']
        S_w = inputs['wing_S_w']
        rho_cruise = inputs['cruise_density_kg_m3']
        V_cruise = inputs['cruise_speed_mps']
        CD0 = inputs['aero_CD0']
        K = inputs['aero_K_drag']

        q_cruise = 0.5 * rho_cruise * V_cruise**2
        
        if q_cruise * S_w > 1e-6:
            CL_cruise = W_cruise_avg / (q_cruise * S_w)
        else:
            CL_cruise = 0.0
        outputs['cruise_CL'] = CL_cruise

        CD_cruise = CD0 + K * CL_cruise**2
        outputs['cruise_CD'] = CD_cruise

        D_cruise = q_cruise * S_w * CD_cruise
        outputs['cruise_Drag_N'] = D_cruise
        outputs['cruise_Thrust_required_N'] = D_cruise # For L=W, T=D steady cruise

        if CD_cruise > 1e-6:
            outputs['cruise_L_D'] = CL_cruise / CD_cruise
        else:
            outputs['cruise_L_D'] = 0.0

        # Thrust available at cruise (simplified lapse model)
        # T_avail_cruise = T_SL * (rho_cruise / rho_SL)^alpha * M_factor
        # Assuming alpha ~ 0.7-0.9 for turbofans
        rho_SL = 1.225 # kg/m^3
        thrust_lapse_factor = (rho_cruise / rho_SL)**0.8 
        # Add Mach effect if available, e.g. T_avail decreases slightly at higher cruise Mach
        T_avail_cruise = inputs['engine_T_TO_total'] * thrust_lapse_factor
        outputs['cruise_Thrust_available_N'] = T_avail_cruise
        
        # Constraints
        Lift_cruise = CL_cruise * q_cruise * S_w # Should be W_cruise_avg
        outputs['lift_equals_weight_constraint'] = Lift_cruise - W_cruise_avg # Should be close to 0
        outputs['thrust_equals_drag_constraint'] = T_avail_cruise - D_cruise


class TakeOffLandingPerformance(om.ExplicitComponent):
    """Estimates takeoff distance and stall speeds."""
    def setup(self):
        self.add_input('weight_W_TO', val=30787.8, units='N')
        self.add_input('wing_S_w', val=12.0, units='m**2')
        self.add_input('perf_CL_max_TO', val=1.9)
        self.add_input('perf_CL_max_LAND', val=2.2)
        self.add_input('engine_T_TO_total', val=11360.0, units='N')
        self.add_input('rho_SL_kg_m3', val=1.225, units='kg/m**3', desc='Air density at sea level')


        self.add_output('take_off_distance_calc_m', val=1200.0, units='m')
        self.add_output('landing_distance_calc_m', val=1000.0, units='m') # Placeholder
        self.add_output('stall_speed_TO_mps', val=50.0, units='m/s')
        self.add_output('stall_speed_LAND_mps', val=45.0, units='m/s')
        self.add_output('V_takeoff_mps', val=60.0, units='m/s', desc='Takeoff speed (1.1*V_stall_TO)')


    def compute(self, inputs, outputs):
        W_TO = inputs['weight_W_TO']
        S_w = inputs['wing_S_w']
        CL_max_TO = inputs['perf_CL_max_TO']
        CL_max_LAND = inputs['perf_CL_max_LAND']
        T_TO = inputs['engine_T_TO_total']
        rho_SL = inputs['rho_SL_kg_m3']

        # Stall Speeds
        if CL_max_TO > 1e-6 and S_w > 1e-6 and rho_SL > 1e-6:
            V_stall_TO = math.sqrt((2 * W_TO) / (rho_SL * S_w * CL_max_TO))
        else:
            V_stall_TO = 1e6 # Large penalty
        outputs['stall_speed_TO_mps'] = V_stall_TO
        
        # Assuming landing weight is ~0.85 * W_TO (can be refined)
        W_Ldg = 0.85 * W_TO 
        if CL_max_LAND > 1e-6 and S_w > 1e-6 and rho_SL > 1e-6:
            V_stall_LAND = math.sqrt((2 * W_Ldg) / (rho_SL * S_w * CL_max_LAND))
        else:
            V_stall_LAND = 1e6
        outputs['stall_speed_LAND_mps'] = V_stall_LAND

        V_TO = 1.1 * V_stall_TO # Takeoff speed
        outputs['V_takeoff_mps'] = V_TO

        # Takeoff Distance (simplified, from Anderson or similar)
        # TOP = (W/S) / (g * rho * CL_max_TO * (T/W - mu_roll)) where T/W is avg during TO roll
        # S_TO = K_TO * (W_TO/S_w) / (rho_SL * g * CL_max_TO * (T_TO/W_TO))
        # This is a very common empirical form: S_g = (V_TO^2) / (2 * g * (T/W - D/W - mu_roll))
        # Or Raymer: S_TOFL (ft) = 37.5 * (W_TO/S_w)_psf / (sigma * CL_max_TO * (T_TO/W_TO))
        # For N, m, kg units:
        sigma = rho_SL / 1.225 # density ratio
        WS_Pa = inputs['weight_W_TO'] / S_w if S_w > 0 else 1e9
        TW_ratio = T_TO / W_TO if W_TO > 0 else 1e-9
        
        if sigma * CL_max_TO * TW_ratio > 1e-9:
            # Factor 37.5 for ft, psf. For m, Pa: 37.5 * (1/3.28) / (1/47.88) = 37.5 * 14.6 approx 547
            # This factor needs careful derivation or use a physics-based model.
            # Using a simplified physics-based ground roll: S_g = V_lof^2 / (2*a_avg)
            # a_avg = g * (T_avg/W_avg - D_avg/W_avg - mu_roll)
            # Assume T_avg ~ 0.75*T_TO, D_avg during ground roll is low, mu_roll ~ 0.02
            # This is complex. Using a common empirical form:
            TOD_calc = (0.20 * WS_Pa) / (N_PER_KG * sigma * CL_max_TO * TW_ratio) # Factor 0.20 is a placeholder!
                                                                           # Needs to be calibrated or use better formula.
                                                                           # Example: (from a source for jet transport)
                                                                           # S_TO_m = (K_TOP * (W_TO/S_w)) / (rho_SL * g * CL_max_TO * (T_TO/W_TO))
                                                                           # where K_TOP is around 2.3-2.5 for balanced field length.
                                                                           # For ground roll only, K_TOP might be lower.
            TOD_calc = 60 * (WS_Pa / (rho_SL * N_PER_KG * CL_max_TO * TW_ratio)) # Another form, factor 60 is empirical
        else:
            TOD_calc = 1e6 # Large penalty

        outputs['take_off_distance_calc_m'] = TOD_calc
        
        # Landing Distance (placeholder, more complex with approach, flare, ground roll)
        # Ldg_dist ~ V_app^2 / (2*a_decel) + S_air_dist
        # V_app = 1.3 * V_stall_LAND
        outputs['landing_distance_calc_m'] = 0.8 * TOD_calc # Very rough relation for now
