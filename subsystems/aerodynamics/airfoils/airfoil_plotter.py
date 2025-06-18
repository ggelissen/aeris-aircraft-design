import numpy as np
import matplotlib.pyplot as plt

# Save directory, same folder as 
# this script, for airfoil data files
DATA_DIR = 'subsystems/aerodynamics/airfoils/'
# --- 1. Load Data ---

def load_airfoil_data(filename):
    """Loads x, y coordinates from a standard airfoil .dat file."""
    # The first line is often the name, and there might be blank lines
    # between upper and lower surfaces.
    x, y = [], []
    with open(filename, 'r') as f:
        # Skip the name line
        next(f, None)
        for line in f:
            try:
                parts = line.strip().split()
                if len(parts) == 2:
                    x.append(float(parts[0]))
                    y.append(float(parts[1]))
            except (ValueError, IndexError):
                continue # Skip blank lines or improperly formatted lines
    return np.array(x), np.array(y)

# Load the airfoil coordinate files (ensure these files are in the same directory)
x_0412, y_0412 = load_airfoil_data('subsystems/aerodynamics/airfoils/sc20412.dat')
x_0612, y_0612 = load_airfoil_data('subsystems/aerodynamics/airfoils/sc20612.dat')

# CFD Results Data (from your prompt)
# You can load this from a file or define it directly as done here
cases = np.arange(1, 11)
alpha = np.array([-3.0, -2.0, -1.0, 0.0, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
cl = np.array([-0.255, -0.069, 0.112, 0.295, 0.481, 0.577, 0.674, 0.774, 0.876, 0.981])
cm = np.array([-0.084, -0.085, -0.089, -0.091, -0.091, -0.089, -0.086, -0.084, -0.085, -0.087])
cdt = np.array([0.0094, 0.0097, 0.0094, 0.0094, 0.0098, 0.0108, 0.0134, 0.0176, 0.0244, 0.0333])
cdw = np.array([0.0009, 0.00001, 0.0000, 0.0000, 0.0002, 0.0014, 0.0027, 0.0078, 0.0134, 0.0180])
cdv = cdt - cdw # Viscous drag is total - wave

# Shock Position Data
shock_cl = np.array([0.481, 0.577, 0.674, 0.774, 0.876, 0.981])
shock_xi = np.array([0.0856, 0.1339, 0.1913, 0.2559, 0.3083, 0.3633])


# --- 2. Generate Plots ---

plt.style.use('seaborn-v0_8-whitegrid')

# --- Plot 1: Airfoil Shape Comparison ---
fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.plot(x_0412, y_0412, 'r-', label='NASA SC(2)-0412 (Selected, 12% t/c)')
ax1.plot(x_0612, y_0612, 'b--', label='NASA SC(2)-0612 (Alternative, 12% t/c)')
ax1.set_title('Airfoil Geometry Comparison', fontsize=16)
ax1.set_xlabel('x/c')
ax1.set_ylabel('y/c')
ax1.axis('equal')
ax1.legend()
ax1.grid(True)
# Path for saving the figure
path_shapes = "subsystems/aerodynamics/airfoils/airfoil_shape_comparison.pdf"
plt.savefig(path_shapes, dpi=300)

# --- Plot 2: Lift and Moment Curves ---
fig2, ax2a = plt.subplots(figsize=(10, 7))
ax2a.plot(alpha, cl, 'o-', color='blue', label='$C_L$ vs $\\alpha$')
ax2a.set_xlabel('Angle of Attack, $\\alpha$ (degrees)', fontsize=12)
ax2a.set_ylabel('Lift Coefficient, $C_L$', fontsize=12, color='blue')
ax2a.tick_params(axis='y', labelcolor='blue')
ax2a.grid(True)

# Create a second y-axis for the pitching moment
ax2b = ax2a.twinx()
ax2b.plot(alpha, cm, 'o-', color='green', label='$C_m$ vs $\\alpha$')
ax2b.set_ylabel('Pitching Moment Coefficient, $C_m$', fontsize=12, color='green')
ax2b.tick_params(axis='y', labelcolor='green')

fig2.suptitle('Lift and Pitching Moment Characteristics (M=0.7)', fontsize=16)
fig2.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
path_moment_curves = "subsystems/aerodynamics/airfoils/lift_moment_curves.png"
plt.savefig(path_moment_curves, dpi=300)


# --- Plot 3: Drag Polar ---
fig3, ax3 = plt.subplots(figsize=(10, 7))
ax3.plot(cdt, cl, 'o-', label='Total Drag ($C_{DT}$)')
ax3.plot(cdv, cl, 'o--', label='Viscous Drag ($C_{DV}$)')
ax3.plot(cdw, cl, 'o--', label='Wave Drag ($C_{DW}$)')
ax3.set_title('Drag Polar at M=0.7', fontsize=16)
ax3.set_xlabel('Drag Coefficient, $C_D$')
ax3.set_ylabel('Lift Coefficient, $C_L$')
ax3.legend()
ax3.grid(True)
path_drag_polar = "subsystems/aerodynamics/airfoils/drag_polar.pdf"
plt.savefig(path_drag_polar, dpi=300)


# --- Plot 4: Shock Position ---
fig4, ax4 = plt.subplots(figsize=(10, 7))
ax4.plot(shock_cl, shock_xi * 100, 'o-') # as percentage
ax4.set_title('Upper Surface Shock Position vs. Lift Coefficient (M=0.7)', fontsize=16)
ax4.set_xlabel('Lift Coefficient, $C_L$')
ax4.set_ylabel('Shock Position, x/c (%)')
ax4.grid(True)
path_shock_position = "subsystems/aerodynamics/airfoils/shock_position.pdf"
plt.savefig(path_shock_position, dpi=300)

print("\nGenerated the following plots:")
print("- airfoil_shape_comparison.png")
print("- lift_moment_curves.png")
print("- drag_polar.png")
print("- shock_position.png")

# To prevent all plots from displaying at once if not desired, comment out plt.show()
# plt.show()