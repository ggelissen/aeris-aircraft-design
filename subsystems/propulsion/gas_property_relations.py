from math import *
from functools import lru_cache

# import numpy
from scipy import optimize, integrate
import numpy as np

__author__ = "Pieter-Jan Proesmans"

t_standard = 288.15  # Sea level standard temperature [K]
p_standard = 101325.  # Sea level standard pressure [Pa]

# Molecular weights
h2o_mw = 18.01528
h2_mw = 2.01588
air_mw = 28.964938527970563
n2_mw = 28.01348
ar_mw = 39.948
co2_mw = 44.0098


# Precompute constant coefficients
A = np.array([0.992313, 0.236688, -1.852148, 6.083152,
              -8.893933, 7.097112, -3.234725, 0.794571,
              -0.081873, 0.422178, 0.001053])
A_water = np.array([1.937043, -0.967916, 3.338905, -3.652122,
                    2.332470, -0.819451, 0.118783, 0.,
                    0., 2.860773, -0.000219])
A_nitrogen = np.array([1.075132, -0.252297, 0.341859, 0.523944,
                       -0.888984, 0.442621, -0.074788, 0.,
                       0., 0.443041, 0.0012622])
A_carbon_dioxide = np.array([0.408089, 2.027201, -2.405549, 2.039166,
                             -1.163088, 0.381364, -0.052763, 0.,
                             0., 0.366740, 0.001736])
B = np.array([-0.718874, 8.747481, -15.863157, 17.254096,
              -10.233795, 3.081778, -0.361112, -0.003919,
              0.0555930, -0.0016079])


# pm_air = pm.get("ig.air")
# pm_h2o = pm.get("ig.H2O")
# pm_h2 = pm.get("ig.H2")
# pm_n2 = pm.get("ig.N2")
# pm_ar = pm.get("ig.Ar")
# pm_co2 = pm.get("ig.CO2")
#
# h2o_mw = pm_h2o.mw()
# h2_mw = pm_h2.mw()
# air_mw = pm_air.mw()
# n2_mw = pm_n2.mw()
# ar_mw = pm_ar.mw()
# co2_mw = pm_co2.mw()

@lru_cache(maxsize=None)
def t_total_to_static(t_total, mach, gas="air",
                      far=0., max_iter=50, err=1.e-5, diff=1.):
    """
    Converts total temperature to static temperature, given a Mach number.

    :param t_total: Total temperature [K]
    :type t_total: float
    :param mach: Mach number [-]
    :type mach: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param max_iter: Maximum of iterations allowed
    :type max_iter: int
    :param err: Maximum error between assumed static temperature and new value
    :type err: float
    :param diff: Initial assumed error to start iterations, set to 1 by default
    :type diff: float
    :return: Static temperature [K]
    :rtype: float
    """
    t_static = t_total
    it = 0
    while (diff > err) and (it < max_iter):
        it = it + 1
        t_ratio = 1. + (mach ** 2.) * (gamma_gas(
            t_static, gas, far=far) - 1.) / 2.
        t_static_update = t_total / t_ratio
        diff = abs(t_static_update - t_static)
        t_static = t_static_update
    return t_static


@lru_cache(maxsize=None)
def cp(t_static, gas="air", far=0.):
    """
    This function calculates the specific heat at constant pressure.

    :param t_static: Static temperature [K]
    :type t_static: Union[float,numpy.ndarray]
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :return: Specific heat at constant pressure [J/(kg*K)]
    :rtype: float

    .. note:: Relations are taken from book Gas Turbine Performance
        (Chapter 3), by Walsh and Fletcher, 2nd ed.
    """

    # Constants required to determine cp for air and kerosene mixture
    a = [0.992313, 0.236688, -1.852148, 6.083152,
         -8.893933, 7.097112, -3.234725, 0.794571,
         -0.081873, 0.422178, 0.001053]

    a_water = [1.937043, -0.967916, 3.338905, -3.652122,
               2.332470, -0.819451, 0.118783, 0.,
               0., 2.860773, -0.000219]

    a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                  -0.888984, 0.442621, -0.074788, 0.,
                  0., 0.443041, 0.0012622]

    a_carbon_dioxide = [0.408089, 2.027201, -2.405549, 2.039166,
                        -1.163088, 0.381364, -0.052763, 0.,
                        0., 0.366740, 0.001736]

    # Constants required to determine cp for kerosene mixture
    b = [-0.718874, 8.747481, -15.863157, 17.254096,
         -10.233795, 3.081778, -0.361112, -0.003919,
         0.0555930, -0.0016079]
    b_short = b[0:-2]  # Only first 7 coefficients are required
    b_short.reverse()

    tz = t_static / 1000.

    cp_air = (a[0] + a[1] * tz
              + a[2] * (tz ** 2.)
              + a[3] * (tz ** 3.)
              + a[4] * (tz ** 4.)
              + a[5] * (tz ** 5.)
              + a[6] * (tz ** 6.)
              + a[7] * (tz ** 7.)
              + a[8] * (tz ** 8.))

    if gas == 'air':
        return cp_air * 1000.

    elif gas == 'kerosene_in_air':
        cp_kia = cp_air + ((far / (1. + far)) * (
                b[0] + b[1] * tz
                + b[2] * (tz ** 2.)
                + b[3] * (tz ** 3.)
                + b[4] * (tz ** 4.)
                + b[5] * (tz ** 5.)
                + b[6] * (tz ** 6.)
                + b[7] * (tz ** 7.)
        ))
        return cp_kia * 1000.

    elif gas == "water":  # H20
        cp_water = (a_water[0] + a_water[1] * tz
                    + a_water[2] * (tz ** 2.)
                    + a_water[3] * (tz ** 3.)
                    + a_water[4] * (tz ** 4.)
                    + a_water[5] * (tz ** 5.)
                    + a_water[6] * (tz ** 6.)
                    + a_water[7] * (tz ** 7.)
                    + a_water[8] * (tz ** 8.))

        return cp_water * 1.e3

    elif gas == "carbon_dioxide":  # CO2
        cp_carbon_dioxide = (a_carbon_dioxide[0] + a_carbon_dioxide[1] * tz
                             + a_carbon_dioxide[2] * (tz ** 2.)
                             + a_carbon_dioxide[3] * (tz ** 3.)
                             + a_carbon_dioxide[4] * (tz ** 4.)
                             + a_carbon_dioxide[5] * (tz ** 5.)
                             + a_carbon_dioxide[6] * (tz ** 6.)
                             + a_carbon_dioxide[7] * (tz ** 7.)
                             + a_carbon_dioxide[8] * (tz ** 8.))

        return cp_carbon_dioxide * 1.e3

    elif gas == "nitrogen":  # N2
        cp_nitrogen = (a_nitrogen[0] + a_nitrogen[1] * tz
                       + a_nitrogen[2] * (tz ** 2.)
                       + a_nitrogen[3] * (tz ** 3.)
                       + a_nitrogen[4] * (tz ** 4.)
                       + a_nitrogen[5] * (tz ** 5.)
                       + a_nitrogen[6] * (tz ** 6.)
                       + a_nitrogen[7] * (tz ** 7.)
                       + a_nitrogen[8] * (tz ** 8.))

        return cp_nitrogen * 1.e3

    elif gas == "oxygen":  # O2
        a_oxygen = [1.006450, -1.047869, 3.729558, -4.934172,
                    3.284147, -1.095203, 0.145737, 0.,
                    0., 0.369790, 0.000491]
        cp_oxygen = (a_oxygen[0] + a_oxygen[1] * tz
                     + a_oxygen[2] * (tz ** 2.)
                     + a_oxygen[3] * (tz ** 3.)
                     + a_oxygen[4] * (tz ** 4.)
                     + a_oxygen[5] * (tz ** 5.)
                     + a_oxygen[6] * (tz ** 6.)
                     + a_oxygen[7] * (tz ** 7.)
                     + a_oxygen[8] * (tz ** 8.))

        return cp_oxygen * 1.e3

    elif gas == "water_in_air":  # dry air by combination of N2 and 02 data

        cp_water = (a_water[0] + a_water[1] * tz
                    + a_water[2] * (tz ** 2.)
                    + a_water[3] * (tz ** 3.)
                    + a_water[4] * (tz ** 4.)
                    + a_water[5] * (tz ** 5.)
                    + a_water[6] * (tz ** 6.)
                    + a_water[7] * (tz ** 7.)
                    + a_water[8] * (tz ** 8.))

        cp_nitrogen = (a_nitrogen[0] + a_nitrogen[1] * tz
                       + a_nitrogen[2] * (tz ** 2.)
                       + a_nitrogen[3] * (tz ** 3.)
                       + a_nitrogen[4] * (tz ** 4.)
                       + a_nitrogen[5] * (tz ** 5.)
                       + a_nitrogen[6] * (tz ** 6.)
                       + a_nitrogen[7] * (tz ** 7.)
                       + a_nitrogen[8] * (tz ** 8.))

        cp_mix = h2o_mw / h2_mw * far * cp_water
        cp_mix += (78.084 / 20.946) * n2_mw / (
                2. * h2_mw) * far * cp_nitrogen
        cp_mix += (1. - air_mw
                   / (2 * 0.20946 * h2_mw) * far) * cp_air
        cp_mix /= (1 + far)

        return cp_mix * 1.e3

    elif gas == "air2":  # dry air by combination of N2 and 02 data
        a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                      -0.888984, 0.442621, -0.074788, 0.,
                      0., 0.443041, 0.0012622]
        cp_nitrogen = (a_nitrogen[0] + a_nitrogen[1] * tz
                       + a_nitrogen[2] * (tz ** 2.)
                       + a_nitrogen[3] * (tz ** 3.)
                       + a_nitrogen[4] * (tz ** 4.)
                       + a_nitrogen[5] * (tz ** 5.)
                       + a_nitrogen[6] * (tz ** 6.)
                       + a_nitrogen[7] * (tz ** 7.)
                       + a_nitrogen[8] * (tz ** 8.))

        a_oxygen = [1.006450, -1.047869, 3.729558, -4.934172,
                    3.284147, -1.095203, 0.145737, 0.,
                    0., 0.369790, 0.000491]
        cp_oxygen = (a_oxygen[0] + a_oxygen[1] * tz
                     + a_oxygen[2] * (tz ** 2.)
                     + a_oxygen[3] * (tz ** 3.)
                     + a_oxygen[4] * (tz ** 4.)
                     + a_oxygen[5] * (tz ** 5.)
                     + a_oxygen[6] * (tz ** 6.)
                     + a_oxygen[7] * (tz ** 7.)
                     + a_oxygen[8] * (tz ** 8.))

        return (0.75 * cp_nitrogen
                + 0.235 * cp_oxygen
                + 0.015 * 523. / 1.e3  # approx. Argon contribution
                ) * 1.e3

    else:
        msg = "Gas type {:} not recognised. Select 'air' or " \
              "'kerosene_in_air' as strings,  or adapt the " \
              "model for the required gas.".format(gas)
        raise ValueError(msg)


