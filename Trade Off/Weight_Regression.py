import matplotlib.pyplot as plt
import numpy as np

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
unmanned_oew_for_line = np.array([0, max(unmanned_oew) + 500]) # Extend line slightly beyond max OEW
unmanned_reg_mtow = unmanned_reg_slope * unmanned_oew_for_line + unmanned_reg_intercept

# Target MTOW for unmanned aircraft
unmanned_target_mtow = 4000
unmanned_target_oew_range = np.array([0, max(unmanned_oew_for_line)]) # Range for horizontal line

# --- Plot Unmanned Aircraft Graph ---
plt.figure(figsize=(12, 7))
plt.scatter(unmanned_oew, unmanned_mtow, label='Aircraft Data (Unmanned Ref.)', color='tab:blue', s=50, zorder=5)
plt.plot(unmanned_oew_for_line, unmanned_reg_mtow, linestyle='--', color='tab:blue',
         label=f'Regression Line\n(MTOW={unmanned_reg_slope:.2f}*OEW + {unmanned_reg_intercept:.2f})')
plt.axhline(y=unmanned_target_mtow, color='tab:green', linestyle='--',
            label=f'Target MTOW = {unmanned_target_mtow} kg')

# Add labels for each point
for i, name in enumerate(unmanned_names):
    plt.annotate(name, (unmanned_oew[i], unmanned_mtow[i]), textcoords="offset points", xytext=(5,5), ha='left', va='bottom')

# Identify intersection point for target MTOW if it's visible on the plot
unmanned_intersection_oew = (unmanned_target_mtow - unmanned_reg_intercept) / unmanned_reg_slope
if unmanned_intersection_oew >= min(unmanned_oew_for_line) and unmanned_intersection_oew <= max(unmanned_oew_for_line):
    plt.plot(unmanned_intersection_oew, unmanned_target_mtow, 'go', markersize=8, zorder=6)

plt.title('Unmanned Aircraft: Maximum Take-Off Weight vs. Operational Empty Weight')
plt.xlabel('Operational Empty Weight (OEW) [kg]')
plt.ylabel('Maximum Take-Off Weight (MTOW) [kg]')
plt.grid(True)
plt.legend()
plt.xlim(0, 3500) # Adjusted based on the original image for better visualization
plt.ylim(0, 8500) # Adjusted based on the original image for better visualization
plt.tight_layout()
plt.savefig('Unmanned_regression_recreated.png')
plt.show()

# --- Data for Manned Aircraft ---
manned_data = {
    'Stratos 714': {'OEW': 2284, 'MTOW': 3820},
    'Cirrus SF-50 Vision': {'OEW': 1610, 'MTOW': 2700},
    'Diamond D-Jet': {'OEW': 1175, 'MTOW': 2320},
    'Eclipse 400': {'OEW': 1125, 'MTOW': 2000},
    'Piperjet': {'OEW': 1415, 'MTOW': 1969}
}
manned_oew = np.array([d['OEW'] for d in manned_data.values()])
manned_mtow = np.array([d['MTOW'] for d in manned_data.values()])
manned_names = list(manned_data.keys())

# Linear regression for manned aircraft (adaptable)
manned_reg_slope, manned_reg_intercept = np.polyfit(manned_oew, manned_mtow, 1)
manned_oew_for_line = np.array([0, 22000]) # Extend line to match original graph's X-axis range
manned_reg_mtow = manned_reg_slope * manned_oew_for_line + manned_reg_intercept

# Target MTOW for manned aircraft
manned_target_mtow = 9500
manned_target_oew_range = np.array([0, 22000]) # Range for horizontal line

# --- Plot Manned Aircraft Graph ---
plt.figure(figsize=(12, 7))
plt.scatter(manned_oew, manned_mtow, label='Manned Aircraft Data (Ref.)', color='tab:blue', s=50, zorder=5)
plt.plot(manned_oew_for_line, manned_reg_mtow, linestyle='--', color='tab:blue',
         label=f'Manned Regression Line\n(MTOW={manned_reg_slope:.2f}*OEW + {manned_reg_intercept:.2f})')
plt.axhline(y=manned_target_mtow, color='tab:green', linestyle='--',
            label=f'Target MTOW = {manned_target_mtow} kg')

# Add labels for each point
for i, name in enumerate(manned_names):
    plt.annotate(name, (manned_oew[i], manned_mtow[i]), textcoords="offset points", xytext=(5,5), ha='left', va='bottom')

plt.title('Manned Aircraft: Maximum Take-Off Weight vs. Operational Empty Weight')
plt.xlabel('Operational Empty Weight (OEW) [kg]')
plt.ylabel('Maximum Take-Off Weight (MTOW) [kg]')
plt.grid(True)
plt.legend()
plt.xlim(0, 22000) # Adjusted based on the original image
plt.ylim(0, 45000) # Adjusted based on the original image
plt.tight_layout()
plt.savefig('Manned_regression_recreated.png')
plt.show()