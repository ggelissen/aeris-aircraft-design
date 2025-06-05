esdu_pitch_lift_derivatives_input = [
    # General
    "UNITS",        # (1 = SI, 2 = British)
    "M",            # (Mach number)
    "R",            # (Reynolds number based on aerodynamic mean chord)
    "alpha_1",      # (lower limit on incidence (deg))
    "alpha_2",      # (upper limit on incidence (deg))
    "NOP",          # (1 = full output, 0 = short output)

    # Body geometry
    "SMOOTH",       # (Marker for fuselage cross-sectional shape: 1=smooth, 0=angular)
    "HBM",          # (Value of local body height in cross-sectional plane that contains maximum local body width)
    "LA",           # (Length of tapered afterbody)
    "LB",           # (Body length)
    "L0",           # (Distance of moment reference point aft of body nose)
    "SB",           # (Planform area of body on Oxy plane)
    "SM",           # (Cross-sectional area of body in plane that contains maximum body width)
    # Conditional Body Parameters (IF SMOOTH = 0)
    "SXTENT",       # (Number of body transverse segments of smooth fuselage cross-section before change to angular)
    "S1",           # (Cross-sectional area of body base)
    "WBM",          # (Maximum value of local body width)
    "WB1",          # (Local body width at body base)
    "body_segments_wh", # Represents WB(I), HB(I) pairs for i=1 to 20. In Python, this would likely be a list of tuples or list of lists.

    # Wing planform geometry
    "DELTA",        # (Marker for wing type: 1=delta/cropped delta, 0=straight-tapered)
    "AR",           # (Wing aspect ratio)
    "BW",           # (Wing span) - Notation b
    "CDBAR",        # (Aerodynamic mean chord of wing) - Notation c_bar
    "X0D",          # (Longitudinal distance of moment ref point, aft of LE of MAC) - Notation x'_0
    "SW",           # (Planform area of gross wing)
    # Conditional Wing Parameters (IF DELTA = 1)
    "LAMDA0",       # (Sweepback of wing leading edge) - Notation Lambda_0
    # Conditional Wing Parameters (IF DELTA = 0)
    "LAMDAQ",       # (Sweepback of wing quarter-chord line) - Notation Lambda_1/4
    "LAMDAH",       # (Sweepback of wing half-chord line) - Notation Lambda_1/2
    "LAMBDA",       # (Taper ratio of wing) - Notation lambda

    # Aerofoil Geometry (Only required for straight-tapered wing, IF DELTA = 0)
    "RCJ",          # (Reynolds number based on flow normal to wing quarter-chord line and c_bar) - Notation R_c
    "XTRBYC",       # (Dimensionless chordwise location of boundary layer transition) - Notation xt/c
    "TBYC",         # (Thickness to chord ratio of aerofoil section) - Notation t/c
    "TAUDEG",       # (Aerofoil trailing-edge angle in degrees) - Notation tau

    # Tailplane Geometry
    "TPLANE",       # (Marker for presence of tailplane: 1=tailplane, 0=no tailplane)
    # Conditional Tailplane Parameters (IF TPLANE = 1)
    "AT",           # (Tailplane aspect ratio)
    "ST",           # (Planform area of gross tailplane) - Notation S_T
    "XT",           # (Longitudinal distance of tailplane quarter-chord MAC, aft of moment ref point) - Notation x_T
    "LAMDHT",       # (Sweepback of tailplane half-chord line) - Notation Lambda_H_T
    "LAMDAT",       # (Taper ratio of tailplane) - Notation lambda_T
    "DEPDAT"        # (Mean effective gradient of downwash at tailplane) - Notation d(epsilon)/d(alpha_T)
]