@lru_cache(maxsize=None)
def r_gas(gas="air", far=0.):
    """
    Returns the gas constant for the gas mixture defined by the type of gas
    and the fuel-to-air-ratio.

    :param gas: Type of gas. Currently "air", "kerosene_in_air",
        "diesel_in_air", "natural_gas_in_air", "oxygen", "nitrogen",
        "hydrogen", "water", "argon", "carbon_dioxide", and "water_in_air" are
        supported
    :type gas: str
    :param far: Fuel-to-air ratio
    :type far: float
    :return: Gas constant R [J/(kg*K)]
    :rtype: float
    """
    if gas == "air":
        return 287.05
    elif gas == "kerosene_in_air":
        return 287.05 - 0.00990 * far + 1e-7 * far ** 2.
    elif gas == "diesel_in_air":
        return 287.05 - 8.0262 * far + 3e-7 * far ** 2.
    elif gas == "natural_gas_in_air":
        return 287.05 + 212.85 * far - 197.89 * far ** 2.
    elif gas == "oxygen":
        return 259.84
    elif gas == "nitrogen":
        return 296.80
    elif gas == "hydrogen":
        return 4124.2
    elif gas == "water":
        # Water vapour
        return 461.52
    elif gas == "argon":
        return 208.13
    elif gas == "carbon_dioxide":
        return 188.92
    elif gas == "water_in_air":
        r_h2o = r_gas(gas="water")
        r_n2 = r_gas(gas="nitrogen")
        r_co2 = r_gas(gas="carbon_dioxide")
        r_ar = r_gas(gas="argon")
        r_air = r_gas(gas="air")

        r_mix = h2o_mw / h2_mw * far * r_h2o
        r_mix += (78.084 / 20.946) * n2_mw / (
                2. * h2_mw) * far * r_n2
        r_mix += (0.934 / 20.946) * ar_mw / (
                2. * h2_mw) * far * r_ar
        r_mix += (0.033 / 20.946) * co2_mw / (
                2. * h2_mw) * far * r_co2
        r_mix += (1. - air_mw
                  / (2 * 0.20946 * h2_mw) * far) * r_air
        r_mix /= (1 + far)

        return r_mix

    else:
        msg = "Gas type {:} not recognised. Select 'air' or " \
              "'kerosene_in_air' as strings,  or adapt the " \
              "model for the required gas.".format(gas)
        raise ValueError(msg)


@lru_cache(maxsize=None)
def gamma_gas(t_static, gas, far=0.):
    """
    This function calculates the specific heat ratio.

    :param t_static: Static temperature [K]
    :type t_static: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :return: Specific heat ratio [-]
    :rtype: float

    .. note:: Relations are taken from book Gas Turbine Performance
    (Chapter 3), by Walsh and Fletcher, 2nd ed.
    """
    r = r_gas(gas=gas, far=far)
    cp_i = cp(t_static, gas, far)
    gamma_i = cp_i / (cp_i - r)
    return gamma_i


def sigma(t, gas, far=0., t_ref=298.0):
    """
    Entropy complement. (!Not entropy change self!)

    :param t: Temperature at the end of the process [K]
    :type t: float | numpy.ndarray
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 298 K, standard
    temperature for standard formation enthalpy
    :type t_ref: float
    :return: Entropy complement [J/(kg*K)]
    :rtype: float
    """

    def aux_fun(ti):
        """
        Auxiliary function, derivative of sigma(T), which fits inside the
        integral of Equation D.7

        :param ti: Temperature [K]
        :return: Derivative of sigma(T)
        :rtype: float
        """
        return cp(ti, gas, far=far) / ti

    # sig = integrate.quad(aux_fun, t_ref, t)

    if isinstance(t, int) or isinstance(t, float):
        sig = integrate.quad(aux_fun, t_ref, t)[0]
    elif isinstance(t, np.ndarray):
        sig = np.zeros_like(t)
        for it, temp in enumerate(t):
            sig[it] = integrate.quad(aux_fun, t_ref, temp)[0]
    else:
        msg = "Type of t unsupported."
        raise Exception(msg)
    return sig


