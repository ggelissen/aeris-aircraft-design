import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

# (Assuming these imports work in your project structure)
# sys.path.append(...)

# --- Plotting Style and Formatting ---

def _set_report_style():
    """Sets a professional plot style suitable for reports."""
    try:
        plt.rcParams['font.family'] = 'Arial'
    except RuntimeError:
        print("Arial font not found, falling back to default sans-serif.")
        plt.rcParams['font.family'] = 'sans-serif'
    
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['lines.linewidth'] = 2.5
    plt.rcParams['lines.markersize'] = 6

COLOR_PALETTE = {
    'blue': '#0d3b66',
    'orange': '#ee964b',
    'grey': '#4F4F4F',
    'green': '#5fad56',
    'red': '#D7263D'
}


# === Buckling Calculation ===
def calculate_critical_buckling_stress(E, I, A, L, K_col=1.0):
    if A == 0 or I == 0 or E == 0 or L == 0:
        return 0.0
    L_eff = K_col * L
    P_cr = (np.pi ** 2) * E * I / (L_eff ** 2)
    sigma_cr = P_cr / A
    return sigma_cr

# === S-N Curve ===
def sn_curve(stress_ampl, A=1e12, m=3.0):
    return (A / stress_ampl) ** (1/m)

# === Miner’s Rule ===
def miners_rule(stress_amplitudes, cycle_counts, A=1e12, m=3.0):
    return sum(n / sn_curve(s, A, m) for s, n in zip(stress_amplitudes, cycle_counts))

# === Mean Stress Correction ===
def corrected_stress(sigma_a, sigma_m, Rm, method='none'):
    if method == 'goodman':
        # Added a check to prevent division by zero or negative values
        if sigma_m >= Rm:
            return float('inf')
        return sigma_a / (1 - sigma_m / Rm)
    elif method == 'gerber':
        if sigma_m >= Rm:
            return float('inf')
        return sigma_a / (1 - (sigma_m / Rm)**2)
    else:
        return sigma_a

# === Plot S-N Curve (Refactored for Report Quality) ===
def plot_sn_curve(sigma_D, ND, m, Rm, sigma_m=0, method='none'):
    """
    Generates a styled, report-quality S-N curve plot.
    """
    _set_report_style()
    
    N = np.logspace(3, 8, 200)
    # Calculate the uncorrected stress amplitude (Basquin's equation)
    sigma_a = sigma_D * (ND / N) ** (1/m)
    
    # Calculate the equivalent stress amplitude with mean stress correction
    sigma_ae = np.array([corrected_stress(sa, sigma_m, Rm, method) for sa in sigma_a])

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plotting the data
    ax.loglog(N, sigma_a, label="Uncorrected (R = -1)", color=COLOR_PALETTE['blue'])
    if method != 'none':
        ax.loglog(N, sigma_ae, label=f"{method.title()} Corrected ($\sigma_m > 0$)", color=COLOR_PALETTE['red'], linestyle='--')

    # --- Aesthetics ---
    #ax.set_title("S-N Curve for Fatigue Analysis")
    ax.set_xlabel("Number of Cycles to Failure  ($N_{cycles}$) [-]")
    ax.set_ylabel("Stress Amplitude ($\sigma_a$) [MPa]")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5, color='lightgrey')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # --- Legend Styling ---
    legend = ax.legend(loc='best', frameon=True)
    frame = legend.get_frame()
    frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
    frame.set_facecolor('white')
    frame.set_edgecolor('black')
    frame.set_alpha(0.85)
    legend.set_zorder(10)

    plt.tight_layout()
    
    # Save the figure instead of showing it
    os.makedirs("Figures", exist_ok=True)
    plt.savefig("Figures/Structures/sn_curve.png", transparent=False)
    plt.close(fig)
    print("Saved plot: Figures/Structures/sn_curve.png")

# === Parameters ===
if __name__ == "__main__":
    # Geometry / Material
    E = 70e9      # Pa
    I = 8e-6      # m^4
    A = 0.004     # m^2
    L = 2.0       # m
    K_col = 1.0

    # Fatigue
    sigma_D = 172   # MPa (Fatigue strength coefficient)
    ND = 1e6        # cycles (Reference cycles)
    m = 5           # Basquin exponent (S-N slope)
    Rm = 400        # MPa (Ultimate Tensile Strength)
    sigma_m = 40    # MPa (Mean stress)
    method = 'goodman'  # Correction method: 'none', 'goodman', or 'gerber'

    # --- Calculations & Plotting ---
    sigma_cr = calculate_critical_buckling_stress(E, I, A, L, K_col)
    print(f"Critical Buckling Stress: {sigma_cr/1e6:.2f} MPa")

    # Plot S-N curve with optional mean stress correction
    plot_sn_curve(sigma_D, ND, m, Rm, sigma_m, method)