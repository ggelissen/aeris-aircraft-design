import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

def plot_wing_planform_comparison(configurations):
    """
    Plot multiple wing planforms overlaid for comparison.
    Shows how different optimization objectives lead to different wing shapes.
    
    Parameters:
    configurations: list of dicts, each containing wing geometry parameters
    """
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    axes = [ax1, ax2, ax3, ax4]
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    for i, config in enumerate(configurations[:len(axes)]):
        ax = axes[i]
        
        # Extract wing parameters
        b_w = config['wingspan']  # Wing span
        c_root = config['root_chord']  # Root chord
        c_tip = config['tip_chord']  # Tip chord
        sweep_LE = config['sweep_LE']  # Leading edge sweep angle (radians)
        
        # Calculate wing coordinates
        # Leading edge points
        LE_root_x = 0
        LE_root_y = 0
        LE_tip_x = (b_w/2) * np.tan(sweep_LE)
        LE_tip_y = b_w/2
        
        # Trailing edge points
        TE_root_x = c_root
        TE_root_y = 0
        TE_tip_x = LE_tip_x + c_tip
        TE_tip_y = b_w/2
        
        # Right wing coordinates
        right_wing_x = [LE_root_x, LE_tip_x, TE_tip_x, TE_root_x, LE_root_x]
        right_wing_y = [LE_root_y, LE_tip_y, TE_tip_y, TE_root_y, LE_root_y]
        
        # Left wing coordinates (mirror)
        left_wing_x = [LE_root_x, LE_tip_x, TE_tip_x, TE_root_x, LE_root_x]
        left_wing_y = [LE_root_y, -LE_tip_y, -TE_tip_y, -TE_root_y, -LE_root_y]
        
        # Plot the wing planform
        color = colors[i % len(colors)]
        ax.fill(right_wing_x, right_wing_y, color=color, alpha=0.6, 
                label=f"{config['name']}")
        ax.fill(left_wing_x, left_wing_y, color=color, alpha=0.6)
        ax.plot(right_wing_x, right_wing_y, color='black', linewidth=1.5)
        ax.plot(left_wing_x, left_wing_y, color='black', linewidth=1.5)
        
        # Add centerline
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Set equal aspect ratio and labels
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Chordwise Distance [m]')
        ax.set_ylabel('Spanwise Distance [m]')
        # Remove units from the ax
        ax.legend(loc = 'upper right', fontsize=10)
        
        # Add configuration details as text
        details = f"""A_w = {config['aspect_ratio']:.1f}
S_w = {config['wing_area']:.1f} m²
Sweep = {np.rad2deg(config['sweep_LE']):.1f}°
Fuel = {config['fuel_weight']:.0f} N
L/D = {config['L_D']:.1f}"""
        
        ax.text(0.02, 0.98, details, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='white', alpha=0.8), fontsize=9)
        
        ax.set_title(f"{config['name']}\n({config['optimization_objective']})")
    
    plt.suptitle('Wing Planform Comparison - Different Optimization Objectives', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

def plot_planform_overlay_comparison(configurations):
    """
    Plot all wing planforms overlaid on a single plot for direct comparison.
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    alphas = [0.7, 0.6, 0.5, 0.5, 0.5, 0.5]  # Make first config more prominent
    
    max_span = 0
    max_chord = 0
    
    for i, config in enumerate(configurations):
        # Extract wing parameters
        b_w = config['wingspan']
        c_root = config['root_chord']
        c_tip = config['tip_chord']
        sweep_LE = config['sweep_LE']
        
        max_span = max(max_span, b_w)
        max_chord = max(max_chord, c_root)
        
        # Calculate wing coordinates
        LE_root_x = 0
        LE_root_y = 0
        LE_tip_x = (b_w/2) * np.tan(sweep_LE)
        LE_tip_y = b_w/2
        
        TE_root_x = c_root
        TE_root_y = 0
        TE_tip_x = LE_tip_x + c_tip
        TE_tip_y = b_w/2
        
        # Right wing coordinates
        right_wing_x = [LE_root_x, LE_tip_x, TE_tip_x, TE_root_x, LE_root_x]
        right_wing_y = [LE_root_y, LE_tip_y, TE_tip_y, TE_root_y, LE_root_y]
        
        # Left wing coordinates
        left_wing_x = [LE_root_x, LE_tip_x, TE_tip_x, TE_root_x, LE_root_x]
        left_wing_y = [LE_root_y, -LE_tip_y, -TE_tip_y, -TE_root_y, -LE_root_y]
        
        # Plot with different styles for better visibility
        color = 'red'#colors[i % len(colors)]
        alpha = 0.5#alphas[i % len(alphas)]
        linewidth = 3 if i == 2 else 2  # Emphasize first configuration
        linestyle = '-' if i == 2 else '--'
        
        ax.fill(right_wing_x, right_wing_y, color=color, alpha=alpha, 
                label=f"{config['name']} (A_w={config['aspect_ratio']:.1f})")
        ax.fill(left_wing_x, left_wing_y, color=color, alpha=alpha)
        ax.plot(right_wing_x, right_wing_y, color=color, linewidth=linewidth, 
                linestyle=linestyle)
        ax.plot(left_wing_x, left_wing_y, color=color, linewidth=linewidth, 
                linestyle=linestyle)
    
    # Add centerline
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.7, linewidth=1)
    
    # Formatting
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('Chordwise Distance [m]', fontsize=12)
    ax.set_ylabel('Spanwise Distance [m]', fontsize=12)
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    ax.set_title('Wing Planform Overlay Comparison\nOptimized for Different Objectives', 
                 fontsize=14, fontweight='bold')
    
    # Set reasonable limits
    #ax.set_xlim(-1, max_chord * 1.1)
    #ax.set_ylim(-max_span * 0.6, max_span * 0.6)
    
    plt.tight_layout()
    plt.show()

def plot_optimization_convergence(convergence_data):
    """
    Plot the optimization convergence showing how the algorithm finds the optimum.
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    iterations = convergence_data['iterations']
    fuel_weights = convergence_data['fuel_weights']
    L_D_values = convergence_data['L_D_values']
    aspect_ratios = convergence_data['aspect_ratios']
    wing_areas = convergence_data['wing_areas']
    
    # Fuel weight convergence
    ax1.plot(iterations, fuel_weights, 'bo-', linewidth=2, markersize=6)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Fuel Weight [N]')
    ax1.set_title('Fuel Weight Convergence')
    ax1.grid(True, alpha=0.3)
    
    # L/D convergence
    ax2.plot(iterations, L_D_values, 'ro-', linewidth=2, markersize=6)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('L/D Cruise Ratio')
    ax2.set_title('L/D Optimization Progress')
    ax2.grid(True, alpha=0.3)
    
    # Parameter evolution
    ax3.plot(iterations, aspect_ratios, 'go-', linewidth=2, markersize=6, label='Aspect Ratio')
    ax3_twin = ax3.twinx()
    ax3_twin.plot(iterations, wing_areas, 'mo-', linewidth=2, markersize=6, label='Wing Area [m²]')
    ax3.set_xlabel('Iteration')
    ax3.set_ylabel('Aspect Ratio', color='g')
    ax3_twin.set_ylabel('Wing Area [m²]', color='m')
    ax3.set_title('Design Parameter Evolution')
    ax3.grid(True, alpha=0.3)
    
    # 2D parameter space exploration
    ax4.scatter(aspect_ratios, wing_areas, c=fuel_weights, cmap='viridis', 
                s=60, alpha=0.7)
    colorbar = plt.colorbar(ax4.collections[0], ax=ax4)
    colorbar.set_label('Fuel Weight [N]')
    
    # Mark optimal point
    min_fuel_idx = np.argmin(fuel_weights)
    ax4.scatter(aspect_ratios[min_fuel_idx], wing_areas[min_fuel_idx], 
                color='red', s=200, marker='*', label='Optimal Point')
    
    ax4.set_xlabel('Aspect Ratio')
    ax4.set_ylabel('Wing Area [m²]')
    ax4.set_title('Parameter Space Exploration')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle('Wing Optimization Convergence Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Sample wing configurations from different optimization objectives
    wing_configs = [
        # {
        #     'name': 'Baseline Design',
        #     'optimization_objective': 'Initial Configuration',
        #     'wingspan': 11.0,
        #     'root_chord': 1.2,
        #     'tip_chord': 0.6,
        #     'sweep_LE': np.deg2rad(25),
        #     'aspect_ratio': 11.0,
        #     'wing_area': 10.5,
        #     'fuel_weight': 9800,
        #     'L_D': 18.5
        # },
        {
            'name': 'Fuel Optimized',
            'optimization_objective': 'Minimum Fuel Burn',
            'wingspan': 11.5,
            'root_chord': 1.1,
            'tip_chord': 0.55,
            'sweep_LE': np.deg2rad(22),
            'aspect_ratio': 12.0,
            'wing_area': 11.2,
            'fuel_weight': 9650,
            'L_D': 19.8
        }
        # {
        #     'name': 'High L/D',
        #     'optimization_objective': 'Maximum L/D',
        #     'wingspan': 12.8,
        #     'root_chord': 0.95,
        #     'tip_chord': 0.48,
        #     'sweep_LE': np.deg2rad(18),
        #     'aspect_ratio': 13.2,
        #     'wing_area': 12.4,
        #     'fuel_weight': 9720,
        #     'L_D': 21.2
        # },
        # {
        #     'name': 'Low Weight',
        #     'optimization_objective': 'Minimum Wing Weight',
        #     'wingspan': 9.8,
        #     'root_chord': 1.35,
        #     'tip_chord': 0.67,
        #     'sweep_LE': np.deg2rad(28),
        #     'aspect_ratio': 9.5,
        #     'wing_area': 10.1,
        #     'fuel_weight': 9880,
        #     'L_D': 17.6
        # }
    ]
    
    # Sample convergence data
    convergence_data = {
        'iterations': np.arange(1, 21),
        'fuel_weights': np.array([9900, 9850, 9800, 9780, 9720, 9700, 9680, 9670, 9665, 9660,
                                 9658, 9656, 9655, 9654, 9653, 9652, 9651, 9650, 9650, 9650]),
        'L_D_values': np.array([17.5, 17.8, 18.2, 18.5, 18.9, 19.2, 19.4, 19.6, 19.7, 19.8,
                               19.82, 19.83, 19.84, 19.85, 19.85, 19.85, 19.85, 19.85, 19.85, 19.85]),
        'aspect_ratios': np.array([11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.65, 11.7, 11.75,
                                  11.76, 11.77, 11.78, 11.79, 11.8, 11.8, 11.8, 11.8, 11.8, 11.8]),
        'wing_areas': np.array([10.0, 10.2, 10.4, 10.6, 10.8, 11.0, 11.1, 11.15, 11.18, 11.2,
                               11.21, 11.21, 11.21, 11.2, 11.2, 11.2, 11.2, 11.2, 11.2, 11.2])
    }
    
    print("Generating Wing Planform Comparison...")
    #plot_wing_planform_comparison(wing_configs)
    
    print("Generating Planform Overlay...")
    plot_planform_overlay_comparison(wing_configs)
    
    print("Generating Convergence Analysis...")
    #plot_optimization_convergence(convergence_data)