def phi_entropy_old(t_s1, t_s2, gas, far=0.):
    """
    [DEPRECATED]
    Temperature dependent portion of entropy S.

    :param t_s1: Reference temperature or temperature at start of process [K]
    :type t_s1: float | numpy.ndarray
    :param t_s2: Temperature at end of process [K]
    :type t_s2: float | numpy.ndarray
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio
    :type far: float
    :return: Temperature dependent portion of entropy [J/(kg*K)]
    :rtype: float | numpy.ndarray

    .. note:: Relations taken from Formulas F3.28 and 3.29 from Walsh and
    Fletcher
    """
    # Constants required to determine cp for air and kerosene mixture
    a = [0.992313, 0.236688, -1.852148, 6.083152,
         -8.893933, 7.097112, -3.234725, 0.794571,
         -0.081873, 0.422178, 0.001053]

    # - for water
    a_water = [1.937043, -0.967916, 3.338905, -3.652122,
               2.332470, -0.819451, 0.118783, 0.,
               0., 2.860773, -0.000219]

    # - for nitrogen
    a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                  -0.888984, 0.442621, -0.074788, 0.,
                  0., 0.443041, 0.0012622]

    # Constants required to determine cp for kerosene mixture
    b = [-0.718874, 8.747481, -15.863157, 17.254096,
         -10.233795, 3.081778, -0.361112, -0.003919,
         0.0555930, -0.0016079]

    # Convert temperatures
    t_z1 = t_s1 / 1000.
    t_z2 = t_s2 / 1000.

    # FT2
    # print("t_z2", t_z2)
    ft2 = (a[0] * np.log(t_z2)
           + a[1] * t_z2
           + a[2] * (t_z2 ** 2.) / 2
           + a[3] * (t_z2 ** 3.) / 3
           + a[4] * (t_z2 ** 4.) / 4
           + a[5] * (t_z2 ** 5.) / 5
           + a[6] * (t_z2 ** 6.) / 6
           + a[7] * (t_z2 ** 7.) / 7
           + a[8] * (t_z2 ** 8.) / 8
           + a[10]
           )

    # FT1
    # print(t_z1)
    ft1 = (a[0] * np.log(t_z1)
           + a[1] * t_z1
           + a[2] * (t_z1 ** 2.) / 2
           + a[3] * (t_z1 ** 3.) / 3
           + a[4] * (t_z1 ** 4.) / 4
           + a[5] * (t_z1 ** 5.) / 5
           + a[6] * (t_z1 ** 6.) / 6
           + a[7] * (t_z1 ** 7.) / 7
           + a[8] * (t_z1 ** 8.) / 8
           + a[10]
           )

    if gas == 'air':
        return (ft2 - ft1) * 1000.
    elif gas == 'kerosene_in_air':
        ft2 += (far / (1. + far)) * (
                b[0] * np.log(t_z2)
                + b[1] * t_z2
                + b[2] * (t_z2 ** 2.) / 2
                + b[3] * (t_z2 ** 3.) / 3
                + b[4] * (t_z2 ** 4.) / 4
                + b[5] * (t_z2 ** 5.) / 5
                + b[6] * (t_z2 ** 6.) / 6
                + b[7] * (t_z2 ** 7.) / 7
                + b[9]
        )
        ft1 += (far / (1. + far)) * (
                b[0] * np.log(t_z1)
                + b[1] * t_z1
                + b[2] * (t_z1 ** 2.) / 2
                + b[3] * (t_z1 ** 3.) / 3
                + b[4] * (t_z1 ** 4.) / 4
                + b[5] * (t_z1 ** 5.) / 5
                + b[6] * (t_z1 ** 6.) / 6
                + b[7] * (t_z1 ** 7.) / 7
                + b[9]
        )
        return (ft2 - ft1) * 1000.

    elif gas == "water":
        # FT2
        ft2 = (a_water[0] * np.log(t_z2)
               + a_water[1] * t_z2
               + a_water[2] * (t_z2 ** 2.) / 2
               + a_water[3] * (t_z2 ** 3.) / 3
               + a_water[4] * (t_z2 ** 4.) / 4
               + a_water[5] * (t_z2 ** 5.) / 5
               + a_water[6] * (t_z2 ** 6.) / 6
               + a_water[7] * (t_z2 ** 7.) / 7
               + a_water[8] * (t_z2 ** 8.) / 8
               + a_water[10]
               )

        # FT1
        ft1 = (a_water[0] * np.log(t_z1)
               + a_water[1] * t_z1
               + a_water[2] * (t_z1 ** 2.) / 2
               + a_water[3] * (t_z1 ** 3.) / 3
               + a_water[4] * (t_z1 ** 4.) / 4
               + a_water[5] * (t_z1 ** 5.) / 5
               + a_water[6] * (t_z1 ** 6.) / 6
               + a_water[7] * (t_z1 ** 7.) / 7
               + a_water[8] * (t_z1 ** 8.) / 8
               + a_water[10]
               )

        return (ft2 - ft1) * 1.e3

    elif gas == "nitrogen":
        # FT2
        ft2 = (a_nitrogen[0] * np.log(t_z2)
               + a_nitrogen[1] * t_z2
               + a_nitrogen[2] * (t_z2 ** 2.) / 2
               + a_nitrogen[3] * (t_z2 ** 3.) / 3
               + a_nitrogen[4] * (t_z2 ** 4.) / 4
               + a_nitrogen[5] * (t_z2 ** 5.) / 5
               + a_nitrogen[6] * (t_z2 ** 6.) / 6
               + a_nitrogen[7] * (t_z2 ** 7.) / 7
               + a_nitrogen[8] * (t_z2 ** 8.) / 8
               + a_nitrogen[10]
               )

        # FT1
        ft1 = (a_nitrogen[0] * np.log(t_z1)
               + a_nitrogen[1] * t_z1
               + a_nitrogen[2] * (t_z1 ** 2.) / 2
               + a_nitrogen[3] * (t_z1 ** 3.) / 3
               + a_nitrogen[4] * (t_z1 ** 4.) / 4
               + a_nitrogen[5] * (t_z1 ** 5.) / 5
               + a_nitrogen[6] * (t_z1 ** 6.) / 6
               + a_nitrogen[7] * (t_z1 ** 7.) / 7
               + a_nitrogen[8] * (t_z1 ** 8.) / 8
               + a_nitrogen[10]
               )

        return (ft2 - ft1) * 1.e3

    elif gas == "water_in_air":
        # Water
        # FT2
        ft_water_2 = (a_water[0] * np.log(t_z2)
                      + a_water[1] * t_z2
                      + a_water[2] * (t_z2 ** 2.) / 2
                      + a_water[3] * (t_z2 ** 3.) / 3
                      + a_water[4] * (t_z2 ** 4.) / 4
                      + a_water[5] * (t_z2 ** 5.) / 5
                      + a_water[6] * (t_z2 ** 6.) / 6
                      + a_water[7] * (t_z2 ** 7.) / 7
                      + a_water[8] * (t_z2 ** 8.) / 8
                      + a_water[10]
                      )

        # FT1
        ft_water_1 = (a_water[0] * np.log(t_z1)
                      + a_water[1] * t_z1
                      + a_water[2] * (t_z1 ** 2.) / 2
                      + a_water[3] * (t_z1 ** 3.) / 3
                      + a_water[4] * (t_z1 ** 4.) / 4
                      + a_water[5] * (t_z1 ** 5.) / 5
                      + a_water[6] * (t_z1 ** 6.) / 6
                      + a_water[7] * (t_z1 ** 7.) / 7
                      + a_water[8] * (t_z1 ** 8.) / 8
                      + a_water[10]
                      )

        # Nitrogen
        # FT2
        ft_nitrogen_2 = (a_nitrogen[0] * np.log(t_z2)
                         + a_nitrogen[1] * t_z2
                         + a_nitrogen[2] * (t_z2 ** 2.) / 2
                         + a_nitrogen[3] * (t_z2 ** 3.) / 3
                         + a_nitrogen[4] * (t_z2 ** 4.) / 4
                         + a_nitrogen[5] * (t_z2 ** 5.) / 5
                         + a_nitrogen[6] * (t_z2 ** 6.) / 6
                         + a_nitrogen[7] * (t_z2 ** 7.) / 7
                         + a_nitrogen[8] * (t_z2 ** 8.) / 8
                         + a_nitrogen[10]
                         )

        # FT1
        ft_nitrogen_1 = (a_nitrogen[0] * np.log(t_z1)
                         + a_nitrogen[1] * t_z1
                         + a_nitrogen[2] * (t_z1 ** 2.) / 2
                         + a_nitrogen[3] * (t_z1 ** 3.) / 3
                         + a_nitrogen[4] * (t_z1 ** 4.) / 4
                         + a_nitrogen[5] * (t_z1 ** 5.) / 5
                         + a_nitrogen[6] * (t_z1 ** 6.) / 6
                         + a_nitrogen[7] * (t_z1 ** 7.) / 7
                         + a_nitrogen[8] * (t_z1 ** 8.) / 8
                         + a_nitrogen[10]
                         )

        # Total
        psi_mix = h2o_mw / h2_mw * far * (ft_water_2 - ft_water_1)
        psi_mix += (79. / 21.) * n2_mw / (
                2. * h2_mw) * far * (ft_nitrogen_2 - ft_nitrogen_1)
        psi_mix += (1. - air_mw
                    / (2 * 0.21 * h2_mw) * far) * (ft2 - ft1)
        psi_mix /= (1 + far)

        return psi_mix * 1.e3

    else:
        msg = "Gas type {:} not recognised. Select 'air' or " \
              "'kerosene_in_air' as strings,  or adapt the " \
              "model for the required gas.".format(gas)
        raise ValueError(msg)


