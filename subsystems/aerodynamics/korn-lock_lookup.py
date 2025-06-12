import numpy as np
import math
import matplotlib.pyplot as plt

# --- Chart Configuration ---
TARGET_MACH = 0.85
TARGET_CL = 0.5

INSPECT_AR = 11.0  # Fixed Aspect Ratio for inspection
def calculate_tc_from_korn(target_cruise_mach, sweep_deg, cl_des):
    """
    Calculates the achievable thickness-to-chord ratio using the Torenbeek/Korn equation.
    This logic is taken from your original optimization script.
    """
    # Parameters from your original script's context
    M_kappa = 0.935  # For supercritical airfoil
    M_dd = target_cruise_mach + 0.015 # Drag divergence Mach number
    
    Lambda_w_rad = np.deg2rad(sweep_deg)
    cos_Lambda_w = np.cos(Lambda_w_rad)
    C_L_hat = cl_des
    
    # Check for invalid inputs
    if C_L_hat < 0:
        return np.nan

    # Rearranged Torenbeek Eq. 10.49 to solve for t/c
    # tc_cos2_val = (cos_Lambda_w**3) * (M_kappa - M_dd * cos_Lambda_w) - 0.115 * C_L_hat**1.5
    # t_c_w = tc_cos2_val / (cos_Lambda_w**2)
    
    term1 = cos_Lambda_w * (M_kappa - M_dd * cos_Lambda_w)
    term2 = (0.115 * C_L_hat**1.5) / (cos_Lambda_w**2)
    
    t_c = term1 - term2
    
    # Return NaN if the result is not physically meaningful
    return t_c if t_c > 0 else np.nan

# --- NEW: Value Inspection Section ---
print("--- Inspecting Behavior for Fixed Parameters ---")
print(f"Target Mach = {TARGET_MACH}, Target CL = {TARGET_CL}, Fixed AR = {INSPECT_AR}\n")
print(f"{'Sweep (deg)':<15} | {'Achievable t/c (%)':<20}")
print("-" * 38)
for sweep_to_check in [29, 32, 35, 38, 40]:
    t_c_result = calculate_tc_from_korn(TARGET_MACH, sweep_to_check, TARGET_CL)
    if t_c_result > 0:
        print(f"{sweep_to_check:<15.1f} | {t_c_result*100:<20.2f}")
    else:
        print(f"{sweep_to_check:<15.1f} | {'Not Feasible':<20}")
print("-" * 38)



# --- 1. Define the Grid for the Axes ---
sweep_range = np.linspace(28, 42, 50)
ar_range = np.linspace(8, 14, 50)
sweep_grid, ar_grid = np.meshgrid(sweep_range, ar_range)

# --- 2. Calculate t/c for Each Point on the Grid ---
tc_grid = np.zeros_like(sweep_grid)

print(f"Calculating t/c grid using Korn-Lock method for M={TARGET_MACH} and CL={TARGET_CL}...")

for i in range(len(ar_range)):
    for j in range(len(sweep_range)):
        # NOTE: The Korn equation does not depend on Aspect Ratio (ar_grid[i,j] is not used)
        t_c = calculate_tc_from_korn(
            target_cruise_mach=TARGET_MACH,
            sweep_deg=sweep_grid[i, j],
            cl_des=TARGET_CL
        )
        tc_grid[i, j] = t_c * 100 if not np.isnan(t_c) else np.nan
        
print("Calculation complete. Generating plot...")

# --- 3. Generate the Contour Plot ---
#plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(12, 9))

levels = np.arange(10, 14.0, 0.5)
contour = ax.contour(sweep_grid, ar_grid, tc_grid, levels=levels)
ax.clabel(contour, inline=True, fontsize=10, fmt='%1.1f%%')
contourf = ax.contourf(sweep_grid, ar_grid, tc_grid, levels=levels, alpha=0.7)
# Highly visible color map for better contrast, blue to red gradient
cbar = plt.colorbar(contourf, ax=ax, orientation='vertical', pad=0.02)

cbar.set_label('Achievable Thickness-to-Chord Ratio (t/c) [%]', fontsize=12)

ax.set_title(f'Wing Design Space using Korn-Lock Method\n(Fixed M = {TARGET_MACH}, Fixed CL = {TARGET_CL})', fontsize=16, pad=20)
ax.set_xlabel('Quarter-Chord Sweep Angle (degrees)', fontsize=12)
ax.set_ylabel('Aspect Ratio', fontsize=12)
save_dir = "subsystems/aerodynamics/Figures"
plt.savefig(f"{save_dir}/korn_lock_lookup_M{TARGET_MACH}_CL{TARGET_CL}.png", dpi=300, bbox_inches='tight')
plt.show()