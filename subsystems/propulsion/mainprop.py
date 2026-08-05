from math import sqrt, nan, isnan # Added nan, isnan for handling potential NaN values
import sys # For potential path debugging
import os  # For potential path debugging4
import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.unit_conversions import *
from config.design_variables import DesignParameters

import gas_property_relations as gpr
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.unit_conversions import *
from config.design_variables import DesignParameters


#main function 1
params = DesignParameters()
params.load_from_yaml("design_config.yaml")
def nacelle_pylon_sizing(params: DesignParameters):
    #speed of sound in air at sea level
    a = (1.4 * 287.05 * 288.15) ** 0.5  # m/s, speed of sound at sea level at ISA + 15C
    T_to = params.engine.T_TO
    D_fan = 0.508 # m, fan diameter
    L_eng = 1.397 # m, engine length
    Bpr = params.engine.Bpr # bypass ratio
    eta_ft = params.engine.eta_fanturb # fan/turbine efficiency
    tt4to = params.engine.tt4to # tt4 temp at takeoff
    G = (tt4to/600)-1.25 # Specific gas turbine power
    eta_nozz = params.engine.eta_nozz # nozzle efficiency
    mdot_air = (T_to/a)*((1+Bpr)/(5*eta_nozz*G*(1+(eta_ft*Bpr))**0.5))

    #print mass flow rate of air
    print(f"Mass flow rate of air: {mdot_air:.2f} kg/s")

    D_s = 0.14224 #spinner diameter, m
    D_inlet = D_fan
    Ds_i = D_s / D_inlet #spinner to inlet diameter ratio
    spinner_inlet_ratio = 0.05 * (1+((0.1*1.225*a)/(mdot_air))+(3*Bpr)/(1+Bpr))
    #print spinner inlet ratio
    print(f"Spinner inlet ratio: {spinner_inlet_ratio:.2f}")
    D_i = 1.65*((mdot_air/(1.225*a)+0.005)/(1-(Ds_i)**2))**0.5 #inlet diameter, m
    print(f"Inlet diameter: {D_i:.2f} m")



    D_inlet = D_fan
    l_n = 1.44 #nacelle length, m
    D_n = D_inlet + (0.06*0.75*l_n) +0.03 #max nacelle diameter, m
    print(f"Maximum nacelle diameter: {D_n:.2f} m")
    D_ef = D_n*(1-(1/3)*0.75**2) #exit fan diameter, m
    print(f"Nacelle exit diameter: {D_ef:.2f} m")

    # Constants
    D_fan = 0.508               # Fan and core diameter
    D_s = 0.14224               # Spinner diameter
    D_ef = 0.49                 # Exit nacelle diameter
    D_n = 0.63                  # Max nacelle diameter
    L_eng = 1.397               # Engine core length
    l_nacelle = L_eng + 0.2     # Total nacelle length with margins

    # # Radius values
    # R_fan = D_fan / 2
    # R_s = D_s / 2
    # R_ef = D_ef / 2
    # R_n = D_n / 2

    # # Nacelle shape profile
    # z_nacelle = np.array([-0.1, l_nacelle * 0.3, l_nacelle * 0.7, l_nacelle])
    # r_nacelle = np.array([R_fan, R_n, R_n, R_ef])

    # z_profile = np.concatenate([z_nacelle, z_nacelle[::-1]])
    # r_profile = np.concatenate([r_nacelle, -r_nacelle[::-1]])

    # # Engine core
    # core_z = [0, L_eng, L_eng, 0, 0]
    # core_r = [R_fan, R_fan, -R_fan, -R_fan, R_fan]

    # # Spinner (cone shape)
    # spinner_z = [-0.1, 0, 0]
    # spinner_r = [0, R_s, -R_s]

    # # Plot
    # plt.figure(figsize=(10, 4))
    # plt.plot(z_profile, r_profile, label="Nacelle Surface", color='steelblue')
    # plt.fill(core_z, core_r, color='gray', alpha=0.6, label="Engine Core")
    # plt.fill(spinner_z, spinner_r, color='red', label="Spinner")

    # # Labels and aesthetics
    # plt.title("Side View of Engine Nacelle with Spinner")
    # plt.xlabel("Length (m)")
    # plt.ylabel("Radius (m)")
    # plt.axis("equal")
    # plt.grid(True)
    # plt.legend()
    # plt.tight_layout()
    # plt.show()

    return {
        "D_inlet": D_inlet,
        "D_n": D_n,
        "D_ef": D_ef,
        "l_nacelle": l_nacelle,
        "mdot_air": mdot_air
    }
if __name__ == "__main__":
    results = nacelle_pylon_sizing(params)
    print("Nacelle and Pylon Sizing Results:")
    for key, value in results.items():
        print(f"{key}: {value:.2f}")

#main function 2 (NOx dallara)    
class atmosphere:
    @staticmethod
    def temperature(h, delta_t_0=0.):
        """
        Returns ISA temperature at altitude h (meters), optionally with deviation delta_t_0 (K).
        """
        # Troposphere up to 11km
        if h < 11000:
            t = 288.15 - 0.0065 * h
        # Stratosphere from 11km to 20km
        elif h <= 20000:
            t = 216.65
        # Stratosphere from 20km to 32km
        else:
             t = 216.65 + 0.001 * (h - 20000)
        return t + delta_t_0

    @staticmethod
    def pressure(h):
        """
        Returns ISA pressure at altitude h (meters).
        """
        # Troposphere up to 11km
        if h < 11000:
            p = 101325 * (1 - 0.0065 * h / 288.15) ** 5.2561
        # Stratosphere from 11km to 20km
        elif h <= 20000:
            p = 22632.1 * np.exp(-9.80665 * (h - 11000) / (287.05 * 216.65))
        # Stratosphere from 20km to 32km
        else:
            p = 5474.89 * (1 + 0.001 * (h - 20000)/216.65) ** (-9.80665/(0.001*287.05))
        return p

    @staticmethod
    def get_altitude_from_pressure(p):
        """
        Estimates altitude (meters) from static pressure (Pa) based on ISA model.
        """
        p_sl = 101325.  # Pa
        p_11k = 22632.1 # Pa

        if p > p_11k: # Troposphere
             # h = (288.15 / 0.0065) * (1 - (p / p_sl) ** (1 / 5.2561))
             h = (288.15 / 0.0065) * (1 - (p / p_sl) ** (0.190263))
        else: # Stratosphere (up to 20km)
             h = 11000 - (287.05 * 216.65 / 9.80665) * np.log(p / p_11k)
        return h

    @staticmethod
    def saturation_vapor_pressure(t):
        """
        Returns saturation vapor pressure (Pa) at temperature t (K).
        """
        t_c = t - 273.15
        return 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))

    @staticmethod
    def specific_humidity(h, relative_humidity=0.6, delta_t_0=0.):
        """
        Returns specific humidity (g/kg) at altitude h (meters), relative humidity (0-1), and delta_t_0 (K).
        """
        t = atmosphere.temperature(h, delta_t_0)
        p = atmosphere.pressure(h)
        e_s = atmosphere.saturation_vapor_pressure(t)
        e = relative_humidity * e_s
        # Specific humidity (kg/kg)
        q = 0.622 * e / (p - (1 - 0.622) * e)
        return q * 1000  # Convert to g/kg

# --- NOx Emission Index Calculation (Dallara/Schwartz/Kroo) ---
def ei_nox_dallara(pt_3, tt_3, h, relative_humidity=0.6, delta_t_isa=0.,
                   reduction_factor=0., lhv=43031.e3, lhv_ref=43031.e3):
    """
    Determines the NOx emission index according to Dallara/Schwartz/Kroo.

    :param pt_3: Total pressure before combustor in Pa
    :param tt_3: Total temperature before combustor in K
    :param h: Altitude in m
    :param relative_humidity: Relative humidity (0-1)
    :param delta_t_isa: ISA deviation in K
    :param reduction_factor: Fractional reduction in NOx (e.g. 0.4 for 40%)
    :param lhv: Lower heating value of fuel (J/kg)
    :param lhv_ref: Reference LHV (J/kg)
    :return: Emission index of NOx in kg_NOx/kg_fuel
    """
    if any(isnan(val) for val in [pt_3, tt_3, h]):
        return nan
        
    humid = atmosphere.specific_humidity(h=h,
                                         relative_humidity=relative_humidity,
                                         delta_t_0=delta_t_isa)
    # The core formula
    ei = (2+28.5*((pt_3/1000)/3100)**0.5 * np.exp((tt_3-825)/250))/1000 #kg/kg

    return ei

# --- Emissions Calculation Code (from emissions.py) ---
def fuelflow_to_emissionflow(mdot_f, ei):
    """
    Calculates the emission flow (in kg/s) from the fuel flow (kg/s) for a
    given emission index.

    :param mdot_f: Fuel mass flow in kg/s
    :param ei: Emission index of a species in kg/kg
    :return: Emission flow in kg/s
    """
    if isnan(mdot_f) or isnan(ei):
        return nan
    return mdot_f * ei

def emissions(mdot_f, ei_nox,
              ei_so4=2.0e-4, ei_soot=4.0e-5,
              ei_co2=3.16, ei_h2o=1.26,
              dt=1.):
    """
    Estimates the emission flow (in kg/s) and the total emission (in kg) for
    a given time step, for several species, given the fuel flow (in kg/s).

    :param mdot_f: Fuel flow in kg/s
    :param ei_nox: Emission index of Nitrogen Oxides (NO and NO2) in kg/kg
    :param ei_so4:  Emission index of Sulfate in kg/kg
    :param ei_soot:  Emission index of soot in kg/kg
    :param ei_co2:  Emission index of Carbon Dioxide in kg/kg
    :param ei_h2o:  Emission index of Water in kg/kg
    :param dt: Time step under consideration in seconds
    :return: Dictionary with emission flows and total emissions for every
    specie considered
    """
    if isnan(mdot_f) or isnan(dt):
        # If mdot_f is NaN, all emissions will be NaN
        return dict(mdot_co2=nan, m_co2=nan,
                    mdot_h2o=nan, m_h2o=nan,
                    mdot_nox=nan, m_nox=nan,
                    mdot_so4=nan, m_so4=nan,
                    mdot_soot=nan, m_soot=nan)

    # Carbon dioxide
    mdot_co2 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_co2)
    m_co2 = mdot_co2 * dt

    # Water
    mdot_h2o = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_h2o)
    m_h2o = mdot_h2o * dt

    # Nitrogen oxides
    mdot_nox = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_nox)
    m_nox = mdot_nox * dt

    # Sulfur
    mdot_so4 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_so4)
    m_so4 = mdot_so4 * dt

    # Soot
    mdot_soot = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_soot)
    m_soot = mdot_soot * dt

    emissions_dict = dict(mdot_co2=mdot_co2, m_co2=m_co2,
                          mdot_h2o=mdot_h2o, m_h2o=m_h2o,
                          mdot_nox=mdot_nox, m_nox=m_nox,
                          mdot_so4=mdot_so4, m_so4=m_so4,
                          mdot_soot=mdot_soot, m_soot=m_soot
                          )
    return emissions_dict

