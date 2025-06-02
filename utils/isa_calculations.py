# IMPORTS
import math


# This module provides functions to calculate the International Standard Atmosphere (ISA) properties
# at various altitudes up to 20 km. It includes temperature, pressure, and density calculations.



# Constants
T0 = 288.15       # Sea-level temperature [K]
P0 = 101325       # Sea-level pressure [Pa]
rho0 = 1.225      # Sea-level density [kg/m³]
a = -0.0065       # Temperature lapse rate in troposphere [K/m]
g0 = 9.80665      # Gravity [m/s²]
R = 287.058       # Gas constant for air [J/(kg·K)]




# Tropopause conditions (at 11,000 m)
h_tropopause = 11000  # m
T11 = T0 + a * h_tropopause  # Temperature at tropopause [K]
P11 = P0 * (T11 / T0) ** (-g0 / (a * R))  # Pressure at tropopause [Pa]
rho11 = P11 / (R * T11)  # Density at tropopause [kg/m³]

def isa_temperature(h):
    """Temperature as function of altitude [m]"""
    if h <= 11000:
        return T0 + a * h
    elif h <= 20000:
        return T11  # Isothermal layer
    else:
        raise ValueError("Altitude above 20 km not supported.")

def isa_pressure(h):
    """Pressure as function of altitude [m]"""
    if h <= 11000:
        T = isa_temperature(h)
        return P0 * (T / T0) ** (-g0 / (a * R))
    elif h <= 20000:
        return P11 * math.exp(-g0 * (h - h_tropopause) / (R * T11))
    else:
        raise ValueError("Altitude above 20 km not supported.")

def isa_density(h):
    """Density as function of altitude [m]"""
    T = isa_temperature(h)
    P = isa_pressure(h)
    return P / (R * T)

def print_isa(h):
    """Prints ISA values at a given altitude"""
    print(f"Altitude: {h} m")
    print(f"Temperature: {isa_temperature(h):.2f} K")
    print(f"Pressure: {isa_pressure(h):.2f} Pa")
    print(f"Density: {isa_density(h):.4f} kg/m³")

