# Filename : exampl73_modified.py

# Calculates the power spectral density of the normal acceleration for multiple scenarios.

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)
# - Modified for multiple scenarios analysis

from math import *
import numpy as np
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2s import cit2s_fun
import pandas as pd

def analyze_turbulence_scenarios(scenarios):
    """
    Analyze atmospheric turbulence scenarios and return results in a table.
    
    Parameters:
    scenarios (dict): Dictionary with scenario names as keys and 
                     {"sigma": value, "Lg": value} as values
    
    Returns:
    pandas.DataFrame: Table with results for each scenario
    """
    
    print('   Multiple Scenario Atmospheric Turbulence Analysis           ')
    print('                                                                ')
    print('   Calculation of the power spectral density of the normal      ')
    print('   acceleration due to longitudinal and vertical turbulence.    ')
    print('   Also, the effect of a lagfree autopilot will be investigated.')
    print('                                                                ')
    
    # Initialize results storage
    results = []
    
    # DEFINE FREQUENCY AXES
    N = 1000 
    omega = np.logspace(-3, 3, N)                 # frequency axis
    
    # MISCELLANEOUS
    g = 9.80665                              # gravitational acc [N/kg]
    
    # Process each scenario
    for scenario_name, params in scenarios.items():
        print(f'\n   Processing scenario: {scenario_name}')
        print(f'   Sigma: {params["sigma"]}, Lg: {params["Lg"]}')
        
        # GET A/C DYNAMICS for this scenario
        A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun(sigma=params["sigma"], Lg=params["Lg"])
        
        # Calculate variance integration weights
        dw = np.diff(omega)
        dw = np.hstack((dw, np.array([0])))  # make vector length equal to N again
        
        # HORIZONTAL TURBULENCE
        iu = 1 # index of the input to be used
        
        # CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
        Cn = A[2, :] - A[1, :] 
        Dn = B[2, iu] - B[1, iu]
        Hn = cm.ss(A, B[:, iu], V/g*Cn, Dn)
        
        # COMPUTE FREQUENCY RESPONSE FUNCTION
        mag = cm.frequency_response(Hn, omega)[0]
        Snn = mag*mag
        
        # VERTICAL TURBULENCE (Elevator fixed)
        iu = 2 # index of the input to be used
        
        # CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
        Cn = A[2, :] - A[1, :] 
        Dn = B[2, iu] - B[1, iu]
        Hn = cm.ss(A, B[:, iu], V/g*Cn, Dn)
        
        # COMPUTE FREQUENCY RESPONSE FUNCTION
        mag = cm.frequency_response(Hn, omega)[0]
        Snn1 = mag*mag
        
        # VERTICAL TURBULENCE WITH PITCH ATTITUDE HOLD SYSTEM
        iu = 2 # index of the input to be used
        
        # CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
        Cn = At[2, :] - At[1, :] 
        Dn = B[2, iu] - B[1, iu]
        Hn = cm.ss(At, B[:, iu], V/g*Cn, Dn)
        
        # COMPUTE FREQUENCY RESPONSE FUNCTION
        mag = cm.frequency_response(Hn, omega)[0]
        Snnt1 = mag*mag
        
        # CALCULATION OF VARIANCES
        varn_horiz = np.sum(Snn.T * dw) / np.pi
        varn_vert = np.sum(Snn1.T * dw) / np.pi
        varn_vert_autopilot = np.sum(Snnt1.T * dw) / np.pi
        
        # Calculate accelerations variances
        varaz_horiz = varn_horiz * g**2
        varaz_vert = varn_vert * g**2
        varaz_vert_autopilot = varn_vert_autopilot * g**2
        
        # Calculate RMS load factors
        rms_horiz = np.sqrt(varn_horiz[0] if hasattr(varn_horiz, '__len__') else varn_horiz)
        rms_vert = np.sqrt(varn_vert[0] if hasattr(varn_vert, '__len__') else varn_vert)
        rms_vert_autopilot = np.sqrt(varn_vert_autopilot[0] if hasattr(varn_vert_autopilot, '__len__') else varn_vert_autopilot)
        
        # Peak load factors (3-sigma)
        peak_horiz = 3 * rms_horiz
        peak_vert = 3 * rms_vert
        peak_vert_autopilot = 3 * rms_vert_autopilot
        
        # Maximum expected load factor
        max_peak = max(peak_horiz, peak_vert, peak_vert_autopilot)
        
        # Store results
        result_row = {
            'Scenario': scenario_name,
            'Sigma': params["sigma"],
            'Lg [m]': params["Lg"],
            'RMS Load Factor (Horizontal) [g]': rms_horiz,
            'RMS Load Factor (Vertical) [g]': rms_vert,
            'RMS Load Factor (Vert+Autopilot) [g]': rms_vert_autopilot,
            'Peak Load Factor (Horizontal) [g]': peak_horiz,
            'Peak Load Factor (Vertical) [g]': peak_vert,
            'Peak Load Factor (Vert+Autopilot) [g]': peak_vert_autopilot,
            'Maximum Expected Load Factor [g]': max_peak,
            'Variance az (Horizontal) [m²/s⁴]': varaz_horiz[0] if hasattr(varaz_horiz, '__len__') else varaz_horiz,
            'Variance az (Vertical) [m²/s⁴]': varaz_vert[0] if hasattr(varaz_vert, '__len__') else varaz_vert,
            'Variance az (Vert+Autopilot) [m²/s⁴]': varaz_vert_autopilot[0] if hasattr(varaz_vert_autopilot, '__len__') else varaz_vert_autopilot
        }
        
        results.append(result_row)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    return df

