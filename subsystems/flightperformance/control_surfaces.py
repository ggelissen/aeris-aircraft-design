import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d, CubicSpline
from design_variables import *
from subsystems.flightperformance.high_lift_surfaces import *

params = DesignParameters()
params.load_from_yaml("design_config.yaml")


def aileron_sizing(params):
    
    b_inboard = 0.8 # Reference distance b_inboard, adjustable
    
    for i in range(100):
            
        C_r = params.wing.root_chord        # Root chord in meters (m)
        C_t = params.wing.tip_chord         # Tip chord in meters (m)    
        b = params.wing.b_w                 # Wing span in meters (m)
        c_l_alpha = params.wing.airfoil_clalpha                # Airfoil lift curve slope
        c_d_0 = params.wing.airfoil_cd0                        # Airfoil 2D drag coefficient
        S_ref = params.wing.S_w            # Reference wing surface area (m^2)
        CA_to_C = 0.2                     # Aileron chord to Wing chord ratio, accounts for rear spar
                                            
        b_outboard = 0.95                    # Reference distance b_outboard, adjustable
        b1 = b_inboard * b/2                # Inboard edge of aileron from centerline in meters (m)
        b2 = b_outboard * b/2               # Outboard edge of aileron from centerline in meters (m)
        rho = 1.225                         # Air density (kg/m^3)
        C_L_max = params.performance.CL_max_cruise               # Maximum lift coefficient in clean configuration
        delta_a = 0.349                     # Maximum Aileron deflection in radians (rad) its 25deg, 75% of the true maximum 32deg.
        bank_angle = 30                     # Desired bank angle in degrees (deg) time for roll authority = 2/3s 45deg/s for UAV
        W = params.weight.W_TO              # Aircraft weight in Newtons (N) 


        # Aileron effectiveness graph from Gudmundsson’s design handbook Aircraft Preliminary Design Handbook

        x_data = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        y_data = np.array([0, 0.26, 0.41, 0.525, 0.6, 0.675, 0.74, 0.8])

        #Interp1d
        f_cubic = interp1d(x_data, y_data, kind='cubic')
        x_new_interp1d = np.linspace(x_data.min(), x_data.max(), 500)
        y_new_interp1d = f_cubic(x_new_interp1d)

        #Cubicspline
        cs = CubicSpline(x_data, y_data)
        x_new_cs = np.linspace(x_data.min(), x_data.max(), 500)
        y_new_cs = cs(x_new_cs)

        input_x_value = CA_to_C

        estimated_y_interp1d = f_cubic(input_x_value)
        #print(f"\nEstimated y for x = {input_x_value} (using interp1d cubic): {estimated_y_interp1d:.4f}")
        estimated_y_cs = cs(input_x_value)
        #print(f"Estimated y for x = {input_x_value} (using CubicSpline): {estimated_y_cs:.4f}")

        # plt.figure(figsize=(10, 6))
        # plt.plot(x_data, y_data, 'o', label='Original Data Points', markersize=8, color='red')
        # # Plot interpolated curve using interp1d
        # plt.plot(x_new_interp1d, y_new_interp1d, '-', label='Interpolated Curve (interp1d cubic)', color='blue', linewidth=2)
        # # Plot interpolated curve using Cubicspline
        # plt.plot(x_new_cs, y_new_cs, '-', label='Interpolated Curve (Cubicspline)', color='yellow', linewidth=1)
        # # Plot the interpolated point
        # plt.plot(input_x_value, estimated_y_interp1d, 'X', label=f'Estimated Point ({input_x_value}, {estimated_y_interp1d:.4f})', markersize=10, color='purple', markeredgecolor='black')

        # plt.title('Cubic Interpolation of Data Points')
        # plt.xlabel('X-axis')
        # plt.ylabel('Y-axis')
        # plt.grid(True)
        # plt.legend()
        # plt.show()

        tau = (f_cubic(CA_to_C) + cs(CA_to_C)) / 2 # Aileron effectiveness interpolated

        V_stall = np.sqrt((W * 2) / (S_ref * rho * C_L_max)) # Stall speed in meters per second (m/s)
        #V_stall = params.stall_speed_clean

        Lambda_LE = params.wing.Lambda_w # Leading edge sweep angle in radians (rad)
        Lambda_TE = params.wing.Lambda_w # Trailing edge sweep angle in radians (rad)


        #derived from the integral of c(y) * y dy, where c(y) is the local chord at span-wise position y.
        I_1 = -(2/3) * ((C_r - C_t) / b) * b2**3 + 0.5 * C_r * b2**2 - (-(2/3) * ((C_r - C_t) / b) * b1**3 + 0.5 * C_r * b1**2)

        #derived from the integral of y^2 * c(y) dy, where c(y) is the local chord at span-wise position y.
        I_2 = -((C_r - C_t) / (2 * b)) * (b/2)**4 + (C_r * (b/2)**3) / 3

        #Aileron control derivative (C_l_delta_a)
        C_l_delta_a = (2 * c_l_alpha * tau * I_1) / (S_ref * b)

        #Roll damping derivative (C_l_p)
        C_l_p = (-4 * (c_l_alpha + c_d_0) * I_2) / (S_ref * b**2)

        #Aircraft steady state roll rate (P)
        P = (-1 * C_l_delta_a * delta_a * 2 * V_stall) / (C_l_p * b)

        #Required time to achieve bank angle (delta_t)
        delta_t = (bank_angle * np.pi) / (180 * P)

        #Loop for optimising aileron size
        if (2/3) - delta_t >= 0.005:
            b_inboard += 0.01
        elif (2/3) - delta_t <= -0.005:
            b_inboard -= 0.01
        else:
            break
        
        #print(f"The required time to achieve a {bank_angle} degree bank angle is: {delta_t:.2f} [s]")
        
        
    #Print the calculated time
    print("\n============================")
    print("Aileron Sizing")
    print("============================")
    
    print(f"\n* Inputs *")
    print(f"The required time to achieve a {bank_angle} degree bank angle is: {delta_t:.2f} [s] (note: must be below 2/3 [s])")
    print(f"TO weight: {W} [N]")
    print(f"Stall speed: {V_stall} [m/s]")
    print(f"CLmax: {C_L_max}")
    
    print(f"\n* Wing Geometry *")
    print(f"root chord: {C_r} [m]")
    print(f"Tip chord: {C_t} [m]")
    print(f"Halfspan: {b/2} [m]")
    
    print(f"\n* Aileron Placement *")
    print(f"b_inboard: {b_inboard} [m]")
    print(f"b_outboard: {b_outboard} [m]")
    print(f"b1: {b1} [m]")
    print(f"b2: {b2} [m]")
    
    print(f"\n* Surface Area *")
    print(f"Surface area wing: {S_ref} [m^2]")
    S_aileron = (b2-b1)* (params.wing.root_chord-params.wing.tip_chord) / (b/2) *b1
    print(f"Surface area aileron (approx): {S_aileron} [m^2]")
    return b1, b2, 
        

