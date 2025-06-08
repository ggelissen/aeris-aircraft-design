import numpy as np

def calculate_critical_spar_buckling_stress(E, I, A, L, K_col):
    """
    Calculates the critical Euler column buckling stress for a spar (general column).

    This formula is typically used for slender columns under compression.

    Parameters:
    E (float): Modulus of Elasticity of the material (e.g., Pascals).
    I (float): Area moment of inertia of the column's cross-section 
               about the axis of buckling (e.g., m^4).
    A (float): Cross-sectional area of the column (e.g., m^2).
    L (float): Actual length of the column (e.g., meters).
    K_col (float, optional): Column effective length factor. Depends on end conditions.
                         Default is 2.0 (Fixed-free, conservative for general spar segments).
                         Common values:
                         - Pinned-pinned: K_col = 1.0
                         - Fixed-fixed: K_col = 0.5
                         - Fixed-pinned: K_col = 0.7
                         - Fixed-free: K_col = 2.0

    Returns:
    float: Critical column buckling stress (e.g., Pascals).
           Returns np.inf if area is zero to avoid division by zero.
           Returns 0.0 if I or E is zero or L_eff is zero.
    """
    if A == 0:
        print("Warning: Cross-sectional area A is zero. Cannot compute stress.")
        return np.inf 
    if I == 0 or E == 0:
        return 0.0
    
    # Effective length
    L_eff = K_col * L
    if L_eff == 0: # Avoid division by zero if effective length is zero
        print("Warning: Effective length L_eff is zero.")
        # Or return a very large stress if I is non-zero, indicating it won't buckle due to length
        return np.inf if I > 0 else 0.0 

    critical_force = (np.pi**2 * E * I) / (L_eff**2)
    sigma_cr = critical_force / A
    
    return sigma_cr

def calculate_critical_stringer_buckling_stress(E, I, A, L, K=1.0): # Default K for stringers often pinned-pinned
    """
    Calculates the critical Euler column buckling stress for a stringer.

    This formula is typically used for slender columns (stringers) under compression.
    Parameters are the same as for calculate_critical_spar_buckling_stress.
    K default is 1.0 (pinned-pinned), common for stringers between ribs/frames.
    """
    # This function is essentially the same as spar buckling but might have different typical K values.
    # We can call the spar function or reimplement for clarity if specific stringer logic is added later.
    return calculate_critical_spar_buckling_stress(E, I, A, L, K_col=K)


def calculate_critical_sparweb_buckling_stress_compression(E, nu, t, b, K_c=3.72): # K_C estimated week 7 SAD CCFF
    """
    Calculates the critical compressive buckling stress for a flat rectangular plate (e.g., spar web in compression, skin panel).

    Parameters:
    E (float): Modulus of Elasticity of the material (e.g., Pascals).
    nu (float): Poisson's ratio of the material.
    t (float): Thickness of the plate (e.g., meters).
    b (float): Width of the plate (dimension perpendicular to the applied compressive load, 
               e.g., spacing between stringers or spars, or height of spar web if compressed along its length) (e.g., meters).
    K_c (float): Compressive buckling coefficient. Depends on aspect ratio and boundary conditions.
                 Default 3.72 might be specific. Common values:
                 - Simply supported (long plate a/b > ~3-4): K_c approx 4.0
                 - Clamped (long plate a/b > ~3-4): K_c approx 6.97

    Returns:
    float: Critical compressive plate buckling stress (e.g., Pascals).
           Returns np.inf if b or t is zero.
           Returns 0.0 if E is zero.
    """
    if b == 0 or t == 0:
        print("Warning: Plate dimension b or thickness t is zero for compression buckling.")
        return np.inf
    if E == 0:
        return 0.0

    # Ensure (1 - nu**2) is not zero or negative
    if not (1 - nu**2 > 0):
        print("Warning: Invalid Poisson's ratio, nu**2 >= 1.")
        return np.nan # Or handle error appropriately

    sigma_cr = (K_c * np.pi**2 * E) / (12 * (1 - nu**2)) * (t / b)**2 
    return sigma_cr