# --- Turbofan Analysis Code) ---
def turbofan_parametric_analysis(
        mach_0, ts_0, ps_0,  # flight conditions
        bpr, pr_fan, pr_lpc, pr_hpc, tt_4,  # design variables
        eta_fan, eta_lpc, eta_hpc, eta_hpt, eta_lpt,  # polytropic efficiencies
        eta_com=0.99, eta_mech_l=0.99, eta_mech_h=0.99,  # other efficiencies
        pr_com=0.95, pr_inl=0.98,
        bleed_to=0., power_tol=0., power_toh=0.,
        cooling_l=0., cooling_h=0.,
        lhv=43.e6,  # lower heating value J/kg
        full_output=True):
    """
    Carries out thermodynamic on-design / parametric analysis for a turbofan.
    """
    # 0 - freestream
    a_0 = gpr.s_o_s(ts_0)
    v_0 = mach_0 * a_0 if not (isnan(mach_0) or isnan(a_0)) else nan
    
    state_0_delta_h = 0.5 * v_0 ** 2 if not isnan(v_0) else nan
    state_0 = gpr.prescribed_delta_h(p_in=ps_0, t_in=ts_0, delta_h=state_0_delta_h, eta_pol=1.)
    pt_0 = state_0["p_out"]
    tt_0 = state_0["t_out"]
    hs_0 = gpr.specific_enthalpy(t=ts_0)
    ht_0 = hs_0 + v_0 ** 2. / 2. if not (isnan(hs_0) or isnan(v_0)) else nan
    tau_0 = ht_0 / hs_0 if hs_0 != 0 and not isnan(ht_0) else nan
    
    # 2 - inlet exit / fan entry
    tt_2 = tt_0
    pt_2 = pr_inl * pt_0 if not (isnan(pr_inl) or isnan(pt_0)) else nan
    ht_2 = ht_0

    # 13 - fan exit
    state_13 = gpr.prescribed_p_ratio(p_in=pt_2, t_in=tt_2, p_ratio=pr_fan, eta_pol=eta_fan)
    pt_13 = state_13["p_out"]
    tt_13 = state_13["t_out"]
    ht_13 = state_13["h_out"]
    tau_fan = ht_13 / ht_2 if ht_2 != 0 and not isnan(ht_13) else nan

    # 25 - LPC exit
    state_25 = gpr.prescribed_p_ratio(p_in=pt_13, t_in=tt_13, p_ratio=pr_lpc, eta_pol=eta_lpc)
    pt_25 = state_25["p_out"]
    tt_25 = state_25["t_out"]
    ht_25 = state_25["h_out"]
    tau_lpc = ht_25 / ht_13 if ht_13 != 0 and not isnan(ht_25) else nan

    # 3 - HPC exit
    state_3 = gpr.prescribed_p_ratio(p_in=pt_25, t_in=tt_25, p_ratio=pr_hpc, eta_pol=eta_hpc)
    pt_3 = state_3["p_out"]
    tt_3 = state_3["t_out"]
    ht_3 = state_3["h_out"]
    tau_hpc = ht_3 / ht_25 if ht_25 != 0 and not isnan(ht_3) else nan

    # 4 - Combustor exit
    far_4 = nan
    if not isnan(ht_3) and not isnan(tt_4) and not isnan(eta_com) and not isnan(lhv):
        far_4i = 0.02 # Initial guess
        far_4 = 0.03
        it = 0
        while abs(far_4 - far_4i) > 0.00001 and it < 50:
            far_4i = far_4
            ht_4i = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4i)
            if isnan(ht_4i):
                far_4 = nan
                break
            denominator = (eta_com * lhv - ht_4i)
            if denominator == 0 or isnan(ht_3):
                far_4 = nan
                break
            far_4 = (ht_4i - ht_3) / denominator
            if isnan(far_4): break
            it += 1
        if it >= 50 and abs(far_4 - far_4i) > 0.00001 : far_4 = nan

    pt_4 = pt_3 * pr_com if not (isnan(pt_3) or isnan(pr_com)) else nan
    ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4) if not isnan(tt_4) and not isnan(far_4) else nan
    tau_lambda = ht_4 / hs_0 if hs_0 != 0 and not isnan(ht_4) and not isnan(hs_0) else nan
    
    # 41 - Nozzle Vane mixing process (HPT entry)
    tau_m1 = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc):
        den_tau_m1 = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h)
        if den_tau_m1 != 0:
            tau_m1_num = (((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) +
                             cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda))
            if not isnan(tau_m1_num):
                tau_m1 = tau_m1_num / den_tau_m1

    # HPT work
    tau_hpt = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_fan) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(eta_mech_h) and not isnan(bpr) and not isnan(power_toh):
        den_tau_hpt_expr_val_part = ((1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) +
                                   cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda)
        if not isnan(den_tau_hpt_expr_val_part):
            den_tau_hpt_expr = eta_mech_h * tau_lambda * den_tau_hpt_expr_val_part
            if den_tau_hpt_expr != 0:
                tau_hpt_num = (tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh)
                if not isnan(tau_hpt_num):
                    tau_hpt = (1. - tau_hpt_num / den_tau_hpt_expr)

    ht_41 = ht_4 * tau_m1 if not (isnan(ht_4) or isnan(tau_m1)) else nan
    
    far_41 = nan
    if not isnan(far_4):
        den_far_41_main = (1. - bleed_to - cooling_h - cooling_l)
        if den_far_41_main != 0:
            den_far_41_sub = (cooling_h / den_far_41_main)
            if not isnan(den_far_41_sub):
                den_far_41 = (1. + den_far_41_sub)
                if den_far_41 != 0:
                    far_41 = far_4 / den_far_41

    pt_41 = pt_4
    tt_41 = gpr.prescribed_h(ht_41, gas="kerosene_in_air", far=far_41) if not isnan(ht_41) and not isnan(far_41) else nan

    # 44 - HPT exit
    ht_44 = ht_41 * tau_hpt if not (isnan(ht_41) or isnan(tau_hpt)) else nan
    delta_h_hpt = ht_44 - ht_41 if not (isnan(ht_44) or isnan(ht_41)) else nan
    state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41,
                                      delta_h=delta_h_hpt,
                                      eta_pol=eta_hpt,
                                      gas="kerosene_in_air", far=far_41)
    pt_44 = state_44["p_out"]
    tt_44 = state_44["t_out"]

    # 45 - HPT end nozzle vane mixing process (LPT entry)
    tau_m2 = nan
    if not isnan(far_4) and not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_lambda) and tau_lambda != 0 and \
       not isnan(tau_m1) and tau_m1 != 0 and \
       not isnan(tau_hpt) and tau_hpt != 0:
        den_tau_m2_main = ((1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + cooling_l)
        if den_tau_m2_main != 0:
            tau_m2_num_term = cooling_l * tau_0 * tau_lpc * tau_hpc / (tau_lambda * tau_m1 * tau_hpt)
            if not isnan(tau_m2_num_term):
                tau_m2_num = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + tau_m2_num_term
                if not isnan(tau_m2_num):
                    tau_m2 = tau_m2_num / den_tau_m2_main
    
    ht_45 = ht_44 * tau_m2 if not (isnan(ht_44) or isnan(tau_m2)) else nan
    
    far_45 = nan
    if not isnan(far_4):
        den_far_45_main = (1. - bleed_to - cooling_h - cooling_l)
        if den_far_45_main != 0:
            den_far_45_sub = (cooling_l + cooling_h) / den_far_45_main
            if not isnan(den_far_45_sub):
                den_far_45 = (1. + den_far_45_sub)
                if den_far_45 != 0:
                    far_45 = far_4 / den_far_45
            
    pt_45 = pt_44
    tt_45 = gpr.prescribed_h(ht_45, gas="kerosene_in_air", far=far_45) if not isnan(ht_45) and not isnan(far_45) else nan

    # 5 - LPT exit
    tau_lpt = nan
    if not isnan(eta_mech_l) and not isnan(tau_lambda) and tau_lambda != 0 and \
       not isnan(tau_hpt) and tau_hpt != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_fan) and not isnan(bpr) and not isnan(power_tol):
        
        term_cool_l_eff = cooling_l / tau_hpt
        if not isnan(term_cool_l_eff):
            term_bracket_coeffs = (cooling_h + term_cool_l_eff) * tau_0 * tau_lpc * tau_hpc / tau_lambda
            if not isnan(term_bracket_coeffs):
                den_tau_lpt_bracket = (1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + term_bracket_coeffs
                if not isnan(den_tau_lpt_bracket):
                    den_tau_lpt_main = eta_mech_l * tau_lambda * tau_hpt * den_tau_lpt_bracket
                    if den_tau_lpt_main != 0:
                        tau_lpt_num_term1 = tau_0 * ((tau_lpc * tau_fan - 1.) + bpr * (tau_fan - 1.))
                        tau_lpt_num_term2 = (1. + bpr) * power_tol
                        if not isnan(tau_lpt_num_term1) and not isnan(tau_lpt_num_term2):
                            tau_lpt_num = tau_lpt_num_term1 + tau_lpt_num_term2
                            tau_lpt = 1. - (tau_lpt_num / den_tau_lpt_main)

    ht_5 = ht_45 * tau_lpt if not (isnan(ht_45) or isnan(tau_lpt)) else nan
    delta_h_lpt = ht_5 - ht_45 if not (isnan(ht_5) or isnan(ht_45)) else nan
    state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45,
                                     delta_h=delta_h_lpt,
                                     eta_pol=eta_lpt,
                                     gas="kerosene_in_air", far=far_45)
    pt_5 = state_5["p_out"]
    tt_5 = state_5["t_out"]

    # 9 - Core exhaust nozzle
    ht_9, tt_9, pt_9, far_9 = ht_5, tt_5, pt_5, far_45
    mach_9 = nan
    ps_9 = nan
    ts_9 = nan
    v_9 = nan
    rho_9 = nan

    if not isnan(pt_9) and not isnan(ps_0) and ps_0 != 0 and not isnan(tt_9) and not isnan(far_9):
        p_total_static_ratio_9 = pt_9 / ps_0
        g_9 = gpr.gamma_gas(tt_9, gas="kerosene_in_air", far=far_9)
        if g_9 > 1. and p_total_static_ratio_9 > 1:
            mach_i_9_sq_term = p_total_static_ratio_9 ** ((g_9 - 1.) / g_9) - 1.
            mach_i_9_sq = (2. / (g_9 - 1.)) * mach_i_9_sq_term
            mach_i_9 = sqrt(mach_i_9_sq)
            mach_9 = 1. if mach_i_9 >= 1. else mach_i_9
        else: mach_9 = 0.0

        ts_9 = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
        g_ts9 = gpr.gamma_gas(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        if not (isnan(g_ts9) or g_ts9 == 1 or isnan(tt_9) or isnan(ts_9) or ts_9 == 0):
            ps_9 = pt_9 / ((tt_9 / ts_9) ** (g_ts9 / (g_ts9 - 1.)))
        else: ps_9 = ps_0

        a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        v_9 = mach_9 * a_9 if not (isnan(mach_9) or isnan(a_9)) else nan
        r_9 = gpr.r_gas(gas="kerosene_in_air", far=far_9)
        rho_9 = ps_9 / (r_9 * ts_9) if not (isnan(ps_9) or isnan(r_9) or isnan(ts_9) or r_9 * ts_9 == 0) else nan

    # 19 - Bypass exhaust nozzle
    ht_19, tt_19, pt_19, far_19 = ht_13, tt_13, pt_13, 0.
    mach_19, ps_19, ts_19, v_19, rho_19 = nan, nan, nan, nan, nan

    if not isnan(pt_19) and not isnan(ps_0) and ps_0 != 0 and not isnan(tt_19):
        p_total_static_ratio_19 = pt_19 / ps_0
        g_19 = gpr.gamma_gas(tt_19, gas="air", far=far_19)
        if g_19 > 1. and p_total_static_ratio_19 > 1:
            mach_i_19_sq = (2. / (g_19 - 1.)) * (p_total_static_ratio_19 ** ((g_19 - 1.) / g_19) - 1.)
            mach_i_19 = sqrt(mach_i_19_sq)
            mach_19 = 1. if mach_i_19 >= 1. else mach_i_19
        else: mach_19 = 0.0

        ts_19 = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
        g_ts19 = gpr.gamma_gas(ts_19, gas="air", far=far_19) if not isnan(ts_19) else nan
        if not (isnan(g_ts19) or g_ts19 == 1 or isnan(tt_19) or isnan(ts_19) or ts_19 == 0):
            ps_19 = pt_19 / ((tt_19 / ts_19) ** (g_ts19 / (g_ts19 - 1.)))
        else: ps_19 = ps_0

        a_19 = gpr.s_o_s(ts_19, gas="air") if not isnan(ts_19) else nan
        v_19 = mach_19 * a_19 if not (isnan(mach_19) or isnan(a_19)) else nan
        r_19 = gpr.r_gas(gas="air", far=far_19)
        rho_19 = ps_19 / (r_19 * ts_19) if not (isnan(ps_19) or isnan(r_19) or isnan(ts_19) or r_19*ts_19 == 0) else nan

    sf = nan
    if not any(isnan(x) for x in [bleed_to, far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19]):
        if (1. + bpr) != 0:
            sf_term1 = (1. - bleed_to) * (1. + far_4) * v_9
            sf_term2 = bpr * v_19
            sf_term3 = (1. + bpr) * v_0
            sf_pressure_core = (ps_9 - ps_0) * (1 - bleed_to) * (1. + far_4) / (rho_9 * v_9) if not (isnan(rho_9) or rho_9 == 0 or isnan(v_9) or v_9 == 0) else 0.
            sf_pressure_bypass = (ps_19 - ps_0) * bpr / (rho_19 * v_19) if not (isnan(rho_19) or rho_19 == 0 or isnan(v_19) or v_19 == 0) else 0.
            sf_gross = sf_term1 + sf_term2 + sf_pressure_core + sf_pressure_bypass
            sf = (sf_gross - sf_term3) / (1. + bpr)
    
    tsfc = nan
    if not (isnan(far_4) or isnan(sf) or sf == 0 or isnan(bpr) or (1.+bpr) == 0):
        tsfc_den = sf * (1. + bpr)
        if tsfc_den != 0:
            tsfc = (far_4 * (1. - bleed_to - cooling_l - cooling_h)) / tsfc_den
    
    opr = pr_fan * pr_lpc * pr_hpc if not any(isnan(x) for x in [pr_fan, pr_lpc, pr_hpc]) else nan

    eta_thermal, eta_propulsive, eta_overall = nan, nan, nan
    
    v_19_id = v_19 + (ps_19 - ps_0) / (rho_19 * v_19) if not any(isnan(x) or x==0 for x in [v_19, rho_19, ps_19, ps_0]) else v_19
    v_9_id = v_9 + (ps_9 - ps_0) / (rho_9 * v_9) if not any(isnan(x) or x==0 for x in [v_9, rho_9, ps_9, ps_0]) else v_9

    if not any(isnan(x) for x in [bpr, v_19_id, bleed_to, far_4, v_9_id, v_0, cooling_h, cooling_l, lhv]):
        num_eta_thermal = bpr * (v_19_id ** 2.) / 2. + \
                          (1. - bleed_to) * (1. + far_4) * (v_9_id ** 2.) / 2. - \
                          (1. + bpr) * (v_0 ** 2.) / 2.
        den_eta_thermal = (1. - bleed_to - cooling_h - cooling_l) * far_4 * lhv
        if not isnan(den_eta_thermal) and den_eta_thermal != 0:
            eta_thermal = num_eta_thermal / den_eta_thermal
        if not (isnan(sf) or isnan(bpr) or isnan(v_0) or isnan(num_eta_thermal) or num_eta_thermal == 0):
            eta_propulsive = (sf * (1.+bpr) * v_0) / num_eta_thermal
    
    if not (isnan(eta_thermal) or isnan(eta_propulsive)):
        eta_overall = eta_thermal * eta_propulsive
    
    output_dict = dict(
        mach_0=mach_0, ts_0=ts_0, ps_0=ps_0, bpr=bpr, tt_4=tt_4,
        pr_fan=pr_fan, pr_lpc=pr_lpc, pr_hpc=pr_hpc, opr=opr,
        far_4=far_4, tsfc=tsfc, sf=sf,
        v_9=v_9, v_19=v_19,
        pt_3=pt_3, tt_3=tt_3, pt_5=pt_5, tt_5=tt_5,
        eta_thermal=eta_thermal, eta_propulsive=eta_propulsive, eta_overall=eta_overall
    )

    if full_output:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    else:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall

def print_detailed_results(results, engine_name="Engine Run"):
    """Prints the turbofan analysis results."""
    if results is None or len(results) < 5: 
        print(f"\n--- {engine_name}: Incomplete or No Results ---")
        return

    sf, tsfc, eta_thermal, eta_propulsive, eta_overall = results[:5]
    print(f"\n--- {engine_name}: Performance Metrics ---")
    print(f"  Specific Thrust (SF):                   {sf:.2f} N/(kg/s)" if not isnan(sf) else "  Specific Thrust (SF):                   N/A")
    print(f"  Thrust Specific Fuel Consumption (TSFC):  {tsfc*1e6:.2f} mg/(N·s)" if not isnan(tsfc) else "  Thrust Specific Fuel Consumption (TSFC):  N/A")
    print(f"  Thermal Efficiency (eta_thermal):         {eta_thermal*100:.2f}%" if not isnan(eta_thermal) else "  Thermal Efficiency (eta_thermal):         N/A")
    print(f"  Propulsive Efficiency (eta_propulsive):   {eta_propulsive*100:.2f}%" if not isnan(eta_propulsive) else "  Propulsive Efficiency (eta_propulsive):   N/A")
    print(f"  Overall Efficiency (eta_overall):         {eta_overall*100:.2f}%" if not isnan(eta_overall) else "  Overall Efficiency (eta_overall):         N/A")

# --- Main Mission Simulation ---
def run_mission_simulation(params: DesignParameters):
    print("Starting Aircraft Mission Emissions Simulation...\n")

    baseline_engine_config = {
        "bpr": params.engine.Bpr, "pr_fan": params.engine.prfan, "pr_lpc": params.engine.prlpc, "pr_hpc": params.engine.prhpc, "tt_4": 1400.,
        "eta_fan": params.engine.etafan, "eta_lpc": params.engine.etalpc, "eta_hpc": params.engine.etahpc,
        "eta_hpt": params.engine.etahpt, "eta_lpt": params.engine.etalpt,
        "eta_com": params.engine.etacom, "eta_mech_l": params.engine.etamechl, "eta_mech_h": params.engine.etamechh,
        "pr_com": params.engine.prcom, "pr_inl": params.engine.prinlet,
        "bleed_to": params.engine.bleedto, "power_tol": params.engine.power_tol, "power_toh": params.engine.power_toh,
        "cooling_l": params.engine.cooling_l, "cooling_h": params.engine.cooling_h,
        "lhv": params.engine.lhv, 
        "full_output": True
    }
    T_to = params.engine.T_TO #N, takeoff thrust 
    mission_segments = [
        {
            "name": "Engine Start & Warm-Up", "duration_minutes": 10,
            "target_thrust_N": 0.07*T_to,
            "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850},
        },
        {
            "name": "Taxi", "duration_minutes": 10,
            "target_thrust_N": 0.12 * T_to,
            "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 900},
        },
        {
            "name": "Take-off", "duration_minutes": 5,
            "target_thrust_N": T_to,
            "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1400},
        },
        {
            "name": "Climb", "duration_minutes": 20,
            "target_thrust_N": 0.85*T_to ,
            "flight_conditions": {"mach_0": 0.65, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 1300},
        },
        {
            "name": "Cruise", "duration_minutes": 400,
            "target_thrust_N": params.engine.cruise_thrust,
            "flight_conditions": {"mach_0": 0.85, "ts_0": 216.65, "ps_0": 18753.9}, # 40000ft
            "engine_params_override": {"tt_4": 1200},
        },
        {
            "name": "Descent", "duration_minutes": 15,
            "target_thrust_N": 0.08*T_to,
            "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, # Avg 20000ft
            "engine_params_override": {"tt_4": 900},
        },
        {
            "name": "Landing", "duration_minutes": 5,
            "target_thrust_N": 0.18*T_to,
            "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 1000},
        },
        {
            "name": "Taxi & Shutdown", "duration_minutes": 15,
            "target_thrust_N": 0.07*T_to,
            "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, 
            "engine_params_override": {"tt_4": 850},
        },
    ]

    total_mission_emissions = {"m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0}
    total_fuel_used_kg = 0.0

    for segment_idx, segment in enumerate(mission_segments):
        print(f"--- Processing Segment {segment_idx + 1}: {segment['name']} ---")
        dt_seconds = segment["duration_minutes"] * 60.0

        current_engine_params = baseline_engine_config.copy()
        current_engine_params.update(segment["flight_conditions"])
        if "engine_params_override" in segment:
            current_engine_params.update(segment["engine_params_override"])
        
        analysis_params = {k: v for k, v in current_engine_params.items() if k not in ['mach_0', 'ts_0', 'ps_0']}
        
        tf_results = None
        segment_fuel_kg = nan
        ei_nox = nan

        try:
            tf_results = turbofan_parametric_analysis(
                mach_0=current_engine_params["mach_0"],
                ts_0=current_engine_params["ts_0"],
                ps_0=current_engine_params["ps_0"],
                **analysis_params 
            )
        except Exception as e:
            print(f"  ERROR during turbofan_parametric_analysis for segment {segment['name']}: {e}")
            tsfc = nan 
        
        if tf_results and len(tf_results) > 5:
            tsfc = tf_results[1]
            output_dict = tf_results[5]
            
            # DYNAMICALLY CALCULATE EI_NOX
            ps_0 = current_engine_params["ps_0"]
            h_est = atmosphere.get_altitude_from_pressure(ps_0)
            pt_3 = output_dict.get('pt_3', nan)
            tt_3 = output_dict.get('tt_3', nan)
            ei_nox = ei_nox_dallara(pt_3, tt_3, h_est)

            print(f"  Flight Conditions: M{current_engine_params['mach_0']}, Est. Alt {h_est:.0f}m")
            print(f"  Combustor Inlet: Tt3={tt_3:.1f}K, Pt3={pt_3/1e5:.2f}bar")
            print(f"  Calculated EI NOx: {ei_nox*1000:.2f} g/kg_fuel" if not isnan(ei_nox) else "  Calculated EI NOx: N/A")
        else:
            tsfc = nan

        if isnan(tsfc) or tsfc <= 0: 
            print(f"  Warning: Invalid TSFC ({tsfc}). Emissions will be NaN.")
            mdot_f = nan
        else: # Valid TSFC path
            mdot_f = segment["target_thrust_N"] * tsfc
            segment_fuel_kg = mdot_f * dt_seconds
            print(f"  Calculated TSFC: {tsfc*1e6:.2f} mg/Ns")
            print(f"  Target Thrust: {segment['target_thrust_N']:.0f} N -> Fuel Flow: {mdot_f:.4f} kg/s")
            print(f"  Fuel used this segment: {segment_fuel_kg:.2f} kg")

        segment_emissions_data = emissions(mdot_f, ei_nox, dt=dt_seconds)
        print(f"  Emissions for this segment (kg):")
        print(f"    m_nox: {segment_emissions_data['m_nox']:.4f}" if not isnan(segment_emissions_data.get('m_nox', nan)) else "    m_nox: NaN")
        
        # Accumulate totals
        if not isnan(segment_fuel_kg):
            if not isnan(total_fuel_used_kg):
                total_fuel_used_kg += segment_fuel_kg
        else:
            total_fuel_used_kg = nan

        for species_mass_key in total_mission_emissions.keys():
            if not isnan(segment_emissions_data.get(species_mass_key, nan)): 
                if not isnan(total_mission_emissions[species_mass_key]):
                    total_mission_emissions[species_mass_key] += segment_emissions_data[species_mass_key]
            else: 
                total_mission_emissions[species_mass_key] = nan
        print("-" * 40)

    print("\n--- Total Mission Summary ---")
    print(f"  Total Fuel Used: {total_fuel_used_kg:.2f} kg" if not isnan(total_fuel_used_kg) else "  Total Fuel Used: NaN kg")
    for species, total_mass in total_mission_emissions.items():
        print(f"  Total {species}: {total_mass:.2f} kg" if not isnan(total_mass) else f"  Total {species}: NaN kg")

    print("\nSimulation Finished.")

if __name__ == '__main__':
    # Initialize mock or real parameters
    params = DesignParameters()
    try:
        # If a real config file exists, use it
        params.load_from_yaml("design_config.yaml")
    except (FileNotFoundError, AttributeError):
        # Otherwise, the mock parameters in the class definition will be used
        print("Note: 'design_config.yaml' not found. Running with default mock parameters.")

    run_mission_simulation(params)

#main function 3 (comparison)
# --- Emissions Calculation Code (from emissions.py) ---
def fuelflow_to_emissionflow(mdot_f, ei):
    """
    Calculates the emission flow (in kg/s) from the fuel flow (kg/s) for a
    given emission index.

    :param mdot_f: Fuel mass flow in kg/s
    :param ei: Emission index of a species in kg/kg
    :return: Emission flow in kg/s
    """
    if isnan(mdot_f) or isnan(ei):
        return nan
    return mdot_f * ei

def emissions(mdot_f, ei_nox,
              ei_so4=2.0e-4, ei_soot=4.0e-5,
              ei_co2=3.16, ei_h2o=1.26,
              dt=1.):
    """
    Estimates the emission flow (in kg/s) and the total emission (in kg) for
    a given time step, for several species, given the fuel flow (in kg/s).
    This calculates emissions for ONE engine.

    :param mdot_f: Fuel flow in kg/s for one engine
    :param ei_nox: Emission index of Nitrogen Oxides (NO and NO2) in kg/kg
    :param ei_so4:  Emission index of Sulfate in kg/kg
    :param ei_soot:  Emission index of soot in kg/kg
    :param ei_co2:  Emission index of Carbon Dioxide in kg/kg
    :param ei_h2o:  Emission index of Water in kg/kg
    :param dt: Time step under consideration in seconds
    :return: Dictionary with emission flows and total emissions for every
    specie considered for one engine
    """
    if isnan(mdot_f) or isnan(dt):
        return dict(mdot_co2=nan, m_co2=nan,
                    mdot_h2o=nan, m_h2o=nan,
                    mdot_nox=nan, m_nox=nan,
                    mdot_so4=nan, m_so4=nan,
                    mdot_soot=nan, m_soot=nan)

    mdot_co2 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_co2)
    m_co2 = mdot_co2 * dt
    mdot_h2o = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_h2o)
    m_h2o = mdot_h2o * dt
    mdot_nox = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_nox)
    m_nox = mdot_nox * dt
    mdot_so4 = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_so4)
    m_so4 = mdot_so4 * dt
    mdot_soot = fuelflow_to_emissionflow(mdot_f=mdot_f, ei=ei_soot)
    m_soot = mdot_soot * dt

    emissions_dict = dict(mdot_co2=mdot_co2, m_co2=m_co2,
                          mdot_h2o=mdot_h2o, m_h2o=m_h2o,
                          mdot_nox=mdot_nox, m_nox=m_nox,
                          mdot_so4=mdot_so4, m_so4=m_so4,
                          mdot_soot=mdot_soot, m_soot=m_soot)
    return emissions_dict

