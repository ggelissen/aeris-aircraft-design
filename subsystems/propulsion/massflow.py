#!/usr/bin/env python

"""
thrust.py: This code is a python translation of the VBA implementation of 
the Thrust function in Common_PFDS_ThrustFunction.xlsm.
The original code is by Paul Roling and Alexander in 't Veld.
Author: Jakub Bartmański
Date: 2025-01-29
Last update: 2025-01-29
"""

import math

class Thrust(object):

    """
    The Thrust class represents an engine and provides a method for computing thrust.

    This class has only one public method, `Thrust.compute`, which calculates the thrust for a single engine. Please, DO READ the docstring of that method for more information.
    """

    @staticmethod
    def __stuw(h, M, dtemp, mfi):

        """
        This is a private method that shall not be called directly or changed. Wrapper method .compute available for public use.
        """
        
        # Compute atmospheric conditions
        temp = 288.15 - 0.0065 * h
        po = 101325 * (temp / 288.15) ** 5.256
        if h >= 11000:
            temp = 216.65
            po = 22631.23 * math.exp(-9.80665 / 216.65 / 287.05 * (h - 11000))
        t_o = temp + dtemp
        tto = t_o * (1 + 0.2 * M ** 2)
        pto = po * (1 + 0.2 * M ** 2) ** 3.5
        a_s = math.sqrt(1.4 * 287.05 * t_o)
        
        # Initialize variables
        elpc1 = 0
        nr = 0.989
        nf = 0.7
        nc = 0.73
        nb = 0.972
        dpt = 0.95
        nt = 0.86
        nm = 0.985
        nnc = 0.925
        nnh = 0.96
        Ac = 0.0779
        Ah = 0.05244
        vo = M * a_s
        pt2 = nr * pto
        tt2 = tto
        tel = 0

        while mfi != 0:
            b = 0
            mhd = 10
            tt3d = 337.466
            c = 0
            while b < 50:
                c += 1
                d = 0
                while d < 30:
                    d += 1
                    ttb = nb * 41.865 * 10 ** 6 * mfi / 1147 / mhd
                    fi = 0.3452334 * (1 + ttb / tt3d)
                    ehpc = (1 + fi * (6.5625 ** (0.4 / 1.4 / nc) - 1)) ** (nc * 1.4 / 0.4)
                    mht3p3 = 0.0011217 * ehpc / math.sqrt(fi) / 6.5625
                    pt3 = mhd * math.sqrt(tt3d) / mht3p3
                    elpc = pt3 / pt2
                    tt3 = tt2 * (elpc ** (0.4 / 1.4 / nf))
                    deltem = tt3d / tt3
                    if deltem > 1.0005 or deltem < 0.9995:
                        tt3d = tt3d + (tt3 - tt3d) * 1.3
                        if tt3d < 100:
                            break
                if pt3 / po < 1:
                    if b > 15:
                        break
                    b += 1
                    mhd = mhd - 0.5
                    c = 0
                else:
                    p3krit = (1 - 0.4 / 2.4 / nnc) ** (-1.4 / 0.4)
                    if pt3 / po < p3krit:
                        wc = math.sqrt(2 * nnc * 1005 * tt3 * (1 - (po / pt3) ** (0.4 / 1.4)))
                        pce = po
                    else:
                        pce = pt3 / p3krit
                        t9 = tt3 * (1 - nnc * (1 - (pce / pt3) ** (0.4 / 1.4)))
                        wc = math.sqrt(1.4 * 287.05 * t9)
                    mc = Ac * pce * wc / 287.05 / t9
                    tt4 = tt3 * (ehpc ** (0.4 / 1.4 / nc))
                    tt5 = tt4 + ttb
                    tt6 = tt5 - 1005 / 1147 / nm * (tt4 - tt3)
                    bpr = mc / mhd
                    tt7 = tt6 - 1005 * (1 + bpr) * (tt3 - tt2) / 1147 / nm
                    if tt7 < 10:
                        if b > 20:
                            break
                        mhd = mhd - 0.5
                        b += 1
                        c = 0
                    else:
                        pt5 = pto * nr * elpc * ehpc * dpt
                        pt6 = pt5 * (tt6 / tt5) ** (1.33 / 0.33 / nt)
                        pt7 = pt6 * (tt7 / tt6) ** (1.33 / 0.33 / nt)
                        if pt7 / po < 1:
                            if b > 35:
                                break
                            mhd = mhd - 0.25
                            b += 1
                            c = 0
                        else:
                            p7krit = (1 - 0.33 / 2.33 / nnh) ** (-1.33 / 0.33)
                            if pt7 / po < p7krit:
                                wh = math.sqrt(2 * nnh * 1147 * tt7 * (1 - (po / pt7) ** (0.33 / 1.33)))
                                t8 = tt7 * (1 - nnh * (1 - (po / pt7) ** (0.33 / 1.33)))
                                phe = po
                            else:
                                phe = pt7 / p7krit
                                t8 = tt7 * (1 - nnh * (1 - (phe / pt7) ** (0.33 / 1.33)))
                                wh = math.sqrt(1.33 * 287.05 * t8)
                            mh = Ah * wh * phe / 287.05 / t8
                            delmh = mh / mhd
                            if c >= 40:
                                break
                            if delmh < 0.999:
                                mhd = mhd + 0.1 * (mh - mhd)
                            elif delmh > 1.001:
                                mhd = mhd + 0.05 * (mh - mhd)
                            else:
                                Tn = mc * (wc - vo) + mh * (wh - vo) + Ac * (pce - po) + Ah * (phe - po)
                                break
            if c >= 40:
                break
            if tel < 20:
                nf1 = -14803 - 0.2407085 + 96754 * elpc + 0.939903 * elpc - 279446 * elpc ** 2 - 0.26169 * elpc ** 2 + 468125 * elpc ** 3 + 0.06834 * elpc ** 3 - 501269 * elpc ** 4 - 0.62651 * elpc ** 4 + 355822 * elpc ** 5 + 0.2019 * elpc ** 5 - 167440 * elpc ** 6 - 0.79086 * elpc ** 6 + 50370 * elpc ** 7 + 0.802172 * elpc ** 7 - 8790 * elpc ** 8 - 0.376607 * elpc ** 8 + 678 * elpc ** 9 + 0.0601726 * elpc ** 9
                nc = nf1 - 0.015
                elpcc = elpc1 / elpc - 1
                if elpcc < 0:
                    elpcc = -elpcc
                if elpcc < 0.001:
                    break
                nf = nf1
                elpc1 = elpc
                tel += 1
            else:
                break
        return Tn

    @staticmethod
    def compute(pressure_altitude: float, M: float, DT: float, m_f_dot: float):

        """
        Compute the thrust for a single engine. Function wrapper. Original code due to Paul Roling and Alexander in 't Veld.

        This function calculates the thrust generated by a single engine based on the provided parameters.

        Parameters (mind the units!):
        ----------
        - `pressure_altitude` (float): Flight pressure altitude in METERS. Note this is NOT the real geometric flight altitude but pressure altitude,
        i.e., altitude computed based on the pressure measured during the flight and the ISA atmosphere model. Note that according to SVV 2024 standards, 
        pressure_altitude is what is recoreded by the aircraft's altimeter and what is available in your flight data sheet
        (with the only possible deviation of the unit).
        - `M` (float): Flight Mach number (UNITLESS).
        - `DT` (float): Delta temperature, representing T_outside - T_ISA, in KELVIN, where:
        T_outside is the outside Static Air Temperature (SAT) in Kelvin and T_ISA is the ISA temperature at `pressure_altitude` in Kelvin.
        - `m_f_dot` (float): Fuel flow in KILOGRAMS PER SECOND (for one engine).

        Returns:
        -------
        - `Fn` (float or None): The computed net thrust in Newtons for a single engine. If an error occurs during computation,
        None is returned, and an error message is printed.

        Note:
        ----
        The public method compute calls the private method `__stuw` to compute the thrust. If an exception occurs
        during the computation, an error message is printed, and Fn is set to None.
        """

        try:
            Fn = Thrust.__stuw(pressure_altitude, M, DT, m_f_dot)
        except Exception as _:
            print(f"An error has occured in thrust.py Thrust.compute method.\nThis might happen if the input parameter values are not valid. Thrust.compute is especially sensitive to too high fuel mass-flow rates (usually values above 0.2 [kg/s] are not admissible). Check your input range, units and try again. Returning None.")
            Fn = None
        return Fn

if __name__ == "__main__":
    t = Thrust.compute(2_131, 0.41, -20, 0.1)
    print(f"Net thrust of one engine: {t} [N]")