@lru_cache(maxsize=None)
def phi_entropy(t_s1, t_s2, gas, far=0.):
    """
    Temperature dependent portion of entropy S.

    :param t_s1: Reference temperature or temperature at start of process [K]
    :type t_s1: float | numpy.ndarray
    :param t_s2: Temperature at end of process [K]
    :type t_s2: float | numpy.ndarray
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio
    :type far: float
    :return: Temperature dependent portion of entropy [J/(kg*K)]
    :rtype: float | numpy.ndarray

    .. note:: Relations taken from Formulas F3.28 and 3.29 from Walsh and
    Fletcher
    """
    # Constants required to determine cp for air and kerosene mixture
    a = [0.992313, 0.236688, -1.852148, 6.083152,
         -8.893933, 7.097112, -3.234725, 0.794571,
         -0.081873, 0.422178, 0.001053]

    # - for water
    a_water = [1.937043, -0.967916, 3.338905, -3.652122,
               2.332470, -0.819451, 0.118783, 0.,
               0., 2.860773, -0.000219]

    # - for nitrogen
    a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                  -0.888984, 0.442621, -0.074788, 0.,
                  0., 0.443041, 0.0012622]

    # Constants required to determine cp for kerosene mixture
    b = [-0.718874, 8.747481, -15.863157, 17.254096,
         -10.233795, 3.081778, -0.361112, -0.003919,
         0.0555930, -0.0016079]

    # Convert temperatures
    t_z1 = t_s1 / 1000.
    t_z2 = t_s2 / 1000.

    # FT2
    # print("t_z2", t_z2)
    ft2 = (a[0] * np.log(t_z2)
           + a[1] * t_z2
           + a[2] * (t_z2 ** 2.) / 2
           + a[3] * (t_z2 ** 3.) / 3
           + a[4] * (t_z2 ** 4.) / 4
           + a[5] * (t_z2 ** 5.) / 5
           + a[6] * (t_z2 ** 6.) / 6
           + a[7] * (t_z2 ** 7.) / 7
           + a[8] * (t_z2 ** 8.) / 8
           # + a[10]
           )

    # FT1
    # print(t_z1)
    ft1 = (a[0] * np.log(t_z1)
           + a[1] * t_z1
           + a[2] * (t_z1 ** 2.) / 2
           + a[3] * (t_z1 ** 3.) / 3
           + a[4] * (t_z1 ** 4.) / 4
           + a[5] * (t_z1 ** 5.) / 5
           + a[6] * (t_z1 ** 6.) / 6
           + a[7] * (t_z1 ** 7.) / 7
           + a[8] * (t_z1 ** 8.) / 8
           # + a[10]
           )

    if gas == 'air':
        return (ft2 - ft1) * 1000.
    elif gas == 'kerosene_in_air':
        ft2 += (far / (1. + far)) * (
                b[0] * np.log(t_z2)
                + b[1] * t_z2
                + b[2] * (t_z2 ** 2.) / 2
                + b[3] * (t_z2 ** 3.) / 3
                + b[4] * (t_z2 ** 4.) / 4
                + b[5] * (t_z2 ** 5.) / 5
                + b[6] * (t_z2 ** 6.) / 6
                + b[7] * (t_z2 ** 7.) / 7
                # + b[9]
        )
        ft1 += (far / (1. + far)) * (
                b[0] * np.log(t_z1)
                + b[1] * t_z1
                + b[2] * (t_z1 ** 2.) / 2
                + b[3] * (t_z1 ** 3.) / 3
                + b[4] * (t_z1 ** 4.) / 4
                + b[5] * (t_z1 ** 5.) / 5
                + b[6] * (t_z1 ** 6.) / 6
                + b[7] * (t_z1 ** 7.) / 7
                # + b[9]
        )
        return (ft2 - ft1) * 1000.

    elif gas == "water":
        # FT2
        ft2 = (a_water[0] * np.log(t_z2)
               + a_water[1] * t_z2
               + a_water[2] * (t_z2 ** 2.) / 2
               + a_water[3] * (t_z2 ** 3.) / 3
               + a_water[4] * (t_z2 ** 4.) / 4
               + a_water[5] * (t_z2 ** 5.) / 5
               + a_water[6] * (t_z2 ** 6.) / 6
               + a_water[7] * (t_z2 ** 7.) / 7
               + a_water[8] * (t_z2 ** 8.) / 8
               # + a_water[10]
               )

        # FT1
        ft1 = (a_water[0] * np.log(t_z1)
               + a_water[1] * t_z1
               + a_water[2] * (t_z1 ** 2.) / 2
               + a_water[3] * (t_z1 ** 3.) / 3
               + a_water[4] * (t_z1 ** 4.) / 4
               + a_water[5] * (t_z1 ** 5.) / 5
               + a_water[6] * (t_z1 ** 6.) / 6
               + a_water[7] * (t_z1 ** 7.) / 7
               + a_water[8] * (t_z1 ** 8.) / 8
               # + a_water[10]
               )

        return (ft2 - ft1) * 1.e3

    elif gas == "nitrogen":
        # FT2
        ft2 = (a_nitrogen[0] * np.log(t_z2)
               + a_nitrogen[1] * t_z2
               + a_nitrogen[2] * (t_z2 ** 2.) / 2
               + a_nitrogen[3] * (t_z2 ** 3.) / 3
               + a_nitrogen[4] * (t_z2 ** 4.) / 4
               + a_nitrogen[5] * (t_z2 ** 5.) / 5
               + a_nitrogen[6] * (t_z2 ** 6.) / 6
               + a_nitrogen[7] * (t_z2 ** 7.) / 7
               + a_nitrogen[8] * (t_z2 ** 8.) / 8
               # + a_nitrogen[10]
               )

        # FT1
        ft1 = (a_nitrogen[0] * np.log(t_z1)
               + a_nitrogen[1] * t_z1
               + a_nitrogen[2] * (t_z1 ** 2.) / 2
               + a_nitrogen[3] * (t_z1 ** 3.) / 3
               + a_nitrogen[4] * (t_z1 ** 4.) / 4
               + a_nitrogen[5] * (t_z1 ** 5.) / 5
               + a_nitrogen[6] * (t_z1 ** 6.) / 6
               + a_nitrogen[7] * (t_z1 ** 7.) / 7
               + a_nitrogen[8] * (t_z1 ** 8.) / 8
               # + a_nitrogen[10]
               )

        return (ft2 - ft1) * 1.e3

    elif gas == "water_in_air":
        # Water
        # FT2
        ft_water_2 = (a_water[0] * np.log(t_z2)
                      + a_water[1] * t_z2
                      + a_water[2] * (t_z2 ** 2.) / 2
                      + a_water[3] * (t_z2 ** 3.) / 3
                      + a_water[4] * (t_z2 ** 4.) / 4
                      + a_water[5] * (t_z2 ** 5.) / 5
                      + a_water[6] * (t_z2 ** 6.) / 6
                      + a_water[7] * (t_z2 ** 7.) / 7
                      + a_water[8] * (t_z2 ** 8.) / 8
                      # + a_water[10]
                      )

        # FT1
        ft_water_1 = (a_water[0] * np.log(t_z1)
                      + a_water[1] * t_z1
                      + a_water[2] * (t_z1 ** 2.) / 2
                      + a_water[3] * (t_z1 ** 3.) / 3
                      + a_water[4] * (t_z1 ** 4.) / 4
                      + a_water[5] * (t_z1 ** 5.) / 5
                      + a_water[6] * (t_z1 ** 6.) / 6
                      + a_water[7] * (t_z1 ** 7.) / 7
                      + a_water[8] * (t_z1 ** 8.) / 8
                      # + a_water[10]
                      )

        # Nitrogen
        # FT2
        ft_nitrogen_2 = (a_nitrogen[0] * np.log(t_z2)
                         + a_nitrogen[1] * t_z2
                         + a_nitrogen[2] * (t_z2 ** 2.) / 2
                         + a_nitrogen[3] * (t_z2 ** 3.) / 3
                         + a_nitrogen[4] * (t_z2 ** 4.) / 4
                         + a_nitrogen[5] * (t_z2 ** 5.) / 5
                         + a_nitrogen[6] * (t_z2 ** 6.) / 6
                         + a_nitrogen[7] * (t_z2 ** 7.) / 7
                         + a_nitrogen[8] * (t_z2 ** 8.) / 8
                         # + a_nitrogen[10]
                         )

        # FT1
        ft_nitrogen_1 = (a_nitrogen[0] * np.log(t_z1)
                         + a_nitrogen[1] * t_z1
                         + a_nitrogen[2] * (t_z1 ** 2.) / 2
                         + a_nitrogen[3] * (t_z1 ** 3.) / 3
                         + a_nitrogen[4] * (t_z1 ** 4.) / 4
                         + a_nitrogen[5] * (t_z1 ** 5.) / 5
                         + a_nitrogen[6] * (t_z1 ** 6.) / 6
                         + a_nitrogen[7] * (t_z1 ** 7.) / 7
                         + a_nitrogen[8] * (t_z1 ** 8.) / 8
                         # + a_nitrogen[10]
                         )

        # Total
        psi_mix = h2o_mw / h2_mw * far * (ft_water_2 - ft_water_1)
        psi_mix += (78.084 / 20.946) * n2_mw / (
                2. * h2_mw) * far * (ft_nitrogen_2 - ft_nitrogen_1)
        psi_mix += (1. - air_mw
                    / (2 * 0.20946 * h2_mw) * far) * (ft2 - ft1)
        psi_mix /= (1 + far)

        return psi_mix * 1.e3

    else:
        msg = "Gas type {:} not recognised. Select 'air' or " \
              "'kerosene_in_air' as strings,  or adapt the " \
              "model for the required gas.".format(gas)
        raise ValueError(msg)


