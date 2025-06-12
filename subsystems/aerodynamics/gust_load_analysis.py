import numpy as np
import matplotlib.pyplot as plt
import os
# --- 1. Setup and Data Processing ---

# User-defined cruise speed
V_FLIGHT = 250.0  # m/s
data_points = 1000  # Number of data points for smooth interpolation

#save_folder = "subsystems/aerodynamics"
save_folder = "." # Change this to your desired save location

# Data extracter from Figure 1, AN INTEGRATED LOADS ANALYSIS MODEL FOR WAKE VORTEX ENCOUNTERS https://core.ac.uk/download/pdf/31018877.pdf
raw_data_string = """
0.01609657947686116, 0.15607859040547112
0.24547283702213285, 0.3000951445104647
0.37424547283702214, 0.5668117230514866
0.47887323943661975, 0.831968555519154
0.5875251509054327, 1.4849822448905314
0.69215291750503, 2.783730808624341
0.7484909456740443, 4.854553678661105
0.7806841046277666, 8.474204399523757
0.8008048289738432, 11.576279381716649
0.8088531187122736, 14.806773457281146
0.8169014084507042, 16.745277868762958
0.8249496981891349, 19.07137917946957
0.8410462776659959, 0.08017094816963066
0.8571428571428572, -22.787006275378374
0.8692152917505032, -18.781058443685367
0.8853118712273642, -15.550044452763103
0.8973843058350099, -12.190091453111442
0.9175050301810863, -9.992409235776414
0.9496981891348089, -8.439941977446068
0.9778672032193159, -7.533729508835961
0.9979879275653922, -7.403230754033245
"""
# Data points removed between the highest and lowest points to avoid discontinuities, data fit should be linear between these points.
#0.8289738430583502, 15.583267044125208
# 0.8370221327967808, 11.707817967234927
#0.8410462776659959, 4.989731671683842
# 0.8450704225352113, -5.2167267168904985
#0.8410462776659959, -11.030940162941477
#0.8490945674044266, -16.715174769547517
#0.8531187122736419, -20.332485871300157

lines = raw_data_string.strip().split('\n')
points = [list(map(float, line.split(','))) for line in lines]
points.sort(key=lambda p: p[0])
time_data_half = np.array([p[0] for p in points])
velocity_data_half = np.array([p[1] for p in points])

# Mirror and interpolate to get the smooth gust velocity profile
time_mirrored = 2.0 - time_data_half[::-1]
full_time_data = np.concatenate((time_data_half, time_mirrored))
full_velocity_data = np.concatenate((velocity_data_half, velocity_data_half[::-1]))
time_smooth = np.linspace(full_time_data.min(), full_time_data.max(), data_points)
velocity_smooth = np.interp(time_smooth, full_time_data, full_velocity_data)

# --- 2. Calculate the Change in Angle of Attack (Δα) ---
delta_alpha_rad = np.arctan(velocity_smooth / V_FLIGHT)
delta_alpha_deg = np.degrees(delta_alpha_rad)

# --- 3. Generate the Plots ---
plt.style.use('seaborn-v0_8-whitegrid')
# Create a figure with two subplots stacked vertically, sharing the x-axis
fig, axs = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
fig.suptitle('Gust Encounter Analysis', fontsize=20)

# --- Plot 1: Gust Velocity ---
axs[0].plot(time_smooth, velocity_smooth, 'b-', label='Gust Velocity Profile')
axs[0].axhline(0, color='black', linestyle='-', linewidth=0.75)
axs[0].axvline(1.0, color='gray', linestyle='--', linewidth=1, label='Mirror Axis (t=1s)')
axs[0].set_ylabel('Gust Velocity (m/s)', fontsize=12)
axs[0].set_title('Gust Velocity vs. Time', fontsize=14)
axs[0].legend()
axs[0].grid(True)

# --- Plot 2: Angle of Attack ---
axs[1].plot(time_smooth, delta_alpha_deg, 'g-', label='Change in Angle of Attack (Δα)')
axs[1].axhline(0, color='black', linestyle='-', linewidth=0.75)
axs[1].axvline(1.0, color='gray', linestyle='--', linewidth=1)
axs[1].set_ylabel('Change in Angle of Attack, Δα (degrees)', fontsize=12)
axs[1].set_title(f'Resulting Change in Angle of Attack (Flight Speed = {V_FLIGHT} m/s)', fontsize=14)
axs[1].set_xlabel('Time (s)', fontsize=12)
axs[1].legend()
axs[1].grid(True)

# Adjust layout and display the plots
plt.tight_layout(rect=[0, 0.03, 1, 0.95])


# --- 4. Save the Plots and Data File ---
try:
    # Ensure the save directory exists
    os.makedirs(save_folder, exist_ok=True)

    # Save the figure
    plot_filename = f"{save_folder}/gust_analysis_plots.png"
    plt.savefig(plot_filename, dpi=300)
    print(f"\nSuccessfully saved plots to '{plot_filename}'")
    
    # Save the data to a file named 'angle_of_attack_data.csv'
    output_data = np.column_stack((time_smooth, delta_alpha_deg))
    header_string = "Time (s),Delta_Alpha (deg)"
    csv_filename = f"{save_folder}/angle_of_attack_data.csv"
    np.savetxt(csv_filename, output_data, delimiter=',', header=header_string, comments='', fmt='%.6f')
    print(f"Successfully saved data to '{csv_filename}'")
    print(f"File contains {len(time_smooth)} data points.")

except Exception as e:
    print(f"\nAn error occurred while saving the files: {e}")

# Finally, show the plot window
plt.show()
