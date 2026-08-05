import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml

# Ensure correct path for importing DesignParameters
sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

from config.design_variables import DesignParameters

def short_period_eigenvalues(params: DesignParameters):
    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)
    KY2 = params.inertia.I_yy / (params.weight.M_TO * params.wing.mac**2)

    A = 2 * muc * KY2 * (2*muc - params.stability_aero.CZadot)
    B = -2*muc * KY2 * params.stability_aero.CZa - (2*muc + params.stability_aero.CZq) * params.stability_aero.Cmadot - (2*muc + params.stability_aero.Cmadot) * params.stability_aero.CZq
    C = params.stability_aero.CZa * params.stability_aero.Cmq - (2*muc + params.stability_aero.CZq) * params.stability_aero.Cma

    eigenvalues = np.roots([A, B, C])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/params.wing.mac

    half_period = - np.log(0.5) / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.real(eigenvalues[0]) != 0 else np.inf
    period = 2*np.pi/ np.imag(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.imag(eigenvalues[0]) != 0 else np.nan
    time_constant = - 1 / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.real(eigenvalues[0]) != 0 else np.inf

    return {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def phugoid_eigenvalues(params: DesignParameters):
    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)

    A = 2* muc * (params.stability_aero.CZa * params.stability_aero.Cmq - 2*muc * params.stability_aero.Cma)
    B = 2*muc * (params.stability_aero.CXu * params.stability_aero.Cma - params.stability_aero.Cmu * params.stability_aero.CXa) + params.stability_aero.Cmq * (params.stability_aero.CZu * params.stability_aero.CXa - params.stability_aero.CXu * params.stability_aero.CZa)
    C = params.stability_aero.CZ0 * (params.stability_aero.Cmu * params.stability_aero.CXa - params.stability_aero.CXu * params.stability_aero.Cma)

    eigenvalues = np.roots([A, B, C])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.mac

    half_period = - np.log(0.5) / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.real(eigenvalues[0]) != 0 else np.inf
    period = 2*np.pi/ np.imag(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.imag(eigenvalues[0]) != 0 else np.nan
    time_constant = - 1 / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed if np.real(eigenvalues[0]) != 0 else np.inf

    return {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def aperiodic_roll_eigenvalues(params: DesignParameters):
    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)

    # Note: Aperiodic roll has only one real eigenvalue
    eigenvalues_val = params.stability_aero.Clp / (4 * mub * KX2)
    eigenvalues = np.array([eigenvalues_val], dtype=complex) # Ensure it's treated as an array of complex numbers for consistency
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.b_w

    half_period = - np.log(0.5) / np.real(eigenvalues_val) * params.wing.b_w / params.cruise_speed if np.real(eigenvalues_val) != 0 else np.inf
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues_val) * params.wing.b_w / params.cruise_speed if np.real(eigenvalues_val) != 0 else np.inf

    return {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def spiral_eigenvalues(params: DesignParameters):
    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)

    # Note: Spiral mode has only one real eigenvalue
    eigenvalues_val = 2*params.performance.CL_cruise * (params.stability_aero.Clb*params.stability_aero.Cnr - params.stability_aero.Cnb*params.stability_aero.Clr) / \
                      (params.stability_aero.Clp * (params.stability_aero.CYb * params.stability_aero.Cnr + 4 * mub * params.stability_aero.Cnb) - \
                       params.stability_aero.Cnp * (params.stability_aero.CYb * params.stability_aero.Clr + 4 * mub * params.stability_aero.Clb))
    eigenvalues = np.array([eigenvalues_val], dtype=complex) # Ensure it's treated as an array of complex numbers
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.b_w # Use b_w for lateral modes

    half_period = - np.log(0.5) / np.real(eigenvalues_val) * params.wing.b_w / params.cruise_speed if np.real(eigenvalues_val) != 0 else np.inf
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues_val) * params.wing.b_w / params.cruise_speed if np.real(eigenvalues_val) != 0 else np.inf

    return {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def dutch_roll_eigenvalues(params: DesignParameters):
    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)
    KZ2 = params.inertia.I_zz / (params.weight.M_TO * params.wing.b_w**2)
    KXZ = params.inertia.I_xz / (params.weight.M_TO * params.wing.b_w**2)

    A = 4* mub**2 * (KZ2 * KX2 - KXZ**2)
    B = -mub * ((params.stability_aero.Clr + params.stability_aero.Cnp) * KXZ + params.stability_aero.Cnr * KX2 + params.stability_aero.Clp * KZ2)
    C = 2 * mub * (params.stability_aero.Cnb * KX2 + params.stability_aero.Clb * KXZ) + (params.stability_aero.Clp * params.stability_aero.Cnr - params.stability_aero.Clr * params.stability_aero.Cnp) / 4
    D = (params.stability_aero.Clb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.Clp) / 2

    eigenvalues = np.roots([A, B, C, D])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.b_w

    # Dutch roll typically has complex conjugate roots
    # Find the complex conjugate pair for period/half_period
    # Assuming the first root is representative if multiple complex roots exist (unlikely for Dutch Roll)
    complex_roots = eigenvalues[np.iscomplex(eigenvalues)]
    if len(complex_roots) > 0:
        # Take the first one for calculations, as they are conjugate pairs
        principal_eigenvalue = complex_roots[0]
        if np.real(principal_eigenvalue) != 0:
            half_period = - np.log(0.5) / np.real(principal_eigenvalue) * params.wing.b_w / params.cruise_speed
        else:
            half_period = np.inf
        if np.imag(principal_eigenvalue) != 0:
            period = 2*np.pi/ np.abs(np.imag(principal_eigenvalue)) * params.wing.b_w / params.cruise_speed
        else:
            period = np.nan
        time_constant = - 1 / np.real(principal_eigenvalue) * params.wing.b_w / params.cruise_speed if np.real(principal_eigenvalue) != 0 else np.inf
    else: # If for some reason Dutch roll yields only real roots (unstable or critically damped)
        half_period = np.inf
        period = np.nan
        time_constant = np.inf


    return {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def asymmetric_eigenvalues(params: DesignParameters):
    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)
    KZ2 = params.inertia.I_zz / (params.weight.M_TO * params.wing.b_w**2)
    KXZ = params.inertia.I_xz / (params.weight.M_TO * params.wing.b_w**2)

    A = 16 * mub**3 * (KX2 * KZ2 - KXZ**2)
    B = -4 * mub**2 * (2 * params.stability_aero.CYb * (KX2 * KZ2 - KXZ**2) + params.stability_aero.Cnr * KX2 + params.stability_aero.Clp * KZ2 + (params.stability_aero.Clr + params.stability_aero.Cnp) * KXZ)
    C = 2 * mub * ((params.stability_aero.CYb * params.stability_aero.Cnr -params.stability_aero.CYr * params.stability_aero.Cnb) * KX2 + (params.stability_aero.CYb * params.stability_aero.Clp - params.stability_aero.Clb * params.stability_aero.CYp) * KZ2 + 
                 ((params.stability_aero.CYb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.CYp) + (params.stability_aero.CYb * params.stability_aero.Clr - params.stability_aero.Clb * params.stability_aero.CYr)) * KXZ +
                 4 * mub * params.stability_aero.Cnb * KX2 + 4 * mub * params.stability_aero.Clb * KXZ + (1/2) * (params.stability_aero.Clp * params.stability_aero.Cnr - params.stability_aero.Cnp * params.stability_aero.Clr))
    D = (-4 * mub * params.performance.CL_cruise * (params.stability_aero.Clb * KZ2 + params.stability_aero.Cnb * KXZ) + 2 * mub * (params.stability_aero.Clb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.Clp) +
                 (1/2) * params.stability_aero.CYb * (params.stability_aero.Clr * params.stability_aero.Cnp - params.stability_aero.Cnr * params.stability_aero.Clp) + (1/2) * params.stability_aero.CYp * (params.stability_aero.Clb * params.stability_aero.Cnr - params.stability_aero.Cnb * params.stability_aero.Clr) +
                 (1/2) * params.stability_aero.CYr * (params.stability_aero.Clp * params.stability_aero.Cnb - params.stability_aero.Cnp * params.stability_aero.Clb))
    E = params.performance.CL_cruise * (params.stability_aero.Clb * params.stability_aero.Cnr - params.stability_aero.Cnb * params.stability_aero.Clr)

    eigenvalues = np.roots([A, B, C, D, E])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.b_w

    # Half-period calculation needs to be more robust for multiple roots
    half_periods = []
    periods = []
    time_constants = []
    for eig in eigenvalues:
        if np.real(eig) != 0:
            half_periods.append(- np.log(0.5) / np.real(eig) * params.wing.b_w / params.cruise_speed)
            time_constants.append(- 1 / np.real(eig) * params.wing.b_w / params.cruise_speed)
        else:
            half_periods.append(np.inf)
            time_constants.append(np.inf)
        if np.imag(eig) != 0:
            periods.append(2*np.pi/ np.abs(np.imag(eig)) * params.wing.b_w / params.cruise_speed)
        else:
            periods.append(np.nan)


    return {"eigenvalues": eigenvalues, "half_period": half_periods, "period": periods, "time_constant": time_constants, "dimensioned_eigenvalues": dimensioned_eigenvalues}