esdu_sideslip_derivatives_inputs = [
    # General (from Section 3.1)
    "TEXT_LINE_1",                      # First line of text for output description (up to 72 chars)
    "TEXT_LINE_2",                      # Second line of text
    "TEXT_LINE_3",                      # Third line of text
    "UNITS",                            # Integer: 1 = SI units, 2 = British units
    "M",                                # Mach number
    "R",                                # Reynolds number based on aerodynamic mean chord of wing
    "alpha1_alpha2",                    # Pair: Lower and upper limits of incidence (deg) (alpha1, alpha2)
    "NOP",                              # Integer: 1 = full output, 0 = restricted output

    # Body geometry (from Section 3.2)
    "l_b_body",                         # Overall body length (notation l_b)
    "l_moment_ref",                     # Longitudinal distance from nose tip to moment reference point (notation l)
    "hb1_body",                         # Body cross-section height at 0.25 l_b
    "hb2_body",                         # Body cross-section height at 0.75 l_b
    "Sb_body",                          # Area of side elevation of body (notation S_b)
    "W_body_at_wing_quarter_chord",     # Width of body cross-section containing quarter-chord point of wing centre-line chord (notation W)
    "H_body_at_wing_quarter_chord",     # Height of body cross-section containing quarter-chord point of wing centre-line chord (notation H)
    "alpha0B_body",                     # Value of alpha for isolated body to be at zero lift (deg) (notation alpha_0B)

    # Wing planform geometry (from Section 3.3.1)
    "b_wing",                           # Wing span
    "xr_wing_root_le",                  # Longitudinal distance from body nose tip to LE of root chord of exposed half wing (notation x_r)
    "cr_wing_exposed_root",             # Root chord of exposed half wing (notation c_r)
    "N_pan_wing",                       # Integer: Number of trapezoidal panels representing each half wing (1 <= N_pan <= 5)
    # For each wing panel i (from 1 to N_pan_wing):
    "s_i_wing_panel_inboard_coord",     # Spanwise distance from plane of symmetry of inboard chord of i'th panel (notation s_i)
    "Lambda_LE_sawtooth_LE_wing_panel", # Pair: LE sweep (deg) and sawtooth depth at LE of inboard chord for i'th panel (Lambda_LEi, d_LEi)
    "Lambda_TE_sawtooth_TE_wing_panel", # Pair: TE sweep (deg) and sawtooth depth at TE of inboard chord for i'th panel (Lambda_TEi, d_TEi)

    # Additional wing geometry (from Section 3.3.2)
    "N_gamma_wing_dihedral_segments",   # Integer: Number of wing segments defining geometric dihedral (1 <= N_gamma <= 5)
    # For each dihedral segment m (from 1 to N_gamma_wing_dihedral_segments):
    "s_m_dihedral_outboard_limit_angle",# Pair: Spanwise distance of outboard limit of m'th segment (s_m) and Dihedral angle (deg) for m'th segment (Gamma_m)
    
    "delta_tip_wing_deflection",        # Wing tip deflection under load (notation delta_tip)
    "t_c_wing_max",                     # Wing maximum thickness/chord ratio
    "t_c_wing_90_chord",                # Wing thickness/chord ratio at 90% chord
    "t_c_wing_99_chord",                # Wing thickness/chord ratio at 99% chord
    "tau_wing_trailing_edge_angle",     # Wing section trailing-edge angle (deg)
    "xtr_c_wing_transition_point",      # Distance of boundary layer transition point aft of LE as fraction of local chord
    "z_W_wing_below_body_centerline",   # Distance of quarter-chord point of wing centre-line chord below body centre-line (positive for low wing)
    "alpha0_wing_body_zero_lift",       # Incidence of body longitudinal axis when the wing-body combination is at zero lift (deg)

    # Fin geometry (from Section 3.4)
    "N_F_tailplane_position_on_fin",    # Integer: 0=none, 1=body mounted, 2=fin mounted
    "m_F_fin_moment_arm",               # Distance of fin root quarter-chord station aft of CG, parallel to body axis
    "h_BF_body_height_at_fin_root",     # Body cross-section height at fin root quarter-chord station
    "w_BF_body_width_at_fin_root",      # Body cross-section width at fin root quarter-chord station
    "z_crF_fin_root_ref_below_chord",   # Height of fin root chord from body axis, normal to body axis (notation z_crF) - *Note: doc says "distance of reference point below root chord" which seems inverse, clarify with full ESDU doc*
    "h_F_fin_height",                   # Height of fin, from fin root chord normal to body axis
    "c_rF_fin_root_chord",              # Fin root chord
    "c_tF_fin_tip_chord",               # Fin tip chord
    "Lambda_quarterF_fin_sweep",        # Fin quarter-chord sweep angle (deg)
    # Conditional Fin Parameters (IF N_F = 1 or 2 for tailplane presence, specifically N_F=2 for fin-mounted)
    "b_T_tailplane_span_on_fin",        # Tailplane span (IF N_F = 2)
    "h_T_tailplane_height_on_fin",      # Height of tailplane on fin above fin root chord (IF N_F = 2)

    # Nacelle geometry (from Section 3.5)
    "N_T_nacelle_type",                 # Integer: 0=no nacelles, 1=under-wing jet, 2=wing-mounted propeller
    # Conditional Nacelle Parameters (IF N_T = 1 or 2)
    "N_n_nacelle_pairs_per_half_wing",  # Integer: Number of nacelles on each half wing
    # For each nacelle pair k (from 1 to N_n_nacelle_pairs_per_half_wing):
    "l_n_nacelle_length_jet",           # Overall length of nacelle (IF N_T = 1)
    "delta_x_n_cowl_le_prop",           # Distance of cowl LE forward of wing LE (IF N_T = 2) (notation delta_x_n)
    "s_n_nacelle_spanwise_pos",         # Spanwise distance from plane of symmetry to nacelle centre-line
    "h_n_nacelle_max_height",           # Maximum height of nacelle cross-section
    "z_n_nacelle_below_wing_pylon_jet", # Vertical distance of nacelle C/L below wing-pylon junction (IF N_T = 1)
    "z_n_nacelle_from_wing_chord_prop", # Vertical distance of nacelle C/L from local wing chord (IF N_T = 2) (+ if below)
    "z_0_nacelle_from_moment_ref",      # Vertical distance of nacelle C/L from moment reference point (+ if below)
    "m_0_nacelle_le_fwd_moment_ref",    # Longitudinal distance of nacelle LE forward of moment reference point
    "h_ne_nacelle_exit_diameter_jet",   # Nacelle exit diameter (IF N_T = 1)

    # Flap geometry (from Section 3.6)
    "N_flap_panels_deployed",           # Integer: Number of deployed flap panels on each half-wing (0 = no flaps)
    # Conditional Flap Parameters (IF N_flap_panels_deployed > 0)
    # For each flap panel j (from 1 to N_flap_panels_deployed):
    "K_flap_user_defined_increments",   # Integer: 0=user-defined delta_CL_flap & delta_CD0_flap, 1/2/3 for program calc (plain/split/slotted) (notation K_j)
    "s_flap_inboard_outboard_limits",   # Pair: Inboard and outboard spanwise limits of j'th panel (s_j,in , s_j,out)
    "Lambda_HL_flap_hinge_line_sweep",  # Hinge-line sweep of j'th flap panel (deg)
    "x_HL0_flap_hinge_line_intersect",  # Longitudinal distance aft from moment ref point to intersection of extended flap hinge line with plane of symmetry
    # Conditional User-defined flap increments (IF K_flap_user_defined_increments = 0)
    "delta_CL_delta_CD0_flap_user",     # Pair: User-defined flap lift and profile drag coefficient increments (delta_CL_flap,j , delta_CD0_flap,j)
    # Conditional Program-calculated flap parameters (IF K_flap_user_defined_increments = 1, 2, or 3)
    "c_f_c_wing_flap_chord_ratio",      # Flap chord / wing chord at mid-span of j'th flap panel (IF K_j = 1, 2, or 3)
    "delta_f_flap_deflection_angle",    # Flap deflection angle (deg) for j'th flap panel (IF K_j = 1, 2, or 3)
    # Conditional for Plain or Split flaps (IF K_flap_user_defined_increments = 1 or 2)
    "tau_s_flap_angle_plain_split",     # Angle between section chord line and line joining TE of undeflected flap to mid-thickness point at hinge (IF K_j = 1 or 2)
    # Conditional for Slotted flaps (IF K_flap_user_defined_increments = 3)
    "c_prime_c_wing_slotted_flap_ext_chord_ratio" # Extended chord / wing chord at mid-span of j'th flap panel (IF K_j = 3)
]


