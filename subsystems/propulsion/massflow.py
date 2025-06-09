import math

class Thrust(object):
    """
    The Thrust class represents an engine and provides methods for computing thrust
    and the required fuel flow for a target thrust.
    """

    @staticmethod
    def __stuw(h, M, dtemp, mfi):
        """
        This is a private method that shall not be called directly.
        Wrapper method .compute available for public use.
        (Minor internal safety checks/clarifications added for robustness with the solver)
        """
        
        # Compute atmospheric conditions
        temp = 288.15 - 0.0065 * h
        po = 101325 * (temp / 288.15) ** 5.256
        if h >= 11000:
            temp = 216.65
            po = 22631.23 * math.exp(-9.80665 * (h - 11000) / (216.65 * 287.05)) # Corrected denominator order
        t_o = temp + dtemp
        tto = t_o * (1 + 0.2 * M ** 2)
        pto = po * (1 + 0.2 * M ** 2) ** 3.5
        a_s = math.sqrt(1.4 * 287.05 * t_o)
        
        Tn = 0.0 # Default Tn; overwritten if calculation succeeds

        if mfi == 0: # If fuel flow is zero, thrust is zero.
            return 0.0

        # Initialize variables
        elpc1 = 0.0
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
        
        elpc = 0.0 # Initialize elpc to ensure it has a value before tel loop if mhd doesn't converge

        b = 0
        mhd = 10.0 
        tt3d = 337.466
        c_loop_counter = 0
        
        while b < 50:
            c_loop_counter += 1
            d = 0
            while d < 30:
                d += 1
                if mhd == 0: raise ValueError("mhd parameter reached zero.")
                if tt3d == 0: raise ValueError("tt3d parameter reached zero.") # Added check
                ttb = nb * 41.865 * 10 ** 6 * mfi / 1147.0 / mhd
                fi = 0.3452334 * (1 + ttb / tt3d)
                if fi <= 0: raise ValueError(f"fi parameter must be positive for sqrt, got {fi}.")
                
                # Handle potential nc=0 if updated by tel loop logic to problematic value
                if nc == 0: raise ValueError("Compressor efficiency nc cannot be zero.")
                ehpc_exponent_denom = (nc * 1.4 / 0.4)
                if ehpc_exponent_denom == 0: raise ValueError("Exponent denominator for ehpc is zero.")
                ehpc = (1 + fi * (6.5625 ** (0.4 / 1.4 / nc) - 1)) ** ehpc_exponent_denom
                
                mht3p3_denom = math.sqrt(fi) * 6.5625
                if mht3p3_denom == 0: raise ValueError("Denominator for mht3p3 is zero.")
                mht3p3 = 0.0011217 * ehpc / mht3p3_denom
                if mht3p3 == 0: raise ValueError("mht3p3 parameter reached zero.")

                if tt3d < 0: raise ValueError("tt3d cannot be negative for sqrt.")
                pt3 = mhd * math.sqrt(tt3d) / mht3p3
                if pt2 == 0: raise ValueError("pt2 is zero.")
                elpc = pt3 / pt2 
                
                # Handle potential nf=0 if updated by tel loop logic
                if nf == 0: raise ValueError("Fan efficiency nf cannot be zero.")
                tt3 = tt2 * (elpc ** (0.4 / 1.4 / nf))
                if tt3 == 0: raise ValueError("tt3 is zero.")
                deltem = tt3d / tt3
                if deltem > 1.0005 or deltem < 0.9995:
                    tt3d = tt3d + (tt3 - tt3d) * 1.3
                    if tt3d < 100: break
            
            if tt3d < 100 and d < 30 : 
                pass 

            if po == 0: raise ValueError("po is zero.")
            if pt3 / po < 1:
                if b > 15: break
                b += 1
                mhd = mhd - 0.5
                c_loop_counter = 0
            else:
                if nnc == 0: raise ValueError("nnc cannot be zero.")
                p3krit = (1 - 0.4 / 2.4 / nnc) ** (-1.4 / 0.4)
                t9_core_exit = 0.0 
                wc = 0.0
                pce = 0.0
                if pt3 / po < p3krit: 
                    if pt3 == 0: raise ValueError("pt3 is zero for pressure ratio.")
                    val_for_sqrt_wc1 = 2 * nnc * 1005 * tt3 * (1 - (po / pt3) ** (0.4 / 1.4))
                    if val_for_sqrt_wc1 < 0: raise ValueError(f"Negative val ({val_for_sqrt_wc1}) for sqrt wc (unchoked).")
                    wc = math.sqrt(val_for_sqrt_wc1)
                    pce = po
                    t9_core_exit = tt3 * (1 - nnc * (1 - (po / pt3) ** (0.4/1.4)))
                else: 
                    pce = pt3 / p3krit
                    t9_core_exit = tt3 * (1 - nnc * (1 - (pce / pt3) ** (0.4 / 1.4)))
                    if t9_core_exit <= 0: raise ValueError(f"t9_core_exit non-positive ({t9_core_exit}) for choked wc.")
                    wc = math.sqrt(1.4 * 287.05 * t9_core_exit) 
                
                if t9_core_exit <= 0: raise ValueError(f"t9_core_exit non-positive ({t9_core_exit}) for mc calc.")
                mc = Ac * pce * wc / 287.05 / t9_core_exit

                if nc == 0: raise ValueError("nc cannot be zero for tt4 calculation.")
                tt4 = tt3 * (ehpc ** (0.4 / 1.4 / nc))
                tt5 = tt4 + ttb
                if nm == 0: raise ValueError("nm is zero.")
                tt6 = tt5 - 1005.0 / 1147.0 / nm * (tt4 - tt3)
                if mhd == 0: raise ValueError("mhd is zero for bpr calculation.")
                bpr = mc / mhd 
                tt7 = tt6 - 1005.0 * (1 + bpr) * (tt3 - tt2) / 1147.0 / nm 
                
                if tt7 < 10:
                    if b > 20: break
                    mhd = mhd - 0.5
                    b += 1
                    c_loop_counter = 0
                else:
                    pt5 = pto * nr * elpc * ehpc * dpt
                    if tt5 == 0 : raise ValueError("tt5 is zero.")
                    if nt == 0: raise ValueError("nt cannot be zero.")
                    pt6 = pt5 * (tt6 / tt5) ** (1.33 / 0.33 / nt)
                    if tt6 == 0 : raise ValueError("tt6 is zero.")
                    pt7 = pt6 * (tt7 / tt6) ** (1.33 / 0.33 / nt)

                    if pt7 / po < 1:
                        if b > 35: break
                        mhd = mhd - 0.25
                        b += 1
                        c_loop_counter = 0
                    else:
                        if nnh == 0: raise ValueError("nnh cannot be zero.")
                        p7krit = (1 - 0.33 / 2.33 / nnh) ** (-1.33 / 0.33)
                        t8 = 0.0 
                        wh = 0.0
                        phe = 0.0
                        if pt7 / po < p7krit: 
                            if pt7 == 0: raise ValueError("pt7 is zero for pressure ratio.")
                            val_for_sqrt_wh1 = 2 * nnh * 1147 * tt7 * (1 - (po / pt7) ** (0.33 / 1.33))
                            if val_for_sqrt_wh1 < 0: raise ValueError(f"Negative val ({val_for_sqrt_wh1}) for sqrt wh (unchoked).")
                            wh = math.sqrt(val_for_sqrt_wh1)
                            t8 = tt7 * (1 - nnh * (1 - (po / pt7) ** (0.33 / 1.33)))
                            phe = po
                        else: 
                            phe = pt7 / p7krit
                            t8 = tt7 * (1 - nnh * (1 - (phe / pt7) ** (0.33 / 1.33)))
                            if t8 <= 0: raise ValueError(f"t8 non-positive ({t8}) for choked wh.")
                            wh = math.sqrt(1.33 * 287.05 * t8)
                        
                        if t8 <= 0: raise ValueError(f"t8 non-positive ({t8}) for mh calc.")
                        mh = Ah * wh * phe / 287.05 / t8
                        if mhd == 0: raise ValueError("mhd is zero for delmh calculation.")
                        delmh = mh / mhd
                        
                        if c_loop_counter >= 40: break 
                        if delmh < 0.999:
                            mhd = mhd + 0.1 * (mh - mhd)
                        elif delmh > 1.001:
                            mhd = mhd + 0.05 * (mh - mhd)
                        else: 
                            Tn = mc * (wc - vo) + mh * (wh - vo) + Ac * (pce - po) + Ah * (phe - po)
                            return Tn 
            
        final_tel_loop_elpc = elpc 
        while tel < 20:
            term0 = -14803.2407085
            term1 = (96754 + 0.939903) * final_tel_loop_elpc
            term2 = (-279446 - 0.26169) * final_tel_loop_elpc**2
            term3 = (468125 + 0.06834) * final_tel_loop_elpc**3
            term4 = (-501269 - 0.62651) * final_tel_loop_elpc**4 
            term5 = (355822 + 0.2019) * final_tel_loop_elpc**5
            term6 = (-167440 - 0.79086) * final_tel_loop_elpc**6
            term7 = (50370 + 0.802172) * final_tel_loop_elpc**7
            term8 = (-8790 - 0.376607) * final_tel_loop_elpc**8
            term9 = (678 + 0.0601726) * final_tel_loop_elpc**9
            nf1 = term0 + term1 + term2 + term3 + term4 + term5 + term6 + term7 + term8 + term9
            
            nc = nf1 - 0.015 # Update nc for next potential iteration (if structure was different)
            
            if final_tel_loop_elpc == 0:
                elpcc = float('inf') if elpc1 != 0 else 0.0
            else:
                elpcc = abs(elpc1 / final_tel_loop_elpc - 1)
            
            if elpcc < 0.001: break 
            
            nf = nf1 # Update nf for next potential iteration
            elpc1 = final_tel_loop_elpc
            tel += 1
        else: 
            pass 
            
        return Tn

    @staticmethod
    def compute(pressure_altitude: float, M: float, DT: float, m_f_dot: float):
        """
        Compute the thrust for a single engine. Function wrapper. Original code due to Paul Roling and Alexander in 't Veld.

        This function calculates the thrust generated by a single engine based on the provided parameters.

        Parameters (mind the units!):
        ----------
        - `pressure_altitude` (float): Flight pressure altitude in METERS.
        - `M` (float): Flight Mach number (UNITLESS).
        - `DT` (float): Delta temperature, representing T_outside - T_ISA, in KELVIN.
        - `m_f_dot` (float): Fuel flow in KILOGRAMS PER SECOND (for one engine).

        Returns:
        -------
        - `Fn` (float or None): The computed net thrust in Newtons for a single engine.
        """
        try:
            Fn = Thrust.__stuw(pressure_altitude, M, DT, m_f_dot)
        except Exception: # Catch any error from __stuw
            print(f"An error has occured in thrust.py Thrust.compute method.\nThis might happen if the input parameter values are not valid. Thrust.compute is especially sensitive to too high fuel mass-flow rates (usually values above 0.2 [kg/s] are not admissible). Check your input range, units and try again. Returning None.")
            Fn = None
        return Fn

    @staticmethod
    def compute_fuel_flow(pressure_altitude: float, M: float, DT: float, target_thrust: float,
                          initial_mf_low: float = 1e-7, 
                          initial_mf_high: float = 0.25, 
                          tol_thrust: float = 0.1,     
                          max_iter: int = 100,
                          mf_precision: float = 1e-6): 

        if target_thrust < 0:
            print(f"Error: Target thrust ({target_thrust:.2f} N) cannot be negative.")
            return None

        if abs(target_thrust) < tol_thrust:
            thrust_at_zero_mf = Thrust.compute(pressure_altitude, M, DT, 0.0)
            if thrust_at_zero_mf is not None and abs(thrust_at_zero_mf) < tol_thrust:
                return 0.0
            print(f"Info: Target thrust is {target_thrust:.2f} N (near zero). Returning m_f_dot = 0.0 kg/s. "
                  f"(Thrust.compute for 0.0 kg/s gave: {thrust_at_zero_mf})")
            return 0.0

        mf_low = initial_mf_low
        thrust_at_mf_low = Thrust.compute(pressure_altitude, M, DT, mf_low)

        if thrust_at_mf_low is None: 
            mf_low = 1e-4 
            thrust_at_mf_low = Thrust.compute(pressure_altitude, M, DT, mf_low)
            if thrust_at_mf_low is None:
                print(f"Error: Thrust computation fails for minimal practical fuel flow {mf_low:.2e} kg/s. Cannot solve.")
                return None
        
        if abs(thrust_at_mf_low - target_thrust) < tol_thrust:
            return mf_low
        if thrust_at_mf_low > target_thrust:
            print(f"Warning: Target thrust {target_thrust:.2f} N is less than thrust at minimum tested fuel flow {mf_low:.2e} kg/s (gives {thrust_at_mf_low:.2f} N). Target might be too low.")
            return None 

        mf_high = initial_mf_high
        thrust_at_mf_high = Thrust.compute(pressure_altitude, M, DT, mf_high)

        temp_mf_high_search = mf_high
        attempt = 0
        max_adjust_attempts = 10
        while thrust_at_mf_high is None and attempt < max_adjust_attempts:
            if temp_mf_high_search <= mf_low + mf_precision: 
                print(f"Error: Could not find a working mf_high (tried down to {temp_mf_high_search:.2e} kg/s) that doesn't error.")
                return None
            temp_mf_high_search = (mf_low + temp_mf_high_search) / 2 
            thrust_at_mf_high = Thrust.compute(pressure_altitude, M, DT, temp_mf_high_search)
            attempt +=1
        
        if thrust_at_mf_high is None: 
             print(f"Error: Thrust computation fails for upper bound fuel flow near {temp_mf_high_search:.2e} kg/s after adjustments.")
             return None
        mf_high = temp_mf_high_search

        if abs(thrust_at_mf_high - target_thrust) < tol_thrust:
            return mf_high
            
        if thrust_at_mf_high < target_thrust:
            mf_high_candidate = mf_high
            for _ in range(5): 
                mf_high_candidate *= 1.5 
                if mf_high_candidate > 2.0: mf_high_candidate = 2.0 
                
                thrust_candidate = Thrust.compute(pressure_altitude, M, DT, mf_high_candidate)
                if thrust_candidate is not None:
                    mf_high = mf_high_candidate
                    thrust_at_mf_high = thrust_candidate
                    if thrust_at_mf_high >= target_thrust: break 
                if mf_high_candidate == 2.0 and (thrust_candidate is None or thrust_candidate < target_thrust): break
            
            if thrust_at_mf_high < target_thrust:
                print(f"Error: Target thrust {target_thrust:.2f} N exceeds thrust at max explored fuel flow {mf_high:.2e} kg/s (gives {thrust_at_mf_high:.2f} N).")
                return None

        if not (thrust_at_mf_low < target_thrust + tol_thrust and thrust_at_mf_high > target_thrust - tol_thrust):
             print(f"Error: Target thrust {target_thrust:.2f} N not bracketed. "
                   f"Low: {mf_low:.2e} kg/s -> {thrust_at_mf_low:.2f} N. High: {mf_high:.2e} kg/s -> {thrust_at_mf_high:.2f} N.")
             return None

        for iteration in range(max_iter):
            mf_mid = (mf_low + mf_high) / 2
            
            if (mf_high - mf_low) < mf_precision : break 

            current_thrust = Thrust.compute(pressure_altitude, M, DT, mf_mid)

            if current_thrust is None: 
                mf_high = mf_mid 
                thrust_at_mf_high = None 
                continue

            error = current_thrust - target_thrust
            if abs(error) < tol_thrust: return mf_mid 

            if error < 0: 
                mf_low = mf_mid
                thrust_at_mf_low = current_thrust
            else: 
                mf_high = mf_mid
                thrust_at_mf_high = current_thrust
        
        final_mf_estimate = (mf_low + mf_high) / 2
        final_thrust_estimate = Thrust.compute(pressure_altitude, M, DT, final_mf_estimate)

        if final_thrust_estimate is not None and abs(final_thrust_estimate - target_thrust) < tol_thrust * 2.0 : 
            return final_mf_estimate
        else:
            print(f"Warning: Failed to converge accurately for target {target_thrust:.2f} N within {max_iter} iterations.")
            print(f"  Final m_f_dot: {final_mf_estimate:.4e} kg/s, gives thrust: {final_thrust_estimate if final_thrust_estimate is not None else 'Error/None'} N.")
            return None