def symmetric_eigenvalues(params: DesignParameters):
    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)
    KY2 = params.inertia.I_yy / (params.weight.M_TO * params.wing.mac**2)
    
    A = 4 * muc**2 * KY2 * (params.stability_aero.CZadot - 2 * muc)
    B = (params.stability_aero.Cmadot * 2 * muc * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.Cmq * 2 * muc * (params.stability_aero.CZadot - 2 * muc) -
         2 * muc * KY2 * (params.stability_aero.CXu * (params.stability_aero.CZadot - 2 * muc) - 2 * muc * params.stability_aero.CZa))
    C = (params.stability_aero.Cma * 2 * muc * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.Cmadot * (2 * muc * params.stability_aero.CX0 + params.stability_aero.CXu * (params.stability_aero.CZq + 2 * muc)) +
        params.stability_aero.Cmq * (params.stability_aero.CXu * (params.stability_aero.CZadot - 2 * muc) - 2 * muc * params.stability_aero.CZa) + 2 * muc * KY2 * (params.stability_aero.CXa * params.stability_aero.CZu - params.stability_aero.CZa * params.stability_aero.CXu))
    D = (params.stability_aero.Cmu * (params.stability_aero.CXa * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.CZ0 * (params.stability_aero.CZadot - 2 * muc)) -
        params.stability_aero.Cma * (2 * muc * params.stability_aero.CX0 + params.stability_aero.CXu * (params.stability_aero.CZq + 2 * muc)) +
        params.stability_aero.Cmadot * (params.stability_aero.CX0 * params.stability_aero.CXu - params.stability_aero.CZ0 * params.stability_aero.CZu) + params.stability_aero.Cmq * (params.stability_aero.CXu * params.stability_aero.CZa - params.stability_aero.CZu * params.stability_aero.CXa))
    E = -params.stability_aero.Cmu * (params.stability_aero.CX0 * params.stability_aero.CXa + params.stability_aero.CZ0 * params.stability_aero.CZa) + params.stability_aero.Cma * (params.stability_aero.CX0 * params.stability_aero.CXu + params.stability_aero.CZ0 * params.stability_aero.CZu)
    
    eigenvalues = np.roots([A, B, C, D, E])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.mac

    half_periods = []
    periods = []
    time_constants = []
    for eig in eigenvalues:
        if np.real(eig) != 0:
            half_periods.append(- np.log(0.5) / np.real(eig) * params.wing.mac / params.cruise_speed)
            time_constants.append(- 1 / np.real(eig) * params.wing.mac / params.cruise_speed)
        else:
            half_periods.append(np.inf)
            time_constants.append(np.inf)
        if np.imag(eig) != 0:
            periods.append(2*np.pi/ np.abs(np.imag(eig)) * params.wing.mac / params.cruise_speed)
        else:
            periods.append(np.nan)

    return {"eigenvalues": eigenvalues, "half_period": half_periods, "period": periods, "time_constant": time_constants, "dimensioned_eigenvalues": dimensioned_eigenvalues}

