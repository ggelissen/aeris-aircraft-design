import numpy as np
import matplotlib.pyplot as plt
import delta_method as dm # Uses the corrected file above

# --- Chart Configuration ---
TARGET_MACH = 0.85
TARGET_CL = 0.5
# Use a fixed Aspect Ratio for the inspection printout
INSPECT_AR = 11.0 

# --- NEW: Value Inspection Section ---
print("--- Inspecting Behavior for Fixed Parameters ---")
print(f"Target Mach = {TARGET_MACH}, Target CL = {TARGET_CL}, Fixed AR = {INSPECT_AR}\n")
print(f"{'Sweep (deg)':<15} | {'Achievable t/c (%)':<20}")
print("-" * 38)
for sweep_to_check in [29, 32, 35, 38]:
    t_c_result = dm.calculate_tc_from_delta_method(TARGET_MACH, INSPECT_AR, sweep_to_check, TARGET_CL)
    if t_c_result > 0:
        print(f"{sweep_to_check:<15.1f} | {t_c_result*100:<20.2f}")
    else:
        print(f"{sweep_to_check:<15.1f} | {'Not Feasible':<20}")
print("-" * 38)


# --- Grid Calculation and Plotting (Same as before) ---
sweep_range = np.linspace(28, 42, 50)
ar_range = np.linspace(8, 14, 50)
sweep_grid, ar_grid = np.meshgrid(sweep_range, ar_range)
tc_grid = np.zeros_like(sweep_grid)

print("\nCalculating t/c grid for plot...")
for i in range(len(ar_range)):
    for j in range(len(sweep_range)):
        t_c = dm.calculate_tc_from_delta_method(TARGET_MACH, ar_grid[i, j], sweep_grid[i, j], TARGET_CL)
        tc_grid[i, j] = t_c * 100 if t_c > 0 else np.nan
print("Calculation complete. Generating plot...")

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(12, 9))
levels = np.arange(10.0, 15.5, 0.5)
contour = ax.contour(sweep_grid, ar_grid, tc_grid, levels=levels, cmap='viridis')
ax.clabel(contour, inline=True, fontsize=10, fmt='%1.1f%%')
contourf = ax.contourf(sweep_grid, ar_grid, tc_grid, levels=levels, cmap='viridis', alpha=0.7)
cbar = fig.colorbar(contourf)
cbar.set_label('Achievable Thickness-to-Chord Ratio (t/c) [%]', fontsize=12)
ax.set_title(f'Wing Design Space using Delta Method \n(Fixed M = {TARGET_MACH}, Fixed CL = {TARGET_CL})', fontsize=16, pad=20)
ax.set_xlabel('Quarter-Chord Sweep Angle (degrees)', fontsize=12)
ax.set_ylabel('Aspect Ratio', fontsize=12)
save_path = 'subsystems/aerodynamics/Figures'
plt.savefig(f"{save_path}/delta_method_design_space.png", dpi=300, bbox_inches='tight')
plt.show()