def plot_scenario_comparison(scenarios):
    """
    Plot power spectral densities for all scenarios for comparison.
    """
    g= 9.80665  # gravitational acceleration [m/s²]
    plt.close('all')
    
    # DEFINE FREQUENCY AXES
    N = 1000 
    omega = np.logspace(-3, 3, N)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    for i, (scenario_name, params) in enumerate(scenarios.items()):
        color = colors[i % len(colors)]
        
        # GET A/C DYNAMICS
        A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun(sigma=params["sigma"], Lg=params["Lg"])
        
        # HORIZONTAL TURBULENCE
        iu = 1
        Cn = A[2, :] - A[1, :] 
        Dn = B[2, iu] - B[1, iu]
        Hn = cm.ss(A, B[:, iu], V/g*Cn, Dn)
        mag = cm.frequency_response(Hn, omega)[0]
        Snn = mag*mag
        
        # VERTICAL TURBULENCE
        iu = 2
        Cn = A[2, :] - A[1, :] 
        Dn = B[2, iu] - B[1, iu]
        Hn = cm.ss(A, B[:, iu], V/g*Cn, Dn)
        mag = cm.frequency_response(Hn, omega)[0]
        Snn1 = mag*mag
        
        # Plot horizontal turbulence
        ax1.loglog(omega, Snn, color=color, label=f'{scenario_name} (σ={params["sigma"]}, Lg={params["Lg"]})')
        
        # Plot vertical turbulence
        ax2.loglog(omega, Snn1, color=color, label=f'{scenario_name} (σ={params["sigma"]}, Lg={params["Lg"]})')
    
    ax1.set_xlabel('Frequency [rad/s]')
    ax1.set_ylabel('Snn')
    ax1.set_title('Power Spectral Density - Horizontal Turbulence')
    ax2.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    ax2.set_xlabel('Frequency [rad/s]')
    ax2.set_ylabel('Snn')
    ax2.set_title('Power Spectral Density - Vertical Turbulence')
    # Locate legend on the upper right corner
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Define scenarios
    scenarios = {
        "Normal Atmospheric": {"sigma": 1.0, "Lg": 150},
        "Light Wake": {"sigma": 3.0, "Lg": 50}, 
        "Moderate Wake": {"sigma": 5.0, "Lg": 10},
        "Severe Wake": {"sigma": 8.0, "Lg": 1}
    }
    
    # Analyze scenarios
    results_table = analyze_turbulence_scenarios(scenarios)
    
    # Display results
    print('\n' + '='*120)
    print('ATMOSPHERIC TURBULENCE ANALYSIS RESULTS')
    print('='*120)
    
    # Print table with formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', '{:.4f}'.format)
    
    print(results_table.to_string(index=False))
    
    # Summary table with key parameters
    print('\n' + '='*80)
    print('SUMMARY - KEY LOAD FACTORS')
    print('='*80)
    
    summary_cols = ['Scenario', 'Sigma', 'Lg [m]', 
                   'Peak Load Factor (Horizontal) [g]', 
                   'Peak Load Factor (Vertical) [g]', 
                   'Maximum Expected Load Factor [g]']
    
    print(results_table[summary_cols].to_string(index=False))
    
    # Plot comparison
    plot_scenario_comparison(scenarios)