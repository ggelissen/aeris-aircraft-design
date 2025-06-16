import matplotlib.pyplot as plt
import numpy as np

# --- Data Extraction ---
# Data extracted from the provided design summaries.
aspect_ratios = [7.00, 9.00, 11.00, 13.00, 15.00, 17.00, 20.00, 25.00, 30.00]
fuel_weights_N = [11553, 10141, 9163, 8580, 8128, 7771, 7352, 6725, 6378]
operating_empty_weights_N = [11334, 11295, 11265, 11370, 11465, 11576, 11732, 11850, 12091]
take_off_weights_N = [28771, 27320, 26312, 25834, 25478, 25231, 24967, 24459, 24353]
ld_cruise = [15.15, 17.13, 18.93, 20.38, 21.70, 22.94, 24.63, 27.47, 29.72]

# --- Data Normalization ---
# Normalize weight data relative to the first data point (baseline AR=7).
norm_fuel = [w / fuel_weights_N[0] for w in fuel_weights_N]
norm_oew = [w / operating_empty_weights_N[0] for w in operating_empty_weights_N]
norm_tow = [w / take_off_weights_N[0] for w in take_off_weights_N]

# --- Plotting ---
# Create a new figure and axes for the plot.
fig, ax1 = plt.subplots(figsize=(12, 8))

# --- Primary Y-Axis (Normalized Weights) ---
ax1.set_title('Aircraft Parameter Trends vs. Wing Aspect Ratio', fontsize=16, fontweight='bold')
ax1.set_xlabel('Wing Aspect Ratio (A_w)', fontsize=12)
ax1.set_ylabel('Normalized Weight (relative to AR=7 baseline)', fontsize=12, color='k')
ax1.tick_params(axis='y', labelcolor='k')

# Plot the normalized weight data series.
p1, = ax1.plot(aspect_ratios, norm_fuel, marker='o', linestyle='-', color='b', label='Normalized Fuel Weight')
p2, = ax1.plot(aspect_ratios, norm_oew, marker='s', linestyle='--', color='g', label='Normalized Operating Empty Weight')
p3, = ax1.plot(aspect_ratios, norm_tow, marker='^', linestyle='-.', color='r', label='Normalized Take-off Weight')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

# --- Secondary Y-Axis (L/D Ratio) ---
# Create a secondary y-axis that shares the same x-axis.
ax2 = ax1.twinx()
ax2.set_ylabel('L/D Cruise Ratio', fontsize=12, color='purple')
ax2.tick_params(axis='y', labelcolor='purple')

# Plot the L/D data series.
p4, = ax2.plot(aspect_ratios, ld_cruise, marker='d', linestyle=':', color='purple', label='L/D Cruise')

# --- Combined Legend ---
# Create a single legend for all plotted lines.
ax1.legend(handles=[p1, p2, p3, p4], loc='best', fontsize=10)

# Improve the layout to prevent labels from overlapping.
plt.tight_layout()

# --- Display the Plot ---
# Show the final plot.
plt.show()