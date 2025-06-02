import math
from scipy.optimize import bisect
import matplotlib.pyplot as plt
import numpy as np

class Thrust:

    @staticmethod
    def __stuw(h, M, dtemp, mfi):
        try:
            temp = 288.15 - 0.0065 * h
            po = 101325 * (temp / 288.15) ** 5.256
            if h >= 11000:
                temp = 216.65
                po = 22631.23 * math.exp(-9.80665 / 216.65 / 287.05 * (h - 11000))
            t_o = temp + dtemp
            tto = t_o * (1 + 0.2 * M ** 2)
            pto = po * (1 + 0.2 * M ** 2) ** 3.5
            a_s = math.sqrt(1.4 * 287.05 * t_o)

            nr = 0.98
            nf = 0.91
            nc = 0.90
            nb = 0.995
            dpt = 0.97
            nt = 0.90
            nm = 0.985
            nnc = 0.975
            nnh = 0.975
            Ac = 0.0505
            Ah = 0.1665

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
                        if fi <= 0:
                            return None
                        ehpc = (1 + fi * (6.5625 ** (0.4 / 1.4 / nc) - 1)) ** (nc * 1.4 / 0.4)
                        try:
                            sqrt_fi = math.sqrt(fi)
                        except ValueError:
                            return None
                        mht3p3 = 0.0011217 * ehpc / sqrt_fi / 6.5625
                        if mht3p3 == 0:
                            return None
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
                            t9 = tt3 * (1 - nnc * (1 - (po / pt3) ** (0.4 / 1.4)))
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
                    tel += 1
                else:
                    break
            return None
        except Exception:
            return None

    @staticmethod
    def compute_mass_flow(pressure_altitude, M, DT, target_thrust):
        def thrust_diff(mfi):
            Tn = Thrust.__stuw(pressure_altitude, M, DT, mfi)
            return float('inf') if Tn is None else Tn - target_thrust

        mf_values = np.linspace(0.001, 0.2, 300)
        valid_range = [(mfi, Thrust.__stuw(pressure_altitude, M, DT, mfi)) for mfi in mf_values]
        valid_range = [(mfi, Tn) for mfi, Tn in valid_range if Tn is not None]

        if not valid_range:
            print("No valid mass flow values found.")
            return None

        for i in range(len(valid_range) - 1):
            m1, T1 = valid_range[i]
            m2, T2 = valid_range[i + 1]
            if T1 <= target_thrust <= T2:
                try:
                    return bisect(thrust_diff, m1, m2, xtol=1e-5)
                except ValueError:
                    return None

        print("Target thrust out of bounds.")
        return None

    @staticmethod
    def plot_thrust_vs_mass_flow(pressure_altitude, M, DT, target_thrust=None):
        mf_values = np.linspace(0.001, 0.2, 300)
        thrust_values = [Thrust.__stuw(pressure_altitude, M, DT, mfi) or np.nan for mfi in mf_values]

        # Optional: print sample values for inspection
        for mfi, thrust in zip(mf_values, thrust_values):
            if not np.isnan(thrust):
                print(f"mfi = {mfi:.5f}, Thrust = {thrust:.2f} N")

        plt.figure(figsize=(8, 5))
        plt.plot(mf_values, thrust_values, label="Thrust vs Fuel Flow")
        if target_thrust:
            plt.axhline(y=target_thrust, color='r', linestyle='--', label=f"Target Thrust = {target_thrust} N")
        plt.xlabel("Fuel Mass Flow (kg/s)")
        plt.ylabel("Thrust (N)")
        plt.title("Thrust Output vs Fuel Mass Flow")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    target_thrust = 1400
    h = 12192
    M = 0.8
    DT = 0

    print("Plotting thrust vs fuel mass flow...")
    Thrust.plot_thrust_vs_mass_flow(h, M, DT, target_thrust)

    mfi = Thrust.compute_mass_flow(h, M, DT, target_thrust)
    if mfi is not None:
        print(f"Required fuel mass flow: {mfi:.6f} kg/s")
        thrust = Thrust._Thrust__stuw(h, M, DT, mfi)
        print(f"Back-computed thrust at {h} m: {thrust:.2f} N")

        if thrust and thrust > 0:
            sfc = (mfi / thrust) * 1e6  # mg/N·s
            print(f"Specific Fuel Consumption (SFC): {sfc:.6f} mg/N·s")
        else:
            print("Invalid thrust value, cannot compute SFC.")
    else:
        print("Could not compute fuel mass flow for the given thrust.")