# --- Turbofan Analysis Code (models ONE engine) ---
def turbofan_parametric_analysis(
        mach_0, ts_0, ps_0,  # flight conditions
        bpr, pr_fan, pr_lpc, pr_hpc, tt_4,  # design variables
        eta_fan, eta_lpc, eta_hpc, eta_hpt, eta_lpt,  # polytropic efficiencies
        eta_com=0.99, eta_mech_l=0.99, eta_mech_h=0.99,  # other efficiencies
        pr_com=0.95, pr_inl=0.98,
        bleed_to=0., power_tol=0., power_toh=0.,
        cooling_l=0., cooling_h=0.,
        lhv=43.e6,  # lower heating value J/kg
        full_output=True):
    """
    Carries out thermodynamic on-design / parametric analysis for a single turbofan engine.
    Returns: sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict (if full_output)
             or sf, tsfc, eta_thermal, eta_propulsive, eta_overall
    """
    global gpr # Allow access to the globally defined gpr (either real or placeholder)
    
    # 0 - freestream
    a_0 = gpr.s_o_s(ts_0, gas="air") # Freestream is air
    v_0 = mach_0 * a_0 if not (isnan(mach_0) or isnan(a_0)) else nan
    
    state_0_delta_h = 0.5 * v_0 ** 2 if not isnan(v_0) else nan
    
    try: # Use try-except for gpr calls as placeholder might be missing methods or fail
        state_0 = gpr.prescribed_delta_h(p_in=ps_0, t_in=ts_0, delta_h=state_0_delta_h, eta_pol=1., gas="air")
        pt_0 = state_0["p_out"]
        tt_0 = state_0["t_out"]
    except Exception as e_gpr:
        # print(f"  DEBUG gpr state_0: {e_gpr}")
        gamma_val_gpr = gpr.gamma_gas(ts_0, gas="air") if hasattr(gpr, 'gamma_gas') else 1.4
        pt_0 = ps_0 * (1 + (gamma_val_gpr-1)/2 * mach_0**2)**(gamma_val_gpr/(gamma_val_gpr-1)) if not isnan(mach_0) and (gamma_val_gpr-1)!=0 else nan
        tt_0 = ts_0 * (1 + (gamma_val_gpr-1)/2 * mach_0**2) if not isnan(mach_0) else nan

    hs_0 = gpr.specific_enthalpy(t=ts_0, gas="air")
    ht_0 = hs_0 + v_0 ** 2. / 2. if not (isnan(hs_0) or isnan(v_0)) else nan
    tau_0 = ht_0 / hs_0 if hs_0 != 0 and not isnan(ht_0) else nan
    
    # 2 - inlet exit / fan entry
    tt_2 = tt_0
    pt_2 = pr_inl * pt_0 if not (isnan(pr_inl) or isnan(pt_0)) else nan
    ht_2 = ht_0 # Enthalpy is conserved if no work/heat transfer in inlet

    # --- Component Calculations ---
    # All component calculations use gas="air" up to combustor inlet (station 3)
    # Fan (station 2 to 13)
    state_13 = gpr.prescribed_p_ratio(p_in=pt_2, t_in=tt_2, p_ratio=pr_fan, eta_pol=eta_fan, gas="air")
    pt_13 = state_13["p_out"]
    tt_13 = state_13["t_out"]
    ht_13 = state_13["h_out"]
    tau_fan = ht_13 / ht_2 if ht_2 != 0 and not isnan(ht_13) else nan

    # LPC (station 13 to 25)
    state_25 = gpr.prescribed_p_ratio(p_in=pt_13, t_in=tt_13, p_ratio=pr_lpc, eta_pol=eta_lpc, gas="air")
    pt_25 = state_25["p_out"]
    tt_25 = state_25["t_out"]
    ht_25 = state_25["h_out"]
    tau_lpc = ht_25 / ht_13 if ht_13 != 0 and not isnan(ht_25) else nan

    # HPC (station 25 to 3)
    state_3 = gpr.prescribed_p_ratio(p_in=pt_25, t_in=tt_25, p_ratio=pr_hpc, eta_pol=eta_hpc, gas="air")
    pt_3 = state_3["p_out"]
    tt_3 = state_3["t_out"] # Temperature at HPC exit / Combustor inlet
    ht_3 = state_3["h_out"] # Enthalpy at HPC exit / Combustor inlet
    tau_hpc = ht_3 / ht_25 if ht_25 != 0 and not isnan(ht_3) else nan

    # 4 - Combustor exit
    far_4 = nan 
    ht_4 = nan  
    
    if not any(isnan(val) for val in [ht_3, tt_3, tt_4, eta_com, lhv]) and lhv > 0 and eta_com > 0:
        cp_approx_comb = 1150.  # J/kg.K, approx for combustion products
        
        # Initial guess for far_4, more robust
        if tt_4 > tt_3:
            far_4_current = (cp_approx_comb * (tt_4 - tt_3)) / (eta_com * lhv - cp_approx_comb * (tt_4 - tt_3)) if (eta_com * lhv - cp_approx_comb * (tt_4 - tt_3)) !=0 else 0.02
            far_4_current = max(0.001, min(far_4_current, 0.07)) # Bound initial guess
        else: # tt_4 <= tt_3, implies no significant heat addition or cooling
            far_4_current = 0.0001 # Minimal far for property calculations if T doesn't rise

        far_4_previous = far_4_current + 1.0 # Ensure loop starts
        
        iterations = 0
        max_iterations = 100 
        tolerance = 1e-7 # Slightly tighter tolerance
        relaxation_factor = 0.6 # Under-relaxation

        while abs(far_4_current - far_4_previous) > tolerance and iterations < max_iterations:
            far_4_previous = far_4_current
            
            h_comb_exit_target_temp = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4_previous)

            if isnan(h_comb_exit_target_temp):
                # print(f"  DEBUG far_4 iter {iterations}: h_comb_exit_target_temp is NaN. far_prev={far_4_previous:.6f}, tt_4={tt_4:.2f}")
                far_4_candidate = nan 
                break 

            denominator = eta_com * lhv - h_comb_exit_target_temp
            
            if abs(denominator) < 1e-3: # Avoid division by very small number
                # print(f"  DEBUG far_4 iter {iterations}: Denominator too small ({denominator:.2e}). far_prev={far_4_previous:.6f}")
                # If denominator is small, it means h_comb_exit_target_temp is close to eta_com * lhv.
                # This usually implies very high FAR or tt_4. Try to break or use previous FAR.
                far_4_candidate = far_4_previous # Attempt to stabilize
                # iterations = max_iterations # Force exit if unstable
                break # Or break and declare non-convergence

            numerator = h_comb_exit_target_temp - ht_3
            far_4_candidate = numerator / denominator
            
            if isnan(far_4_candidate):
                # print(f"  DEBUG far_4 iter {iterations}: far_4_candidate NaN. Num={numerator:.2f},Denom={denominator:.2e},h_target={h_comb_exit_target_temp:.2f},ht_3={ht_3:.2f}")
                break

            far_4_current = far_4_previous + relaxation_factor * (far_4_candidate - far_4_previous)
            far_4_current = max(0.00001, min(far_4_current, 0.1)) # Bound current far_4

            iterations += 1

        if abs(far_4_current - far_4_previous) <= tolerance and not isnan(far_4_current):
            far_4 = far_4_current
        else:
            print(f"  WARNING: far_4 calculation did NOT converge after {iterations} iterations for tt_4={tt_4:.1f}K.")
            print(f"           Last far_4 values: current={far_4_current:.6f}, previous={far_4_previous:.6f}, diff={abs(far_4_current - far_4_previous):.2e}")
            print(f"           Inputs: ht_3={ht_3:.1f}, tt_3={tt_3:.1f}K, eta_com={eta_com}, lhv={lhv:.2e}")
            print(f"           Problematic calculated far_4 value before being set to NaN: {far_4_current}")
            far_4 = nan 

    if not isnan(far_4):
        ht_4 = gpr.specific_enthalpy(tt_4, gas="kerosene_in_air", far=far_4)
        if isnan(ht_4):
            # print(f"  WARNING: far_4 converged to {far_4:.6f}, but resulting ht_4 is NaN for tt_4 = {tt_4:.2f}")
            far_4 = nan # Invalidate far if ht_4 computation fails
    else:
        ht_4 = nan # Ensure ht_4 is NaN if far_4 is NaN

    pt_4 = pt_3 * pr_com if not (isnan(pt_3) or isnan(pr_com)) else nan
    tau_lambda = ht_4 / hs_0 if hs_0 != 0 and not isnan(ht_4) and not isnan(hs_0) else nan # Global enthalpy ratio
    
    # Station properties from here use gas="kerosene_in_air" and the calculated far_4
    # 41 - HPT Stator Inlet (after first cooling mixing if applicable)
    tau_m1 = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc):
        # Numerator: ( (1-bleed-coolL-coolH)*(1+far) + coolH * (tau0*tau_lpc*tau_hpc)/tau_lambda )
        # Denominator: ( (1-bleed-coolL-coolH)*(1+far) + coolH )
        term_cooling_h_eff = cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda if tau_lambda != 0 else nan
        
        if not isnan(term_cooling_h_eff):
            num_tau_m1 = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + term_cooling_h_eff
            den_tau_m1 = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h
            if den_tau_m1 != 0 and not isnan(num_tau_m1):
                tau_m1 = num_tau_m1 / den_tau_m1
    
    ht_41 = ht_4 * tau_m1 if not (isnan(ht_4) or isnan(tau_m1)) else nan
    
    # Effective FAR at station 41
    far_41 = nan
    if not isnan(far_4) and not (bleed_to + cooling_l + cooling_h >=1): # ensure (1-bleed-coolL-coolH) is positive
         # far_41 = far_4 / (1 + cooling_h / ((1-bleed-cool_l-cool_h)*(1+far_4))) -- this form is complex
         # Simpler: total fuel / (total air - fuel part of bleed/cool)
         # Effective fuel = (1-bleed-cool_l-cool_h)*far_4 (assuming fuel not in cooling air)
         # Effective air = (1-bleed-cool_l-cool_h) + cooling_h (core air + HPT cooling air)
         if ( (1. - bleed_to - cooling_l - cooling_h) + cooling_h ) != 0: # Total air at 41
            far_41 = ((1. - bleed_to - cooling_l - cooling_h) * far_4) / \
                     ((1. - bleed_to - cooling_l - cooling_h) + cooling_h)
    
    pt_41 = pt_4 # Pressure assumed constant through this mixing
    tt_41 = gpr.prescribed_h(ht_41, gas="kerosene_in_air", far=far_41) if not isnan(ht_41) and not isnan(far_41) else nan

    # HPT Work (station 41 to 44)
    tau_hpt = nan
    if not isnan(tau_lambda) and tau_lambda != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_fan) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(eta_mech_h) and not isnan(bpr) and not isnan(power_toh):
        
        # Numerator: tau0 * tau_fan * tau_lpc * (tau_hpc - 1) + (1+bpr)*power_toh / (hs0 * mdot_core_ref=1) -> power_toh is per unit core flow
        # Denominator: eta_mech_h * tau_lambda * [ (1-bleed-coolH-coolL)*(1+far) + coolH * (tau0*tau_lpc*tau_hpc)/tau_lambda ]
        # The term in bracket is den_tau_m1 from tau_m1 calculation if we assume m_dot_core_ref = 1 for power_toh
        # power_toh is specific power W / (kg/s) of core inlet air. Specific enthalpy hs0 J/kg. power_toh/hs0 is dimensionless
        power_toh_nondim = power_toh / hs_0 if hs_0 !=0 else 0.0

        num_tau_hpt = tau_0 * tau_fan * tau_lpc * (tau_hpc - 1.) + (1. + bpr) * power_toh_nondim
        
        term_cooling_h_eff_den = cooling_h * tau_0 * tau_lpc * tau_hpc / tau_lambda if tau_lambda != 0 else nan
        if not isnan(term_cooling_h_eff_den):
            den_tau_hpt_bracket = (1. - bleed_to - cooling_h - cooling_l) * (1. + far_4) + term_cooling_h_eff_den
            if not isnan(den_tau_hpt_bracket):
                den_tau_hpt = eta_mech_h * tau_lambda * den_tau_hpt_bracket
                if den_tau_hpt != 0 and not isnan(num_tau_hpt):
                    tau_hpt = 1. - (num_tau_hpt / den_tau_hpt)

    ht_44 = ht_41 * tau_hpt if not (isnan(ht_41) or isnan(tau_hpt)) else nan
    delta_h_hpt = ht_44 - ht_41 if not (isnan(ht_44) or isnan(ht_41)) else nan
    state_44 = gpr.prescribed_delta_h(p_in=pt_41, t_in=tt_41, delta_h=delta_h_hpt,
                                      eta_pol=eta_hpt, gas="kerosene_in_air", far=far_41)
    pt_44 = state_44["p_out"]
    tt_44 = state_44["t_out"]

    # 45 - LPT Stator Inlet (after second cooling mixing if applicable)
    tau_m2 = nan
    if not isnan(far_4) and not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_lambda) and tau_lambda != 0 and not isnan(tau_m1) and tau_m1 !=0 and \
       not isnan(tau_hpt) and tau_hpt != 0:
        # Numerator: (1-bleed-coolL-coolH)*(1+far) + coolH + coolL * (tau0*tau_lpc*tau_hpc)/(tau_lambda*tau_m1*tau_hpt)
        # Denominator: (1-bleed-coolL-coolH)*(1+far) + coolH + coolL
        den_tau_m1_hpt = tau_m1 * tau_hpt
        if den_tau_m1_hpt !=0:
            term_cooling_l_eff = cooling_l * tau_0 * tau_lpc * tau_hpc / (tau_lambda * den_tau_m1_hpt) if tau_lambda !=0 else nan
            if not isnan(term_cooling_l_eff):
                num_tau_m2 = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + term_cooling_l_eff
                den_tau_m2 = (1. - bleed_to - cooling_l - cooling_h) * (1. + far_4) + cooling_h + cooling_l
                if den_tau_m2 != 0 and not isnan(num_tau_m2):
                    tau_m2 = num_tau_m2 / den_tau_m2
    
    ht_45 = ht_44 * tau_m2 if not (isnan(ht_44) or isnan(tau_m2)) else nan
        
    far_45 = nan
    if not isnan(far_4) and not (bleed_to + cooling_l + cooling_h >=1):
         # Effective fuel = (1-bleed-cool_l-cool_h)*far_4
         # Effective air = (1-bleed-cool_l-cool_h) + cooling_h + cooling_l (core air + HPT cool + LPT cool)
         total_air_at_45 = (1. - bleed_to - cooling_l - cooling_h) + cooling_h + cooling_l
         if total_air_at_45 != 0:
            far_45 = ((1. - bleed_to - cooling_l - cooling_h) * far_4) / total_air_at_45
            
    pt_45 = pt_44 # Pressure assumed constant
    tt_45 = gpr.prescribed_h(ht_45, gas="kerosene_in_air", far=far_45) if not isnan(ht_45) and not isnan(far_45) else nan

    # LPT Work (station 45 to 5)
    tau_lpt = nan
    if not isnan(eta_mech_l) and not isnan(tau_lambda) and tau_lambda != 0 and \
       not isnan(tau_hpt) and tau_hpt != 0 and not isnan(far_4) and \
       not isnan(tau_0) and not isnan(tau_lpc) and not isnan(tau_hpc) and \
       not isnan(tau_fan) and not isnan(bpr) and not isnan(power_tol):


        power_tol_nondim = power_tol / hs_0 if hs_0 != 0 else 0.0
        

        # If power_tol is per unit core inlet flow:
        num_tau_lpt = tau_0 * ( tau_fan*(tau_lpc-1) + (1.+bpr)*(tau_fan-1) ) + (1.+bpr)*power_tol_nondim


        # Enthalpy available to LPT, nondimensionalized by hs0
        # (m_flow_LPT / m_core_ref) * (ht_45 - ht_5) / hs0 = (m_flow_LPT / m_core_ref) * tau_lambda * tau_m1 * tau_hpt * tau_m2 * (1 - tau_lpt) / eta_mech_l
        # m_flow_LPT / m_core_ref approx (1-bleed_to-cooling_h-cooling_l)*(1+far_4) + cooling_h + cooling_l
        m_ratio_lpt_gas = (1. - bleed_to - cooling_h - cooling_l)*(1.+far_4) + cooling_h + cooling_l if not isnan(far_4) else nan
        
        if not isnan(m_ratio_lpt_gas) and not isnan(tau_m1) and not isnan(tau_m2): #tau_m1 might be from HPT mixing
            den_tau_lpt_factor = eta_mech_l * tau_lambda * tau_m1 * tau_hpt * tau_m2 * m_ratio_lpt_gas
            if den_tau_lpt_factor != 0 and not isnan(num_tau_lpt):
                tau_lpt = 1. - (num_tau_lpt / den_tau_lpt_factor)

    ht_5 = ht_45 * tau_lpt if not (isnan(ht_45) or isnan(tau_lpt)) else nan
    delta_h_lpt = ht_5 - ht_45 if not (isnan(ht_5) or isnan(ht_45)) else nan
    state_5 = gpr.prescribed_delta_h(p_in=pt_45, t_in=tt_45, delta_h=delta_h_lpt,
                                     eta_pol=eta_lpt, gas="kerosene_in_air", far=far_45)
    pt_5 = state_5["p_out"]
    tt_5 = state_5["t_out"]

    # Nozzle calculations
    # 9 - Core exhaust nozzle
    # Properties at station 5 are tt_5, pt_5, ht_5, far_45 (effective FAR at LPT exit)
    ht_9, tt_9, pt_9, far_9 = ht_5, tt_5, pt_5, far_45
    mach_9, ps_9, ts_9, v_9, rho_9 = nan, nan, nan, nan, nan

    if not any(isnan(x) for x in [pt_9, ps_0, tt_9, far_9]) and ps_0 != 0:
        p_total_static_ratio_9 = pt_9 / ps_0
        g_9 = gpr.gamma_gas(tt_9, gas="kerosene_in_air", far=far_9)
        if not isnan(g_9) and g_9 > 1. and p_total_static_ratio_9 > 0:
            # Critical pressure ratio for choked flow
            pr_crit_9 = ( (g_9 + 1.) / 2. )**(g_9 / (g_9 - 1.)) if (g_9-1)!=0 else nan
            
            if not isnan(pr_crit_9) and p_total_static_ratio_9 >= pr_crit_9 : # Choked flow
                mach_9 = 1.0
                ts_9_val = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9) # T_static at throat
                ps_9_val = pt_9 / pr_crit_9 # P_static at throat
            else: # Unchoked flow
                # M^2 = (2/(gamma-1)) * [ (P0/P)^((gamma-1)/gamma) - 1 ]
                mach_i_9_sq_term = p_total_static_ratio_9 ** ((g_9 - 1.) / g_9) - 1. if (g_9)!=0 else nan
                if not isnan(mach_i_9_sq_term) and mach_i_9_sq_term >= 0 and (g_9-1)!=0:
                    mach_i_9_sq = (2. / (g_9 - 1.)) * mach_i_9_sq_term
                    mach_9 = sqrt(mach_i_9_sq)
                else: mach_9 = 0.0 # if P0/P <=1 or other issues
                ts_9_val = gpr.t_total_to_static(tt_9, mach_9, gas="kerosene_in_air", far=far_9)
                ps_9_val = ps_0 # Static pressure at nozzle exit is ambient for unchoked, unadapted nozzle

            ts_9 = ts_9_val
            ps_9 = ps_9_val
        else: # Cannot determine nozzle conditions
            mach_9, ts_9, ps_9 = 0.0, tt_9, pt_9 # Fallback if g_9 invalid or P0/P <=0 (should not happen)
            if p_total_static_ratio_9 <= 1 : ps_9 = ps_0 # Ensure exit pressure is at least ambient

        a_9 = gpr.s_o_s(ts_9, gas="kerosene_in_air", far=far_9) if not isnan(ts_9) else nan
        v_9 = mach_9 * a_9 if not (isnan(mach_9) or isnan(a_9)) else nan
        r_9 = gpr.r_gas(gas="kerosene_in_air", far=far_9)
        rho_9 = ps_9 / (r_9 * ts_9) if not any(isnan(x) for x in [ps_9,r_9,ts_9]) and r_9 * ts_9 != 0 else nan

    # 19 - Bypass exhaust nozzle
    # Properties at station 13 are tt_13, pt_13, ht_13 (gas is air, far=0)
    ht_19, tt_19, pt_19, far_19 = ht_13, tt_13, pt_13, 0.0 # Bypass is air
    mach_19, ps_19, ts_19, v_19, rho_19 = nan, nan, nan, nan, nan

    if not any(isnan(x) for x in [pt_19, ps_0, tt_19]) and ps_0 != 0:
        p_total_static_ratio_19 = pt_19 / ps_0
        g_19 = gpr.gamma_gas(tt_19, gas="air", far=far_19) # far_19 = 0
        if not isnan(g_19) and g_19 > 1. and p_total_static_ratio_19 > 0:
            pr_crit_19 = ( (g_19 + 1.) / 2. )**(g_19 / (g_19 - 1.)) if (g_19-1)!=0 else nan

            if not isnan(pr_crit_19) and p_total_static_ratio_19 >= pr_crit_19: # Choked
                mach_19 = 1.0
                ts_19_val = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
                ps_19_val = pt_19 / pr_crit_19
            else: # Unchoked
                mach_i_19_sq_term = p_total_static_ratio_19 ** ((g_19 - 1.) / g_19) - 1. if g_19!=0 else nan
                if not isnan(mach_i_19_sq_term) and mach_i_19_sq_term >= 0 and (g_19-1)!=0 :
                    mach_i_19_sq = (2. / (g_19 - 1.)) * mach_i_19_sq_term
                    mach_19 = sqrt(mach_i_19_sq)
                else: mach_19 = 0.0
                ts_19_val = gpr.t_total_to_static(tt_19, mach_19, gas="air", far=far_19)
                ps_19_val = ps_0
            
            ts_19 = ts_19_val
            ps_19 = ps_19_val
        else:
            mach_19, ts_19, ps_19 = 0.0, tt_19, pt_19
            if p_total_static_ratio_19 <=1 : ps_19 = ps_0

        a_19 = gpr.s_o_s(ts_19, gas="air", far=far_19) if not isnan(ts_19) else nan
        v_19 = mach_19 * a_19 if not (isnan(mach_19) or isnan(a_19)) else nan
        r_19 = gpr.r_gas(gas="air", far=far_19)
        rho_19 = ps_19 / (r_19 * ts_19) if not any(isnan(x) for x in [ps_19,r_19,ts_19]) and r_19*ts_19 != 0 else nan


    sf = nan

    # Check all inputs to SF. Note: far_4 is used for mass, far_9 for v_9 properties.
    if not any(isnan(x) for x in [far_4, v_9, bpr, v_19, v_0, ps_9, ps_0, rho_9, ps_19, rho_19, bleed_to]):
        if (1. + bpr) != 0: # Avoid division by zero if bpr = -1 (not physical)
            # Momentum thrust components
            # Core momentum relative to core inlet: (1-bleed_to)*(1+far_4)*v_9
            # Bypass momentum relative to core inlet: bpr*v_19
            # Inlet momentum relative to core inlet: (1+bpr)*v_0
            gross_thrust_mom_norm_by_core_inlet = (1.-bleed_to)*(1.+far_4)*v_9 + bpr*v_19
            ram_drag_norm_by_core_inlet = (1.+bpr)*v_0

            # Pressure thrust components (normalized by core inlet mass flow)
            # A_core_nozzle / m_dot_core_inlet = ( (1-bleed_to)*(1+far_4) ) / (rho_9 * v_9)
            # A_bypass_nozzle / m_dot_core_inlet = bpr / (rho_19 * v_19)
            pressure_thrust_core_norm = 0.0
            if not (rho_9 == 0 or v_9 == 0):
                pressure_thrust_core_norm = (ps_9 - ps_0) * (1.-bleed_to)*(1.+far_4) / (rho_9 * v_9)
            
            pressure_thrust_bypass_norm = 0.0
            if not (rho_19 == 0 or v_19 == 0):
                 pressure_thrust_bypass_norm = (ps_19 - ps_0) * bpr / (rho_19 * v_19)

            # Total net thrust normalized by core inlet mass flow
            net_thrust_norm_by_core_inlet = gross_thrust_mom_norm_by_core_inlet - ram_drag_norm_by_core_inlet + \
                                            pressure_thrust_core_norm + pressure_thrust_bypass_norm
            
            # Specific thrust is net thrust / total inlet mass flow (m_dot_0)
            # m_dot_0 = m_dot_core_inlet * (1+bpr)
            # So, SF = net_thrust_norm_by_core_inlet / (1+bpr)
            sf = net_thrust_norm_by_core_inlet / (1. + bpr)

    tsfc = nan # Thrust Specific Fuel Consumption (kg_fuel/sec) / N
    # TSFC = ( m_dot_fuel / m_dot_core_inlet ) / ( F_net / m_dot_core_inlet )
    # m_dot_fuel / m_dot_core_inlet = far_4 * (1 - bleed_to - cooling_h - cooling_l) (fuel burned per unit core inlet air)
    # F_net / m_dot_core_inlet = sf * (1+bpr)
    fuel_flow_norm_by_core_inlet = far_4 * (1. - bleed_to - cooling_l - cooling_h) if not isnan(far_4) else nan
    
    if not isnan(fuel_flow_norm_by_core_inlet) and not isnan(sf) and sf != 0 and (1.+bpr)!=0 :
        # net_thrust_norm_by_core_inlet = sf * (1.+bpr)
        # if net_thrust_norm_by_core_inlet != 0 :
        #     tsfc = fuel_flow_norm_by_core_inlet / net_thrust_norm_by_core_inlet
        # Or using sf directly: TSFC = far_4_comb / (SF * (1+BPR_eff)) where BPR_eff depends on where SF is normalized
        # If SF is F_net / m_dot_0_total, then TSFC = (m_dot_f / m_dot_0_total) / SF
        # m_dot_f / m_dot_0_total = far_4_comb_eff * (m_dot_core_main / m_dot_0_total)
        # m_dot_core_main / m_dot_0_total = (1-bleed-coolH-coolL)/(1+bpr)
        # TSFC = [ far_4 * (1-bleed-coolH-coolL) / (1+bpr) ] / SF
        tsfc_num = fuel_flow_norm_by_core_inlet / (1.+bpr) # Fuel flow per unit total air m_dot_0
        if sf != 0: # Avoid division by zero if specific thrust is zero
             tsfc = tsfc_num / sf
    
    opr = pr_inl * pr_fan * pr_lpc * pr_hpc if not any(isnan(x) for x in [pr_inl, pr_fan, pr_lpc, pr_hpc]) else nan

    # Efficiencies
    eta_thermal, eta_propulsive, eta_overall = nan, nan, nan
    
    
    # Ideal exit velocities including pressure thrust term (v_effective)
    v_9_eff = v_9
    if not (isnan(v_9) or isnan(rho_9) or rho_9 == 0 or v_9 == 0 or isnan(ps_9) or isnan(ps_0)):
        v_9_eff += (ps_9 - ps_0) / (rho_9 * v_9)
    v_19_eff = v_19
    if not (isnan(v_19) or isnan(rho_19) or rho_19 == 0 or v_19 == 0 or isnan(ps_19) or isnan(ps_0)):
        v_19_eff += (ps_19 - ps_0) / (rho_19 * v_19)

    # Net rate of KE increase (joule/sec per kg/sec of m_dot_0)
    # This is essentially the specific work output of the cycle that becomes jet power.
    delta_ke_specific = nan
    if not any(isnan(x) for x in [far_4, v_9_eff, bpr, v_19_eff, v_0, bleed_to]):
        # Mass fraction of core exhaust relative to m_dot_0
        mf_core_exit = (1.-bleed_to)*(1.+far_4) / (1.+bpr)
        # Mass fraction of bypass exhaust relative to m_dot_0
        mf_bypass_exit = bpr / (1.+bpr)
        
        delta_ke_specific = mf_core_exit * (v_9_eff**2 / 2.) + \
                            mf_bypass_exit * (v_19_eff**2 / 2.) - \
                            (v_0**2 / 2.) # Inlet KE relative to m_dot_0

    # Fuel energy input per unit of m_dot_0
    fuel_energy_specific = nan
    if not isnan(fuel_flow_norm_by_core_inlet) and not isnan(lhv):
        fuel_energy_specific = (fuel_flow_norm_by_core_inlet / (1.+bpr)) * lhv # fuel_flow_norm_by_core_inlet already has (1-b-c-c)

    if not isnan(delta_ke_specific) and not isnan(fuel_energy_specific) and fuel_energy_specific != 0:
        eta_thermal = delta_ke_specific / fuel_energy_specific
    
    # Propulsive efficiency: eta_p = (Net Thrust * v_0) / Rate of KE increase
    # Net Thrust * v_0 = (sf * m_dot_0) * v_0. Per unit m_dot_0 = sf * v_0
    # Rate of KE increase = delta_ke_specific * m_dot_0. Per unit m_dot_0 = delta_ke_specific
    if not isnan(sf) and not isnan(v_0) and not isnan(delta_ke_specific) and delta_ke_specific != 0:
         eta_propulsive = (sf * v_0) / delta_ke_specific

    if not (isnan(eta_thermal) or isnan(eta_propulsive)):
        eta_overall = eta_thermal * eta_propulsive
    
    output_dict = dict(
        mach_0=mach_0, ts_0=ts_0, ps_0=ps_0, bpr=bpr, tt_4=tt_4,
        pr_fan=pr_fan, pr_lpc=pr_lpc, pr_hpc=pr_hpc, opr=opr,
        far_4=far_4, tsfc=tsfc, sf=sf,
        v_9=v_9, v_19=v_19,
        tt_3=tt_3, tt_5=tt_5, tt_9=tt_9, tt_19=tt_19,
        eta_thermal=eta_thermal, eta_propulsive=eta_propulsive, eta_overall=eta_overall,
        pt_0=pt_0, pt_2=pt_2, pt_13=pt_13, pt_25=pt_25, pt_3=pt_3, pt_4=pt_4,
        pt_41=pt_41, pt_44=pt_44, pt_45=pt_45, pt_5=pt_5, pt_9=pt_9, pt_19=pt_19,
        tt_0=tt_0, tt_2=tt_2, tt_13=tt_13, tt_25=tt_25, tt_41=tt_41, tt_44=tt_44, tt_45=tt_45, 
        tau_0=tau_0, tau_fan=tau_fan, tau_lpc=tau_lpc, tau_hpc=tau_hpc, tau_lambda=tau_lambda,
        tau_m1=tau_m1, tau_hpt=tau_hpt, tau_m2=tau_m2, tau_lpt=tau_lpt,
        eta_fan=eta_fan, eta_lpc=eta_lpc, eta_hpc=eta_hpc, eta_hpt=eta_hpt, eta_lpt=eta_lpt,
        eta_com=eta_com, eta_mech_l=eta_mech_l, eta_mech_h=eta_mech_h,
        pr_com=pr_com, pr_inl=pr_inl,
        bleed_to=bleed_to, power_tol=power_tol, power_toh=power_toh,
        cooling_l=cooling_l, cooling_h=cooling_h, lhv=lhv,
        far_41=far_41, far_45=far_45,
        ht_0=ht_0, ht_2=ht_2, ht_13=ht_13, ht_25=ht_25, ht_3=ht_3, ht_4=ht_4, 
        ht_41=ht_41, ht_44=ht_44, ht_45=ht_45, ht_5=ht_5, ht_9=ht_9, ht_19=ht_19,
        v_0=v_0, ps_9=ps_9, ts_9=ts_9, mach_9=mach_9, ps_19=ps_19, ts_19=ts_19, mach_19=mach_19, # Added more nozzle details
        rho_9=rho_9, rho_19=rho_19 # Added densities
    )

    if full_output:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    else:
        return sf, tsfc, eta_thermal, eta_propulsive, eta_overall

