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
    'cruise_speed': np.linspace(200, 300, 20),  # Vary cruise speed from 200 m/s to 300 m/s
    'range': np.linspace(6000e3, 10000e3, 20),  # Vary range from 6,000 km to 10,000 km
    'weight.W_PL': np.linspace(300 * 9.81, 1100 * 9.81, 20), # Vary payload from 300kg to 1100kg (in N)
    'engine.cruise_tsfc': np.linspace(0.55, 0.80, 20), # Vary TSFC (lb/hr/lbf)
    'wing.A_w_target': np.linspace(7, 30, 20) # Vary wing aspect ratio from 7 to 30
}

OUTPUT_METRICS = {
    'W_TO': 'weight.W_TO',
    'W_F': 'weight.W_F',
    'W_OE': 'weight.W_OE',
    #'S_w': 'wing.S_w',
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


def _set_report_style():
    """Sets a professional plot style suitable for reports."""
    # Set font to Arial, falling back to a generic sans-serif
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
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['lines.markersize'] = 6

# Dictionary to map technical parameter paths to pretty labels for plots
# This now includes labels for the output metrics for consistent legends.
LABEL_MAPPING = {
    'wing.A_w_target': 'Wing Aspect Ratio ($A_w$)',
    'cruise_mach': 'Cruise Mach Number',
    'range': 'Design Range [km]',
    'weight.W_PL': 'Payload Weight ($W_{PL}$) [N]',
    'engine.cruise_tsfc': 'Thrust-Specific Fuel Consumption (TSFC)',
    
    # Labels for metrics used in legends
    'weight.W_TO': 'Take-off Weight ($W_{TO}$)',
    'weight.W_F': 'Fuel Weight ($W_F$)',
    'weight.W_OE': 'Operating Empty Weight ($W_{OE}$)',
    'wing.S_w': 'Wing Area ($S_w$)',
    'performance.L_D_cruise': 'L/D Ratio (Cruise)'
}

# A cohesive and colorblind-friendly color palette
COLOR_PALETTE = {
    'blue': '#0d3b66',
    'green': '#5fad56',
    'red': '#f95738',
    'purple': '#8E6E95',
    'orange': '#ee964b'
}


def plot_aspect_ratio_trade_study(data: dict):
    """
    Generates a specialized, dual-axis plot for Aspect Ratio sensitivity
    with final report-quality aesthetics and legend control.
    """
    _set_report_style()
    param_path = 'wing.A_w_target'
    print(f"\n--- Generating Final Report Plot for {param_path} ---")

    plot_dir = "Figures/class2/sensitivity_analysis"
    os.makedirs(plot_dir, exist_ok=True)

    if not data.get('inputs'):
        print(f"Skipping plot for '{param_path}' due to no valid results.")
        return

    inputs = data['inputs']
    outputs = data['outputs']

    # --- Normalization ---
    baseline_point = outputs[0]
    norm_fuel = [o.get('W_F', np.nan) / baseline_point.get('W_F', 1) for o in outputs]
    norm_oew = [o.get('W_OE', np.nan) / baseline_point.get('W_OE', 1) for o in outputs]
    norm_tow = [o.get('W_TO', np.nan) / baseline_point.get('W_TO', 1) for o in outputs]
    ld_cruise = [o.get('L/D_cruise', np.nan) for o in outputs]

    # --- Plotting ---
    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.set_xlabel(LABEL_MAPPING.get(param_path, param_path))
    ax1.set_ylabel(f'Normalized Weight (relative to $A_w={inputs[0]:.0f}$)')
    p1, = ax1.plot(inputs, norm_fuel, marker='o', linestyle='-', color=COLOR_PALETTE['blue'], label=LABEL_MAPPING['weight.W_F'])
    p2, = ax1.plot(inputs, norm_oew, marker='s', linestyle='--', color=COLOR_PALETTE['green'], label=LABEL_MAPPING['weight.W_OE'])
    p3, = ax1.plot(inputs, norm_tow, marker='^', linestyle='-.', color=COLOR_PALETTE['red'], label=LABEL_MAPPING['weight.W_TO'])
    
    ax1.grid(True, which='both', linestyle=':', linewidth=0.7, color='grey', alpha=0.6)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.tick_params(axis='y')

    ax2 = ax1.twinx()
    ax2.set_ylabel(LABEL_MAPPING['performance.L_D_cruise'])
    p4, = ax2.plot(inputs, ld_cruise, marker='d', linestyle=':', color=COLOR_PALETTE['purple'], label=LABEL_MAPPING['performance.L_D_cruise'])
    
    ax2.spines['top'].set_visible(False)
    ax2.tick_params(axis='y')
    
    # --- Final Legend Styling (Corrected Method) ---
    handles = [p1, p2, p3, p4]
    # 1. Create the legend
    legend = ax1.legend(handles=handles, loc='best', frameon=True)
    
    # 2. Get the frame and apply styles to it
    frame = legend.get_frame()
    frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
    frame.set_facecolor('white')
    frame.set_edgecolor('black')
    frame.set_alpha(0.8)
    frame.set_linewidth(0.5)

    # 3. Set the zorder on the legend object itself
    legend.set_zorder(10)
    
    plt.tight_layout()
    filename = "report_sensitivity_aspect_ratio.pdf"
    save_path = os.path.join(plot_dir, filename)
    plt.savefig(save_path, transparent=False)
    print(f"Saved plot: {save_path}")
    plt.close(fig)

def plot_general_sensitivity_results(param_path: str, data: dict, baseline_outputs: dict):
    """
    Generates a general-purpose sensitivity plot with final report-quality
    aesthetics and legend control.
    """
    _set_report_style()
    print(f"\n--- Generating Final Report Plot for {param_path} ---")
    plot_dir = "Figures/class2/sensitivity_analysis"
    os.makedirs(plot_dir, exist_ok=True)
    
    if not data.get('inputs'):
        print(f"Skipping plot for '{param_path}' due to no valid results.")
        return

    inputs = data['inputs']
    outputs = data['outputs']
    
    x_label = LABEL_MAPPING.get(param_path, param_path)
    if param_path == 'range':
        inputs = [val / 1000 for val in inputs]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xlabel(x_label)
    ax1.set_ylabel('Relative Change from Baseline [%]')
    
    colors = [COLOR_PALETTE[c] for c in ['blue', 'green', 'red', 'orange', 'purple']]
    markers = ['o', 's', '^', 'd', 'X']
    
    for i, (metric_name, metric_path) in enumerate(OUTPUT_METRICS.items()):
        baseline_value = baseline_outputs.get(metric_name)
        if baseline_value is None or baseline_value == 0: continue
        
        absolute_values = [o.get(metric_name, np.nan) for o in outputs]
        normalized_values = [((val - baseline_value) / baseline_value) * 100 for val in absolute_values]
        
        label_text = LABEL_MAPPING.get(metric_path, metric_name)
        ax1.plot(inputs, normalized_values, marker=markers[i % len(markers)], 
                 linestyle='-', color=colors[i % len(colors)], label=label_text)

    ax1.grid(True, which='both', linestyle=':', linewidth=0.7, color='grey', alpha=0.6)
    ax1.axhline(0, color='black', linewidth=1, linestyle='--')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # --- Final Legend Styling (Corrected Method) ---
    # 1. Create the legend
    legend = ax1.legend(loc='best', frameon=True)
    
    # 2. Get the frame and apply styles to it
    frame = legend.get_frame()
    frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
    frame.set_facecolor('white')
    frame.set_edgecolor('black')
    frame.set_alpha(0.8)
    frame.set_linewidth(0.5)

    # 3. Set the zorder on the legend object itself
    legend.set_zorder(10)

    plt.tight_layout()
    filename = f"report_sensitivity_{param_path.replace('.', '_')}.pdf"
    save_path = os.path.join(plot_dir, filename)
    plt.savefig(save_path, transparent=False)
    print(f"Saved plot: {save_path}")
    plt.close(fig)


if __name__ == "__main__":
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'design_config.yaml')
    
    analysis_results, baseline_results = run_sensitivity_analysis(SENSITIVITY_CONFIG, config_file_path)

    # --- Smart Plotting ---
    for param, data in analysis_results.items():
        if param == 'wing.A_w_target':
            # Use the specialized plotter for aspect ratio
            plot_aspect_ratio_trade_study(data)
        else:
            # Use the general plotter for all other parameters
            plot_general_sensitivity_results(param, data, baseline_results)
    
    print("\nAnalysis and plotting complete.")