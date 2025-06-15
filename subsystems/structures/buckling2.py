import numpy as np
import matplotlib.pyplot as plt

def calculate_critical_spar_buckling_stress(E, I, A, L, K_col=2.0):
    if A == 0:
        return np.inf 
    if I == 0 or E == 0:
        return 0.0
    L_eff = K_col * L
    if L_eff == 0:
        return np.inf if I > 0 else 0.0 
    critical_force = (np.pi**2 * E * I) / (L_eff**2)
    sigma_cr = critical_force / A
    return sigma_cr

def calculate_critical_stringer_buckling_stress(E, I, A, L, K=1.0):
    return calculate_critical_spar_buckling_stress(E, I, A, L, K_col=K)

def calculate_critical_sparweb_buckling_stress_compression(E, nu, t, b, K_c=3.72):
    if b == 0 or t == 0:
        return np.inf
    if E == 0:
        return 0.0
    if not (1 - nu**2 > 0):
        return np.nan
    sigma_cr = (K_c * np.pi**2 * E) / (12 * (1 - nu**2)) * (t / b)**2 
    return sigma_cr

def calculate_critical_skin_buckling_stress_shear(E, nu, t, b, K_s):
    if b == 0 or t == 0:
        return np.inf
    if E == 0:
        return 0.0
    if not (1 - nu**2 > 0):
        return np.nan
    tau_cr = (K_s * np.pi**2 * E) / (12 * (1 - nu**2)) * (t / b)**2
    return tau_cr

def calculate_stiffened_skin_compressive_strength(
    E_modulus, nu_poisson, skin_thickness, stiffener_spacing, 
    skin_buckling_coeff_Kc, stiffener_crippling_stress_sigma_cc, stiffener_area_As):

    if not (E_modulus > 0 and 0 < nu_poisson < 0.5 and skin_thickness > 0 and \
            stiffener_spacing >= 0 and skin_buckling_coeff_Kc > 0 and \
            stiffener_crippling_stress_sigma_cc > 0 and stiffener_area_As >= 0):
        return np.nan

    sigma_cr_skin = (skin_buckling_coeff_Kc * np.pi**2 * E_modulus) / (12 * (1 - nu_poisson**2)) * (skin_thickness / stiffener_spacing)**2 \
                    if stiffener_spacing > 0 else np.inf

    two_w_e = 0.0
    if skin_thickness > 0 and stiffener_spacing > 0 and stiffener_crippling_stress_sigma_cc > 0:
        denom = 12 * (1 - nu_poisson**2) * stiffener_crippling_stress_sigma_cc
        term = (skin_buckling_coeff_Kc * np.pi**2 * E_modulus) / denom
        if term > 0:
            two_w_e = skin_thickness * np.sqrt(term)
        two_w_e = min(two_w_e, stiffener_spacing)
        two_w_e = max(0, two_w_e)

    load_stiffener = stiffener_crippling_stress_sigma_cc * stiffener_area_As
    load_skin_effective = stiffener_crippling_stress_sigma_cc * two_w_e * skin_thickness
    remaining_skin_width = stiffener_spacing - two_w_e
    load_skin_buckled_remainder = 0.0
    if remaining_skin_width > 0 and np.isfinite(sigma_cr_skin):
        load_skin_buckled_remainder = sigma_cr_skin * remaining_skin_width * skin_thickness

    total_load = load_stiffener + load_skin_effective + load_skin_buckled_remainder
    total_area = stiffener_area_As + stiffener_spacing * skin_thickness

    return total_load / total_area if total_area > 0 else np.nan

def plot_buckling_vs_thickness(E, nu, b, K_c_vals, thickness_range):
    plt.figure(figsize=(10, 6))
    for K_c in K_c_vals:
        stresses = [(K_c * np.pi**2 * E) / (12 * (1 - nu**2)) * (t / b)**2 for t in thickness_range]
        plt.plot(thickness_range * 1e3, np.array(stresses) / 1e6, label=f"Kc = {K_c}")
    plt.xlabel("Plate Thickness (mm)")
    plt.ylabel("Buckling Stress (MPa)")
    plt.title("Compressive Buckling Stress vs. Plate Thickness")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("Figures/Structures/buckling_vs_thickness.png")

def plot_panel_strength_vs_spacing(E, nu, skin_thickness, K_c, sigma_cc_stiffener, A_stiffener, spacing_range):
    strengths = []
    for spacing in spacing_range:
        strength = calculate_stiffened_skin_compressive_strength(
            E, nu, skin_thickness, spacing, K_c, sigma_cc_stiffener, A_stiffener
        )
        strengths.append(strength / 1e6)
    plt.figure(figsize=(10, 6))
    plt.plot(spacing_range * 1e3, strengths, marker='o')
    plt.xlabel("Stiffener Spacing (mm)")
    plt.ylabel("Stiffened Panel Compressive Strength (MPa)")
    plt.title("Panel Strength vs. Stiffener Spacing")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("Figures/Structures/panel_strength_vs_spacing.png")

# # Constants for plots
# E_material = 70e9
# nu_material = 0.33
# skin_t = 0.0015
# K_c_values = [3.0, 4.0, 5.0]
# thickness_range = np.linspace(0.0005, 0.005, 50)
# spacing_range = np.linspace(0.05, 0.5, 20)
# sigma_cc_stiffener = 250e6
# A_stiffener = 1.2e-4

# # Output critical stress calculations
# print("--- Critical Stress Outputs ---")
# print(f"Spar Buckling Stress: {calculate_critical_spar_buckling_stress(E_material, 1e-7, 2e-4, 1.0, 1.0) / 1e6:.2f} MPa")
# print(f"Stringer Buckling Stress: {calculate_critical_stringer_buckling_stress(E_material, 5e-9, 1e-4, 0.5, 1.0) / 1e6:.2f} MPa")
# print(f"Spar Web Compression Buckling Stress: {calculate_critical_sparweb_buckling_stress_compression(E_material, nu_material, 0.002, 0.15, 4.0) / 1e6:.2f} MPa")
# print(f"Skin Shear Buckling Stress: {calculate_critical_skin_buckling_stress_shear(E_material, nu_material, 0.001, 0.10, 6.3) / 1e6:.2f} MPa")
# print(f"Stiffened Panel Strength: {calculate_stiffened_skin_compressive_strength(E_material, nu_material, skin_t, 0.10, 4.0, sigma_cc_stiffener, A_stiffener) / 1e6:.2f} MPa")
#
# # Plotting
# plot_buckling_vs_thickness(E_material, nu_material, 0.15, K_c_values, thickness_range)
# plot_panel_strength_vs_spacing(E_material, nu_material, skin_t, 4.0, sigma_cc_stiffener, A_stiffener, spacing_range)
