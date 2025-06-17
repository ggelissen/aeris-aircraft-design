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
    'cruise_mach': np.linspace(0.75, 0.90, 20), # Vary cruise Mach number from 0.75 to 0.90
    'range': np.linspace(6000e3, 10000e3, 20),  # Vary range from 6,000 km to 10,000 km
    'weight.W_PL': np.linspace(300 * 9.81, 1100 * 9.81, 20), # Vary payload from 300kg to 1100kg (in N)
    'engine.cruise_tsfc': np.linspace(0.55, 0.80, 20), # Vary TSFC (lb/hr/lbf)
    'wing.A_w_target': np.linspace(7, 30, 20) # Vary wing aspect ratio from 7 to 30
}

OUTPUT_METRICS = {
    'W_TO': 'weight.W_TO',
    'W_F': 'weight.W_F',
    'W_OE': 'weight.W_OE',
    'S_w': 'wing.S_w',
    'L/D_cruise': 'performance.L_D_cruise'
}

G = 9.80665

def run_sensitivity_analysis(config: dict, baseline_config_path: str) -> tuple[dict, dict]:
    """
    Runs sensitivity analysis and returns both absolute and baseline results.
    """
    print("--- Starting Sensitivity Analysis ---")

    # --- 1. Establish Baseline ---
    print("\n--- Running Baseline Configuration ---")
    baseline_params = DesignParameters(initial_config_path=baseline_config_path)
    final_baseline_params, _, baseline_converged = master_design_process(
        params_in=copy.deepcopy(baseline_params),
        max_iterations=15, tolerance=0.02, verbose=False
    )
    if not baseline_converged:
        raise RuntimeError("Baseline configuration failed to converge. Cannot proceed with sensitivity analysis.")

    baseline_outputs = {name: final_baseline_params.get_parameter(path) for name, path in OUTPUT_METRICS.items()}
    print(f"  -> Baseline Converged. MTOW = {baseline_outputs['W_TO'] / G:.0f} kg")

    # --- 2. Run Sensitivity Sweeps ---
    results = {}
    for param_path, values in config.items():
        print(f"\n{'='*60}\nAnalyzing sensitivity to: {param_path}\n{'='*60}")
        param_results = {'inputs': [], 'outputs': []}

        for value in values:
            print(f"\n--- Running for {param_path} = {value:.3f} ---")
            current_params = copy.deepcopy(baseline_params)
            current_params.update_parameter(param_path, value)

            try:
                final_params, _, converged = master_design_process(
                    params_in=current_params,
                    max_iterations=15, tolerance=0.02, verbose=False
                )
                if converged:
                    print(f"  -> Converged. MTOW = {final_params.weight.W_TO / G:.0f} kg")
                    param_results['inputs'].append(value)
                    output_data = {name: final_params.get_parameter(path) for name, path in OUTPUT_METRICS.items()}
                    param_results['outputs'].append(output_data)
                else:
                    print(f"  -> Did not converge. Skipping this data point.")
            except Exception as e:
                print(f"  -> ERROR during execution for {param_path}={value}: {e}")

        results[param_path] = param_results

    print("\n--- Sensitivity Analysis Complete ---")
    return results, baseline_outputs


def plot_sensitivity_results(results: dict, baseline_outputs: dict):
    """
    Generates and saves plots with results normalized to the baseline.
    """
    print("\n--- Generating Normalized Plots ---")
    plot_dir = "Figures/class2/sensitivity_analysis"
    os.makedirs(plot_dir, exist_ok=True)

    for param_path, data in results.items():
        if not data['inputs']:
            print(f"Skipping plot for '{param_path}' due to no valid results.")
            continue

        inputs = data['inputs']
        outputs = data['outputs']

        fig, ax1 = plt.subplots(figsize=(12, 7))
        ax1.set_xlabel(param_path, fontsize=12)
        ax1.set_ylabel('Relative Change from Baseline (%)', fontsize=12)
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Normalize and plot each metric
        for metric_name, metric_path in OUTPUT_METRICS.items():
            baseline_value = baseline_outputs.get(metric_name)
            if baseline_value is None or baseline_value == 0:
                continue

            absolute_values = [o.get(metric_name, np.nan) for o in outputs]
            # Calculate relative change in percent
            normalized_values = [((val - baseline_value) / baseline_value) * 100 for val in absolute_values]
            
            ax1.plot(inputs, normalized_values, marker='o', linestyle='-', label=metric_name)

        ax1.legend(loc='best')
        ax1.axhline(0, color='black', linewidth=0.8, linestyle='--') # Add a zero line for reference
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        filename = f"sensitivity_normalized_{param_path.replace('.', '_')}.png"
        save_path = os.path.join(plot_dir, filename)
        plt.savefig(save_path)
        print(f"Saved plot: {save_path}")
        plt.close(fig)



if __name__ == "__main__":

    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'design_config.yaml')

    analysis_results, baseline_results = run_sensitivity_analysis(SENSITIVITY_CONFIG, config_file_path)

    plot_sensitivity_results(analysis_results, baseline_results)
    print("\nAnalysis finished. Plotting function is ready to be used.")