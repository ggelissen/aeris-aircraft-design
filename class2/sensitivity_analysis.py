# sensitivity_analysis.py

import os
import sys
import copy
import matplotlib.pyplot as plt
import numpy as np
import yaml
import json
import toml
import math as m

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from master_design_loop import master_design_process
from design_variables import DesignParameters


SENSITIVITY_CONFIG = {
    # Parameter Path: [List of values to test]
    'range': np.linspace(6000e3, 10000e3, 5),  # Vary range from 6,000 km to 10,000 km
    'weight.W_PL': np.linspace(300 * 9.81, 1100 * 9.81, 5), # Vary payload from 300kg to 1100kg (in N)
    'engine.cruise_tsfc': np.linspace(0.55, 0.80, 5), # Vary TSFC (lb/hr/lbf)
    'performance.take_off_distance': np.linspace(1000, 1500, 5), # Vary takeoff distance from 1000m to 1500m
    'wing.A_w_target': np.linspace(8.0, 14.0, 5), # Vary initial Aspect Ratio guess
}

OUTPUT_METRICS = {
    'W_TO': 'weight.W_TO',
    'W_F': 'weight.W_F',
    'W_OE': 'weight.W_OE',
    'S_w': 'wing.S_w',
    'A_w': 'wing.A_w_target',
    'T_W': 'weight.T_W',
    'L/D_cruise': 'performance.L_D_cruise',
}

G = 9.80665

def run_sensitivity_analysis(config: dict, baseline_config_path: str) -> dict:
    """
    Runs a one-at-a-time sensitivity analysis based on the provided configuration.

    Args:
        config (dict): A dictionary defining which parameters to vary and their ranges.
        baseline_config_path (str): Path to the baseline YAML configuration file.

    Returns:
        dict: A dictionary containing the results of the analysis.
    """
    print("--- Starting Sensitivity Analysis ---")
    
    # Load baseline parameters
    baseline_params = DesignParameters()
    baseline_params.load_from_yaml(baseline_config_path)
    print(f"Loaded baseline configuration from '{baseline_config_path}'")

    results = {}

    for param_path, values in config.items():
        print(f"\n{'='*60}\nAnalyzing sensitivity to: {param_path}\n{'='*60}")
        param_results = {'inputs': [], 'outputs': []}

        for value in values:
            print(f"\n--- Running for {param_path} = {value:.3f} ---")
            
            # Create a deep copy to avoid modifying the baseline
            current_params = copy.deepcopy(baseline_params)
            current_params.update_parameter(param_path, value)

            try:
                # Run the master design process
                final_params, history, converged = master_design_process(
                    config_file=baseline_config_path,  # master_design_process reloads, so we pass the path
                    max_iterations=15,
                    tolerance=0.02,
                    verbose=False # Keep the output clean for the analysis
                )
                
                # We need to manually update the param that was changed for this run
                # as master_design_process reloads the original file.
                final_params.update_parameter(param_path, value)

                if converged:
                    print(f"  -> Converged. MTOW = {final_params.weight.W_TO / G:.0f} kg")
                    # Store results
                    param_results['inputs'].append(value)
                    
                    output_data = {}
                    for metric_name, metric_path in OUTPUT_METRICS.items():
                        try:
                            output_data[metric_name] = final_params.get_parameter(metric_path)
                        except AttributeError:
                            output_data[metric_name] = np.nan
                    param_results['outputs'].append(output_data)

                else:
                    print(f"  -> Did not converge. Skipping this data point.")

            except Exception as e:
                print(f"  -> ERROR during execution for {param_path}={value}: {e}")
                import traceback
                traceback.print_exc()

        results[param_path] = param_results
        
    print("\n--- Sensitivity Analysis Complete ---")
    return results


def plot_sensitivity_results(results: dict):
    """
    Generates and saves plots for the sensitivity analysis results.

    Args:
        results (dict): The results dictionary from run_sensitivity_analysis.
    """
    print("\n--- Generating Plots ---")
    
    # Create a directory for plots
    plot_dir = "Figures/class2/sensitivity_analysis"
    os.makedirs(plot_dir, exist_ok=True)
    
    for param_path, data in results.items():
        if not data['inputs']:
            print(f"Skipping plot for '{param_path}' due to no valid results.")
            continue

        inputs = data['inputs']
        outputs = data['outputs']
        
        fig, ax1 = plt.subplots(figsize=(12, 7))
        fig.suptitle(f'Sensitivity to "{param_path}"', fontsize=16, fontweight='bold')

        # --- Primary Y-Axis (Weights in kg) ---
        ax1.set_xlabel(param_path, fontsize=12)
        ax1.set_ylabel('Weight (kg)', fontsize=12, color='k')
        ax1.tick_params(axis='y', labelcolor='k')
        
        w_to_kg = [o.get('W_TO', np.nan) / G for o in outputs]
        w_f_kg = [o.get('W_F', np.nan) / G for o in outputs]
        w_oe_kg = [o.get('W_OE', np.nan) / G for o in outputs]

        p1, = ax1.plot(inputs, w_to_kg, marker='o', linestyle='-', color='r', label='Max Take-Off Weight (MTOW)')
        p2, = ax1.plot(inputs, w_f_kg, marker='s', linestyle='--', color='b', label='Fuel Weight')
        p3, = ax1.plot(inputs, w_oe_kg, marker='^', linestyle=':', color='g', label='Operating Empty Weight')
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

        # --- Secondary Y-Axis (Geometry/Performance) ---
        ax2 = ax1.twinx()
        ax2.set_ylabel('Wing Area (m²) / Aspect Ratio', fontsize=12, color='purple')
        ax2.tick_params(axis='y', labelcolor='purple')
        
        s_w = [o.get('S_w', np.nan) for o in outputs]
        a_w = [o.get('A_w', np.nan) for o in outputs]

        p4, = ax2.plot(inputs, s_w, marker='d', linestyle='-.', color='purple', label='Wing Area (S_w)')
        p5, = ax2.plot(inputs, a_w, marker='x', linestyle='--', color='orange', label='Aspect Ratio (A_w)')
        
        # Combine legends
        handles = [p1, p2, p3, p4, p5]
        ax1.legend(handles=handles, loc='best')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Save the plot
        filename = f"sensitivity_{param_path.replace('.', '_')}.png"
        save_path = os.path.join(plot_dir, filename)
        plt.savefig(save_path)
        print(f"Saved plot: {save_path}")
        plt.close(fig)


if __name__ == "__main__":
 
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'design_config.yaml')
    
    if not os.path.exists(config_file_path):
        print(f"FATAL: Baseline config file not found at '{config_file_path}'")
        sys.exit(1)

    # Run the analysis
    analysis_results = run_sensitivity_analysis(SENSITIVITY_CONFIG, config_file_path)
    
    # Plot the results
    plot_sensitivity_results(analysis_results)