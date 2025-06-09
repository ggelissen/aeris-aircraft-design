import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# --- Constants and Assumptions (Values are illustrative and based on typical transonic transports) ---
# Aerodynamic Parameters
M_DES = 0.82  # Design cruise Mach number
Q_CRUISE_PA = 20000  # Dynamic pressure at cruise (Pa), e.g., at 11km altitude, M 0.82 -> q approx 20-25 kPa
RHO_CRUISE = 0.364 # Air density at cruise altitude (kg/m^3) e.g. 11km
V_CRUISE = M_DES * np.sqrt(1.4 * 287 * 216.65) # Cruise speed (m/s) for q calculation if needed
GAMMA_AIR = 1.4 # Ratio of specific heats
P_STATIC_CRUISE = 22632 # Static pressure at 11km (Pa)
# Q_CRUISE_PA = 0.5 * RHO_CRUISE * V_CRUISE**2 # More accurate q

M_PRIME = 0.935  # Aerodynamic technology factor for Korn's equation (e.g., 0.935 for supercritical)
DELTA_M_DD = 0.03 # Margin for M_dd over M_des (M_dd = M_des + DELTA_M_DD)
M_DD_TARGET = M_DES + DELTA_M_DD

C_F_SKIN = 0.0028  # Skin friction coefficient (turbulent, representative)
D_W_H_FACTOR = 1.25  # Factor for horizontal tail profile drag relative to wing
R_T_FACTOR = 3.0  # Shape factor for thickness drag
OSWALD_EFF_MODIFIED = 0.92  # Modified Oswald efficiency factor (e_tilde) for wing design
CD_COMPRESSIBILITY_TARGET = 0.0008  # Target compressibility drag at M_des

# Propulsion Parameters
R_EQ_KM = 6000  # Equivalent range (km)
ETA_O_ENGINE = 0.35  # Overall engine efficiency
H_G_FUEL_KM = 4350  # Fuel specific energy (km)
MU_T_PROP_WEIGHT = 0.28  # Power plant weight per unit take-off thrust (kg/N or dimensionless if TTO in N)
TAU_THRUST_LAPSE = 0.25  # Cruise thrust / Take-off thrust at cruise altitude
DELTA_PRESSURE_RATIO = P_STATIC_CRUISE / 101325 # Pressure ratio at cruise altitude

# Structural Parameters (Illustrative - these are complex to derive)
# From Eq 10.35 for Lambda_3
R_H_TAIL_WEIGHT = 0.10 # Horizontal tail weight as fraction of wing weight
ETA_CP_WING = 0.45    # Spanwise center of pressure
N_ULT_LOAD_FACTOR = 3.75 # Ultimate load factor
W_MZF_GUESS_KG = 100000 * 9.81 # Max Zero Fuel Weight (N) - initial guess
B_REF_STRUCT_M = 100 # Reference span for wing weight (m)
LAMBDA_3_BASE = 0.0013 * (1 + R_H_TAIL_WEIGHT) * ETA_CP_WING * N_ULT_LOAD_FACTOR * np.sqrt(W_MZF_GUESS_KG / Q_CRUISE_PA) / B_REF_STRUCT_M

# From Eq 10.13 for Lambda_2
SIGMA_S_SECONDARY_STRUCT_PA = 2100 # Secondary structure specific weight (N/m^2 or Pa)
LAMBDA_2_BASE = (1 + R_H_TAIL_WEIGHT) * SIGMA_S_SECONDARY_STRUCT_PA / Q_CRUISE_PA

# Weight Parameters for MTOW (Illustrative)
W_PAY_N = 25000 * 9.81  # Payload weight (N)
DELTA_W_FIX_N = 60000 * 9.81  # Fixed weight components (N) (fuselage, systems etc.)
CD_FIXED_DRAG_AREA_M2 = 2.0  # Fixed parasite drag area (m^2) (fuselage, vert tail)
MU_RESF = 0.045  # Reserve fuel fraction of MTOW
MU_LG = 0.04  # Landing gear weight fraction of MTOW