if __name__ == "__main__":
    print("Fuel Flow Calculator for Target Thrust")
    print("-" * 35)

    try:
        h_input = float(input("Enter pressure altitude (in meters): "))
        M_input = float(input("Enter Mach number (unitless): "))
        DT_input = float(input("Enter delta temperature (T_outside - T_ISA, in Kelvin): "))
        target_thrust_input = float(input("Enter target thrust (in Newtons): "))
        print("-" * 35)

        calculated_mf = Thrust.compute_fuel_flow(
            pressure_altitude=h_input,
            M=M_input,
            DT=DT_input,
            target_thrust=target_thrust_input
        )

        if calculated_mf is not None:
            print(f"\n---> Calculated fuel mass flow: {calculated_mf:.6f} [kg/s]")
            # Verification step
            thrust_check = Thrust.compute(h_input, M_input, DT_input, calculated_mf)
            if thrust_check is not None:
                print(f"     Verification: Thrust with this m_f_dot ({calculated_mf:.6f} kg/s) is {thrust_check:.2f} [N]")
                print(f"     (Target was: {target_thrust_input:.2f} [N], Difference: {abs(thrust_check - target_thrust_input):.2f} N)")
            else:
                print(f"     Verification step failed: Thrust.compute returned None for the calculated m_f_dot.")
        else:
            print("\n---> Could not calculate the fuel mass flow for the specified target thrust and conditions.")

    except ValueError:
        print("\nError: Invalid input. Please enter numeric values.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")