import numpy as np
import math as m

def kg_to_N(mass_kg):
    """Converts mass in kg to weight in N."""
    return mass_kg * 9.80665

def N_to_kg(weight_N):
    """Converts weight in N to mass in kg."""
    return weight_N / 9.80665

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

def psf_to_Npm2(psf):
    """
    Convert pounds per square foot to Newtons per square meter.
    """
    return psf * 47.8803

def N_to_lbf(weight_N):
    """
    Convert Newtons to pounds-force.
    """
    return weight_N / 4.44822

def lbf_to_N(weight_lbf):
    """
    Convert pounds-force to Newtons.
    """
    return weight_lbf * 4.44822

def m2_to_ft2(area_m2):
    """
    Convert square meters to square feet.
    """
    return area_m2 * 10.7639