# Constraint Parameters
ETA_TANK_VOL = 0.55 # Volumetric efficiency of wing tank
R_M_FUEL_KM = R_EQ_KM + 1500 # Max mission range for fuel tank sizing (km)
C_RESF_FUEL_FRAC = 0.15 # Reserve fuel as fraction of mission fuel for tank sizing
RHO_FUEL_KGM3 = 800 # Fuel density (kg/m^3)
CL_BUFFET_LIMIT = 0.75 # Buffet onset CL at M_des
A_W_PITCH_UP_LIMIT = 11.0 # Max aspect ratio for pitch-up for given sweep
TOFL_PROXY_SPAN_LOADING_LIMIT_NM2 = 5000 # Max W_MTO/b_w^2 (N/m^2) as a proxy for TOFL

# Fixed Design Variables for 2D plots
LAMBDA_W_DEG = 30.0  # Wing sweep angle (degrees)
LAMBDA_W_RAD = np.deg2rad(LAMBDA_W_DEG)

# --- Helper Functions ---
def calculate_geometry(CL_design, W_MTO_estimate_N, q_cruise_Pa, A_w):
    """Calculates wing area and span."""
    if q_cruise_Pa <= 0 or CL_design <= 0:
        return np.nan, np.nan
    S_w_m2 = W_MTO_estimate_N / (q_cruise_Pa * CL_design)
    if S_w_m2 <= 0 or A_w <=0:
        return np.nan, np.nan
    b_w_m = np.sqrt(A_w * S_w_m2)
    return S_w_m2, b_w_m

def calculate_tc_w_from_Mdd_constraint(M_dd_target, CL_design, Lambda_w_rad, M_prime_tech):
    """
    Calculates (t/c)_w based on M_dd constraint (rearranged from Eq. 10.49).
    (t/c)_w * (cos Lambda_w_rad)^2 = (cos Lambda_w_rad)^3 * (M_prime - M_dd_target * cos Lambda_w_rad) - 0.115 * CL_design^1.5
    """
    cos_L = np.cos(Lambda_w_rad)
    if cos_L == 0: return np.nan
    
    term1 = (cos_L**3) * (M_prime_tech - M_dd_target * cos_L)
    term2 = 0.115 * CL_design**1.5
    
    tc_cos2_lambda = term1 - term2
    if tc_cos2_lambda <= 0 or cos_L**2 == 0: # t/c must be positive
        return np.nan 
    tc_w = tc_cos2_lambda / (cos_L**2)
    return tc_w

def calculate_profile_drag_coeff_wing(tc_w, Lambda_w_rad, C_f_skin, d_w_h_factor, r_t_factor):
    """Calculates wing profile drag coefficient (Eq. 10.39)."""
    if np.isnan(tc_w): return np.nan
    cos_L_sq = np.cos(Lambda_w_rad)**2
    # (C_tilde_Dp)_w from Eq 10.37
    C_tilde_Dp_w_val = 2 * d_w_h_factor * (1 + r_t_factor * tc_w * cos_L_sq) * C_f_skin
    return C_tilde_Dp_w_val

def calculate_induced_drag_coeff(CL_design, A_w, oswald_eff_modified):
    """Calculates induced drag coefficient (Part of Eq. 10.40)."""
    if A_w <= 0 or oswald_eff_modified <=0: return np.nan
    return CL_design**2 / (np.pi * A_w * oswald_eff_modified)

def calculate_total_airframe_drag_coeff(C_profile_Dp_w, CL_design, C_induced_DL, CD_compressibility_target, S_w_m2, CD_fixed_drag_area_m2):
    """Calculates total airframe drag coefficient and L/D."""
    if np.isnan(C_profile_Dp_w) or np.isnan(C_induced_DL) or S_w_m2 <= 0:
        return np.nan, np.nan
    
    # CD0 based on Eq 8.16: CD0_airframe = C_profile_Dp_w + CD_fixed_drag_area_m2 / S_w_m2
    # This C_profile_Dp_w is (C_tilde_Dp)w from Eq 10.39, which is CD0 for the wing+tail part
    CD0_airframe = C_profile_Dp_w + (CD_fixed_drag_area_m2 / S_w_m2 if S_w_m2 > 0 else np.inf)

    C_D_total = CD0_airframe + C_induced_DL + CD_compressibility_target
    
    L_D_ratio = CL_design / C_D_total if C_D_total > 0 else np.nan
    return C_D_total, L_D_ratio

