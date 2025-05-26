import math
from design_variables import DesignParameters


# --- Constants ---
G = 9.80665  # Acceleration due to gravity (m/s^2)

# --- Conversion Functions ---
def kg_to_N(mass_kg):
    """Converts mass in kg to weight in N."""
    return mass_kg * G

def N_to_kg(weight_N):
    """Converts weight in N to mass in kg."""
    return weight_N / G

def km_to_m(dist_km):
    """Converts kilometers to meters."""
    return dist_km * 1000

def m_to_km(dist_m):
    """Converts meters to kilometers."""
    return dist_m / 1000

def kmh_to_ms(speed_kmh):
    """Converts km/h to m/s."""
    return speed_kmh / 3.6

def ms_to_kmh(speed_ms):
    """Converts m/s to km/h."""
    return speed_ms * 3.6

def min_to_s(time_min):
    """Converts minutes to seconds."""
    return time_min * 60

def lb_hr_hp_to_kg_J(cp_lb_hr_hp):
    """Converts specific fuel consumption from lb/(hr*hp) to kg/J."""
    # 1 lb = 0.453592 kg
    # 1 hp = 745.7 W = 745.7 J/s
    # 1 hr = 3600 s
    return cp_lb_hr_hp * (0.453592 / (3600 * 745.7))

def lb_hr_lbf_to_kg_Ns(cj_lb_hr_lbf):
    """Converts specific fuel consumption from lb_mass/(hr*lb_force) to kg/(N*s)."""
    # 1 lb_mass = 0.453592 kg
    # 1 hr = 3600 s
    # 1 lb_force = 4.44822 N
    return cj_lb_hr_lbf * (0.453592 / (3600 * 4.44822))

def ft_to_m(feet):
    """
    Convert feet to meters.
    """
    return feet * 0.3048

def m_to_ft(meters):
    """
    Convert meters to feet.
    """
    return meters / 0.3048

def kts_to_ms(knots):
    """
    Convert knots to meters per second.
    """
    return knots * 0.514444

def N_to_lbf(weight_N):
    """Converts weight in N to pounds."""
    # 1 N = 0.224809 lb
    return weight_N * 0.224809



params = DesignParameters()
params.load_from_yaml('design_config.yaml')

S_emp = params.empennage.S_t

def wing_weight_N(WTO, wing_params):
    #choose the appropriate method based on the wing type

def fuselage_weight_lb(params: DesignParameters):
    #equation from Gundlach
    l_f_ft = m_to_ft(params.fuselage.l_f)   # ft
    W_PL_LBS = N_to_lbf(W_PL_N)              # lbs
    V_eqMax = params.max_eq_velocity        # kts
    N_z = params.max_load_factor            # g
    
    F_MG = 1.07     # 1.07 if main gear on fuselage, 1 if on wing
    F_NG = 1.04     # 1.04 if nose gear on fuselage, 1 if on wing
    F_press = 1     # 1.0 if unpressurized, 1.08 if pressurized
    F_VT = 1        # 1 if vertical tail not included, 1.1 if included
    F_matl = 1      #1 is carbonfiber or metal, 2 if fiberglass or unknown, 2.187 if wood
   
    W_fus_lb = 0.5257 * F_MG * F_NG * F_press * F_VT * F_matl * l_f_ft**0.3796 * (W_PL_LBS * N_z)**0.4863 * V_eqMax**2

    return W_fus_lb

def nacelle_weight_lb(params: DesignParameters):
    # equation from Gundlach
    F_nac = 0.06                     #0.055 for low bypass turbofan, 0.065 for high bypass turbofan
    T_max = N_to_lbf(params.engine_max_thrust)   # lbf
    W_nacelle_lb = F_nac*T_max                  #lbf
    return W_nacelle_lb

def landing_gear_weight_lb(params: DesignParameters):
    # equation from Roskam
    

def empennage_weight(WTO, empennage_params):
    #equation from Gundlach
    W_emp = W_HT*math.cos**2(vtail_dihedral) + W_VT*math.sin**2(vtail_dihedral)
