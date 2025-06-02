import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

def calculate_initial_planform_params(M_cruise, M_star, S_m2, A):
    """
    Calculates initial wing planform parameters, including dihedral.
    Formulas are based on Section 2.4 of the accompanying document (A05_WP2.pdf).

    Args:
        M_cruise (float): Cruise Mach number.
        M_star (float): Technology factor for supercritical airfoils.
        S_m2 (float): Wing surface area in square meters.
        A (float): Aspect ratio.

    Returns:
        dict: A dictionary containing the calculated planform parameters.
              Returns None if an invalid calculation occurs (e.g., math domain error).
    """
    params = {}
    params['M_cruise'] = M_cruise
    params['M_star'] = M_star
    params['S_m2'] = S_m2
    params['A'] = A

    # 1. Quarter-chord Sweep Angle (Lambda_c4)
    denominator_lambda_c4 = M_cruise + 0.03
    if denominator_lambda_c4 == 0:
        print("Error: Denominator for Lambda_c4 calculation is zero.")
        return None
    
    cos_Lambda_c4_val = 0.75 * M_star / denominator_lambda_c4
    if not (-1 <= cos_Lambda_c4_val <= 1):
        print(f"Error: Invalid value for acos: {cos_Lambda_c4_val}. Check M_cruise and M_star inputs.")
        print("cos(Lambda_c/4) must be between -1 and 1.")
        return None
    Lambda_c4_rad = math.acos(cos_Lambda_c4_val)
    params['Lambda_c4_deg'] = math.degrees(Lambda_c4_rad)

    # 2. Wing Span (b)
    if S_m2 < 0 or A < 0:
        print("Error: Wing surface area (S) and Aspect ratio (A) must be non-negative.")
        return None
    b_m = math.sqrt(S_m2 * A)
    params['b_m'] = b_m

    # 3. Taper Ratio (lambda_taper)
    lambda_taper = 0.2 * (2 - params['Lambda_c4_deg'] * math.pi / 180.0)
    params['lambda_taper'] = lambda_taper

    # 4. Root Chord (Cr_m)
    denominator_cr = (1 + lambda_taper) * b_m
    if denominator_cr == 0:
        print("Error: Denominator for Cr calculation is zero.")
        return None
    Cr_m = (2 * S_m2) / denominator_cr
    params['Cr_m'] = Cr_m

    # 5. Tip Chord (Ct_m)
    Ct_m = lambda_taper * Cr_m
    params['Ct_m'] = Ct_m

    # 6. Leading Edge Sweep Angle (Lambda_LE)
    if b_m == 0:
        print("Error: Wing span (b) is zero, cannot calculate LE sweep.")
        return None
    tan_Lambda_LE = math.tan(Lambda_c4_rad) - (Cr_m / (2 * b_m)) * (lambda_taper - 1)
    Lambda_LE_rad = math.atan(tan_Lambda_LE)
    params['Lambda_LE_deg'] = math.degrees(Lambda_LE_rad)

    # 7. Mean Aerodynamic Chord (C_MAC_m)
    denominator_cmac = (1 + lambda_taper)
    if denominator_cmac == 0:
        print("Error: Denominator for C_MAC calculation is zero.")
        return None
    C_MAC_m = (2.0/3.0) * Cr_m * ((1 + lambda_taper + lambda_taper**2) / denominator_cmac)
    params['C_MAC_m'] = C_MAC_m

    # 8. Y-position of MAC (y_MAC_m) - Spanwise location from centerline
    if denominator_cmac == 0:
        print("Error: Denominator for y_MAC calculation is zero.")
        return None
    y_MAC_m = (b_m / 6.0) * ((1 + 2 * lambda_taper) / denominator_cmac)
    params['y_MAC_m'] = y_MAC_m

    # 9. X-position of Leading Edge of MAC (x_LEMAC_m) - Chordwise location from root LE line
    x_LEMAC_m = y_MAC_m * math.tan(Lambda_LE_rad) # This is the chordwise offset of MAC LE
    params['x_LEMAC_m'] = x_LEMAC_m
    
    params['C_avg_m'] = (Cr_m + Ct_m) / 2.0

    # 10. Dihedral Angle (Gamma_deg)
    # Formula from document (Eq 2.10, page 16) for low wing: Gamma = 3 - (Lambda_c/4_deg / 10) + 2
    # This simplifies to Gamma = 5 - (Lambda_c/4_deg / 10)
    # Assuming low wing configuration as per document's decision (page 4).
    Gamma_deg = 5 - (params['Lambda_c4_deg'] / 10.0)
    params['Gamma_deg'] = Gamma_deg
    
    return params