def calculate_propulsion_function(R_eq_km, eta_o_engine, H_g_fuel_km, mu_T_prop_weight, tau_thrust_lapse, delta_pressure_ratio):
    """Calculates the propulsion function F_prop (Eq. 10.9 related)."""
    if eta_o_engine <= 0 or H_g_fuel_km <=0 or tau_thrust_lapse <=0 or delta_pressure_ratio <=0:
        return np.nan
    term_fuel = R_eq_km / (eta_o_engine * H_g_fuel_km)
    term_engine_weight = mu_T_prop_weight / (tau_thrust_lapse * delta_pressure_ratio)
    return term_fuel + term_engine_weight

def calculate_wing_struct_weight_params(Lambda_3_base_val, tc_w, Lambda_w_rad, Lambda_2_base_val):
    """Calculates Lambda_1_eff and Lambda_2_eff for WPF formula, adapting Lambda_1 for t/c and sweep."""
    # Adapting Lambda_3 from Eq 10.35 to match structure of Lambda_1 in Eq 10.12 for WPF formula
    # Lambda_1_eff = Lambda_3_base / (tc_w * (np.cos(Lambda_w_rad))**2)
    # Lambda_2_eff = Lambda_2_base
    # The WPF formula (Eq 10.43) uses Lambda_3 directly with tc_w and cos(Lambda_w) in the denominator
    return Lambda_3_base_val, Lambda_2_base_val


def calculate_wpf(Lambda_3_eff, A_w, CL_design, tc_w, Lambda_w_rad, Lambda_2_eff, F_prop,
                  C_profile_Dp_w, CD_compressibility_target, oswald_eff_modified):
    """Calculates Wing Penalty Function (Eq. 10.43)."""
    if np.isnan(tc_w) or tc_w <=0 or CL_design <=0 or A_w <=0 or oswald_eff_modified <=0: return np.nan
    
    term_struct_primary = Lambda_3_eff * A_w * np.sqrt(A_w / CL_design) / (tc_w * (np.cos(Lambda_w_rad))**2)
    term_struct_secondary = Lambda_2_eff / CL_design
    
    term_prop_profile = F_prop * (C_profile_Dp_w + CD_compressibility_target) / CL_design
    term_prop_induced = F_prop * CL_design / (np.pi * A_w * oswald_eff_modified)
    
    wpf_val = term_struct_primary + term_struct_secondary + term_prop_profile + term_prop_induced
    return wpf_val

def calculate_mtow_N(W_pay_N, delta_W_fix_N, F_prop, q_cruise_Pa, CD_fixed_drag_area_m2,
                     mu_resf, mu_lg, wpf):
    """Calculates Maximum Take-Off Weight (N) (Eq. 10.15)."""
    if np.isnan(wpf): return np.nan
    
    numerator = W_pay_N + delta_W_fix_N + F_prop * q_cruise_Pa * CD_fixed_drag_area_m2
    denominator = 1 - (mu_resf + mu_lg + wpf)
    
    if denominator <= 0: # Avoid division by zero or negative (unphysical)
        return np.nan
    return numerator / denominator

# --- Main Visualization Logic ---
CL_design_range = np.linspace(0.3, 0.7, 21)  # Range for Design Lift Coefficient
A_w_range = np.linspace(6, 14, 21)      # Range for Aspect Ratio

WPF_results = np.zeros((len(A_w_range), len(CL_design_range)))
MTOW_results_N = np.zeros((len(A_w_range), len(CL_design_range)))
TC_W_results = np.zeros((len(A_w_range), len(CL_design_range)))
S_W_results = np.zeros((len(A_w_range), len(CL_design_range)))
B_W_results = np.zeros((len(A_w_range), len(CL_design_range)))

# Constraint satisfaction matrices
fuel_vol_ok = np.zeros_like(WPF_results, dtype=bool)
buffet_ok = np.zeros_like(WPF_results, dtype=bool)
aspect_ratio_ok = np.zeros_like(WPF_results, dtype=bool)
span_loading_ok = np.zeros_like(WPF_results, dtype=bool)
tc_w_valid = np.zeros_like(WPF_results, dtype=bool)


# Iterative MTOW calculation (simple fixed-point iteration)
W_MTO_current_N = 150000 * 9.81 # Initial guess for MTOW (N)

# Pre-calculate F_prop as it's constant for fixed engine/mission params
F_prop_val = calculate_propulsion_function(R_EQ_KM, ETA_O_ENGINE, H_G_FUEL_KM, MU_T_PROP_WEIGHT, TAU_THRUST_LAPSE, DELTA_PRESSURE_RATIO)