def print_detailed_results(results, engine_name="Engine Run"):
    """Prints the turbofan analysis results."""
    if results is None or len(results) < 5: 
        print(f"\n--- {engine_name}: Incomplete or No Results ---")
        if results: pprint.pprint(results) # Use pprint for potentially complex partial results
        return

    sf, tsfc, eta_thermal, eta_propulsive, eta_overall = results[:5]
    output_dict = results[5] if len(results) > 5 else {}

    print(f"\n--- {engine_name}: Performance Metrics (Single Engine) ---")
    print(f"  Specific Thrust (SF):                   {sf:.2f} N/(kg/s)" if not isnan(sf) else "  Specific Thrust (SF):                   N/A")
    print(f"  Thrust Specific Fuel Consumption (TSFC):  {tsfc*1e6:.2f} mg/(N·s)" if not isnan(tsfc) else "  Thrust Specific Fuel Consumption (TSFC):  N/A")
    print(f"  Thermal Efficiency (eta_thermal):       {eta_thermal*100:.2f}%" if not isnan(eta_thermal) else "  Thermal Efficiency (eta_thermal):       N/A")
    print(f"  Propulsive Efficiency (eta_propulsive): {eta_propulsive*100:.2f}%" if not isnan(eta_propulsive) else "  Propulsive Efficiency (eta_propulsive): N/A")
    print(f"  Overall Efficiency (eta_overall):       {eta_overall*100:.2f}%" if not isnan(eta_overall) else "  Overall Efficiency (eta_overall):       N/A")
    
    opr_val = output_dict.get('opr', nan)
    print(f"  Overall Pressure Ratio (OPR):           {opr_val:.2f}" if not isnan(opr_val) else "  Overall Pressure Ratio (OPR):           N/A")

    if output_dict: 
        print(f"\n--- {engine_name}: Selected Cycle Parameters (from output_dict) ---")
        # Extended list of keys for detailed printing
        ordered_keys = [
            # Inputs
            'mach_0', 'ts_0', 'ps_0', 'bpr', 'tt_4', 'lhv',
            'pr_inl', 'pr_fan', 'pr_lpc', 'pr_hpc', 'pr_com', 
            'eta_fan', 'eta_lpc', 'eta_hpc', 'eta_hpt', 'eta_lpt',
            'eta_com', 'eta_mech_l', 'eta_mech_h',
            'bleed_to', 'power_tol', 'power_toh', 'cooling_l', 'cooling_h',
            # Key Calculated Ratios & Values
            'opr', 'far_4', 'far_41', 'far_45',
            'tau_0', 'tau_lambda', 'tau_fan', 'tau_lpc', 'tau_hpc', 
            'tau_m1', 'tau_hpt', 'tau_m2', 'tau_lpt',
            # Temperatures at stations
            'tt_0', 'tt_2', 'tt_13', 'tt_25', 'tt_3', 'tt_41', 'tt_44', 'tt_45', 'tt_5', 'tt_9', 'tt_19',
            # Pressures at stations
            'pt_0', 'pt_2', 'pt_13', 'pt_25', 'pt_3', 'pt_4', 'pt_41', 'pt_44', 'pt_45', 'pt_5', 'pt_9', 'pt_19',
            # Enthalpies (optional, can be verbose)
            # 'ht_0', 'ht_2', 'ht_13', 'ht_25', 'ht_3', 'ht_4', 'ht_41', 'ht_44', 'ht_45', 'ht_5', 'ht_9', 'ht_19',
            # Nozzle Exit Conditions
            'v_0', 'v_9', 'mach_9', 'ts_9', 'ps_9', 'rho_9',
            'v_19', 'mach_19', 'ts_19', 'ps_19', 'rho_19',
            # Performance
            'sf', 'tsfc', 'eta_thermal', 'eta_propulsive', 'eta_overall'
        ]
        printed_keys = set()
        for key in ordered_keys:
            if key in output_dict:
                value = output_dict[key]
                # Choose formatting based on typical magnitude or type
                if key in ['lhv', 'ht_0', 'ht_2', 'ht_13', 'ht_25', 'ht_3', 'ht_4', 'ht_41', 'ht_44', 'ht_45', 'ht_5', 'ht_9', 'ht_19', 'ps_0', 'ps_9', 'ps_19', 'pt_0', 'pt_2', 'pt_13', 'pt_25', 'pt_3', 'pt_4', 'pt_41', 'pt_44', 'pt_45', 'pt_5', 'pt_9', 'pt_19']:
                     print(f"  {key:<20}: {value:.2e}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")
                elif key in ['tsfc', 'far_4', 'far_41', 'far_45']:
                     print(f"  {key:<20}: {value:.4e}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")
                else:
                     print(f"  {key:<20}: {value:.3f}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")
                printed_keys.add(key)
        
        remaining_keys = set(output_dict.keys()) - printed_keys
        if remaining_keys:
            print("\n  --- Other Parameters (Not in Ordered List from output_dict) ---")
            for key in sorted(list(remaining_keys)):
                value = output_dict[key]
                print(f"  {key:<20}: {value:.4f}" if isinstance(value, float) and not isnan(value) else f"  {key:<20}: {value}")

    print("--- End of Detailed Report ---")