def ruddervator_sizing(params):
    #Sizing the Darth is an important step in determining required tail area
    CD_to_C = 0.3
    b_inboard = 0.25   # Start of the Darth
    b_outboard = 0.9    # End of the Darth
    
    Tail_b  = params.empennage.b_v                              # V_Tail Span in m
    Tail_ct = params.empennage.c_t                              # V-Tail Tip Chord in m
    Tail_cr = params.empennage.c_r                              # V-Tail Root Chord in m
    Tail_Sh = params.empennage.S_h                              # Horizontal Stabilizer Area in m^2
    Tail_Sv = params.empennage.S_v                              # Vertical Stabilizer Area in m^2
    Tail_dihedral = params.empennage.Gamma_h                    # V-tail dihedral
    
    Darth_start = b_inboard * Tail_b/2
    Darth_end = b_outboard * Tail_b/2
    Darth_depth = Tail_cr * CD_to_C
    Darth_S = 2 * Darth_depth * (Darth_end-Darth_start)
    
    Darth_Sh = Darth_S * np.cos(Tail_dihedral)
    Darth_Sv = Darth_S * np.sin(Tail_dihedral)
    
    Ratio_h = Darth_Sh / Tail_Sh
    Ratio_v = Darth_Sv / Tail_Sv
    print("\n============================")
    print("Ruddervator Sizing")
    print("============================")
    
    print(f"\n* Wing Geometry *")
    print(f"Tail span (b_v): {Tail_b:.3f} [m]")
    print(f"Tail root chord (c_r): {Tail_cr:.3f} m, tip chord (c_t): {Tail_ct:.3f} [m]")
    print(f"Horizontal tail area (S_h): {Tail_Sh:.3f} [m^2]")
    print(f"Vertical tail area (S_v): {Tail_Sv:.3f} [m^2]")
    print(f"Tail dihedral angle (Gamma_h): {np.degrees(Tail_dihedral):.2f} [°]")

    print(f"\n* Darth Placement *")
    print(f"Darth spanwise start: {Darth_start:.3f} [m], end: {Darth_end:.3f} [m]")
    print(f"Darth depth: {Darth_depth:.3f} [m]")
    print(f"Darth surface area (total): {Darth_S:.3f} [m^2]")

    print(f"\n* Surface Area *")
    print(f"Projected Darth horizontal area (Sh): {Darth_Sh:.3f} [m^2]")
    print(f"Projected Darth vertical area (Sv): {Darth_Sv:.3f} [m^2]")
    print(f"Horizontal area ratio (Darth_Sh / Tail_Sh): {Ratio_h:.3f} [%]")
    print(f"Vertical area ratio (Darth_Sv / Tail_Sv): {Ratio_v:.3f} [%]")
    
    return Darth_start, Darth_end


aileron_sizing(params)   
ruddervator_sizing(params)
print("\n")