def calculate_critical_skin_buckling_stress_shear(E, nu, t, b, K_s):
    """
    Calculates the critical shear buckling stress for a flat rectangular plate (e.g., skin panel in shear, spar web in shear).

    Parameters:
    E (float): Modulus of Elasticity of the material (e.g., Pascals).
    nu (float): Poisson's ratio of the material.
    t (float): Thickness of the plate (e.g., meters).
    b (float): Shorter dimension of the plate panel (e.g., height of spar web, 
               or width of skin panel between stiffeners) (e.g., meters).
               For spar webs, 'b' is typically the spar height and 'a' (used to find K_s) is the rib spacing.
    K_s (float): Shear buckling coefficient. Depends on aspect ratio (a/b) and boundary conditions.
                 Common values for long plates (a/b -> infinity, where 'a' is the long dimension):
                 - Simply supported: K_s approx 5.34
                 - Clamped: K_s approx 8.98
                 For specific a/b ratios, consult charts (e.g., Niu, Bruhn, ESDU).

    Returns:
    float: Critical shear plate buckling stress (e.g., Pascals).
           Returns np.inf if b or t is zero.
           Returns 0.0 if E is zero.
    """
    if b == 0 or t == 0:
        print("Warning: Plate dimension b or thickness t is zero for shear buckling.")
        return np.inf
    if E == 0:
        return 0.0
    
    if not (1 - nu**2 > 0):
        print("Warning: Invalid Poisson's ratio, nu**2 >= 1.")
        return np.nan

    tau_cr = (K_s * np.pi**2 * E) / (12 * (1 - nu**2)) * (t / b)**2
    return tau_cr