def save_data(eigenvalue_data):
    df_data = []
    for mode, data in eigenvalue_data.items():
        if isinstance(data['dimensioned_eigenvalues'], np.ndarray):
            for eig in data['dimensioned_eigenvalues']:
                df_data.append({
                    'Mode': mode,
                    'Eigenvalue (Real)': np.real(eig),
                    'Eigenvalue (Imaginary)': np.imag(eig),
                    'Half-Period': data['half_period'][0] if isinstance(data['half_period'], list) else data['half_period'], # Take first if list
                    'Period': data['period'][0] if isinstance(data['period'], list) else data['period'], # Take first if list
                    'Time Constant': data['time_constant'][0] if isinstance(data['time_constant'], list) else data['time_constant'] # Take first if list
                })
        else: # For single eigenvalues like aperiodic roll and spiral
             df_data.append({
                    'Mode': mode,
                    'Eigenvalue (Real)': np.real(data['dimensioned_eigenvalues']),
                    'Eigenvalue (Imaginary)': np.imag(data['dimensioned_eigenvalues']),
                    'Half-Period': data['half_period'],
                    'Period': data['period'],
                    'Time Constant': data['time_constant']
                })

    df = pd.DataFrame(df_data)
    filepath = os.path.join("modelling", "eigenvalue_data", f"eigenvalue_data.csv")
    os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure directory exists
    df.to_csv(filepath, index=False)
    print("Data saved to eigenvalue_data.csv")