for i, A_w_val in enumerate(A_w_range):
    for j, CL_val in enumerate(CL_design_range):
        # Step 1 (Implicit): W_MTO_current_N is the iterated MTOW
        # Step 2: Geometry (depends on W_MTO)
        S_w_val, b_w_val = calculate_geometry(CL_val, W_MTO_current_N, Q_CRUISE_PA, A_w_val)
        S_W_results[i,j] = S_w_val
        B_W_results[i,j] = b_w_val

        # Step 3.1: Thickness ratio from Mdd constraint
        tc_w_val = calculate_tc_w_from_Mdd_constraint(M_DD_TARGET, CL_val, LAMBDA_W_RAD, M_PRIME)
        TC_W_results[i,j] = tc_w_val
        tc_w_valid[i,j] = not np.isnan(tc_w_val) and 0.06 < tc_w_val < 0.18 # Practical limits

        if not tc_w_valid[i,j]:
            WPF_results[i, j] = np.nan
            MTOW_results_N[i, j] = np.nan
            continue

        # Step 3.2 - 3.5: Drag components
        C_profile_Dp_w_val = calculate_profile_drag_coeff_wing(tc_w_val, LAMBDA_W_RAD, C_F_SKIN, D_W_H_FACTOR, R_T_FACTOR)
        C_induced_DL_val = calculate_induced_drag_coeff(CL_val, A_w_val, OSWALD_EFF_MODIFIED)
        # CD_total_val, L_D_val = calculate_total_airframe_drag_coeff(C_profile_Dp_w_val, CL_val, C_induced_DL_val, CD_COMPRESSIBILITY_TARGET, S_w_val, CD_FIXED_DRAG_AREA_M2)
        # Step 4: Propulsion Function (already calculated as F_prop_val)

        # Step 5: Wing Structural Weight Parameters
        Lambda_3_eff_val, Lambda_2_eff_val = calculate_wing_struct_weight_params(LAMBDA_3_BASE, tc_w_val, LAMBDA_W_RAD, LAMBDA_2_BASE)
        
        # Step 6: Wing Penalty Function
        wpf_calc = calculate_wpf(Lambda_3_eff_val, A_w_val, CL_val, tc_w_val, LAMBDA_W_RAD, Lambda_2_eff_val, F_prop_val,
                                 C_profile_Dp_w_val, CD_COMPRESSIBILITY_TARGET, OSWALD_EFF_MODIFIED)
        WPF_results[i, j] = wpf_calc
        
        # Step 7: MTOW Calculation
        # Simple iteration for MTOW convergence
        mtow_iter_N = W_MTO_current_N
        for _ in range(5): # Iterate a few times
             # Recalculate S_w with new MTOW estimate for WPF parameters if they depend on MTOW (Lambda_3 does via W_MZF)
             # For this visualization, assume Lambda_3_base is fixed based on an initial W_MZF_GUESS
             # This simplifies, otherwise WPF itself becomes dependent on the MTOW iteration.
            mtow_new_N = calculate_mtow_N(W_PAY_N, DELTA_W_FIX_N, F_prop_val, Q_CRUISE_PA, CD_FIXED_DRAG_AREA_M2,
                                        MU_RESF, MU_LG, wpf_calc if not np.isnan(wpf_calc) else 1.0) # Use 1.0 if wpf is nan to avoid error
            if np.isnan(mtow_new_N) or abs(mtow_new_N - mtow_iter_N) < 1000: # Converged if change < 1kN
                break
            mtow_iter_N = mtow_new_N
        MTOW_results_N[i, j] = mtow_iter_N
        
        # Update S_w and b_w with the converged MTOW for constraint checks
        S_w_final, b_w_final = calculate_geometry(CL_val, mtow_iter_N, Q_CRUISE_PA, A_w_val)

        # Step 8: Evaluate Constraints (using final MTOW and geometry)
        if np.isnan(mtow_iter_N) or np.isnan(S_w_final) or np.isnan(b_w_final) or np.isnan(tc_w_val):
            continue

        # Fuel Tank Volume (Eq. 10.30, 10.31)
        V_tank_m3 = 0.90 * ETA_TANK_VOL * tc_w_val * S_w_final**1.5 * A_w_val**-0.5
        
        # Simplified W_misf_for_tank_sizing (based on R_M_FUEL_KM)
        # Recalculate CD_total for R_M_FUEL_KM (using CL_val, which might not be optimal for max range but is a simplification)
        CD_total_for_RM, _ = calculate_total_airframe_drag_coeff(C_profile_Dp_w_val, CL_val, C_induced_DL_val, CD_COMPRESSIBILITY_TARGET, S_w_final, CD_FIXED_DRAG_AREA_M2)
        W_misf_for_tank_N = (R_M_FUEL_KM / (ETA_O_ENGINE * H_G_FUEL_KM * (CL_val / CD_total_for_RM if CD_total_for_RM > 0 else np.inf))) * mtow_iter_N if not np.isnan(CD_total_for_RM) else np.inf

        W_fuel_total_req_N = W_misf_for_tank_N * (1 + C_RESF_FUEL_FRAC)
        V_fuel_total_req_m3 = W_fuel_total_req_N / (RHO_FUEL_KGM3 * 9.81)
        fuel_vol_ok[i, j] = V_tank_m3 >= V_fuel_total_req_m3 if not np.isnan(V_tank_m3) and not np.isnan(V_fuel_total_req_m3) else False

        # Buffet Onset
        buffet_ok[i, j] = CL_val <= CL_BUFFET_LIMIT

        # Aspect Ratio Limit (Pitch-up)
        aspect_ratio_ok[i, j] = A_w_val <= A_W_PITCH_UP_LIMIT
        
        # Span Loading (TOFL proxy)
        span_loading_N_m2 = mtow_iter_N / (b_w_final**2) if b_w_final > 0 else np.inf
        span_loading_ok[i,j] = span_loading_N_m2 <= TOFL_PROXY_SPAN_LOADING_LIMIT_NM2 if not np.isnan(span_loading_N_m2) else False