esdu_roll_rate_derivatives_inputs = [
    # GENERAL and CASE DATA
    "TEXT_LINE_1",                      # First line of text for output description
    "TEXT_LINE_2",                      # Second line of text
    "TEXT_LINE_3",                      # Third line of text
    "UNITS",                            # Integer: 1 = SI units, 2 = British units
    "M",                                # Mach number
    "RCJ",                              # Reynolds number per unit length based on free-stream flow
    "ALPHA",                            # Angle of attack (deg)
    "XACB",                             # Longitudinal distance (rearward from yawing axis) to wing aero centre (fraction of wing span)

    # BODY GEOMETRY INPUT
    "W_body_at_wing_qc",                # Width of body cross-section containing quarter-chord point of wing centre-line chord
    "HBW_body_height_at_wing_qc",       # Height of body cross-section containing quarter-chord point of wing centre-line chord

    # WING PLANFORM GEOMETRY INPUT
    "BW_wing_span",                     # Wing span
    "XBD_wing_root_le_from_nose",       # Longitudinal distance from body nose tip to LE of root chord of exposed half-wing
    "CBD_wing_exposed_root_chord",      # Root chord of exposed half-wing
    "NPAN_wing_panels",                 # Integer: Number of trapezoidal panels for each exposed half-wing (1 <= NPAN <= 5)
    # For each wing panel I (from 1 to NPAN_wing_panels):
    "Y_I_wing_panel_inboard_coord",     # Spanwise distance from plane of symmetry of inboard chord of I'th panel
    "LDL_I_NDL_I_wing_panel_le_sweep_sawtooth", # Pair: LE sweep (deg) and sawtooth depth at LE of inboard chord for I'th panel
    "LDT_I_NDT_I_wing_panel_te_sweep_sawtooth", # Pair: TE sweep (deg) and sawtooth depth at TE of inboard chord for I'th panel

    # ADDITIONAL WING GEOMETRY INPUT
    "NG_wing_dihedral_segments",        # Integer: Number of wing spanwise dihedral segments (1 <= NG <= 5)
    # For each dihedral segment I (from 1 to NG_wing_dihedral_segments):
    "ETA1_I_GM_I_dihedral_outboard_limit_angle", # Pair: Spanwise distance to outboard limit of I'th segment & Dihedral angle (deg)
    "DT_wing_tip_deflection_load",      # Wing tip deflection due to load
    "A1MRKW_wing_section_lift_slope_marker", # Integer: 1=user input, 2=program calculated
    # Conditional Wing Aerofoil Parameters (IF A1MRKW = 1)
    "A10MW_wing_section_lift_slope_user", # User input: Two-dimensional lift-curve slope of wing section at M
    # Conditional Wing Aerofoil Parameters (IF A1MRKW = 2)
    "T_wing_max_thickness_chord_ratio", # Maximum thickness/chord ratio (for program calculation)
    "Y90_wing_tc_at_90_chord",          # Thickness/chord ratio at 90% chord
    "Y99_wing_tc_at_99_chord",          # Thickness/chord ratio at 99% chord
    "TAU_wing_trailing_edge_angle_deg", # Wing section trailing-edge angle (deg)
    "XT_wing_transition_point_chord_fraction", # Chordwise distance of boundary-layer transition point aft of LE

    # ADDITIONAL WING GEOMETRY INPUT (continued)
    "H0_wing_height_above_fuselage_centerline", # Height of quarter-chord point of wing C/L above fuselage C/L (+ for high wing)
    "AW_wing_body_zero_lift_incidence_deg", # Incidence of body axis when wing-body is at zero lift (deg)
    "ZETA_wing_vertical_offset_mrc_fraction_semispan", # Perpendicular distance of wing C/L chord below wing moment ref centre (fraction of semi-span, + for low wing)
    "EXI_wing_longitudinal_offset_mrc_fraction_semispan", # Distance of wing moment ref centre ahead of wing aero centre (fraction of semi-span)
    "ATTACH_flow_attachment_marker",    # Integer: 0=not fully attached, 1=fully attached
    # Conditional Wing Parameter (IF ATTACH = 0)
    "DCDDA_viscous_drag_change_with_alpha_deg", # Rate of change of viscous drag coeff with AoA (per degree)

    # FIN GEOMETRY INPUT
    "TPTYPE_tailplane_position_marker", # Integer: 0=none, 1=body-mounted, 2=fin-mounted
    "MF_fin_moment_arm_from_cg",        # Distance of fin root quarter-chord aft of CG
    "ZCRF_fin_root_chord_height_from_body_axis", # Height of fin root chord from body axis
    "HF_fin_height",                    # Height of fin from fin root chord
    "CRF_fin_root_chord",               # Fin root chord
    "CTF_fin_tip_chord",                # Fin tip chord
    "LD25F_fin_quarter_chord_sweep_deg",# Fin quarter-chord sweep angle (deg)

    # TAILPLANE GEOMETRY INPUT
    # Conditional Tailplane Parameters (IF TPTYPE_tailplane_position_marker = 1 OR 2)
    "ST_tailplane_area",                # Tailplane planform (reference) area
    "BT_tailplane_span",                # Tailplane span
    "CDBART_tailplane_mac",             # Tailplane aerodynamic mean chord
    "LAMDAT_tailplane_taper_ratio",     # Tailplane taper ratio
    "LAMDQT_tailplane_quarter_chord_sweep_deg", # Tailplane quarter-chord sweep angle (deg)
    "A1MRKT_tailplane_section_lift_slope_marker", # Integer: 1=user input, 2=program calculated
    # Conditional Tailplane Aerofoil (IF A1MRKT_tailplane_section_lift_slope_marker = 1)
    "A10MT_tailplane_section_lift_slope_user", # User input: 2D lift-curve slope of tailplane section at M
    # Conditional Tailplane Aerofoil (IF A1MRKT_tailplane_section_lift_slope_marker = 2)
    "TBYCT_tailplane_max_tc_ratio",     # Maximum thickness to chord ratio of tailplane aerofoil
    "Y90T_tailplane_tc_at_90_chord",    # Thickness/chord ratio at 90% chord of tailplane
    "Y99T_tailplane_tc_at_99_chord",    # Thickness/chord ratio at 99% chord of tailplane
    "TAUDGT_tailplane_trailing_edge_angle_deg", # Tailplane aerofoil trailing-edge angle (deg)
    "XTRCT_tailplane_transition_point_chord_fraction", # Chordwise distance of boundary-layer transition for tailplane

    # Conditional Tailplane Geometry (IF TPTYPE_tailplane_position_marker = 2, i.e., fin-mounted)
    "ZT_tailplane_height_on_fin",       # Height of intersection of fin-mounted tailplane with fin, from fin root chord

    # FLAPS GEOMETRY INPUT
    "NF_flap_panels_deployed",          # Integer: Number of deployed flap panels on each half-wing (0 <= NF <= 4, 0 = no flaps)
    # Conditional Flap Parameters (IF NF_flap_panels_deployed > 0)
    # For each flap panel j (from 1 to NF_flap_panels_deployed):
    "FTYPE_flap_calculation_type",      # Integer: 0=user-defined increments, 1=plain, 2=split, 3=single-slotted (notation FTYPE_j)
    "SFI_SFO_flap_inboard_outboard_limits", # Pair: Inboard and outboard spanwise limits of j'th panel (notation s_fi,j, s_fo,j)
    "LDH_flap_hinge_line_sweep_deg",    # Hinge-line sweep of j'th flap panel (deg) (notation Lambda_hj)
    "LH_flap_hinge_line_intersect_from_mrp", # Longitudinal distance aft from moment ref point to intersection of extended hinge line with plane of symmetry (notation l_hj)
    # Conditional User-defined flap increments (IF FTYPE_flap_calculation_type = 0)
    "DCLFL_user_defined_flap_lift_increment", # User-defined flap lift coefficient increment for j'th panel (notation Delta_CL_f,j)
        # Note: The document also mentions Delta_CD_f,j for FTYPE=0. It's listed as DCLFL in the table for user-defined values.
        # You might need to handle this as a pair or two separate inputs if the program expects both.
        # For simplicity, I'm using one placeholder. The full ESDU doc would clarify.
    # Conditional Program-calculated flap parameters (IF FTYPE_flap_calculation_type = 1, 2, or 3)
    "CF_flap_chord_ratio",              # Flap chord / wing chord at mid-span of j'th panel (notation c_f,j / c_j)
    "DF_flap_deflection_angle_deg",     # Flap deflection angle (deg) for j'th panel (notation delta_f,j)
    # Conditional for Slotted flaps (IF FTYPE_flap_calculation_type = 3)
    "CX_slotted_flap_extended_chord_ratio" # Extended chord / wing chord at mid-span of j'th flap panel (notation c'_j / c_j)
]


