import matplotlib.pyplot as plt
import numpy as np

# Use Arial font for better readability
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 13

# --- Data for Unmanned Aircraft ---
unmanned_data = {
    'XQ-58A': {'OEW': 1134, 'MTOW': 2722},
    'MQ-20': {'OEW': 3312, 'MTOW': 8255},
    'MQ-28': {'OEW': 1500, 'MTOW': 3000}
}
unmanned_oew = np.array([d['OEW'] for d in unmanned_data.values()])
unmanned_mtow = np.array([d['MTOW'] for d in unmanned_data.values()])
unmanned_names = list(unmanned_data.keys())

# Linear regression for unmanned aircraft (adaptable)
unmanned_reg_slope, unmanned_reg_intercept = np.polyfit(unmanned_oew, unmanned_mtow, 1)
unmanned_oew_for_line = np.array([0, 4000]) # Extend line slightly beyond max OEW
unmanned_reg_mtow = unmanned_reg_slope * unmanned_oew_for_line + unmanned_reg_intercept

# Target MTOW for unmanned aircraft
unmanned_target_mtow = 4000
unmanned_target_oew_range = np.array([0, 4000]) # Range for horizontal line

# Convert masses to Mega grams (Mg) for unmanned aircraft
unmanned_oew_Mg = unmanned_oew / 1000
unmanned_mtow_Mg = unmanned_mtow / 1000
unmanned_oew_for_line_Mg = unmanned_oew_for_line / 1000
unmanned_reg_mtow_Mg = unmanned_reg_mtow / 1000
unmanned_target_mtow_Mg = unmanned_target_mtow / 1000

# --- Plot Unmanned Aircraft Graph (in Mg) ---
plt.figure(figsize=(8,5))
plt.scatter(unmanned_oew_Mg, unmanned_mtow_Mg, label='Aircraft Data (Unmanned Ref.)', color='tab:blue', s=50, zorder=5)
plt.plot(unmanned_oew_for_line_Mg, unmanned_reg_mtow_Mg, linestyle='--', color='tab:blue',
         label=f'Regression Line\n(MTOW={unmanned_reg_slope:.2f}*OEW + {unmanned_reg_intercept:.2f})')
plt.axhline(y=unmanned_target_mtow_Mg, color='tab:green', linestyle='--',
            label=f'Target MTOW = {unmanned_target_mtow_Mg:.2f} Mg')

# Add labels for each point with slight offset to the right and top
for i, name in enumerate(unmanned_names):
    plt.annotate(name, (unmanned_oew_Mg[i], unmanned_mtow_Mg[i]), xytext=(6, 6), textcoords='offset points', fontsize=12, bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, lw=0))

# Identify intersection point for target MTOW if it's visible on the plot
unmanned_intersection_oew_Mg = (unmanned_target_mtow_Mg - unmanned_reg_intercept / 1000) / (unmanned_reg_slope / 1000)
if unmanned_intersection_oew_Mg >= min(unmanned_oew_for_line_Mg) and unmanned_intersection_oew_Mg <= max(unmanned_oew_for_line_Mg):
    plt.plot(unmanned_intersection_oew_Mg, unmanned_target_mtow_Mg, 'go', markersize=8, zorder=6)

plt.xlabel('Operational Empty Weight (OEW) [Mg]')
plt.ylabel('Maximum Take-Off Weight (MTOW) [Mg]')
plt.grid(True)
plt.legend()
plt.xlim(0, 4) # 3500 kg = 3.5 Mg
plt.ylim(0, 9.5) # 8500 kg = 8.5 Mg
plt.tight_layout()
plt.savefig('Unmanned_regression_recreated.pdf')
plt.show()

# --- Data for Manned Aircraft ---

manned_data = {
    'Falcon 20 E-5': {'OEW': 8390, 'MTOW': 13755},
    'Cessna Citation II': {'OEW': 3725, 'MTOW': 6620},
    'Bombardier 35A': {'OEW': 4717, 'MTOW': 8890}
    #'Gulfstream G550 HALO': {'OEW': 22120, 'MTOW': 41277}
}
manned_oew = np.array([d['OEW'] for d in manned_data.values()])
manned_mtow = np.array([d['MTOW'] for d in manned_data.values()])
manned_names = list(manned_data.keys())

# Linear regression for manned aircraft (adaptable)
manned_reg_slope, manned_reg_intercept = np.polyfit(manned_oew, manned_mtow, 1)
manned_oew_for_line = np.array([0, 15000]) # Extend line to match original graph's X-axis range
manned_reg_mtow = manned_reg_slope * manned_oew_for_line + manned_reg_intercept

# Target MTOW for manned aircraft
manned_target_mtow = 9500
manned_target_oew_range = np.array([0, 15000]) # Range for horizontal line

# Convert masses to Mega grams (Mg)
manned_oew_Mg = manned_oew / 1000
manned_mtow_Mg = manned_mtow / 1000
manned_oew_for_line_Mg = manned_oew_for_line / 1000
manned_reg_mtow_Mg = manned_reg_mtow / 1000
manned_target_mtow_Mg = manned_target_mtow / 1000

# --- Plot Manned Aircraft Graph (in Mg) ---
plt.figure(figsize=(8, 5))
plt.scatter(manned_oew_Mg, manned_mtow_Mg, label='Manned Aircraft Data (Ref.)', color='tab:blue', s=50, zorder=5)
plt.plot(manned_oew_for_line_Mg, manned_reg_mtow_Mg, linestyle='--', color='tab:blue',
         label=f'Manned Regression Line\n(MTOW={manned_reg_slope:.2f}*OEW + {manned_reg_intercept:.2f})')
plt.axhline(y=manned_target_mtow_Mg, color='tab:green', linestyle='--',
            label=f'Target MTOW = {manned_target_mtow_Mg:.2f} Mg')

# Add labels for each point (slight offset to right and top)
for i, name in enumerate(manned_names):
    plt.annotate(name, (manned_oew_Mg[i], manned_mtow_Mg[i]), xytext=(6, 6), textcoords='offset points', fontsize=12, bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, lw=0))

plt.xlabel('Operational Empty Weight (OEW) [Mg]')
plt.ylabel('Maximum Take-Off Weight (MTOW) [Mg]')
plt.grid(True)
plt.legend()
plt.xlim(0, 15) # 23000 kg = 23 Mg
plt.ylim(0, 25) # 45000 kg = 45 Mg
plt.tight_layout()
plt.savefig('Manned_regression_recreated.pdf')
plt.show()