def phi_entropy_prime(t_s2, gas, far):
    """
    Derivative of phi_entropy function.

    :param t_s2: Temperature at end of process [K]
    :type t_s2: float | numpy.ndarray
    :param gas: Type of gas. Currently, "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio
    :type far: float
    :return: Derivative of phi_entropy function w.r.t. t_s2
    """

    if gas == "air":
        dffx = 1000. * phi_entropy_fa_prime(t_z=t_s2/1000., a_list=A)
        return dffx
    elif gas == "kerosene_in_air":
        dffx = 1000. * (phi_entropy_fa_prime(t_z=t_s2/1000., a_list=A)
                        + phi_entropy_fb_prime(t_z=t_s2/1000., b_list=B,
                                               far=far))
        return dffx
    else:
        msg = "Gas {:} not supported".format(gas)
        raise Exception(msg)


def phi_entropy_fa_prime(a_list, t_z):
    return (a_list[0] * 1 / t_z / 1000.
            + (a_list[1]
            + a_list[2] * (t_z ** 1.)
            + a_list[3] * (t_z ** 2.)
            + a_list[4] * (t_z ** 3.)
            + a_list[5] * (t_z ** 4.)
            + a_list[6] * (t_z ** 5.)
            + a_list[7] * (t_z ** 6.)
            + a_list[8] * (t_z ** 7.)) / 1000.
            )


def phi_entropy_fb_prime(b_list, t_z, far):
    return (far / (1. + far)) * (
                b_list[0] / t_z / 1000.
                + b_list[1]
                + b_list[2] * (t_z ** 1.)
                + b_list[3] * (t_z ** 2.)
                + b_list[4] * (t_z ** 3.)
                + b_list[5] * (t_z ** 4.)
                + b_list[6] * (t_z ** 5.)
                + b_list[7] * (t_z ** 6.))/1000.


@lru_cache(maxsize=None)
def relative_pressure(t, gas="air", far=0.):
    """
    Calculates the relative (or reduced) pressure ratio for a given
    temperature.

    :param t: Temperature in K
    :type t: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    """
    r = r_gas(gas=gas, far=far)
    return exp(phi_entropy(273., t, gas=gas, far=far) / r)


@lru_cache(maxsize=None)
def prescribed_relative_pressure(pr, gas="air", far=0., t_guess=1000.):
    """
    Finds the corresponding temperature for a given relative pressure.

    :param pr: Relative pressure
    :type pr: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_guess: Initial temperature guess in K
    :type t_guess: float
    :return: Temperature for a given relative pressure [K]
    """

    def aux(t):
        """
        Auxiliary function.

        :param t: Temperature [K]
        :type t: float
        :return: Residual
        :rtype: float
        """
        res = relative_pressure(t, gas=gas, far=far) - pr
        return res

    def aux_prime(t):
        """
        Auxiliary function.
        :return: Residual
        :rtype: float
        """
        r = r_gas(gas=gas, far=far)
        res_prime = (1. / r) * relative_pressure(t, gas=gas, far=far)
        res_prime *= phi_entropy_prime(t, gas=gas, far=far)
        return res_prime

    try:
        t_out = optimize.newton(aux, t_guess,
                                # aux_prime,
                                tol=1.e-1)
        return t_out
    except ValueError:
        msg = "Relative pressure iterations failed"
        raise Exception(msg)


def specific_enthalpy_integration(t, gas="air",
                                  delta_h_formation=0.,
                                  far=0.,
                                  t_ref=0):
    """
    Calculates the specific enthalpy through integration of cp. Can also be
        used to determine the change in enthalpy between two temperatures.

    :param t: Temperature [K]
    :type t: float | numpy.ndarray
    :param gas: Type of gas, currently 'air', 'water', 'nitrogen',
        'kerosene_in_air', and 'water_in_air' are supported
    :type gas: str
    :param delta_h_formation: Heat of formation [J/kg] Not important for gas
        turbine performance, therefore set to 0.
    :type delta_h_formation: float
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 298 K, standard
        temperature for standard formation enthalpy
    :type t_ref: float
    :return: Specific enthalpy [J/kg]
    :rtype: float | numpy.ndarray
    """
    if isinstance(t, int) or isinstance(t, float):
        delta_h = integrate.quad(cp, t_ref, t, args=(gas, far))
        h = delta_h_formation + delta_h[0]
    elif isinstance(t, np.ndarray):
        h = np.zeros_like(t)
        for ti, temp in enumerate(t):
            h[ti] = delta_h_formation + integrate.quad(cp, t_ref, temp,
                                                       args=(gas, far))[0]
    else:
        msg = "Type of t unsupported."
        raise Exception(msg)
    return h