# --- Main Mission Simulation Function ---
def run_mission_simulation(aircraft_name: str, config: dict):
    print(f"Starting Aircraft Mission Emissions Simulation for {aircraft_name.upper()}...\n")

    num_engines = config["num_engines"]
    baseline_engine_config_single_engine = config["baseline_engine_config"]
    mission_segments = config["mission_segments"] 

    print(f"Aircraft: {aircraft_name.upper()}, Number of Engines: {num_engines}")
    print(f"Baseline Engine Config (single engine):")
    pprint.pprint(baseline_engine_config_single_engine, indent=2)
    print("-" * 40)

    total_mission_emissions_single_engine = {
        "m_co2": 0.0, "m_h2o": 0.0, "m_nox": 0.0, "m_so4": 0.0, "m_soot": 0.0
    }
    total_fuel_used_kg_single_engine = 0.0
    
    all_segments_valid = True # Flag to track if all segments produced valid TSFC

    for segment_idx, segment in enumerate(mission_segments):
        print(f"--- Processing Segment {segment_idx + 1}: {segment['name']} for {aircraft_name.upper()} ---")

        dt_seconds = segment["duration_minutes"] * 60.0
        target_thrust_N_per_engine = segment["target_thrust_N"] 

        current_engine_params_single_engine = baseline_engine_config_single_engine.copy()
        current_engine_params_single_engine.update(segment["flight_conditions"])
        if "engine_params_override" in segment:
            current_engine_params_single_engine.update(segment["engine_params_override"])
        
        analysis_params_single_engine = {
            k: v for k, v in current_engine_params_single_engine.items() 
            if k not in ['mach_0', 'ts_0', 'ps_0']
        }
        
        tf_results_single_engine = None
        segment_fuel_kg_single_engine = nan
        tsfc_single_engine = nan 

        try:
            tf_results_single_engine = turbofan_parametric_analysis(
                mach_0=current_engine_params_single_engine["mach_0"],
                ts_0=current_engine_params_single_engine["ts_0"],
                ps_0=current_engine_params_single_engine["ps_0"],
                **analysis_params_single_engine 
            )
            if tf_results_single_engine is not None and len(tf_results_single_engine) > 1:
                 tsfc_single_engine = tf_results_single_engine[1]
            else: # Should not happen if no exception, but as a safeguard
                 tsfc_single_engine = nan

        except Exception as e: # Catch any exception during turbofan_parametric_analysis
            print(f"  ERROR during turbofan_parametric_analysis for segment {segment['name']}: {e}")
            # This prints the exception object, which might include the "Failed to converge..." message if it was raised as an exception.
            # If it was just a print in gpr, this 'e' might be a subsequent math error.
            print(f"  Problematic inputs for single engine: M0={current_engine_params_single_engine['mach_0']}, Ts0={current_engine_params_single_engine['ts_0']}, Ps0={current_engine_params_single_engine['ps_0']}")
            tsfc_single_engine = nan # Ensure tsfc is nan if analysis fails

        # Check tsfc_single_engine irrespective of exception for NaN or non-positive
        if isnan(tsfc_single_engine) or tsfc_single_engine <= 0: 
            all_segments_valid = False # Mark that at least one segment had issues
            print(f"  Warning: Invalid or zero TSFC ({tsfc_single_engine}) obtained for segment {segment['name']} (single engine). Emissions for this segment will be NaN.")
            if tf_results_single_engine is not None and len(tf_results_single_engine) > 5 and tf_results_single_engine[5]: # Check if output_dict exists
                print_detailed_results(tf_results_single_engine, f"Details for {segment['name']} (Invalid TSFC - Single Engine)")
            else:
                print(f"  No detailed turbofan results available for {segment['name']} due to earlier failure or NaN TSFC.")

            mdot_f_single_engine = nan
            segment_emissions_data_single_engine = emissions(nan, segment["ei_nox"], dt=dt_seconds) # Emissions will be NaN
        else: # Valid TSFC
            mdot_f_single_engine = target_thrust_N_per_engine * tsfc_single_engine
            segment_fuel_kg_single_engine = mdot_f_single_engine * dt_seconds
            
            print(f"  Flight Conditions: M0={current_engine_params_single_engine['mach_0']}, Ts0={current_engine_params_single_engine['ts_0']:.2f}K, Ps0={current_engine_params_single_engine['ps_0']:.0f}Pa")
            print(f"  Target Thrust PER ENGINE: {target_thrust_N_per_engine:.0f} N")
            print(f"  Calculated TSFC (single engine): {tsfc_single_engine:.4e} (kg_fuel/s)/N")
            print(f"  Calculated Fuel Flow (mdot_f) (single engine): {mdot_f_single_engine:.4f} kg/s")
            print(f"  Fuel used this segment (single engine): {segment_fuel_kg_single_engine:.2f} kg")

            segment_emissions_data_single_engine = emissions(mdot_f_single_engine, segment["ei_nox"], dt=dt_seconds)
            print(f"  Emissions for this segment (single engine) (kg):")
            for species, mass in segment_emissions_data_single_engine.items():
                if species.startswith("m_"): 
                    print(f"    {species}: {mass:.4f}" if not isnan(mass) else f"    {species}: NaN")
        
        if not isnan(segment_fuel_kg_single_engine):
            if not isnan(total_fuel_used_kg_single_engine): # Only add if total is not already NaN
                total_fuel_used_kg_single_engine += segment_fuel_kg_single_engine
        else: # If current segment fuel is NaN, total becomes NaN
            total_fuel_used_kg_single_engine = nan

        for species_mass_key in total_mission_emissions_single_engine.keys():
            segment_species_mass = segment_emissions_data_single_engine.get(species_mass_key, nan)
            if not isnan(segment_species_mass): 
                if not isnan(total_mission_emissions_single_engine[species_mass_key]):
                    total_mission_emissions_single_engine[species_mass_key] += segment_species_mass
            else: # If current segment emission is NaN, total for that species becomes NaN
                total_mission_emissions_single_engine[species_mass_key] = nan 
        print("-" * 40)

    # Calculate total for all engines
    total_fuel_used_kg_all_engines = total_fuel_used_kg_single_engine * num_engines if not isnan(total_fuel_used_kg_single_engine) else nan
    total_mission_emissions_all_engines = {
        key: (value * num_engines if not isnan(value) else nan)
        for key, value in total_mission_emissions_single_engine.items()
    }

    print(f"\n--- Total Mission Summary for {aircraft_name.upper()} ({num_engines} engine(s)) ---")
    if not all_segments_valid:
        print("  NOTE: One or more segments failed to produce valid results. Total mission values may be NaN or incomplete.")
    print(f"  Total Fuel Used (all engines): {total_fuel_used_kg_all_engines:.2f} kg" if not isnan(total_fuel_used_kg_all_engines) else "  Total Fuel Used (all engines): NaN kg")
    for species, total_mass in total_mission_emissions_all_engines.items():
        print(f"  Total {species} (all engines): {total_mass:.2f} kg" if not isnan(total_mass) else f"  Total {species} (all engines): NaN kg")

    print(f"\nSimulation for {aircraft_name.upper()} Finished.\n" + "="*50 + "\n")