combined_esdu_inputs = [
    # === GENERAL & FLIGHT CONDITIONS ===
    # (Common to most ESDU aero programs)
    "TEXT_LINE_1",                      # Descriptive text
    "TEXT_LINE_2",                      # Descriptive text
    "TEXT_LINE_3",                      # Descriptive text
    "UNITS",                            # Integer: 1 = SI units, 2 = British units
    "M",                                # Mach number
    "R_global",                         # Reynolds number based on aerodynamic mean chord of wing (used in 00025/90010)
    "RCJ_per_unit_length",              # Reynolds number per unit length based on free-stream flow (used in 85010 for roll rate)
                                        # Note: R_global and RCJ_per_unit_length are related but defined differently.
                                        # One might be derivable from the other if mean chord is known.
    "alpha_limits_deg",                 # Pair: Lower and upper limits of incidence (deg) (e.g., alpha_1, alpha_2)
                                        # (00025/90010 define a range for calculation at 0.5deg intervals)
    "ALPHA_single_deg",                 # Single Angle of attack (deg) (used in 85010 for roll rate)
                                        # Note: Choose one alpha definition based on program needs.
    "NOP_output_format",                # Integer: 1 = full output, 0 = restricted output (from 00025/90010)

    # === REFERENCE DIMENSIONS & POINTS ===
    # (Generally common, but specific definitions might vary slightly per ESDU item)
    "L0_moment_ref_from_nose",          # Longitudinal distance of moment reference point aft of body nose (ESDU 90010: L0)
                                        # (ESDU 00025: l_moment_ref, 'l')
    "SREF_area",                        # Reference area for coefficients (ESDU 90010: SW for wing; ESDU 00025: S for wing; ESDU 85010: ST for tail, S for wing)
                                        # -> Need a clear, consistent SREF for the whole aircraft. Often gross wing area.
    "CBAR_mean_aerodynamic_chord",      # Aerodynamic mean chord (ESDU 90010: CDBAR; ESDU 85010: CDBART for tail)
                                        # -> Need a consistent CBAR for the wing (often the primary reference length).
    "BW_span",                          # Wing span (ESDU 90010: BW; ESDU 00025: b_wing; ESDU 85010: BW_wing_span, BT for tail)
                                        # -> Need a consistent reference span (usually wing span).
    "XACB_wing_ac_from_yaw_axis",       # Longitudinal distance rearward from yawing axis (coord origin) to wing AC (fraction of wing span) (ESDU 85010 specific)
    "X0D_mrp_aft_wing_mac_le",          # Longitudinal distance of moment ref point, aft of LE of wing MAC (ESDU 90010)

    # === BODY (FUSELAGE) GEOMETRY ===
    # (Largely common definitions needed across programs)
    "LB_body_length",                   # Overall body length (ESDU 90010: LB; ESDU 00025: l_b_body)
    "SMOOTH_body_shape_marker",         # Marker for fuselage cross-sectional shape (ESDU 90010)
    "HBM_body_max_height_at_max_width", # Body height in plane of max body width (ESDU 90010)
    "LA_body_afterbody_length",         # Length of tapered afterbody (ESDU 90010)
    "SB_body_side_area",                # Planform area of body on Oxy plane / Area of side elevation (ESDU 90010 / 00025)
    "SM_body_max_cross_section_area",   # Max cross-sectional area of body (ESDU 90010)
    # Conditional for SMOOTH=0 (ESDU 90010)
    "SXTENT_body_smooth_to_angular_segments",
    "S1_body_base_area",
    "WBM_body_max_width",
    "WB1_body_base_width",
    "body_segments_width_height_array", # Represents WB(I), HB(I) pairs (ESDU 90010)
    # From ESDU 00025 (may overlap or be more specific ways to define body for that program)
    "hb1_body_height_at_025LB",         # Body cross-section height at 0.25 l_b
    "hb2_body_height_at_075LB",         # Body cross-section height at 0.75 l_b
    "W_body_width_at_wing_qc_loc",      # Width of body at wing quarter-chord location (ESDU 00025 & 85010)
    "H_body_height_at_wing_qc_loc",     # Height of body at wing quarter-chord location (ESDU 00025)
    "HBW_body_height_at_wing_qc_loc_alt", # Alternate name for similar concept (ESDU 85010 uses HBW)
    "alpha0B_body_zero_lift_incidence_deg", # Incidence for zero body-alone lift (deg) (ESDU 00025)

    # === WING GEOMETRY ===
    # (Many common parameters, panel method inputs are specific to some ESDU items)
    "DELTA_wing_type_marker",           # 1=delta, 0=straight-tapered (ESDU 90010)
    "AR_wing_aspect_ratio",             # Wing aspect ratio (ESDU 90010 uses AR; others might use b & S to imply it)
    # BW_span already listed under Reference Dimensions
    # CDBAR_mean_aerodynamic_chord already listed
    # X0D_mrp_aft_wing_mac_le already listed
    "SW_wing_gross_area",               # Planform area of gross wing (ESDU 90010)
    # Conditional on DELTA_wing_type_marker (ESDU 90010)
    "LAMDA0_wing_le_sweep_delta",       # Wing LE sweep for delta wings
    "LAMDAQ_wing_qc_sweep_straight",    # Wing quarter-chord sweep for straight-tapered
    "LAMDAH_wing_hc_sweep_straight",    # Wing half-chord sweep for straight-tapered
    "LAMBDA_wing_taper_ratio_straight", # Wing taper ratio for straight-tapered

    # Wing Panel Definition (Used by ESDU 00025 & 85010 for more detailed wing shape)
    "XBD_wing_exposed_root_le_from_nose", # Longitudinal distance from body nose to LE of exposed root chord (ESDU 00025 & 85010)
    "CBD_wing_exposed_root_chord_val",  # Root chord of exposed half-wing (ESDU 00025 & 85010)
    "NPAN_wing_num_panels",             # Integer: Number of trapezoidal panels per half-wing
    # For each wing panel I (from 1 to NPAN_wing_num_panels):
    "Y_I_wing_panel_inboard_span_coord",# Spanwise distance from plane of symmetry to inboard chord of I'th panel
    "LDL_I_NDL_I_wing_panel_le_details",# Pair: LE sweep (deg) and sawtooth depth at LE of inboard chord
    "LDT_I_NDT_I_wing_panel_te_details",# Pair: TE sweep (deg) and sawtooth depth at TE of inboard chord

    # Additional Wing Geometry (Dihedral, Aerofoil, Thickness, Mounting)
    "NG_wing_num_dihedral_segments",    # Integer: Number of wing spanwise dihedral segments
    # For each dihedral segment I (from 1 to NG_wing_num_dihedral_segments):
    "ETA1_I_GM_I_dihedral_segment_details", # Pair: Spanwise distance to outboard limit & Dihedral angle (deg)
    "DT_wing_tip_deflection",           # Wing tip deflection due to load
    
    # Wing Aerofoil Section Properties (some conditional on DELTA or A1MRKW)
    "A1MRKW_wing_lift_slope_marker",    # Integer: 1=user input for a10, 2=program calculates a10 from t/c etc. (ESDU 85010)
    "A10MW_wing_user_a10_at_M",         # User input: 2D lift-curve slope of wing section at M (IF A1MRKW=1)
    "TBYC_wing_max_tc_ratio",           # Max thickness/chord ratio (ESDU 90010: TBYC; ESDU 85010: T_wing_max_thickness_chord_ratio)
    "Y90_wing_tc_at_90_chord_val",      # Thickness/chord ratio at 90% chord (ESDU 85010)
    "Y99_wing_tc_at_99_chord_val",      # Thickness/chord ratio at 99% chord (ESDU 85010)
    "TAUDEG_wing_trailing_edge_angle",  # Aerofoil trailing-edge angle in degrees (ESDU 90010: TAUDEG; ESDU 85010: TAU_wing_trailing_edge_angle_deg)
    "XTRBYC_wing_transition_loc",       # Dimensionless chordwise location of boundary layer transition (ESDU 90010: XTRBYC; ESDU 85010: XT_wing_transition_point_chord_fraction)
    
    # Wing-Body Integration / Mounting
    "z_W_wing_vertical_pos_rel_body",   # Distance of wing qc of C/L chord below body C/L (+ for low wing) (ESDU 00025)
    "H0_wing_qc_height_rel_fuselage_cl",# Height of wing qc of C/L chord above fuselage C/L (+ for high wing) (ESDU 85010)
                                        # Note: z_W and H0 represent similar concepts (vertical wing position) but with different sign conventions/definitions.
    "alpha0_wing_body_zero_lift_inc",   # Incidence of body axis for zero wing-body lift (deg) (ESDU 00025 uses alpha0; ESDU 85010 uses AW)
    
    # Wing Moment Reference Parameters (ESDU 85010 specific)
    "ZETA_wing_mrc_vertical_offset_frac_semispan", # Perp. dist of wing C/L chord below wing moment ref centre (frac of semi-span, + low)
    "EXI_wing_mrc_longitudinal_offset_frac_semispan",# Dist of wing moment ref centre ahead of wing AC (frac of semi-span)
    
    "ATTACH_flow_attachment_marker_val",# Integer: 0=not fully attached, 1=fully attached (ESDU 85010)
    # Conditional (IF ATTACH = 0)
    "DCDDA_viscous_drag_slope_deg",     # Rate of change of viscous drag coeff with AoA (per deg) (ESDU 85010)

    # === FIN (VERTICAL TAIL) GEOMETRY ===
    # (Parameters common if a vertical surface is defined)
    "TPTYPE_tailplane_pos_marker_fin",  # Integer denoting tailplane position (0=none, 1=body, 2=fin) (ESDU 85010, similar to N_F in 00025)
    "MF_fin_moment_arm_val",            # Distance of fin root qc aft of CG (ESDU 00025 & 85010)
    "h_BF_body_height_at_fin",          # Body cross-section height at fin root qc (ESDU 00025)
    "w_BF_body_width_at_fin",           # Body cross-section width at fin root qc (ESDU 00025)
    "ZCRF_fin_root_chord_height",       # Height of fin root chord from body axis (ESDU 00025 & 85010)
    "HF_fin_height_val",                # Height of fin from fin root chord (ESDU 00025 & 85010)
    "CRF_fin_root_chord_val",           # Fin root chord (ESDU 00025 & 85010)
    "CTF_fin_tip_chord_val",            # Fin tip chord (ESDU 00025 & 85010)
    "LD25F_fin_qc_sweep_deg",           # Fin quarter-chord sweep angle (deg) (ESDU 00025 & 85010)

    # === TAILPLANE (HORIZONTAL TAIL) GEOMETRY ===
    # (Parameters common if a horizontal surface is defined)
    "TPLANE_tailplane_presence_marker", # Marker for presence of tailplane (1=yes, 0=no) (ESDU 90010)
                                        # (ESDU 00025 uses N_F, ESDU 85010 uses TPTYPE for similar concept)
    # Conditional (IF tailplane is present)
    "AT_tailplane_aspect_ratio",        # Tailplane aspect ratio (ESDU 90010)
    "ST_tailplane_area_val",            # Planform area of gross tailplane (ESDU 90010 & 85010)
    "XT_tailplane_qc_mac_pos_from_mrp", # Longitudinal distance of tailplane qc of MAC, aft of moment ref point (ESDU 90010)
    "LAMDHT_tailplane_hc_sweep",        # Sweepback of tailplane half-chord line (ESDU 90010)
    "LAMDAT_tailplane_taper_ratio_val", # Taper ratio of tailplane (ESDU 90010 & 85010)
    "DEPDAT_downwash_gradient_at_tail", # Mean effective gradient of downwash at tailplane (ESDU 90010)
    
    "BT_tailplane_span_val",            # Tailplane span (ESDU 00025 for fin-mounted tail & ESDU 85010)
    "CDBART_tailplane_mac_val",         # Tailplane aerodynamic mean chord (ESDU 85010)
    "LAMDQT_tailplane_qc_sweep_deg",    # Tailplane quarter-chord sweep angle (deg) (ESDU 85010)
    
    # Tailplane Aerofoil Section Properties (ESDU 85010 specific)
    "A1MRKT_tailplane_lift_slope_marker", # Integer: 1=user input for a10, 2=program calculates a10
    "A10MT_tailplane_user_a10_at_M",    # User input: 2D lift-curve slope of tailplane section at M (IF A1MRKT=1)
    "TBYCT_tailplane_max_tc_ratio_val", # Max t/c ratio of tailplane aerofoil (IF A1MRKT=2)
    "Y90T_tailplane_tc_at_90_chord_val",# t/c at 90% chord of tailplane (IF A1MRKT=2)
    "Y99T_tailplane_tc_at_99_chord_val",# t/c at 99% chord of tailplane (IF A1MRKT=2)
    "TAUDGT_tailplane_te_angle_deg",    # Tailplane aerofoil trailing-edge angle (deg) (IF A1MRKT=2)
    "XTRCT_tailplane_transition_loc",   # Chordwise BL transition location for tailplane (IF A1MRKT=2)

    # Fin-Mounted Tailplane Specific (ESDU 00025 & 85010)
    "h_T_tailplane_height_on_fin_val",  # Height of tailplane on fin above fin root chord (ESDU 00025, if N_F=2)
    "ZT_tailplane_height_on_fin_alt",   # Alternate name (ESDU 85010, if TPTYPE=2)

    # === NACELLE GEOMETRY ===
    # (From ESDU 00025, assuming similar inputs might be needed if nacelles are considered for other programs)
    "N_T_nacelle_config_type",          # Integer: 0=no nacelles, 1=under-wing jet, 2=wing-mounted propeller
    # Conditional (IF N_T = 1 or 2)
    "N_n_num_nacelle_pairs",            # Integer: Number of nacelles on each half wing
    # For each nacelle pair k:
    "l_n_nacelle_length_jet_val",       # Overall length of nacelle (IF N_T = 1)
    "delta_x_n_cowl_le_fwd_wing_le_prop",# Distance of cowl LE forward of wing LE (IF N_T = 2)
    "s_n_nacelle_spanwise_pos_val",     # Spanwise distance from plane of symmetry to nacelle C/L
    "h_n_nacelle_max_height_val",       # Maximum height of nacelle cross-section
    "z_n_nacelle_below_wing_pylon_jet_val", # Vertical distance nacelle C/L below wing-pylon junction (IF N_T = 1)
    "z_n_nacelle_from_wing_chord_prop_val", # Vertical distance nacelle C/L from local wing chord (IF N_T = 2)
    "z_0_nacelle_from_mrp_val",         # Vertical distance nacelle C/L from moment reference point
    "m_0_nacelle_le_fwd_mrp_val",       # Longitudinal distance nacelle LE forward of moment reference point
    "h_ne_nacelle_exit_dia_jet_val",    # Nacelle exit diameter (IF N_T = 1)

    # === FLAPS GEOMETRY ===
    # (From ESDU 00025 & ESDU 85010, detailed flap inputs)
    "NF_num_flap_panels_deployed",      # Integer: Number of deployed flap panels on each half-wing (0=no flaps)
    # Conditional (IF NF_num_flap_panels_deployed > 0)
    # For each flap panel j:
    "FTYPE_flap_calc_type_j",           # Integer: 0=user-defined increments, 1=plain, 2=split, 3=single-slotted
    "SFI_SFO_flap_span_limits_j",       # Pair: Inboard & outboard spanwise limits of j'th panel
    "LDH_flap_hinge_sweep_deg_j",       # Hinge-line sweep of j'th flap panel (deg)
    "LH_flap_hinge_intersect_from_mrp_j",# Longitudinal distance aft from MRP to extended hinge line intersection with plane of symmetry
    # Conditional (IF FTYPE_flap_calc_type_j = 0)
    "DCLFL_user_flap_lift_incr_j",      # User-defined flap lift coefficient increment for j'th panel
                                        # (ESDU 00025 also mentions Delta_CD0_flap,j - may need a pair)
    # Conditional (IF FTYPE_flap_calc_type_j = 1, 2, or 3)
    "CF_flap_chord_ratio_j",            # Flap chord / wing chord at mid-span of j'th panel
    "DF_flap_deflection_deg_j",         # Flap deflection angle (deg) for j'th panel
    # Conditional for Slotted flaps (IF FTYPE_flap_calc_type_j = 3, ESDU 85010 specific for CX)
    "CX_slotted_flap_extended_chord_ratio_j" # Extended chord / wing chord at mid-span for slotted
]