# --- Plotting Results ---
X, Y = np.meshgrid(CL_design_range, A_w_range)

fig, ax = plt.subplots(figsize=(12, 10))

# Plot WPF contours
contour_wpf = ax.contourf(X, Y, WPF_results, levels=np.linspace(np.nanmin(WPF_results), np.nanmin(WPF_results) + 0.1, 20), extend='both', cmap='viridis_r')
plt.colorbar(contour_wpf, label='Wing Penalty Function (WPF)')
contour_lines_wpf = ax.contour(X, Y, WPF_results, levels=np.linspace(np.nanmin(WPF_results), np.nanmin(WPF_results) + 0.1, 10), colors='black', linewidths=0.5)
ax.clabel(contour_lines_wpf, inline=True, fontsize=8, fmt='%1.3f')

# Plot MTOW contours (as an alternative FOM)
# contour_mtow = ax.contour(X, Y, MTOW_results_N / 9.81 / 1000, levels=10, colors='grey', linestyles='--', linewidths=1.0) # MTOW in tonnes
# ax.clabel(contour_mtow, inline=True, fontsize=8, fmt='%1.0f t')

# Overlay Constraint Boundaries
# Fuel Volume Constraint (where fuel_vol_ok becomes False)
fuel_constraint_plot = np.ma.masked_where(fuel_vol_ok, np.ones_like(fuel_vol_ok))
fuel_contour = ax.contour(X, Y, fuel_vol_ok.astype(int), levels=[0.5], colors='red', linestyles='-.', linewidths=2)

# Buffet Constraint
buffet_constraint_plot = np.ma.masked_where(buffet_ok, np.ones_like(buffet_ok))
buffet_contour = ax.contour(X, Y, buffet_ok.astype(int), levels=[0.5], colors='orange', linestyles='--', linewidths=2)

# Aspect Ratio Limit
aspect_ratio_constraint_plot = np.ma.masked_where(aspect_ratio_ok, np.ones_like(aspect_ratio_ok))
ar_contour = ax.contour(X, Y, aspect_ratio_ok.astype(int), levels=[0.5], colors='purple', linestyles=':', linewidths=2)

# Span Loading Limit (TOFL proxy)
span_loading_constraint_plot = np.ma.masked_where(span_loading_ok, np.ones_like(span_loading_ok))
span_loading_contour = ax.contour(X, Y, span_loading_ok.astype(int), levels=[0.5], colors='green', linestyles='-', linewidths=2)