def specific_enthalpy_old(t, gas="air", far=0.):
    """
    [DEPRECATED]
    Calculates the specific enthalpy. Can also be used to determine the change
    in enthalpy between two temperatures.

    :param t: Temperature [K]
    :type t: float | numpy.ndarray
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :return: Specific enthalpy [J/kg]
    :rtype: float
    """
    # Constants required to determine cp for air and kerosene mixture
    a = [0.992313, 0.236688, -1.852148, 6.083152,
         -8.893933, 7.097112, -3.234725, 0.794571,
         -0.081873, 0.422178, 0.001053]

    # - for water
    a_water = [1.937043, -0.967916, 3.338905, -3.652122,
               2.332470, -0.819451, 0.118783, 0.,
               0., 2.860773, -0.000219]

    # - for nitrogen
    a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                  -0.888984, 0.442621, -0.074788, 0.,
                  0., 0.443041, 0.0012622]

    # Constants required to determine cp for kerosene mixture
    b = [-0.718874, 8.747481, -15.863157, 17.254096,
         -10.233795, 3.081778, -0.361112, -0.003919,
         0.0555930, -0.0016079]

    tz = t / 1000.

    h = (a[0] * tz +
         a[1] * (tz ** 2.) / 2 +
         a[2] * (tz ** 3.) / 3 +
         a[3] * (tz ** 4.) / 4 +
         a[4] * (tz ** 5.) / 5 +
         a[5] * (tz ** 6.) / 6 +
         a[6] * (tz ** 7.) / 7 +
         a[7] * (tz ** 8.) / 8 +
         a[8] * (tz ** 9.) / 9
         + a[9]
         )

    if gas == 'air':
        return h * 1e6

    elif gas == "water":
        h = (a_water[0] * tz +
             a_water[1] * (tz ** 2.) / 2 +
             a_water[2] * (tz ** 3.) / 3 +
             a_water[3] * (tz ** 4.) / 4 +
             a_water[4] * (tz ** 5.) / 5 +
             a_water[5] * (tz ** 6.) / 6 +
             a_water[6] * (tz ** 7.) / 7 +
             a_water[7] * (tz ** 8.) / 8 +
             a_water[8] * (tz ** 9.) / 9
             + a_water[9]
             )

        return h * 1e6

    elif gas == "nitrogen":
        h = (a_nitrogen[0] * tz +
             a_nitrogen[1] * (tz ** 2.) / 2 +
             a_nitrogen[2] * (tz ** 3.) / 3 +
             a_nitrogen[3] * (tz ** 4.) / 4 +
             a_nitrogen[4] * (tz ** 5.) / 5 +
             a_nitrogen[5] * (tz ** 6.) / 6 +
             a_nitrogen[6] * (tz ** 7.) / 7 +
             a_nitrogen[7] * (tz ** 8.) / 8 +
             a_nitrogen[8] * (tz ** 9.) / 9
             + a_nitrogen[9]
             )

        return h * 1e6

    elif gas == 'kerosene_in_air':
        h += (far / (1. + far)) * (
                b[0] * tz +
                b[1] * (tz ** 2.) / 2 +
                b[2] * (tz ** 3.) / 3 +
                b[3] * (tz ** 4.) / 4 +
                b[4] * (tz ** 5.) / 5 +
                b[5] * (tz ** 6.) / 6 +
                b[6] * (tz ** 7.) / 7 +
                b[8]
        )
        return h * 1e6

    elif gas == "water_in_air":
        h_water = (a_water[0] * tz +
                   a_water[1] * (tz ** 2.) / 2 +
                   a_water[2] * (tz ** 3.) / 3 +
                   a_water[3] * (tz ** 4.) / 4 +
                   a_water[4] * (tz ** 5.) / 5 +
                   a_water[5] * (tz ** 6.) / 6 +
                   a_water[6] * (tz ** 7.) / 7 +
                   a_water[7] * (tz ** 8.) / 8 +
                   a_water[8] * (tz ** 9.) / 9
                   + a_water[9]
                   )

        h_nitrogen = (a_nitrogen[0] * tz +
                      a_nitrogen[1] * (tz ** 2.) / 2 +
                      a_nitrogen[2] * (tz ** 3.) / 3 +
                      a_nitrogen[3] * (tz ** 4.) / 4 +
                      a_nitrogen[4] * (tz ** 5.) / 5 +
                      a_nitrogen[5] * (tz ** 6.) / 6 +
                      a_nitrogen[6] * (tz ** 7.) / 7 +
                      a_nitrogen[7] * (tz ** 8.) / 8 +
                      a_nitrogen[8] * (tz ** 9.) / 9
                      + a_nitrogen[9]
                      )

        h_mix = h2o_mw / h2_mw * far * h_water
        h_mix += (78.084 / 20.946) * n2_mw / (
                2. * h2_mw) * far * h_nitrogen
        h_mix += (1. - air_mw
                  / (2 * 0.20946 * h2_mw) * far) * h
        h_mix /= (1 + far)

        return h_mix * 1e6

        # h_mix = pm_h2o.mw() / pm_h2.mw() * far * pm_h2o.h(t)
        # h_mix += (78.084 / 20.946) * pm_n2.mw() / (
        #         2. * pm_h2.mw()) * far * pm_n2.h(t)
        # h_mix += (0.934 / 20.946) * pm_ar.mw() / (
        #         2. * pm_h2.mw()) * far * pm_ar.h(t)
        # h_mix += (0.033 / 20.946) * pm_co2.mw() / (
        #         2. * pm_h2.mw()) * far * pm_co2.h(t)
        # h_mix += (1. - pm_air.mw()
        #            / (2 * 0.20946 * pm_h2.mw()) * far) * pm_air.h(t)
        # h_mix /= (1 + far)
        #
        # return h_mix * 1e3

    else:
        msg = "Gas type {:} not recognised. Select 'air' or " \
              "'kerosene_in_air' as strings,  or adapt the " \
              "model for the required gas.".format(gas)
        raise ValueError(msg)


@lru_cache(maxsize=None)
def specific_enthalpy(t, gas="air", far=0.,
                      t_ref=None,
                      ):
    """
    Calculates the specific enthalpy of a gas.

    :param t: Temperature [K]
    :type t: float | numpy.ndarray
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 0 K, standard
        temperature for standard formation enthalpy (deprecated)
    :type t_ref: None | float
    :return: Specific enthalpy [J/kg]
    :rtype: float
    """
    # Constants required to determine cp for air and kerosene mixture
    a = [0.992313, 0.236688, -1.852148, 6.083152,
         -8.893933, 7.097112, -3.234725, 0.794571,
         -0.081873, 0.422178, 0.001053]

    # - for water
    a_water = [1.937043, -0.967916, 3.338905, -3.652122,
               2.332470, -0.819451, 0.118783, 0.,
               0., 2.860773, -0.000219]

    # - for nitrogen
    a_nitrogen = [1.075132, -0.252297, 0.341859, 0.523944,
                  -0.888984, 0.442621, -0.074788, 0.,
                  0., 0.443041, 0.0012622]

    # Constants required to determine cp for kerosene mixture
    b = [-0.718874, 8.747481, -15.863157, 17.254096,
         -10.233795, 3.081778, -0.361112, -0.003919,
         0.0555930, -0.0016079]

    tz = t / 1000.

    h = (a[0] * tz +
         a[1] * (tz ** 2.) / 2 +
         a[2] * (tz ** 3.) / 3 +
         a[3] * (tz ** 4.) / 4 +
         a[4] * (tz ** 5.) / 5 +
         a[5] * (tz ** 6.) / 6 +
         a[6] * (tz ** 7.) / 7 +
         a[7] * (tz ** 8.) / 8 +
         a[8] * (tz ** 9.) / 9
         # + a[9]
         )

    # Correct for reference non-zero K temperature
    if t_ref is None:
        h_ref = 0.
    else:
        h_ref = specific_enthalpy(t=t_ref, gas=gas, far=far, t_ref=None)

    if gas == 'air':
        return h * 1e6

    elif gas == "water":
        h = (a_water[0] * tz +
             a_water[1] * (tz ** 2.) / 2 +
             a_water[2] * (tz ** 3.) / 3 +
             a_water[3] * (tz ** 4.) / 4 +
             a_water[4] * (tz ** 5.) / 5 +
             a_water[5] * (tz ** 6.) / 6 +
             a_water[6] * (tz ** 7.) / 7 +
             a_water[7] * (tz ** 8.) / 8 +
             a_water[8] * (tz ** 9.) / 9
             # + a_water[9]
             )

        return h * 1e6 - h_ref

    elif gas == "nitrogen":
        h = (a_nitrogen[0] * tz +
             a_nitrogen[1] * (tz ** 2.) / 2 +
             a_nitrogen[2] * (tz ** 3.) / 3 +
             a_nitrogen[3] * (tz ** 4.) / 4 +
             a_nitrogen[4] * (tz ** 5.) / 5 +
             a_nitrogen[5] * (tz ** 6.) / 6 +
             a_nitrogen[6] * (tz ** 7.) / 7 +
             a_nitrogen[7] * (tz ** 8.) / 8 +
             a_nitrogen[8] * (tz ** 9.) / 9
             # + a_nitrogen[9]
             )

        return h * 1e6 - h_ref

    elif gas == 'kerosene_in_air':
        h += (far / (1. + far)) * (
                b[0] * tz +
                + b[1] * (tz ** 2.) / 2
                + b[2] * (tz ** 3.) / 3
                + b[3] * (tz ** 4.) / 4
                + b[4] * (tz ** 5.) / 5
                + b[5] * (tz ** 6.) / 6
                + b[6] * (tz ** 7.) / 7
                + b[8]
        )
        return h * 1e6 - h_ref

    elif gas == "water_in_air":
        h = (a[0] * tz +
             a[1] * (tz ** 2.) / 2 +
             a[2] * (tz ** 3.) / 3 +
             a[3] * (tz ** 4.) / 4 +
             a[4] * (tz ** 5.) / 5 +
             a[5] * (tz ** 6.) / 6 +
             a[6] * (tz ** 7.) / 7 +
             a[7] * (tz ** 8.) / 8 +
             a[8] * (tz ** 9.) / 9
             # + a[9]
             )

        h_water = (a_water[0] * tz +
                   a_water[1] * (tz ** 2.) / 2 +
                   a_water[2] * (tz ** 3.) / 3 +
                   a_water[3] * (tz ** 4.) / 4 +
                   a_water[4] * (tz ** 5.) / 5 +
                   a_water[5] * (tz ** 6.) / 6 +
                   a_water[6] * (tz ** 7.) / 7 +
                   a_water[7] * (tz ** 8.) / 8 +
                   a_water[8] * (tz ** 9.) / 9
                   # + a_water[9]
                   )

        h_nitrogen = (a_nitrogen[0] * tz +
                      a_nitrogen[1] * (tz ** 2.) / 2 +
                      a_nitrogen[2] * (tz ** 3.) / 3 +
                      a_nitrogen[3] * (tz ** 4.) / 4 +
                      a_nitrogen[4] * (tz ** 5.) / 5 +
                      a_nitrogen[5] * (tz ** 6.) / 6 +
                      a_nitrogen[6] * (tz ** 7.) / 7 +
                      a_nitrogen[7] * (tz ** 8.) / 8 +
                      a_nitrogen[8] * (tz ** 9.) / 9
                      # + a_nitrogen[9]
                      )

        h_mix = h2o_mw / h2_mw * far * h_water
        h_mix += (78.084 / 20.946) * n2_mw / (
                2. * h2_mw) * far * h_nitrogen
        h_mix += (1. - air_mw
                  / (2 * 0.20946 * h2_mw) * far) * h
        h_mix /= (1 + far)

        return h_mix * 1e6 - h_ref

    else:
        msg = "Gas type {:} not recognised. Select 'air', 'water', " \
              "'nitrogen', 'kerosene_in_air' or 'water_in_air' as strings, " \
              "or adapt the model for the required gas.".format(gas)
        raise ValueError(msg)


