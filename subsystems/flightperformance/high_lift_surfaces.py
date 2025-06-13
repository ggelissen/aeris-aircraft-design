import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d, CubicSpline
from design_variables import *
from class1.preliminary_sizing.prelim_sizing_wing import calculate_sweep_angle_LE

params = DesignParameters()
params.load_from_yaml("design_config.yaml")


def flaps_TE_sizing(params):
    
    print("\n============================")
    print("Trailing Edge Flap Sizing")
    print("============================")

    S_ref = params.wing.S_w                                                         # Wing surface area
    b_w = params.wing.b_w                                                           # Wing span [m]
    Lambda_025c = params.wing.Lambda_025c_w                                         # Quarter-chord sweep [rad]
    lambda_w = params.wing.lambda_w                                                 # Wing Taper ratio
    root_chord = params.wing.root_chord                                             # Root chord [m]
    Lambda_LE = calculate_sweep_angle_LE(Lambda_025c, root_chord,b_w,lambda_w)      # Leading edge sweep
    airfoil_clalpha = params.wing.airfoil_clalpha                                   # Cl alpha airfoil
    W = params.weight.W_TO                                                          # WTO
    CL_max = params.performance.CL_max_cruise                                       # Cl max
    rho = 1.225                                                                     # Density [kg/m^3]
    fus_diam = params.fuselage.D_f                                                  # Fuselage Diameter [m]
    CF_to_C = 0.34                                                                  # c_flap / c, conservative estimate
    delta_Cl_max_per_c_ratio = 1.3                                                  # for double slotted flaps
    
    c_ave = S_ref / b_w
    c_ave_HLD_TE = CF_to_C * c_ave
    cprime_over_c = (c_ave + CF_to_C * c_ave) / c_ave

    print(f"\n* Wing Geometry *")
    print(f"Wing span (b_w): {b_w:.2f} [m]")
    print(f"Root chord: {root_chord:.2f} [m]")
    print(f"Reference area (S_ref): {S_ref:.2f} [m^2]")
    print(f"Mean aerodynamic chord (approx): {c_ave:.2f} [m]")
    print(f"Trailing edge flap chord: {c_ave_HLD_TE:.2f} [m]")
    print(f"Flap chord ratio (c_flap/c): {CF_to_C:.2f}")
    print(f"Lambda_LE: {np.degrees(Lambda_LE):.2f} [°]")
    print(f"Planform taper ratio (lambda_w): {lambda_w:.2f}")

    Swf_TE = 0
    placement = []
    for i, flap in enumerate(params.wing.flapgroups):
        span_start = flap.spanwise_pos_frac_inbound * ((b_w - fus_diam) / 2)
        placement.append(span_start)
        span_end = flap.spanwise_pos_frac_outbound * ((b_w - fus_diam) / 2)
        placement.append(span_end)
        b_flap = span_end - span_start
        area = 2 * b_flap * c_ave * flap.flapwidth  # 2 for symmetric
        Swf_TE += area

        print(f"\n* Flap Group {i+1} *")
        print(f"Spanwise position (inboard): {flap.spanwise_pos_frac_inbound:.2f}")
        print(f"Spanwise position (outboard): {flap.spanwise_pos_frac_outbound:.2f}")
        print(f"Spanwise start (actual): {span_start:.2f} [m]")
        print(f"Spanwise end (actual): {span_end:.2f} [m]")
        print(f"Flap span: {b_flap:.2f} [m]")
        print(f"Flap reference area (2 sides): {area:.2f} [m^2]")

    print(f"\n* Flap Summary *")
    print(f"Total flap area (Swf_TE): {Swf_TE:.2f} [m^2]")
    print(f"Flap area as % of S_ref: {(Swf_TE / S_ref) * 100:.2f} [%]")

    delta_Cl_max = delta_Cl_max_per_c_ratio * cprime_over_c #Full flaps = landing config.
    #delta_Cl_max = 0.6 * delta_Cl_max_per_c_ratio * cprime_over_c #Not full flaps = take-off config.
    
    x_over_c = 0.75  # Hinge location ratio 
    lambda_hinge = np.arctan(np.tan(Lambda_LE) - x_over_c * 2 * root_chord / b_w * (1 - lambda_w))

    delta_CL_max = 0.9 * delta_Cl_max * (Swf_TE / S_ref) * np.cos(lambda_hinge)
    CL_max_flapped = CL_max + delta_CL_max

    print(f"\n* Aerodynamic Effects *")
    print(f"Delta Cl_max (airfoil): {delta_Cl_max:.3f}")
    print(f"Hinge sweep angle (lambda_hinge): {np.degrees(lambda_hinge):.2f}[°]")
    print(f"Delta CL_max (wing): {delta_CL_max:.3f}")
    print(f"Original CL_max: {CL_max:.3f}")
    print(f"Flapped CL_max: {CL_max_flapped:.3f}")

    V_stall_clean = np.sqrt((2 * W) / (S_ref * rho * CL_max))
    V_stall_flapped = V_stall_clean * np.sqrt(CL_max / CL_max_flapped)

    print(f"\n* Stall Speeds *")
    print(f"Stall speed (clean): {V_stall_clean:.2f} [m/s]")
    print(f"Stall speed (flapped): {V_stall_flapped:.2f} [m/s] (note: should be lower than 43.72 [knts] for landing)")
    return placement[0],placement[1],placement[2],placement[3], c_ave*CF_to_C
    