if __name__ == '__main__':

    # if not gpr_module_loaded_successfully:
    #     print("*"*70)
    #     print("*" + " " * 68 + "*")
    #     print("* CRITICAL WARNING: The actual 'gas_property_relations.py' module   *")
    #     print("* was NOT loaded. A basic placeholder is being used.              *")
    #     print("* RESULTS FOR COMBUSTION, TURBINE, AND NOZZLE CALCULATIONS WILL BE  *")
    #     print("* HIGHLY INACCURATE OR MAY FAIL (e.g. 'far_4' convergence).       *")
    #     print("* Please ensure 'gas_property_relations.py' is in your Python     *")
    #     print("* path and does not have import errors itself.                    *")
    #     print("*" + " " * 68 + "*")
    #     print("*"*70 + "\n")

    T_TAKEOFF_ORIGINAL_PER_ENGINE = params.engine.T_TO # Original takeoff thrust per engine in Newtons (from the original code)
    
    aircraft_configs = {
        "AERIS": {
            "num_engines": 1, 
            "baseline_engine_config": {
                "bpr": 3.3, "pr_fan": 1.9, "pr_lpc": 1.5, "pr_hpc": 5.65, "tt_4": 1400.,
                "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9,
                "eta_hpt": 0.93, "eta_lpt": 0.93,
                "eta_com": 0.99, "eta_mech_l": 0.99, "eta_mech_h": 0.99,
                "pr_com": 0.95, "pr_inl": 0.98,
                "bleed_to": 0., "power_tol": 0., "power_toh": 0.,
                "cooling_l": 0., "cooling_h": 0.,
                "lhv": 43.e6, 
                "full_output": True
            },
            "mission_segments": [
#               {"name": "Engine Start & Warm-Up", "duration_minutes": 10, "target_thrust_N": 0.07 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.0, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}, "ei_nox": 0.004 },
#               {"name": "Taxi", "duration_minutes": 10, "target_thrust_N": 0.12 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.02, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 900}, "ei_nox": 0.005 },
                {"name": "Take-off", "duration_minutes": 5, "target_thrust_N": T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.21, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1450, "pr_fan": 2.0, "pr_hpc": 6.0}, "ei_nox": 0.020 },
                {"name": "Climb", "duration_minutes": 20, "target_thrust_N": 0.85 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.65, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1350}, "ei_nox": 0.018 },
                {"name": "Cruise", "duration_minutes": 200, "target_thrust_N": params.engine.cruise_thrust, "flight_conditions": {"mach_0": 0.80, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1250}, "ei_nox": 0.012 },
            #    {"name": "Diversion Cruise (460km)", "duration_minutes": 34, "target_thrust_N": 2000, "flight_conditions": {"mach_0": 0.75, "ts_0": 228.7, "ps_0": 30090}, "engine_params_override": {"tt_4": 1200}, "ei_nox": 0.011 },
            #    {"name": "Loiter (2 hours)", "duration_minutes": 120, "target_thrust_N": 800, "flight_conditions": {"mach_0": 0.25, "ts_0": 285.2, "ps_0": 95970}, "engine_params_override": {"tt_4": 880}, "ei_nox": 0.005 },
            #    {"name": "Descent (to Diversion Airport)", "duration_minutes": 15, "target_thrust_N": 0.08 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.55, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 900}, "ei_nox": 0.006 },
            #    {"name": "Landing (at Diversion Airport)", "duration_minutes": 5, "target_thrust_N": 0.18 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.20, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1000}, "ei_nox": 0.008 },
            #    {"name": "Taxi & Shutdown (at Diversion Airport)", "duration_minutes": 5, "target_thrust_N": 0.07 * T_TAKEOFF_ORIGINAL_PER_ENGINE, "flight_conditions": {"mach_0": 0.01, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 850}, "ei_nox": 0.004 },
            ]
        },
        "HALO": {
            "num_engines": 2, 
            "baseline_engine_config": {
                "bpr": 4.2, "pr_fan": 1.5, "pr_lpc": 1.2, "pr_hpc": 24.0, "tt_4": 1500.,
                "eta_fan": 0.92, "eta_lpc": 0.91, "eta_hpc": 0.90,
                "eta_hpt": 0.93, "eta_lpt": 0.94,
                "eta_com": 0.99, "eta_mech_l": 0.99, "eta_mech_h": 0.99,
                "pr_com": 0.96, "pr_inl": 0.98,
                "bleed_to": 0.01, "power_tol": 10e3, "power_toh": 15e3, 
                "cooling_l": 0.03, "cooling_h": 0.05, 
                "lhv": 43.e6, 
                "full_output": True
            },
            "mission_segments": [
                { "name": "Take-off HALO", "duration_minutes": 5, "target_thrust_N": 26220, "flight_conditions": {"mach_0": 0.25, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1550}, "ei_nox": 0.020 },
                { "name": "Climb HALO", "duration_minutes": 20, "target_thrust_N": 22287, "flight_conditions": {"mach_0": 0.70, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1450}, "ei_nox": 0.018 }, #cruise thrust is 0.2 mtto
                { "name": "Cruise HALO", "duration_minutes": 400, "target_thrust_N": 7866.15, "flight_conditions": {"mach_0": 0.82, "ts_0": 216.65, "ps_0": 18753.9}, "engine_params_override": {"tt_4": 1300}, "ei_nox": 0.010 },
                # Add more HALO segments here
            ]
        },
        "PH_LAB": {
            "num_engines": 2, 
            "baseline_engine_config": {
                "bpr": 3.9, "pr_fan": 1.55, "pr_lpc": 1.2, "pr_hpc": 7.47, "tt_4": 1283.15, 
                "eta_fan": 0.915, "eta_lpc": 0.9, "eta_hpc": 0.9,
                "eta_hpt": 0.93, "eta_lpt": 0.93,
                "eta_com": 0.99, "eta_mech_l": 0.99, "eta_mech_h": 0.99,
                "pr_com": 0.95, "pr_inl": 0.98,
                "bleed_to": 0., "power_tol": 0., "power_toh": 0.,
                "cooling_l": 0., "cooling_h": 0.,
                "lhv": 43.e6, 
                "full_output": True
            },
            "mission_segments": [
                { "name": "Take-off PH_LAB", "duration_minutes": 5, "target_thrust_N": 9711.9, "flight_conditions": {"mach_0": 0.22, "ts_0": 288.15, "ps_0": 101325}, "engine_params_override": {"tt_4": 1650}, "ei_nox": 0.020 },
                { "name": "Climb PH_LAB", "duration_minutes": 20, "target_thrust_N": 8255.115, "flight_conditions": {"mach_0": 0.4, "ts_0": 249.1, "ps_0": 46560}, "engine_params_override": {"tt_4": 1500}, "ei_nox": 0.018},
                { "name": "Cruise PH-LAB", "duration_minutes": 120, "target_thrust_N": 2913.57, "flight_conditions": {"mach_0": 0.7, "ts_0": 230.0, "ps_0": 35000.0}, "engine_params_override": {"tt_4": 1200}, "ei_nox": 0.0010 },
                # Add more PH_LAB segments here
            ]
        }
    }

    for aircraft_name, config_data in aircraft_configs.items():
        if not config_data["mission_segments"]:
            print(f"Skipping {aircraft_name.upper()} as mission segments are not defined.")
            print("="*50 + "\n")
            continue
        if not config_data["baseline_engine_config"] or config_data["baseline_engine_config"].get("tt_4", 0) == 0: 
             print(f"Skipping {aircraft_name.upper()} as baseline_engine_config is not fully defined (e.g., tt_4 is 0 or dict is empty).")
             print("="*50 + "\n")
             continue
        run_mission_simulation(aircraft_name, config_data)

    