def plot_eigenvalues(eigenvalue_results, save_path="eigenvalue_plot.png"):
    """
    Plots the eigenvalues on a complex plane.

    Args:
        eigenvalue_results (dict): Dictionary containing the results from
                                   short_period_eigenvalues, phugoid_eigenvalues,
                                   aperiodic_roll_eigenvalues, dutch_roll_eigenvalues,
                                   and spiral_eigenvalues functions.
        save_path (str): Path to save the plot image.
    """
    plt.figure(figsize=(10, 8))
    plt.axvline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8)

    # Add stability region lines (examples, adjust as needed based on requirements)
    # Damping ratio lines for common stability criteria (e.g., zeta = 0.707 for critically damped)
    # Lines for natural frequency for typical short period or Dutch roll
    # This part can be more detailed if you have specific stability requirements.
    # For a basic plot, just showing the axes is fine.

    # Plot Dutch Roll
    dutch_roll_eigs = eigenvalue_results["dutch_roll"]["dimensioned_eigenvalues"]
    plt.plot(np.real(dutch_roll_eigs), np.imag(dutch_roll_eigs), 'o', color='blue', label='Dutch Roll')
    # Plot conjugate if complex
    for eig in dutch_roll_eigs:
        if np.imag(eig) != 0 and np.real(eig) != 0:
            plt.plot([np.real(eig), np.real(eig)], [np.imag(eig), -np.imag(eig)], ':', color='blue', linewidth=0.5)


    # Plot Aperiodic Roll
    aperiodic_roll_eig = eigenvalue_results["aperiodic_roll"]["dimensioned_eigenvalues"]
    plt.plot(np.real(aperiodic_roll_eig), np.imag(aperiodic_roll_eig), 'x', color='red', label='Aperiodic Roll')

    # Plot Spiral
    spiral_eig = eigenvalue_results["spiral"]["dimensioned_eigenvalues"]
    plt.plot(np.real(spiral_eig), np.imag(spiral_eig), '^', color='green', label='Spiral')

    # Optional: Plot Short Period and Phugoid if desired, but focus is on lateral modes
    # short_period_eigs = eigenvalue_results["short_period"]["dimensioned_eigenvalues"]
    # plt.plot(np.real(short_period_eigs), np.imag(short_period_eigs), 'o', color='purple', label='Short Period')
    # phugoid_eigs = eigenvalue_results["phugoid"]["dimensioned_eigenvalues"]
    # plt.plot(np.real(phugoid_eigs), np.imag(phugoid_eigs), 's', color='orange', label='Phugoid')


    plt.title('Eigenvalues of Lateral-Directional Modes')
    plt.xlabel('Real Part (Damping, $\sigma$) [1/s]')
    plt.ylabel('Imaginary Part (Frequency, $\omega$) [rad/s]')
    plt.grid(True)
    plt.legend()
    plt.axis('equal') # Ensures real and imaginary axes have same scaling
    plt.xlim([-2, 2]) # Adjust limits based on expected eigenvalue ranges
    plt.ylim([-2, 2]) # Adjust limits based on expected eigenvalue ranges

    plt.savefig(save_path)
    plt.show()


if __name__ == "__main__":
    params = DesignParameters()
    params.load_from_yaml("design_config.yaml")

    # Store results in a dictionary
    eigenvalue_results = {}
    
    eigs_short_period = short_period_eigenvalues(params)
    eigenvalue_results["short_period"] = eigs_short_period
    print(f"short period {eigs_short_period}")

    eigs_phugoid = phugoid_eigenvalues(params)
    eigenvalue_results["phugoid"] = eigs_phugoid
    print(f"phugoid {eigs_phugoid}")

    eigs_aperiodic = aperiodic_roll_eigenvalues(params)
    eigenvalue_results["aperiodic_roll"] = eigs_aperiodic
    print(f"aperiodic roll {eigs_aperiodic}")

    eigs_dutch = dutch_roll_eigenvalues(params)
    eigenvalue_results["dutch_roll"] = eigs_dutch
    print(f"dutch roll {eigs_dutch}")

    eigs_spiral = spiral_eigenvalues(params)
    eigenvalue_results["spiral"] = eigs_spiral
    print(f"spiral {eigs_spiral}")

    # You can also use the asymmetric and symmetric functions to get all eigenvalues at once
    # eigs_asymmetric = asymmetric_eigenvalues(params)
    # eigenvalue_results["asymmetric"] = eigs_asymmetric
    # print(f"asymmetric {eigs_asymmetric}")

    # eigs_symmetric = symmetric_eigenvalues(params)
    # eigenvalue_results["symmetric"] = eigs_symmetric
    # print(f"symmetric {eigs_symmetric}")

    # Save data (if needed)
    # save_data(eigenvalue_results) # This function seems to expect a different structure for half_period/period/time_constant when dealing with lists vs single values. Adjust save_data or collect data consistently.

    # Plot the eigenvalues
    plot_eigenvalues(eigenvalue_results, save_path="lateral_eigenvalues_plot.png")