@lru_cache(maxsize=None)
def prescribed_delta_h(p_in, t_in, delta_h, eta_pol, gas="air",
                       far=0., t_ref=298.0):
    """
    Calculates output of physical process where a change in enthalpy is
    prescribed.

    :param p_in: Inlet pressure of process [Pa]
    :type p_in: float
    :param t_in: Inlet temperature of process [K]
    :type t_in: float
    :param delta_h: Change in specific enthalpy [J/kg] ! delta_h > 0 for
    compression and < 0 for expansion
    :param eta_pol: Polytropic efficiency of process [-]
    :type eta_pol: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 298 K, standard
    temperature for standard formation enthalpy
    :type t_ref: float
    :return: Dictionary consisting of p_out, t_out, h_out and sigma_out
    :rtype: dict
    .. note:: Function is based on TASOPT sections D.5.4 and B.3.5
    """
    # Calculate gas mixture properties of incoming flow
    r = r_gas(gas=gas, far=far)
    sigma_in = sigma(t_in, gas=gas, far=far, t_ref=t_ref)
    cp_in = cp(t_in, gas=gas, far=far)
    h_in = specific_enthalpy(t_in, gas=gas, far=far,
                             # t_ref=t_ref
                             )

    # Determine t_out using Newton iteration method
    t_initial_guess = t_in + delta_h / cp_in  # Initial guess for t_out

    # print t_initial_guess

    def residual(t):
        """
        Residual function based on Equation B.37.

        :param t: Temperature [K]
        :type t: float
        :return: Residual
        :rtype: float
        """
        res = specific_enthalpy(t,
                                gas=gas, far=far,
                                # t_ref=t_ref
                                ) - h_in - delta_h
        return res

    def residual_prime(t):
        """
        Derivative of the residual function wrt temperature, based on
        Equation B.37.

        :param t: Temperature [K]
        :type t: float
        :return: Local derivative of the residual
        :rtype: float
        """
        res_prime = cp(t, gas=gas, far=far)
        return res_prime

    t_out = optimize.newton(residual, t_initial_guess, residual_prime,
                            tol=1.e-1)

    # Determine whether it is a compression or an expansion process
    if delta_h >= 0.:
        coefficient_eta = eta_pol
    else:
        coefficient_eta = 1. / eta_pol

    # Determine outlet gas properties
    sigma_out = sigma(t_out, gas=gas, far=far, t_ref=t_ref)
    p_out = p_in * exp(coefficient_eta * (sigma_out - sigma_in) / r)
    # p_out = p_in * exp((phi_entropy(273., t_out, gas=gas, far=far) -
    # phi_entropy(273., t_out, gas=gas, far=far)) / r)
    h_out = specific_enthalpy(t_out, gas=gas, far=far,
                              # t_ref=t_ref
                              )

    # Store properties in a dictionary
    state = dict(p_out=p_out, t_out=t_out, h_out=h_out, sigma_out=sigma_out)

    return state


@lru_cache(maxsize=None)
def prescribed_p_ratio(p_in, t_in, p_ratio, eta_pol, gas="air",
                       far=0., t_ref=298.0):
    """
    Calculates output of physical process where a change in pressure
    is prescribed.

    :param p_in: Inlet total pressure of process [Pa]
    :type p_in: float
    :param t_in: Inlet total temperature of process [K]
    :type t_in: float
    :param p_ratio: Total pressure ratio [-]
    :type p_ratio: float
    :param eta_pol: Polytropic efficiency of process [-]
    :type eta_pol: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 298 K, standard temperature
     for standard formation enthalpy
    :type t_ref: float
    :return: Dictionary consisting of p_out, t_out, h_out and sigma_out
    :rtype: dict
    .. note:: Function is based on TASOPT sections D.5.1 and B.3.3
    """
    # Calculate gas mixture properties of incoming flow
    r = r_gas(gas=gas, far=far)
    sigma_in = sigma(t_in, gas=gas, far=far, t_ref=t_ref)
    cp_in = cp(t_in, gas=gas, far=far)

    # Determine whether it is a compression or an expansion process
    if p_ratio >= 1.:
        coefficient_eta = eta_pol
    else:
        coefficient_eta = 1. / eta_pol

    # Determine t_out using Newton iteration method
    t_initial_guess = t_in * p_ratio ** (r / (cp_in * coefficient_eta))

    def residual(t):
        """
        Residual function based on Equation D.13.

        :param t: Temperature [K]
        :type t: float
        :return: Residual
        :rtype: float
        """
        # print t
        res = (sigma(t, gas=gas, far=far, t_ref=t_ref) /
               r) - (sigma_in / r) - (log(p_ratio) / coefficient_eta)
        # print 'res', res
        return res

    def residual_prime(t):
        """
        Derivative of the residual function wrt temperature, based on
        Equation D.14.

        :param t: Temperature [K]
        :type t: float
        :return: Local derivative of the residual
        :rtype: float
        """
        res_prime = cp(t, gas=gas, far=far) / (r * t)
        # print 'prime', res_prime
        return res_prime

    t_out = optimize.newton(residual, t_initial_guess, residual_prime,
                            tol=1.e-1)

    # Determine outlet gas properties
    sigma_out = sigma(t_out, gas=gas, far=far, t_ref=t_ref)
    p_out = p_in * p_ratio
    h_out = specific_enthalpy(t_out, gas=gas, far=far,
                              # t_ref=t_ref
                              )

    # Store properties in a dictionary
    state = dict(p_out=p_out, t_out=t_out, h_out=h_out, sigma_out=sigma_out)

    # eta_is = (p_ratio**((g-1.)/g)-1.)/(p_ratio**((g-1)/(g*eta_pol))-1.)
    # print eta_is

    return state


