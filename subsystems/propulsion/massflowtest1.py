import math
from scipy.optimize import bisect
import matplotlib.pyplot as plt
import numpy as np

class Thrust:

    @staticmethod
    def __stuw(h, M, dtemp, mfi):
        temp = 288.15 - 0.0065 * h
        po = 101325 * (temp / 288.15) ** 5.256
        if h >= 11000:
            temp = 216.65
            po = 22631.23 * math.exp(-9.80665 / 216.65 / 287.05 * (h - 11000))
        t_o = temp + dtemp
        tto = t_o * (1 + 0.2 * M ** 2)
        pto = po * (1 + 0.2 * M ** 2) ** 3.5
        a_s = math.sqrt(1.4 * 287.05 * t_o)

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
                                return Tn
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
        return None

    @staticmethod
    def compute_mass_flow(pressure_altitude, M, DT, target_thrust):
        def thrust_diff(mfi):
            try:
                Tn = Thrust.__stuw(pressure_altitude, M, DT, mfi)
                return Tn - target_thrust
            except:
                return float('inf')

        try:
            low = Thrust.__stuw(pressure_altitude, M, DT, 0.001)
            high = Thrust.__stuw(pressure_altitude, M, DT, 0.2)
            print(f"Thrust range: {low:.2f} N to {high:.2f} N")

            if low is None or high is None or not (low <= target_thrust <= high):
                print("Target thrust out of bounds or model failure.")
                return None

            mfi = bisect(thrust_diff, 0.001, 0.2, xtol=1e-5)
        except ValueError:
            mfi = None

        return mfi

    @staticmethod
    def plot_thrust_vs_mass_flow(pressure_altitude, M, DT):
        mf_values = np.linspace(0.001, 0.2, 100)
        thrust_values = [Thrust.__stuw(pressure_altitude, M, DT, mfi) or 0 for mfi in mf_values]

        plt.figure(figsize=(8, 5))
        plt.plot(mf_values, thrust_values, label="Thrust vs Fuel Flow")
        plt.xlabel("Fuel Mass Flow (kg/s)")
        plt.ylabel("Thrust (N)")
        plt.title("Thrust Output vs Fuel Mass Flow")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    target_thrust = 800
    mfi = Thrust.compute_mass_flow(2131, 0.41, -20, target_thrust)
    if mfi is not None:
        print(f"Required fuel mass flow: {mfi:.6f} kg/s")
        thrust = Thrust._Thrust__stuw(2131, 0.41, -20, mfi)
        print(f"Back-computed thrust: {thrust:.2f} N")
    else:
        print("Could not compute fuel mass flow for the given thrust.")

    # Plot dynamic thrust vs mass flow
    Thrust.plot_thrust_vs_mass_flow(2131, 0.41, -20)
