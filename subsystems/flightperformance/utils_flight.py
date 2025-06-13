import math

def __ISA__(altitude: float):
    """
    Calculates atmospheric properties based on altitude using the International Standard Atmosphere (ISA) model.

    Parameters:
    altitude (float): Altitude in meters.

    Returns:
    tuple: Temperature (K), pressure (Pa), density (kg/m^3), and speed of sound (m/s) at the given altitude.
    """
    # ISA constants
    T0 = 288.15  # Sea level standard temperature (K)
    L = 0.0065   # Temperature lapse rate (K/m)
    p0 = 101325  # Sea level standard pressure (Pa)
    g0 = 9.80665 # Standard gravity (m/s^2)
    R = 287.05   # Specific gas constant for dry air (J/kg*K)
    gamma = 1.4  # Adiabatic index for dry air
    rho0 = 1.225 # Sea level standard density (kg/m^3)

    if altitude < 0:
        # Below sea level (assuming sea level conditions)
        T = 288.15
        p = p0
        rho = rho0
    elif altitude < 11000:
        # Troposphere (up to 11 km)
        T = T0 - L * altitude
        p = p0 * (1 - L/T0*altitude)**(g0/(R*L))
        rho = rho0 * (1 - L/T0*altitude)**(g0/(R*L)-1)
    else:
        # Stratosphere (above 11 km, constant temperature)
        T = T0 - L * 11000 # Temperature at 11 km
        p11 = p0 * (1 - L/T0*11000)**(g0/(R*L)) # Pressure at 11 km
        rho11 = rho0 * (1 - L/T0*11000)**(g0/(R*L)-1) # Density at 11 km
        p = p11 * math.exp(-g0/(R*T)*(altitude-11000))
        rho = rho11 * math.exp(-g0/(R*T)*(altitude-11000))

    a = (gamma * R * T)**0.5 # Speed of sound
    temperature = T
    pressure = p
    density = rho
    speed_of_sound = a

    return temperature,pressure,density,speed_of_sound


if __name__ == "__main__":
    result = __ISA__(12000)
    print(result)