def plot_wing_planform(params):
    """
    Plots the wing planform, similar to Figure 2.1 from A05_WP2.pdf and image_8e6452.png.
    Plots the right half-wing. Span is horizontal, chord is vertical (y_plot=0 at Root LE, increasing downwards).
    """
    if params is None:
        print("Cannot plot: Parameters are None.")
        return

    Cr = params['Cr_m']
    Ct = params['Ct_m']
    b_half = params['b_m'] / 2.0
    Lambda_LE_rad = math.radians(params['Lambda_LE_deg'])
    Lambda_c4_rad = math.radians(params['Lambda_c4_deg'])
    x_LEMAC_plot_coord = params['x_LEMAC_m'] 
    y_MAC_plot_coord = params['y_MAC_m']   
    C_MAC = params['C_MAC_m']

    rle_plot = (0, 0)
    rte_plot = (0, Cr)
    tle_plot_x = b_half
    tle_plot_y = b_half * math.tan(Lambda_LE_rad)
    tle_plot = (tle_plot_x, tle_plot_y)
    tte_plot_x = b_half
    tte_plot_y = tle_plot_y + Ct
    tte_plot = (tte_plot_x, tte_plot_y)

    wing_x_coords = [rle_plot[0], tle_plot[0], tte_plot[0], rte_plot[0], rle_plot[0]]
    wing_y_coords = [rle_plot[1], tle_plot[1], tte_plot[1], rte_plot[1], rle_plot[1]]

    qc_root_plot = (0, Cr / 4.0)
    qc_tip_plot_x = b_half
    qc_tip_plot_y = (Cr / 4.0) + b_half * math.tan(Lambda_c4_rad)
    qc_tip_plot = (qc_tip_plot_x, qc_tip_plot_y)
    
    qc_line_x_coords = [qc_root_plot[0], qc_tip_plot[0]]
    qc_line_y_coords = [qc_root_plot[1], qc_tip_plot[1]]

    fig, ax = plt.subplots(figsize=(12, 9))
    ax.plot(wing_x_coords, wing_y_coords, 'k-', lw=1.0)
    ax.plot(qc_line_x_coords, qc_line_y_coords, 'k:', lw=0.8) # Quarter-chord line remains dotted

    dim_line_color = 'k'
    dim_text_color = 'k'
    proj_line_style = '-' # Solid projection lines for dimensions
    dim_lw = 0.8

    dim_offset_x_major = -b_half * 0.15 
    dim_offset_x_minor = -b_half * 0.05

    # Root Chord (Cr)
    ax.plot([dim_offset_x_minor, dim_offset_x_minor], [0, Cr], color=dim_line_color, lw=dim_lw)
    ax.plot([dim_offset_x_minor, 0], [0,0], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.plot([dim_offset_x_minor, 0], [Cr,Cr], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.text(dim_offset_x_minor - b_half*0.02, Cr / 2, f"{Cr:.1f}", color=dim_text_color, ha='right', va='center', fontsize=9)

    # x_LEMAC and "14.9" (x_LEMAC + C_MAC)
    dim_val_14_9 = x_LEMAC_plot_coord + C_MAC
    ax.plot([dim_offset_x_major, dim_offset_x_major], [0, x_LEMAC_plot_coord], color=dim_line_color, lw=dim_lw)
    ax.plot([dim_offset_x_major, y_MAC_plot_coord], [x_LEMAC_plot_coord, x_LEMAC_plot_coord], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.text(dim_offset_x_major - b_half*0.02, x_LEMAC_plot_coord / 2, f"{x_LEMAC_plot_coord:.1f}", color=dim_text_color, ha='right', va='center', fontsize=9)
    
    ax.plot([dim_offset_x_major, dim_offset_x_major], [0, dim_val_14_9], color=dim_line_color, lw=dim_lw) # Main vertical dim line
    ax.plot([dim_offset_x_major, 0], [0,0], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw) # Proj to root LE
    mac_te_y_coord = x_LEMAC_plot_coord + C_MAC
    ax.plot([dim_offset_x_major, y_MAC_plot_coord], [mac_te_y_coord, mac_te_y_coord], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.text(dim_offset_x_major - b_half*0.02, (x_LEMAC_plot_coord + dim_val_14_9) / 2 , f"{dim_val_14_9:.1f}", color=dim_text_color, ha='right', va='center', fontsize=9)
    
    # Tip Chord (Ct)
    tip_dim_offset_x = b_half * 1.05
    ax.plot([tip_dim_offset_x, tip_dim_offset_x], [tle_plot_y, tte_plot_y], color=dim_line_color, lw=dim_lw)
    ax.plot([b_half, tip_dim_offset_x], [tle_plot_y, tle_plot_y], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.plot([b_half, tip_dim_offset_x], [tte_plot_y, tte_plot_y], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.text(tip_dim_offset_x + b_half*0.02, (tle_plot_y + tte_plot_y) / 2, f"{Ct:.1f}", color=dim_text_color, ha='left', va='center', fontsize=9)

    dim_offset_y_span = -Cr * 0.3 
    # Half Span (b_half)
    ax.plot([0, b_half], [dim_offset_y_span, dim_offset_y_span], color=dim_line_color, lw=dim_lw)
    ax.plot([0,0], [dim_offset_y_span, 0], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.plot([b_half, b_half], [dim_offset_y_span, tle_plot_y], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
    ax.text(b_half / 2, dim_offset_y_span - Cr*0.05, f"{b_half:.1f}", color=dim_text_color, ha='center', va='top', fontsize=9)
    
    # y_MAC (spanwise position of MAC)
    y_mac_dim_offset_y_chord = tle_plot_y + Ct + Cr*0.2 
    if y_MAC_plot_coord < b_half * 0.85 : 
        ax.plot([0, y_MAC_plot_coord], [y_mac_dim_offset_y_chord, y_mac_dim_offset_y_chord], color=dim_line_color, lw=dim_lw)
        ax.plot([y_MAC_plot_coord, y_MAC_plot_coord], [y_mac_dim_offset_y_chord, x_LEMAC_plot_coord], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw)
        ax.plot([0,0], [y_mac_dim_offset_y_chord, 0], color=dim_line_color, linestyle=proj_line_style, lw=dim_lw) 
        ax.text(y_MAC_plot_coord / 2, y_mac_dim_offset_y_chord + Cr*0.05, f"{y_MAC_plot_coord:.1f}", color=dim_text_color, ha='center', va='bottom', fontsize=9)

    angle_arc_display_radius_factor = 0.20 
    
    # Lambda_LE (Leading Edge Sweep)
    le_angle_deg_val = params['Lambda_LE_deg']
    le_display_radius = b_half * angle_arc_display_radius_factor
    ax.plot([rle_plot[0], rle_plot[0]], [rle_plot[1], rle_plot[1] - le_display_radius], 
            color=dim_line_color, linestyle='-', lw=dim_lw) 
    le_arc = Arc(rle_plot, le_display_radius * 2, le_display_radius * 2, angle=0,
                   theta1=le_angle_deg_val, theta2=90, color=dim_line_color, lw=dim_lw, linestyle='-')
    ax.add_patch(le_arc)
    mid_angle_le_rad = math.radians((le_angle_deg_val + 90) / 2.0)
    text_radius_le = le_display_radius * 0.65 
    ax.text(rle_plot[0] + text_radius_le * math.cos(mid_angle_le_rad),
            rle_plot[1] - text_radius_le * math.sin(mid_angle_le_rad), 
            f"{le_angle_deg_val:.0f}°", color=dim_text_color, ha='center', va='center', fontsize=9)

    # Lambda_c/4 (Quarter Chord Sweep)
    qc_angle_deg_val = params['Lambda_c4_deg']
    qc_display_radius = b_half * angle_arc_display_radius_factor * 1.1 
    ax.plot([qc_root_plot[0], qc_root_plot[0]], [qc_root_plot[1], qc_root_plot[1] - qc_display_radius], 
            color=dim_line_color, linestyle='-', lw=dim_lw)
    qc_arc = Arc(qc_root_plot, qc_display_radius * 2, qc_display_radius * 2, angle=0,
                   theta1=qc_angle_deg_val, theta2=90, color=dim_line_color, lw=dim_lw, linestyle='-')
    ax.add_patch(qc_arc)
    mid_angle_qc_rad = math.radians((qc_angle_deg_val + 90) / 2.0)
    text_radius_qc = qc_display_radius * 0.65
    ax.text(qc_root_plot[0] + text_radius_qc * math.cos(mid_angle_qc_rad),
            qc_root_plot[1] - text_radius_qc * math.sin(mid_angle_qc_rad),
            f"{qc_angle_deg_val:.0f}°", color=dim_text_color, ha='center', va='center', fontsize=9)

    front_text_x = b_half * 0.9
    front_text_y = tle_plot_y + Ct + Cr*0.3
    ax.text(front_text_x, front_text_y, "FRONT\n(1:100)", ha='center', va='center', fontsize=8, color=dim_text_color)

    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    
    min_plot_x_limit = dim_offset_x_major - b_half * 0.1
    max_plot_x_limit = tip_dim_offset_x + b_half * 0.1
    min_plot_y_limit = dim_offset_y_span - Cr * 0.2
    max_plot_y_limit = max(Cr, tte_plot_y, qc_tip_plot_y, y_mac_dim_offset_y_chord, front_text_y) + Cr * 0.2
    
    ax.set_xlim(min_plot_x_limit, max_plot_x_limit)
    ax.set_ylim(max_plot_y_limit, min_plot_y_limit) 

    plt.show()

# --- Main Execution ---
if __name__ == "__main__":
    input_M_cruise = 0.85
    input_M_star = 0.935
    input_S_m2 = 12.0
    input_A = 9

    print("--- Input Parameters ---")
    print(f"  Cruise Mach (M_cruise): {input_M_cruise}")
    print(f"  Technology Factor (M_star): {input_M_star}")
    print(f"  Wing Surface Area (S): {input_S_m2} m^2")
    print(f"  Aspect Ratio (A): {input_A}")
    print("-" * 30)

    calculated_params = calculate_initial_planform_params(
        input_M_cruise, input_M_star, input_S_m2, input_A
    )

    if calculated_params:
        print("--- Calculated Planform Parameters (Target: Match Table 2.1 from A05_WP2.pdf) ---")
        print(f"  Wing Span (b): {calculated_params['b_m']:.1f} m               (Expected: 55.0 m)")
        print(f"  Taper Ratio (lambda): {calculated_params['lambda_taper']:.2f}            (Expected: 0.27)")
        print(f"  Root Chord (Cr): {calculated_params['Cr_m']:.1f} m             (Expected: 8.3 m)")
        print(f"  Tip Chord (Ct): {calculated_params['Ct_m']:.1f} m              (Expected: 2.2 m)")
        print(f"  LE Sweep (Lambda_LE): {calculated_params['Lambda_LE_deg']:.1f} degrees   (Expected: 39.0 degrees)")
        print(f"  Quarter-Chord Sweep (Lambda_c/4): {calculated_params['Lambda_c4_deg']:.1f} degrees (Expected: 37.0 degrees)")
        print(f"  Dihedral Angle (Gamma): {calculated_params['Gamma_deg']:.1f} degrees       (Expected: 1.3 degrees)")
        # ... (other parameters can be printed here too)
        print("-" * 30)
        
        plot_wing_planform(calculated_params)
    else:
        print("Planform calculation failed. Please check input values and error messages.")

# Note: The expected values in the print statements are based on the example provided in the original code.