#main function 4
    # Propulsion System Weight Calculation
def calculate_propulsion_system_weight(params: DesignParameters):
    lbs_to_kg = 0.45359237
    kg_to_lbs = 1 / lbs_to_kg
    n_to_lbf = 0.224809
    m_to_ft = 3.28084# Convert units


    We = 516 #lbs, engine weight
    We_kg = We * lbs_to_kg  # convert to kg
    T_to = 7450 * n_to_lbf  #lbf, thrust takeoff
    L_d = 7.28 #duct lenght, ft
    Kd = 1 #curved duct
    A_inl = 9.5 #inlet area, ft^2

    W_ai = 11.45*(L_d*Kd*A_inl**0.5)**0.7331
    W_ai_kg = W_ai * lbs_to_kg  # convert to kg

    Ksp = 6.47 #lbs/gal (density of Jet A-1)
    W_fuel = 1429.18 * kg_to_lbs # fuel weight in lbs
    W_fs = (0.4/Ksp) * W_fuel  # lbs, fuel system weight
    W_fs_kg = W_fs * lbs_to_kg  # convert to kg
    print(f"Fuel System Weight: {W_fs:.2f} lbs / {W_fs_kg:.2f} kg")


    L_fus = 10*m_to_ft  # fuselage length in ft
    Kec = 0.686
    W_ec = Kec *(L_fus**0.792) #Engine control weight in lbs
    W_ec_kg = W_ec * lbs_to_kg  # convert to kg
    W_e = 1400 * kg_to_lbs  #empty weight of the engine in lbs
    W_ess = 38.93*(W_e/1000)**0.918 #lbs, engine starter system weight
    W_ess_kg = W_ess * lbs_to_kg  # convert to kg

    W_nacelle = 0.065*T_to  # lbs, nacelle weight
    W_nacelle_kg = W_nacelle * lbs_to_kg  # convert to kg

    W_prop_sys = We + W_ai + W_fs + W_ec + W_ess + W_nacelle  # total propulsion system weight in lbs
    W_prop_sys_kg = W_prop_sys * lbs_to_kg  # convert to kg

    #weight includes, engine, starter, fuel system, air induction systems and nacelle
    # nacelle weight includes pylon weight
    print(f"Propulsion System Weight: {W_prop_sys:.2f} lbs / {W_prop_sys_kg:.2f} kg")
    #print engine starter weight
    #print(f"Engine Starter System Weight: {W_ess:.2f} lbs / {W_ess_kg:.2f} kg")
    #print nacelle weight
    print(f"Nacelle Weight: {W_nacelle:.2f} lbs / {W_nacelle_kg:.2f} kg")

    W_electrical = 140 # kg, electrical system weight
    W_electrical_lbs = W_electrical * kg_to_lbs  # convert to lbs
    print(f"Electrical System Weight: {W_electrical_lbs:.2f} lbs / {W_electrical:.2f} kg")

    return {
        'propulsion_system_weight_kg': W_prop_sys_kg,
        'engine_weight_kg': We_kg,
        'fuel_system_weight_kg': W_fs_kg,
        'nacelle_weight_kg': W_nacelle_kg,
        'electrical_system_weight_kg': W_electrical
    }

