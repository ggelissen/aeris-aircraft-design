import matplotlib.pyplot as plt
import numpy as np

# Data from the previous step
aircraft_names = ['XQ-58A', 'MQ-20', 'MQ-28']
oew_kg = np.array([1134, 3312, 1500])  # Operational Empty Weight in kg
mtow_kg = np.array([2722, 8255, 3000]) # Maximum Take-Off Weight in kg

# Perform linear regression
slope, intercept = np.polyfit(oew_kg, mtow_kg, 1)

# Create the regression line data
regression_line_x = np.array([min(oew_kg) - 100, max(oew_kg) + 100])
regression_line_y = slope * regression_line_x + intercept

# --- New: Calculate OEW for a target MTOW of 4000 kg ---
target_mtow = 4000
corresponding_oew = (target_mtow - intercept) / slope
print(f"For a target MTOW of {target_mtow} kg, the estimated OEW using the regression is: {corresponding_oew:.2f} kg")

# Create the plot
plt.figure(figsize=(10, 7)) # Adjusted figure size slightly for new elements

# Scatter plot of the data points
plt.scatter(oew_kg, mtow_kg, color='dodgerblue', label='Aircraft Data (Unmanned Ref.)')

# Add labels next to each point
for i, name in enumerate(aircraft_names):
    plt.text(oew_kg[i] + 50, mtow_kg[i], name)

# Plot the regression line (dashed)
plt.plot(regression_line_x, regression_line_y, color='dodgerblue', linestyle='--', label=f'Regression Line\n(MTOW={slope:.2f}*OEW + {intercept:.2f})')

# --- New: Add horizontal line at MTOW = 4000 kg ---
plt.axhline(y=target_mtow, color='green', linestyle=':', linewidth=2, label=f'Target MTOW = {target_mtow} kg')

# --- New: Optionally, mark the corresponding OEW on the regression line ---
if min(regression_line_x) <= corresponding_oew <= max(regression_line_x):
    plt.plot(corresponding_oew, target_mtow, 'go') # Green dot

# Adjust plot limits if necessary to ensure visibility of the new line and point
current_xlim = plt.xlim()
current_ylim = plt.ylim()
plt.xlim(min(current_xlim[0], corresponding_oew - 200, 0), max(current_xlim[1], corresponding_oew + 200)) # Ensure OEW is visible, start x-axis from 0 or slightly less
plt.ylim(min(current_ylim[0], target_mtow - 500, 0), max(current_ylim[1], target_mtow + 500)) # Ensure MTOW line is visible, start y-axis from 0

# Add labels and title
plt.xlabel('Operational Empty Weight (OEW) [kg]')
plt.ylabel('Maximum Take-Off Weight (MTOW) [kg]')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()

#################################################################################################################

# New Data for Manned Aircraft
aircraft_names_manned = [
    'Falcon 20 E-5', 'Falcon 20 GF', 'Cessna Citation II',
    'Gulfstream G550 HALO', 'Bombardier 35A', 'Gulfstream V (HIAPER)'
]
oew_kg_manned = np.array([
    8390, 8500, 3725,
    22120, 4717, 20956
])  # Operational Empty Weight in kg
mtow_kg_manned = np.array([
    13755, 14500, 6620,
    41277, 8890, 41050
]) # Maximum Take-Off Weight in kg

# Perform linear regression for manned aircraft
slope_manned, intercept_manned = np.polyfit(oew_kg_manned, mtow_kg_manned, 1)

# Create the regression line data for manned aircraft
# Extend slightly for better visualization, ensuring it covers potential target OEW
min_oew_manned = np.min(oew_kg_manned)
max_oew_manned = np.max(oew_kg_manned)
regression_line_x_manned = np.array([min_oew_manned * 0.9, max_oew_manned * 1.1])
regression_line_y_manned = slope_manned * regression_line_x_manned + intercept_manned

# --- Calculate OEW for a target MTOW of 9500 kg ---
target_mtow_manned = 9500
corresponding_oew_manned = (target_mtow_manned - intercept_manned) / slope_manned
print(f"For a target MTOW of {target_mtow_manned} kg (manned aircraft regression), the estimated OEW is: {corresponding_oew_manned:.2f} kg")

# Create the plot
plt.figure(figsize=(12, 8)) # Adjusted figure size for more data points and labels

# Scatter plot of the manned aircraft data points
plt.scatter(oew_kg_manned, mtow_kg_manned, color='dodgerblue', label='Manned Aircraft Data (Ref.)')

# Add labels next to each point
for i, name in enumerate(aircraft_names_manned):
    if name == 'Gulfstream V (HIAPER)':
        plt.text(oew_kg_manned[i] + 200, mtow_kg_manned[i] - 1000, name, fontsize=9)
    else:
        plt.text(oew_kg_manned[i] + 200, mtow_kg_manned[i], name, fontsize=9)

# Plot the regression line for manned aircraft (dashed)
plt.plot(regression_line_x_manned, regression_line_y_manned, color='dodgerblue', linestyle='--',
         label=f'Manned Regression Line\n(MTOW={slope_manned:.2f}*OEW + {intercept_manned:.2f})')

# --- Add horizontal line at MTOW = 9500 kg ---
plt.axhline(y=target_mtow_manned, color='green', linestyle=':', linewidth=2,
            label=f'Target MTOW = {target_mtow_manned} kg')

# --- Mark the corresponding OEW on the regression line ---
# Check if the calculated OEW falls within the plotted range of the regression line for sensible plotting
if regression_line_x_manned[0] <= corresponding_oew_manned <= regression_line_x_manned[1]:
    plt.plot(corresponding_oew_manned, target_mtow_manned, 'go') 

# Adjust plot limits for better visibility
plt.xlim(min(0, min_oew_manned * 0.8, corresponding_oew_manned * 0.8 if corresponding_oew_manned > 0 else 0),
         max(max_oew_manned * 1.1, corresponding_oew_manned * 1.1 if corresponding_oew_manned > 0 else max_oew_manned * 1.1))
plt.ylim(0, max(np.max(mtow_kg_manned) * 1.1, target_mtow_manned * 1.1))


# Add labels and title
plt.xlabel('Operational Empty Weight (OEW) [kg]', fontsize=12)
plt.ylabel('Maximum Take-Off Weight (MTOW) [kg]', fontsize=12)
plt.legend(fontsize=9)
plt.grid(True)
plt.tight_layout() 

# Show the plot
plt.show()

print(f"Manned aircraft regression line equation: MTOW = {slope_manned:.4f} * OEW + {intercept_manned:.4f}")