def calculate_stiffened_skin_compressive_strength(
    E_modulus, 
    nu_poisson, 
    skin_thickness, 
    stiffener_spacing, 
    skin_buckling_coeff_Kc, 
    stiffener_crippling_stress_sigma_cc, 
    stiffener_area_As
    ):
    """
    Calculates the average compressive strength of a stiffened skin panel.

    This function implements a common procedure for stiffened panels under compression,
    based on the provided image and typical aerospace analysis methods.
    The panel strength is an average stress over the stiffener and one bay of skin.

    Parameters:
    E_modulus (float): Modulus of Elasticity of the material (Pa).
    nu_poisson (float): Poisson's ratio of the material.
    skin_thickness (float): Thickness of the skin (m).
    stiffener_spacing (float): Spacing between stiffeners (width 'b' of the skin bay) (m).
    skin_buckling_coeff_Kc (float): Compressive buckling coefficient for the skin panel
                                   (of width 'stiffener_spacing' and thickness 'skin_thickness').
                                   This is K_c in the skin buckling formula.
    stiffener_crippling_stress_sigma_cc (float): Crippling stress of the stiffener alone (Pa).
                                                This is (sigma_cc)_stiffener.
    stiffener_area_As (float): Cross-sectional area of the stiffener (m^2).

    Returns:
    float: Average compressive strength of the stiffened panel (Pa).
           Returns np.nan for invalid inputs or if total area is zero.
    """

    # Input Validation
    if not (E_modulus > 0 and 0 < nu_poisson < 0.5 and skin_thickness > 0 and \
            stiffener_spacing >= 0 and skin_buckling_coeff_Kc > 0 and \
            stiffener_crippling_stress_sigma_cc > 0 and stiffener_area_As >= 0):
        print("Warning: Invalid input parameters for stiffened panel calculation.")
        if E_modulus <=0: print(f"E_modulus ({E_modulus}) must be > 0")
        if not (0 < nu_poisson < 0.5): print(f"nu_poisson ({nu_poisson}) must be between 0 and 0.5")
        if skin_thickness <=0: print(f"skin_thickness ({skin_thickness}) must be > 0")
        if stiffener_spacing <0: print(f"stiffener_spacing ({stiffener_spacing}) must be >= 0") # Allow 0 for only stiffener case
        if skin_buckling_coeff_Kc <=0: print(f"skin_buckling_coeff_Kc ({skin_buckling_coeff_Kc}) must be > 0")
        if stiffener_crippling_stress_sigma_cc <=0: print(f"stiffener_crippling_stress_sigma_cc ({stiffener_crippling_stress_sigma_cc}) must be > 0")
        if stiffener_area_As <0: print(f"stiffener_area_As ({stiffener_area_As}) must be >= 0") # Allow 0 for only skin case
        return np.nan

    # Step 1: Calculate initial skin buckling stress (sigma_cr)_skin
    # This is for the skin panel of width 'stiffener_spacing'
    sigma_cr_skin = calculate_critical_sparweb_buckling_stress_compression(
        E_modulus, nu_poisson, skin_thickness, stiffener_spacing, skin_buckling_coeff_Kc
    )
    if np.isnan(sigma_cr_skin) and stiffener_spacing > 0 : # Propagate NaN if calculation failed and skin exists
        return np.nan
    # If stiffener_spacing is 0, sigma_cr_skin will be np.inf. This is handled later.
    if stiffener_spacing == 0: # No skin bay
        sigma_cr_skin = np.inf # Effectively, no skin to buckle

    # Step 2: Stiffener crippling stress (sigma_cc)_stiffener is an input.

    # Step 3: Calculate effective width 2*w_e of skin acting with the stiffener.
    # The formula from the image for w_e is:
    # w_e = (t/2) * sqrt( (C * pi^2) / (12*(1-nu^2)) ) * sqrt( E / (sigma_cc)_stiffener )
    # Here, C is taken as skin_buckling_coeff_Kc.
    # So, 2*w_e = t * sqrt( (K_c * pi^2 * E) / (12*(1-nu^2)*(sigma_cc)_stiffener) )
    
    two_w_e = 0.0 # Initialize effective width
    if skin_thickness > 0 and stiffener_spacing > 0 and stiffener_crippling_stress_sigma_cc > 0: # only if skin exists and stiffener can take load
        denominator_eff_width = 12 * (1 - nu_poisson**2) * stiffener_crippling_stress_sigma_cc
        if denominator_eff_width <= 0: 
            print("Warning: Denominator for effective width calculation is zero or negative.")
            return np.nan
            
        term_inside_sqrt = (skin_buckling_coeff_Kc * np.pi**2 * E_modulus) / denominator_eff_width
        
        if term_inside_sqrt > 0: 
            two_w_e = skin_thickness * np.sqrt(term_inside_sqrt)
        
        # Effective width cannot exceed the physical width of the skin bay (stiffener_spacing)
        two_w_e = min(two_w_e, stiffener_spacing)
        two_w_e = max(0, two_w_e)
    else: # No skin or no stiffener crippling stress to base effective width on
        two_w_e = 0.0


    # Step 5: Calculate panel average compressive strength (sigma_cc)_panel
    # (sigma_cc)_panel = P_total / A_total
    # P_total = P_stiffener + P_skin_effective + P_skin_buckled_remainder
    # A_total = A_stiffener + A_skin_bay

    load_stiffener = stiffener_crippling_stress_sigma_cc * stiffener_area_As
    
    # Load carried by the effective width of skin
    load_skin_effective = stiffener_crippling_stress_sigma_cc * two_w_e * skin_thickness
    
    # Load carried by the remainder of the skin (if any), stressed to sigma_cr_skin
    remaining_skin_width = stiffener_spacing - two_w_e
    load_skin_buckled_remainder = 0.0
    if remaining_skin_width > 0 and skin_thickness > 0:
        # sigma_cr_skin should be finite if stiffener_spacing > 0 and skin_thickness > 0
        if np.isinf(sigma_cr_skin): # This implies an issue, e.g. stiffener_spacing was actually 0 earlier
             print(f"Warning: sigma_cr_skin is infinite ({sigma_cr_skin}) but remaining_skin_width ({remaining_skin_width}) > 0. Check logic.")
             # Conservatively, assume it carries no additional load beyond effective width if this state is reached.
             # Or, if sigma_cr_skin is inf because b (stiffener_spacing) was 0, then remaining_skin_width should be 0.
        else:
            load_skin_buckled_remainder = sigma_cr_skin * remaining_skin_width * skin_thickness

    total_load = load_stiffener + load_skin_effective + load_skin_buckled_remainder
    
    total_area_skin_bay = stiffener_spacing * skin_thickness
    total_area = stiffener_area_As + total_area_skin_bay

    if total_area <= 0:
        # Handle cases where only stiffener or only skin might exist, though typically both are present.
        if stiffener_area_As > 0 and total_area_skin_bay <= 0: # Only stiffener
             return stiffener_crippling_stress_sigma_cc
        elif stiffener_area_As <= 0 and total_area_skin_bay > 0: # Only skin (unlikely for "stiffened panel")
             return sigma_cr_skin # Strength is just the skin buckling stress
        print("Warning: Total panel area is zero or negative, and neither stiffener-only nor skin-only case applies.")
        return np.nan 

    panel_strength = total_load / total_area
    
    return panel_strength