#main function 5
def fuselage_exhaust_cone_analysis():
    # 2. Create an instance of the DesignParameters class.
    #    This object will contain all the nested parameter objects, including 'fuselage'.
    aircraft = DesignParameters()

    # 3. Now you can access the fuselage object and its attributes directly.
    fuselage_length = aircraft.fuselage.l_f
    max_diameter = aircraft.fuselage.D_f
    nose_length = aircraft.fuselage.l_n
    cross_sections = aircraft.fuselage.crosssections

    # 4. You can now use these variables in your new script.
    print(f"Aircraft Fuselage Length: {fuselage_length} m")
    print(f"Maximum Fuselage Diameter: {max_diameter} m")

    # You can also access nested data like the dimensions of a specific cross-section
    section_2_width = cross_sections['crosssection_2']['Dimensions']['Width']
    print(f"Width of fuselage cross-section 2: {section_2_width} m")

    # You can also pass the fuselage object itself to other functions
    def analyze_fuselage(fuselage_params):
        print("\n--- Running Fuselage Analysis ---")
        print(f"Analyzing a fuselage with length-to-diameter ratio of: {fuselage_params.lf_df:.2f}")


    # Access the 'Width' from the 'Dimensions' of 'crosssection_3'
    cs3_width = aircraft.fuselage.crosssections['crosssection_3']['Dimensions']['Width']

    print(f"The width of fuselage cross-section 3 is: {cs3_width} m")

    eng_nozz_diameter = 0.49   # Example nozzle diameter in meters
    distance_to_edge = cs3_width/2 - eng_nozz_diameter/2  # Distance from the edge of the fuselage to the nozzle edge
    print(f"Distance from the edge of fuselage to engine nozzle edge: {distance_to_edge} m")

    #do the distance from edge of fuselage to engine nozzle edge over tan(10 degrees)
    # This is to ensure the engine exhaust cone does not interfere with the v-tail
    x_eng = distance_to_edge / np.tan(np.radians(15)) 
    print(f"Maximum distance the engine can to be placed from end of v-tail: {x_eng} m")

    return {
        'distance_to_edge': distance_to_edge,
        'x_eng': x_eng
    }
print("Fuselage Exhaust Cone Analysis Results:")
results = fuselage_exhaust_cone_analysis()

