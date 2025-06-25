"""
MDAO Convergence Analysis and Visualization

This script analyzes the convergence results from the master design process
and creates visualizations showing parameter evolution and convergence behavior.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

def extract_convergence_data(output_text: str) -> Dict:
    """
    Extract convergence data from the master design process output.
    
    Parameters:
        output_text: The raw output from the design process
        
    Returns:
        Dictionary containing iteration data
    """
    
    # Manual extraction based on the provided output
    iterations = {
        'iteration': [1, 2],
        'W_OEW': [11277.0, 12377.7260],  # Starting values
        'W_TO': [27000.0, 28829.0220],   # Starting values
        'W_S': [3218.59, 3123.1440],    # Starting values  
        'T_W': [0.3050, 0.3159],        # Starting values
        'S_w': [8.3888, 9.2308],        # Starting values
        'A_w': [12.0, 12.0],            # Constant
        'CD0': [0.0172, 0.0254],        # Starting values
        
        # Final converged values for iteration 2
        'W_OEW_final': [12377.7260, 12402.2906],
        'W_TO_final': [28829.0220, 28869.5669],
        'W_S_final': [3123.1440, 3127.5364],
        'T_W_final': [0.3159, 0.3159],
        'S_w_final': [9.2308, 9.2308],
        'A_w_final': [12.0, 12.0],
        'CD0_final': [0.0254, 0.0254],
        
        # Convergence criteria (percentage changes)
        'rel_diff_W_OEW': [9.8, 0.2],
        'rel_diff_W_TO': [6.8, 0.1],
        'rel_diff_W_S': [3.0, 0.1],
        'rel_diff_T_W': [3.6, 0.0],
        'rel_diff_S_w': [10.0, 0.0],
        'rel_diff_A_w': [0.0, 0.0],
        'rel_diff_CD0': [48.0, 0.2],
        
        'converged': [False, True],
        'tolerance': 1.5  # 1.5% tolerance
    }
    
    return iterations

def create_parameter_evolution_plot(data: Dict) -> plt.Figure:
    """Create plots showing parameter evolution through iterations."""
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 10))
    fig.suptitle('MDAO Parameter Evolution Through Iterations', fontsize=16, fontweight='bold')
    
    # Parameters to plot
    params = [
        ('W_TO', 'Take-off Weight [N]', 'blue'),
        ('W_OEW', 'Operating Empty Weight [N]', 'green'), 
        ('W_S', 'Wing Loading [N/m²]', 'red'),
        ('T_W', 'Thrust-to-Weight Ratio [-]', 'purple'),
        ('S_w', 'Wing Area [m²]', 'orange'),
        ('A_w', 'Aspect Ratio [-]', 'brown'),
        ('CD0', 'Zero-Lift Drag Coefficient [-]', 'pink'),
        ('rel_diff_W_TO', 'W_TO Relative Change [%]', 'blue')
    ]
    
    iterations = data['iteration']
    
    for i, (param, ylabel, color) in enumerate(params):
        row = i // 4
        col = i % 4
        ax = axes[row, col]
        
        if param == 'rel_diff_W_TO':
            # Plot relative differences for convergence monitoring
            ax.plot(iterations, data[param], 'o-', color=color, linewidth=2, markersize=8)
            ax.axhline(y=data['tolerance'], color='red', linestyle='--', alpha=0.7, label='Tolerance (1.5%)')
            ax.legend()
        else:
            # Plot initial and final values
            initial_values = data[param]
            final_values = data[f'{param}_final']
            
            # Plot starting points
            ax.plot(iterations, initial_values, 'o-', color=color, linewidth=2, 
                   markersize=8, label='Start of iteration')
            
            # Plot final converged values
            ax.plot(iterations, final_values, 's--', color=color, alpha=0.7, 
                   linewidth=2, markersize=6, label='End of iteration')
            
            ax.legend(fontsize=8)
        
        ax.set_xlabel('Iteration')
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{param}')
        
        # Ensure we show both iteration points
        ax.set_xlim(0.5, 2.5)
        ax.set_xticks([1, 2])
    
    plt.tight_layout()
    return fig

def create_convergence_monitoring_plot(data: Dict) -> plt.Figure:
    """Create convergence monitoring plot showing all relative differences."""
    # Set scientific style font
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica'],
        'font.size': 14,
        'axes.titlesize': 14,
        'axes.labelsize': 14,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 14,
        'figure.titlesize': 16
    })
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('MDAO Convergence Monitoring', fontsize=16, fontweight='bold')
    
    # Parameters and their relative differences
    convergence_params = [
        ('W_OEW', 'rel_diff_W_OEW', 'Operating Empty Weight'),
        ('W_TO', 'rel_diff_W_TO', 'Take-off Weight'),
        ('W_S', 'rel_diff_W_S', 'Wing Loading'),
        ('T_W', 'rel_diff_T_W', 'Thrust-to-Weight'),
        ('S_w', 'rel_diff_S_w', 'Wing Area'),
        ('A_w', 'rel_diff_A_w', 'Aspect Ratio'),
        ('CD0', 'rel_diff_CD0', 'Zero-Lift Drag')
    ]
    
    iterations = data['iteration']
    tolerance = data['tolerance']
    
    # Plot 1: All relative differences on log scale
    colors = plt.cm.tab10(np.linspace(0, 1, len(convergence_params)))
    
    for i, (param, rel_diff_param, label) in enumerate(convergence_params):
        rel_diffs = data[rel_diff_param]
        ax1.plot(iterations, rel_diffs, 'o-', color=colors[i], linewidth=2, 
                markersize=6, label=label)
    
    ax1.axhline(y=tolerance, color='red', linestyle='--', linewidth=2, 
               alpha=0.8, label=f'Tolerance ({tolerance}%)')
    ax1.set_xlabel('Iteration', fontsize=14)
    ax1.set_ylabel('Relative Change [%]', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right', fontsize=14)
    ax1.set_xlim(0.5, 2.5)
    ax1.set_xticks([1, 2])
    
    # Plot 2: Convergence status (pass/fail)
    param_names = [label for _, _, label in convergence_params]
    iteration_1_status = [data[rel_diff][0] <= tolerance for _, rel_diff, _ in convergence_params]
    iteration_2_status = [data[rel_diff][1] <= tolerance for _, rel_diff, _ in convergence_params]
    
    x = np.arange(len(param_names))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, iteration_1_status, width, label='Iteration 1', 
                   color='lightcoral', alpha=0.8)
    bars2 = ax2.bar(x + width/2, iteration_2_status, width, label='Iteration 2', 
                   color='lightgreen', alpha=0.8)
    
    ax2.set_xlabel('Design Parameters')
    ax2.set_ylabel('Converged (1=Yes, 0=No)')
    ax2.set_title('Convergence Status by Parameter')
    ax2.set_xticks(x)
    ax2.set_xticklabels(param_names, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(-0.1, 1.1)
    
    # Add value labels on bars
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        height1 = bar1.get_height()
        height2 = bar2.get_height()
        if height1:
            ax2.text(bar1.get_x() + bar1.get_width()/2., height1 + 0.02, '✓',
                    ha='center', va='bottom', fontweight='bold', color='green')
        else:
            ax2.text(bar1.get_x() + bar1.get_width()/2., height1 + 0.02, '✗',
                    ha='center', va='bottom', fontweight='bold', color='red')
            
        if height2:
            ax2.text(bar2.get_x() + bar2.get_width()/2., height2 + 0.02, '✓',
                    ha='center', va='bottom', fontweight='bold', color='green')
        else:
            ax2.text(bar2.get_x() + bar2.get_width()/2., height2 + 0.02, '✗',
                    ha='center', va='bottom', fontweight='bold', color='red')
    
    plt.tight_layout()
    return fig

# def create_design_space_exploration_plot() -> plt.Figure:
#     """Create a plot showing how different objective functions affect design."""
    
#     fig, axes = plt.subplots(1, 3, figsize=(15, 5))
#     fig.suptitle('Impact of Different Objective Functions on Wing Design', fontsize=14, fontweight='bold')
    
#     # Data from the wing planform comparison (from Image 4)
#     design_cases = {
#         'Baseline Design': {'A_w': 11.0, 'fuel_weight': 10800, 'LD_ratio': 15.2, 'color': 'blue'},
#         'Fuel Optimized': {'A_w': 12.0, 'fuel_weight': 10400, 'LD_ratio': 16.8, 'color': 'red'},
#         'High L/D': {'A_w': 13.2, 'fuel_weight': 10600, 'LD_ratio': 17.5, 'color': 'green'},
#         'Low Weight': {'A_w': 9.5, 'fuel_weight': 11200, 'LD_ratio': 14.8, 'color': 'orange'}
#     }
    
#     # Plot 1: Aspect Ratio vs Fuel Weight
#     ax1 = axes[0]
#     for name, data in design_cases.items():
#         ax1.scatter(data['A_w'], data['fuel_weight'], c=data['color'], s=100, 
#                    label=name, alpha=0.8, edgecolors='black')
    
#     ax1.set_xlabel('Wing Aspect Ratio [-]')
#     ax1.set_ylabel('Mission Fuel Weight [N]')
#     ax1.set_title('Aspect Ratio vs Fuel Weight')
#     ax1.grid(True, alpha=0.3)
#     ax1.legend()
    
#     # Plot 2: Aspect Ratio vs L/D
#     ax2 = axes[1]
#     for name, data in design_cases.items():
#         ax2.scatter(data['A_w'], data['LD_ratio'], c=data['color'], s=100, 
#                    label=name, alpha=0.8, edgecolors='black')
    
#     ax2.set_xlabel('Wing Aspect Ratio [-]')
#     ax2.set_ylabel('Lift-to-Drag Ratio [-]')
#     ax2.set_title('Aspect Ratio vs L/D Ratio')
#     ax2.grid(True, alpha=0.3)
    
#     # Plot 3: Trade-off visualization
#     ax3 = axes[2]
#     for name, data in design_cases.items():
#         ax3.scatter(data['LD_ratio'], data['fuel_weight'], c=data['color'], s=100, 
#                    label=name, alpha=0.8, edgecolors='black')
    
#     ax3.set_xlabel('Lift-to-Drag Ratio [-]')
#     ax3.set_ylabel('Mission Fuel Weight [N]')
#     ax3.set_title('L/D vs Fuel Weight Trade-off')
#     ax3.grid(True, alpha=0.3)
    
#     # Add arrows showing the Pareto front concept
#     ax3.annotate('Better Performance\n(Higher L/D)', xy=(17.2, 10300), xytext=(16.5, 10200),
#                 arrowprops=dict(arrowstyle='->', color='green', lw=2))
#     ax3.annotate('Lower Fuel Burn', xy=(16.5, 10300), xytext=(15.5, 10100),
#                 arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    
#     plt.tight_layout()
#     return fig

# def print_convergence_summary(data: Dict):
#     """Print a summary of the convergence results."""
    
#     print("="*80)
#     print("MDAO CONVERGENCE ANALYSIS SUMMARY")
#     print("="*80)
    
#     print(f"\nTolerance: {data['tolerance']}%")
#     print(f"Total Iterations: {len(data['iteration'])}")
#     print(f"Converged: {'Yes' if data['converged'][-1] else 'No'}")
    
#     print(f"\nFinal Design Parameters:")
#     print(f"  Take-off Weight (W_TO):     {data['W_TO_final'][-1]:8.1f} N")
#     print(f"  Operating Empty Weight:     {data['W_OEW_final'][-1]:8.1f} N") 
#     print(f"  Wing Loading (W/S):         {data['W_S_final'][-1]:8.1f} N/m²")
#     print(f"  Thrust-to-Weight (T/W):     {data['T_W_final'][-1]:8.4f}")
#     print(f"  Wing Area (S_w):            {data['S_w_final'][-1]:8.2f} m²")
#     print(f"  Aspect Ratio (A_w):         {data['A_w_final'][-1]:8.1f}")
#     print(f"  Zero-Lift Drag (CD0):       {data['CD0_final'][-1]:8.6f}")
    
#     print(f"\nFinal Iteration Relative Changes:")
#     convergence_params = ['W_OEW', 'W_TO', 'W_S', 'T_W', 'S_w', 'A_w', 'CD0']
#     for param in convergence_params:
#         rel_diff = data[f'rel_diff_{param}'][-1]
#         status = "✓ PASS" if rel_diff <= data['tolerance'] else "✗ FAIL"
#         print(f"  {param:<6}: {rel_diff:6.1f}% {status}")
    
#     print("\n" + "="*80)

def main():
    """Main execution function."""
    
    # For this example, we'll use the provided output data
    # In practice, you would load this from the actual output file
    output_text = ""  # The raw output would go here
    
    # Extract convergence data
    data = extract_convergence_data(output_text)
    
    # Print summary
    # print_convergence_summary(data)
    
    # Create visualizations
    print("Creating convergence visualizations...")
    
    # Parameter evolution plot
    fig1 = create_parameter_evolution_plot(data)
    fig1.savefig('mdao_parameter_evolution.png', dpi=300, bbox_inches='tight')
    print("  Saved: mdao_parameter_evolution.png")
    
    # Convergence monitoring plot  
    fig2 = create_convergence_monitoring_plot(data)
    fig2.savefig('mdao_convergence_monitoring.png', dpi=300, bbox_inches='tight')
    print("  Saved: mdao_convergence_monitoring.png")
    
    # Design space exploration plot
    # fig3 = create_design_space_exploration_plot()
    # fig3.savefig('mdao_design_space_exploration.png', dpi=300, bbox_inches='tight')
    # print("  Saved: mdao_design_space_exploration.png")
    
    # Show plots
    plt.show()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()