if __name__ == '__main__':
    print("--- Buckling Calculations ---")

    # --- Column Buckling Example (e.g., a spar CAP or stringer as a column) ---
    E_material = 70e9  # Pa (Aluminum)
    nu_material = 0.33 # Poisson's ratio for Aluminum

    # Spar Cap Example
    I_spar_cap = 1e-7  # m^4 (Moment of inertia)
    A_spar_cap = 2e-4  # m^2 (Cross-sectional area)
    L_spar_cap_segment = 1.0 # m (Actual length of the spar segment between supports)
    K_eff_spar_cap = 2.0  # Assuming pinned-pinned for this segment

    sigma_cr_spar_val = calculate_critical_spar_buckling_stress(E_material, I_spar_cap, A_spar_cap, L_spar_cap_segment, K_eff_spar_cap)
    print(f"Critical Spar/Column Buckling Stress (K={K_eff_spar_cap}): {sigma_cr_spar_val / 1e6:.2f} MPa")

    # Stringer Example (as a column)
    I_str_col = 5e-9  # m^4 
    A_str_col = 1e-4  # m^2 
    L_str_segment = 0.5  # m (Length of the stringer between ribs/frames)
    K_eff_str = 1.0   # Pinned-pinned typical for stringer segment

    sigma_cr_str_val = calculate_critical_stringer_buckling_stress(E_material, I_str_col, A_str_col, L_str_segment, K_eff_str)
    print(f"Critical Stringer (as column) Buckling Stress (K={K_eff_str}): {sigma_cr_str_val / 1e6:.2f} MPa")

    # --- Plate Buckling in Compression Example (e.g., UNSTIFFENED skin panel or spar web under axial compression) ---
    t_plate_comp = 0.002 # m (2 mm thickness)
    b_plate_width_comp = 0.15  # m (150 mm width, e.g., between potential stiffeners, or spar web height if axially compressed)
    K_c_plate_ss = 4.0 # K_c for a long plate, simply supported edges.

    sigma_cr_plate_comp_val = calculate_critical_sparweb_buckling_stress_compression(E_material, nu_material, t_plate_comp, b_plate_width_comp, K_c_plate_ss)
    print(f"Critical Compressive Buckling Stress for UNSTIFFENED plate: {sigma_cr_plate_comp_val / 1e6:.2f} MPa")

    # --- Spar Web Shear Buckling Example ---
    print("\n--- Spar Web Shear Buckling Example ---")
    t_spar_web = 0.0025  # m (2.5 mm thickness)
    h_spar_web = 0.12   # m (Spar web height, this is 'b' in the formula)
    a_rib_spacing = 0.45 # m (Rib spacing, this is 'a' used to find K_s)
    
    # K_s depends on aspect ratio a/b and boundary conditions.
    # Aspect ratio a/b = a_rib_spacing / h_spar_web
    aspect_ratio_web = a_rib_spacing / h_spar_web 
    # Example K_s: For a/b = 0.45/0.12 = 3.75. 
    # Assuming simply supported edges, K_s for a/b=3 is ~6.3, for a/b=4 is ~5.9. 
    # For a long plate (a/b -> inf), K_s is ~5.34.
    # Let's use K_s = 5.8 as an example for a/b approx 3.75 (consult charts for accuracy).
    K_s_spar_web_example = 5.8 
    print(f"Spar Web Aspect Ratio (a/b): {aspect_ratio_web:.2f}, using K_s = {K_s_spar_web_example} (example value)")

    tau_cr_spar_web_val = calculate_critical_skin_buckling_stress_shear(
        E_material, nu_material, t_spar_web, h_spar_web, K_s_spar_web_example
    )
    if not np.isnan(tau_cr_spar_web_val):
        print(f"Critical Shear Buckling Stress for Spar Web: {tau_cr_spar_web_val / 1e6:.2f} MPa")
    else:
        print("Spar web shear buckling calculation resulted in NaN.")


    # --- General Skin Panel Shear Buckling Example (could be different dimensions) ---
    # This is distinct from the spar web, could be a skin panel between stringers and ribs.
    print("\n--- General Skin Panel Shear Buckling Example ---")
    t_skin_panel_shear = 0.001 # m (1 mm thickness)
    b_skin_panel_shorter_dim = 0.10  # m (100 mm shorter dimension of the skin panel, e.g., stringer spacing)
    # Assume longer dimension 'a' is 0.3m (e.g. rib spacing). a/b = 3.
    # For a/b=3, simply supported, K_s is approx 6.3
    K_s_skin_panel_example = 6.3
    print(f"Skin Panel Shorter Dim (b): {b_skin_panel_shorter_dim}m, using K_s = {K_s_skin_panel_example} (for a/b approx 3, S.S.)")


    tau_cr_skin_panel_val = calculate_critical_skin_buckling_stress_shear(
        E_material, nu_material, t_skin_panel_shear, b_skin_panel_shorter_dim, K_s_skin_panel_example
    )
    if not np.isnan(tau_cr_skin_panel_val):
        print(f"Critical Shear Buckling Stress for Skin Panel: {tau_cr_skin_panel_val / 1e6:.2f} MPa")
    else:
        print("Skin panel shear buckling calculation resulted in NaN.")


    # --- Stiffened Skin Panel Compressive Strength Example ---
    print("\n--- Stiffened Panel Compressive Strength Example ---")
    panel_skin_t = 0.0015 # m (1.5 mm skin)
    panel_b_stiff_spacing = 0.10 # m (100 mm stiffener spacing)
    panel_Kc_skin = 4.0 # Assuming simply supported skin bays (K_c for compression)
    
    # Stiffener properties (example Z-stiffener or L-stiffener)
    # These would come from detailed stiffener analysis or database
    sigma_cc_stiffener = 250e6 # Pa (Crippling stress of the stiffener alone)
    area_stiffener = 1.2e-4    # m^2 (Cross-sectional area of one stiffener)

    panel_strength_val = calculate_stiffened_skin_compressive_strength(
        E_material, nu_material, panel_skin_t, panel_b_stiff_spacing, panel_Kc_skin,
        sigma_cc_stiffener, area_stiffener
    )
    if not np.isnan(panel_strength_val):
        print(f"Calculated Stiffened Panel Compressive Strength: {panel_strength_val / 1e6:.2f} MPa")
    else:
        print("Stiffened panel calculation resulted in NaN, check inputs/logic.")

    # Test case: No skin, only stiffener
    panel_strength_only_stiffener = calculate_stiffened_skin_compressive_strength(
        E_material, nu_material, 0, 0, panel_Kc_skin, # skin_thickness=0, stiffener_spacing=0
        sigma_cc_stiffener, area_stiffener
    )
    if not np.isnan(panel_strength_only_stiffener):
         print(f"Stiffened Panel (Stiffener Only) Strength: {panel_strength_only_stiffener / 1e6:.2f} MPa (should be {sigma_cc_stiffener/1e6:.2f} MPa)")
    
    # Test case: Very wide spacing (skin likely buckles early)
    panel_strength_wide_spacing = calculate_stiffened_skin_compressive_strength(
        E_material, nu_material, panel_skin_t, 0.5, panel_Kc_skin, # 500mm spacing
        sigma_cc_stiffener, area_stiffener
    )
    if not np.isnan(panel_strength_wide_spacing):
        print(f"Stiffened Panel (Wide Spacing) Strength: {panel_strength_wide_spacing / 1e6:.2f} MPa")

    # Test case: Very thick skin (skin less likely to buckle early)
    panel_strength_thick_skin = calculate_stiffened_skin_compressive_strength(
        E_material, nu_material, 0.005, panel_b_stiff_spacing, panel_Kc_skin, # 5mm thick skin
        sigma_cc_stiffener, area_stiffener
    )
    if not np.isnan(panel_strength_thick_skin):
        print(f"Stiffened Panel (Thick Skin) Strength: {panel_strength_thick_skin / 1e6:.2f} MPa")

    # # --- Test edge cases for original functions (uncomment if needed) ---
    # print("\n--- Edge Case Tests for Original Functions ---")
    # print(f"Column buckling with A=0: {calculate_critical_spar_buckling_stress(E_material, I_spar_cap, 0, L_spar_cap_segment, K_eff_spar_cap)}")
    # print(f"Column buckling with I=0: {calculate_critical_spar_buckling_stress(E_material, 0, A_spar_cap, L_spar_cap_segment, K_eff_spar_cap)}")
    # print(f"Plate compression with t=0: {calculate_critical_sparweb_buckling_stress_compression(E_material, nu_material, 0, b_plate_width_comp, K_c_plate_ss)}")
    # print(f"Plate shear with b=0: {calculate_critical_skin_buckling_stress_shear(E_material, nu_material, t_spar_web, 0, K_s_spar_web_example)}")