# Identify feasible region
feasible_region = tc_w_valid & fuel_vol_ok & buffet_ok & aspect_ratio_ok & span_loading_ok
ax.contourf(X, Y, feasible_region.astype(float), levels=[0.5, 1.5], colors=['none', 'lightgray'], alpha=0.3)
feasible_contour = ax.contour(X, Y, feasible_region.astype(float), levels=[0.5], colors='black', linewidths=2.5)


# Find and plot the minimum WPF in the feasible region
if np.any(feasible_region):
    wpf_feasible = np.where(feasible_region, WPF_results, np.inf)
    min_wpf_idx = np.unravel_index(np.argmin(wpf_feasible), wpf_feasible.shape)
    min_CL = CL_design_range[min_wpf_idx[1]]
    min_Aw = A_w_range[min_wpf_idx[0]]
    min_WPF_val = WPF_results[min_wpf_idx]
    ax.plot(min_CL, min_Aw, 'ko', markersize=10, label=f'Min WPF ({min_WPF_val:.3f}) at CL={min_CL:.2f}, Aw={min_Aw:.1f}')
    
    # Also print the MTOW at this point
    mtow_at_min_wpf_tonnes = MTOW_results_N[min_wpf_idx] / 9.81 / 1000
    print(f"Optimal Point (Min WPF): CL={min_CL:.2f}, Aw={min_Aw:.1f}, WPF={min_WPF_val:.4f}")
    print(f"  Corresponding (t/c)_w: {TC_W_results[min_wpf_idx]:.4f}")
    print(f"  Corresponding MTOW: {mtow_at_min_wpf_tonnes:.1f} tonnes")
    print(f"  Corresponding Wing Area: {S_W_results[min_wpf_idx]:.1f} m^2")
    print(f"  Corresponding Wing Span: {B_W_results[min_wpf_idx]:.1f} m")


ax.set_xlabel('Design Lift Coefficient ($C_L$)')
ax.set_ylabel('Aspect Ratio ($A_w$)')
ax.set_title(f'Transonic Wing Design Space (WPF Contours) for $\\Lambda_w = {LAMBDA_W_DEG}°$')

# Create a legend for constraint lines using Line2D objects
handles, labels = [], []
if np.any(~fuel_vol_ok):
    handles.append(plt.Line2D([0], [0], color='red', linestyle='-.', linewidth=2))
    labels.append('Fuel Vol. Limit')
if np.any(~buffet_ok):
    handles.append(plt.Line2D([0], [0], color='orange', linestyle='--', linewidth=2))
    labels.append('Buffet Limit')
if np.any(~aspect_ratio_ok):
    handles.append(plt.Line2D([0], [0], color='purple', linestyle=':', linewidth=2))
    labels.append('Aspect Ratio Limit')
if np.any(~span_loading_ok):
    handles.append(plt.Line2D([0], [0], color='green', linestyle='-', linewidth=2))
    labels.append('TOFL Proxy Limit')
if np.any(feasible_region):
    handles.append(plt.Line2D([0], [0], color='black', linewidth=2.5))
    labels.append('Feasible Region')
    if 'Min WPF' in ax.get_legend_handles_labels()[1]: # Check if min_wpf_plot exists
         h_opt, l_opt = ax.get_legend_handles_labels()
         handles.append(h_opt[l_opt.index(f'Min WPF ({min_WPF_val:.3f}) at CL={min_CL:.2f}, Aw={min_Aw:.1f}')]) # Add existing label
         labels.append(f'Min WPF ({min_WPF_val:.3f})')


ax.legend(handles, labels, loc='upper right', fontsize='small')
ax.grid(True, linestyle=':', alpha=0.7)
plt.tight_layout()
plt.show()

print("\nNote: This script provides a visualization of the algorithm's sensitivity.")
print("The 'optimal' point is based on the discretized grid and assumed constants.")
print("It uses simplified formulas from Chapter 10 of Torenbeek's 'Advanced Aircraft Design'.")
print(f"Assumed fixed sweep angle: {LAMBDA_W_DEG} degrees.")
print(f"Assumed design cruise Mach number: {M_DES}.")
print(f"Assumed (t/c)_w is calculated to meet M_dd = {M_DD_TARGET} using a Korn-like equation.")