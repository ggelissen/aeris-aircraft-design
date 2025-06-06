import numpy as np
import matplotlib.pyplot as plt
import pandas as pd





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
        return sigma_a / (1 - sigma_m / Rm)
    elif method == 'gerber':
        return sigma_a / (1 - (sigma_m / Rm)**2)
    else:
        return sigma_a

# === Plot S-N Curve ===
def plot_sn_curve(sigma_D, ND, m, Rm, sigma_m=0, method='none'):
    N = np.logspace(3, 8, 200)
    sigma_a = sigma_D * (ND / N) ** (1/m)
    sigma_ae = np.array([corrected_stress(sa, sigma_m, Rm, method) for sa in sigma_a])

    plt.figure(figsize=(8, 6))
    plt.loglog(N, sigma_a, label="Uncorrected")
    if method != 'none':
        plt.loglog(N, sigma_ae, label=f"Corrected ({method.title()})")
    plt.xlabel("Number of Cycles to Failure (N)")
    plt.ylabel("Stress Amplitude (MPa)")
    plt.title("S-N Curve")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()

# === Parameters ===
if __name__ == "__main__":
    # Geometry / Material
    E = 70e9       # Pa
    I = 8e-6       # m^4
    A = 0.004      # m^2
    L = 2.0        # m
    K_col = 1.0

    # Fatigue
    sigma_D = 140  # MPa
    ND = 1e6       # cycles
    m = 5          # S-N slope
    Rm = 400       # MPa (ultimate)
    sigma_m = 40   # MPa (mean stress)
    method = 'goodman'  # 'none', 'goodman', or 'gerber'

    sigma_cr = calculate_critical_buckling_stress(E, I, A, L, K_col)
    print(f"Critical Buckling Stress: {sigma_cr/1e6:.2f} MPa")

    # Plot S-N curve with optional mean stress correction
    plot_sn_curve(sigma_D, ND, m, Rm, sigma_m, method)