@lru_cache(maxsize=None)
def prescribed_h(h_specified, gas, far=0., t_ref=None, t_initial_guess=1400.):
    """
    Calculates the temperature that corresponds with the specified enthalpy

    :param h_specified: Specific enthalpy [J/kg]
    :type h_specified: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: uel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param t_ref: Reference temperature [K] Default 298 K, standard
    temperature for standard formation enthalpy (deprecated)
    :type t_ref: float | None
    :param t_initial_guess: Initial guess for temperature
    :type t_initial_guess: float
    :return: Corresponding temperature
    :rtype: float
    """
    # Select initial guess of temperature
    # t_initial_guess = 1400.

    def residual(t):
        """
        Residual function based on TASOPT Equation B.8.

        :param t: Temperature [K]
        :type t: float
        :return: Residual
        :rtype: float
        """
        res = specific_enthalpy(
            t, gas=gas, far=far,
            t_ref=t_ref) - h_specified
        return res

    def residual_prime(t):
        """
        Derivative of the residual function with respect to temperature.

        :param t: Temperature [K]
        :type t: float
        :return: Residual
        :rtype: float
        """
        return cp(t, gas=gas, far=far)

    # Solve for corresponding temperature via Newton iteration
    t_solution = optimize.newton(residual, t_initial_guess, residual_prime,
                                 tol=1.e-1)

    return t_solution


def combustion(tt_in, mdot_in, tt_out, eta_combustion, h_fuel,
               # tt_fuel, cp_fuel,
               gas_in="air", gas_out='kerosene_in_air', far_in=0.,
               # delta_h_formation_in=0.,
               max_iter=50, err=1.e-5, diff=1.):
    """
    Model of a combustion process, calculates the added fuel flow, fuel-to-air
    ratio and exit total enthalpy.

    :param tt_in: Total temperature at the inlet of the duct [K]
    :type tt_in: float
    :param mdot_in: Mass flow at the inlet of the duct [kg/s]
    :type mdot_in: float
    :param eta_combustion: Burner efficiency, indication for amount of
    unburned fuel [-]
    :type eta_combustion: float
    :param tt_out: Total temperature at the outlet of the combustion process
    :type tt_out: float
    # :param cp_fuel: Specific heat of the injected fuel [J/(K*kg)]
    # :type cp_fuel: float
    :param h_fuel: Fuel heat of combustion [J/kg]
    :type h_fuel: float
    # :param tt_fuel: Total temperature of the injected fuel [K]
    # :type tt_fuel: float
    :param gas_in: Type of gas entering the combustor ('air' or
    'kerosene_in_air')
    :type gas_in: str
    :param far_in: Fuel-to-air ratio of gas entering the combustor
    :type far_in: float
    :param gas_out: Type of gas leaving the combustor, by default
    'kerosene_in_air'
    :type gas_out: str
    # :param delta_h_formation_in: Formation enthalpy, more a reference
    # value [J/kg] (deprecated)
    # :type delta_h_formation_in: float
    :param max_iter: Maximum of iterations allowed
    :type max_iter: int
    :param err: Maximum error between assumed static temperature and
    updated value
    :type err: float
    :param diff: Initial assumed error to start iterations, set to 1 by default
    :type diff: float
    :return: Dictionary containing gas properties after the combustion process
    (mdot_fuel_added, far_out, ht_out)
    :rtype: dict
    .. note:: Based on enthalpy balance discussed by York, Hoburg and Drela
    (2017), Section IV.A.
    """

    # Pre-combustion conditions
    ht_in = specific_enthalpy(tt_in, gas=gas_in, far=far_in,
                              # delta_h_formation=delta_h_formation_in
                              )
    mdot_air_in = mdot_in / (1 + far_in)

    # The outlet enthalpy has to be iterated since it depends on the
    # fuel-to-air ratio, which in turn depends on the
    # outlet enthalpy

    # First guess ht_out
    ht_out = specific_enthalpy(tt_out, gas=gas_out, far=far_in,
                               # delta_h_formation=delta_h_formation_in
                               )

    mdot_fuel = 0.
    far_out = 0.
    it = 0
    while (diff >= err) and (it <= max_iter):
        it = it + 1

        # mdot_fuel = mdot_in * (ht_out - ht_in) / (eta_combustion * h_fuel
        # - cp_fuel * (tt_out - tt_fuel))
        mdot_fuel = mdot_in * (ht_out - ht_in) / (
                eta_combustion * h_fuel - ht_out)
        far_out = far_in + mdot_fuel / mdot_air_in
        ht_out_update = specific_enthalpy(
            tt_out, gas=gas_out, far=far_out,
            # delta_h_formation=delta_h_formation_in
        )

        diff = abs(ht_out_update - ht_out) / ht_out
        ht_out = ht_out_update

    state = dict(mdot_fuel_added=mdot_fuel, far_out=far_out, ht_out=ht_out)
    return state


def s_o_s(ts, gas="air", far=0.):
    """
    Calculates speed of sounds (in m/s) for a given static temperature (in K).

    :param ts: Static temperature in K
    :type ts: float
    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    """
    r = r_gas(gas=gas, far=far)
    return sqrt(gamma_gas(ts, gas=gas) * r * ts)


def massfp(tt, far, mach, gas):
    """
    Returns the mass flow parameter.

    :param tt: Total temperature in K
    :type tt: float
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param mach: Mach number
    :type mach: float
    :param gas: TType of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :return: Mass flow parameter
    """
    r = r_gas(gas=gas, far=far)
    ts = t_total_to_static(t_total=tt, mach=mach, gas=gas, far=far)
    gamma_g = gamma_gas(ts, gas=gas, far=far)
    # a = s_o_s(ts, gas=gas, far=far)
    # v = mach * a
    pt_to_ps = (tt / ts) ** (gamma_g / (gamma_g - 1))
    mfp = (mach / pt_to_ps) * sqrt(gamma_g * tt / (r * ts))
    return mfp


def compressor_eta_is_from_poly(eta_pol, pr, tt, gas="air", far=0.):
    """
    Calculates the isentropic efficiency of a compression process for the
    provided polytropic efficiency.

    :param gas: Type of gas, currently only 'air' and 'kerosene_in_air'
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param eta_pol: Polytropic efficiency
    :param pr: Pressure ratio
    :param tt: Temperature of process (to calculate gamma)
    :return: Isentropic efficiency
    """

    gamma_g = gamma_gas(tt, gas=gas, far=far)
    eta_is = pr ** ((gamma_g - 1.) / gamma_g) - 1.
    eta_is /= pr ** ((gamma_g - 1.) / (gamma_g * eta_pol)) - 1.

    return eta_is


def turbine_eta_is_from_poly(eta_pol, pr, tt, gas="air", far=0.):
    """
    Calculates the isentropic efficiency of a turbine / expansion process for
    the provided polytropic efficiency.

    :param gas: Type of gas. Currently "air", "water", "nitrogen",
        "kerosene_in_air" and "water_in_air" are supported.
    :type gas: str
    :param far: Fuel-to-air ratio, defined as mdot_fuel/mdot_air [-]
    :type far: float
    :param eta_pol: Polytropic efficiency
    :param pr: Expansion ratio
    :param tt: Temperature of process (to calculate gamma)
    :return: Isentropic efficiency
    """

    gamma_g = gamma_gas(tt, gas=gas, far=far)
    eta_is = 1. - pr ** (eta_pol * (gamma_g - 1.) / gamma_g)
    eta_is /= 1. - pr ** ((gamma_g - 1.) / gamma_g)

    return eta_is


if __name__ == '__main__':
    import time

    t_test = 700.
    print("t_test", t_test)
    print("cp 0", cp(0))
    print("h 0", specific_enthalpy(0))
    print("cp test", cp(t_test))
    print("pr test", relative_pressure(t_test))
    print("h test", specific_enthalpy(t_test),
          specific_enthalpy(t_test) - 756.44e3)
    print("cp test+100", cp(t_test + 100))
    print("pr test+100", relative_pressure(t_test + 100))
    print("h test+100", specific_enthalpy(t_test + 100),
          specific_enthalpy(t_test + 100) - 866.08e3)
    print(prescribed_h(specific_enthalpy(t_test), gas="air"))
    s = time.time()
    print(prescribed_relative_pressure(relative_pressure(556)))
    print(time.time() - s)
