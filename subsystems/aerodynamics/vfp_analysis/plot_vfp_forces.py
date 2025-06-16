import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from vfp_aoa_sweep import wing_name

# ==============================================================================
# 1. DEFINE PLOTTING PARAMETERS
# ==============================================================================
# This script should be placed in the root project folder.

# --- Main Control ---
# Specify the name of the wing you want to plot the results for.
wing_name_to_plot = wing_name  # Reference the wing name from vfp_sweep.py

# --- Plotting Options ---
save_plots = True # Set to True to save the plots as image files
plot_file_format = 'png' # 'png', 'pdf', 'svg', etc.

# ==============================================================================
# 2. HELPER AND PARSING FUNCTIONS
# ==============================================================================

def parse_case_name(case_name):
    """Parses a run folder name to extract wing_name, mach, alpha, and re identifiers."""
    try:
        # Updated pattern to handle optional underscores between components and enforce full string match
        pattern = r"^(.+?)_?(m\d+(?:\.\d+)?)_?(a[m]?\d+(?:_?\d+)?(?:p\d+)?)_?(re\d+(?:m\d+)?)$"
        match = re.match(pattern, case_name)
        
        if match:
            wing_id, mach_id, alpha_id, re_id = match.groups()
            
            # Extract Mach number
            mach_val = float(mach_id[1:]) / 100  # Convert m025 to 0.25
            
            # Handle alpha values with improved parsing
            alpha_val = None
            if alpha_id.startswith('am'):  # Negative angles
                alpha_str = alpha_id[2:].replace('_', '.').replace('p', '.')
                alpha_val = -float(alpha_str)
            else:  # Positive angles
                alpha_str = alpha_id[1:].replace('_', '.').replace('p', '.')
                alpha_val = float(alpha_str)
            
            return {
                "wing_id": wing_id,
                "mach_id": mach_id,
                "mach_val": mach_val,
                "alpha_id": alpha_id,
                "re_id": re_id,
                "alpha_val": alpha_val,
                "full_name": case_name
            }
        
        print(f"Warning: Case name '{case_name}' didn't match expected pattern")
        return None
        
    except Exception as e:
        print(f"Error parsing case name '{case_name}': {e}")
        return None

def parse_forces_file_to_numpy(file_path):
    """
    Parses a VFP .forces file into a clean NumPy array for analysis and plotting.
    This function handles the multi-block, fixed-width format of the output file.
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Find the last block with force data (look for LEV= marker)
        force_block_start = -1
        for i, line in enumerate(reversed(lines)):
            if "LEV= " in line:
                force_block_start = len(lines) - i
                break
        
        if force_block_start == -1:
            return None
        
        # Skip header lines to get to the data
        data_start = force_block_start + 3
        
        # Parse the force data block
        force_data = []
        for line in lines[data_start:]:
            if "CLTOT" in line:
                break
            try:
                parts = line.split()
                if len(parts) >= 8 and parts[0].strip().isdigit():
                    j, yave, cl, cd, cm = int(parts[0]), float(parts[1]), float(parts[5]), float(parts[6]), float(parts[7])
                    force_data.append([yave, cl, None, None, cm])  # Placeholder None for CD values
            except:
                continue
        
        # Find the viscous drag data block
        visc_block_start = -1
        for i, line in enumerate(lines):
            if "VISCOUS DRAG DATA" in line:
                visc_block_start = i + 3
                break
                
        if visc_block_start == -1:
            return None
            
        # Parse the viscous drag data and merge with force data
        for line in lines[visc_block_start:]:
            if "Total viscous drag" in line:
                break
            try:
                parts = line.split()
                if len(parts) >= 8 and parts[0].strip().isdigit():
                    j = int(parts[0])
                    cd_wake = float(parts[6])
                    cd_te = float(parts[8])
                    # Update the corresponding force data entry (j-2 because of indexing)
                    if 0 <= j-2 < len(force_data):
                        force_data[j-2][2] = cd_wake
                        force_data[j-2][3] = cd_te
            except:
                continue
        
        # Convert to numpy array and remove any rows with None values
        result = np.array(force_data)
        result = result[~np.any(np.equal(result, None), axis=1)]
        
        return result

    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return None

def parse_integrated_forces(file_path):
    """Extracts integrated force coefficients from a .forces file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the last occurrence of force coefficients (in case of multiple iterations)
        matches = {
            'CLTOT_VFP': re.findall(r'CLTOT\(VFP\)=\s*([-+]?\d*\.\d+)', content),
            'CDTOT_VFP': re.findall(r'CDTOT\(VFP\)=\s*([-+]?\d*\.\d+)', content),
            'CMTOT_VFP': re.findall(r'CMTOT\(VFP\)=\s*([-+]?\d*\.\d+)', content),
            'CLTOT_IBE': re.findall(r'CLTOT\(IBE\)=\s*([-+]?\d*\.\d+)', content),
            'CDTOT_IBE': re.findall(r'CDTOT\(IBE\)=\s*([-+]?\d*\.\d+)', content),
        }
        
        return {k: float(v[-1]) for k, v in matches.items() if v}
    except Exception as e:
        print(f"Error parsing integrated forces from {file_path}: {e}")
        return None

# ==============================================================================
# 3. PLOTTING FUNCTION
# ==============================================================================

# Set up Seaborn style
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.1)

# Additional matplotlib customization
plt.rcParams.update({
    'figure.figsize': (10, 12),
    'font.family': 'serif',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'lines.markersize': 4,
    'lines.linewidth': 1.5
})

def plot_spanwise_loading(wing_name, all_case_data, mach_number):
    """
    Generates and displays plots from a dictionary of NumPy arrays.
    """
    if not all_case_data:
        print("No data to plot.")
        return

    # Set up color-blind friendly palette
    n_colors = len(all_case_data)
    colors = sns.color_palette("colorblind", n_colors)
    
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))
    fig.suptitle(f'Spanwise Loading Distributions\nWing Case: {wing_name.upper()}, M = {mach_number:.3f}', 
                 fontsize=16, y=0.95, fontweight='bold')
    
    # Sort cases by alpha value
    sorted_cases = sorted(all_case_data.items())

    for i, (alpha, data_array) in enumerate(sorted_cases):
        label = f'alpha = {alpha:+.1f}°'
        color = colors[i]
        
        y_s = data_array[:, 0]
        cll = data_array[:, 1]
        cd_wake = data_array[:, 2]
        cd_te = data_array[:, 3]
        cml = data_array[:, 4]

        # Plot with improved styling and markers for better distinction
        axes[0].plot(y_s, cll, marker='o', linestyle='-', markersize=4, 
                    label=label, color=color, linewidth=1.5, markerfacecolor='white')
        
        axes[1].plot(y_s, cd_wake, marker='o', linestyle='-', markersize=4,
                    label=f'{label}', color=color, linewidth=1.5, markerfacecolor='white')
        # Use different marker and pattern for TE data
        axes[1].plot(y_s, cd_te, marker='s', linestyle=':', markersize=4,
                    color=color, alpha=0.7, linewidth=1.5, markerfacecolor='white',
                    label=f'{label} (TE)')
        
        axes[2].plot(y_s, cml, marker='o', linestyle='-', markersize=4, 
                    label=label, color=color, linewidth=1.5, markerfacecolor='white')

    # Customize each subplot
    for ax in axes:
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(direction='out')
        ax.set_xlim(0, max(data_array[:, 0])*1.05)

    # Customize titles and labels
    axes[0].set_ylabel('Section Lift Coefficient ($C_{l}$)')
    axes[0].set_title('Spanwise Lift Distribution', pad=10)
    
    axes[1].set_ylabel('Section Viscous Drag Coefficient ($C_{d,v}$)')
    axes[1].set_title('Spanwise Viscous Drag Distribution\n(Solid=Wake Profile, Dashed=Trailing Edge)', pad=10)
    
    axes[2].set_ylabel('Section Pitching Moment ($C_{m}$)')
    axes[2].set_title('Spanwise Pitching Moment Distribution', pad=10)
    axes[2].set_xlabel('Non-dimensional Spanwise Position ($y/s$)')

    # Customize legends
    for ax in axes:
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', 
                 borderaxespad=0, frameon=True, fancybox=True, 
                 shadow=True, ncol=1)

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])
    
    if save_plots:
        # Create directory if it doesn't exist
        script_root = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(script_root, "results", wing_name)
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, f"{wing_name}_m{int(mach_number*100):03d}_spanwise_plots.{plot_file_format}")
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"\nPlots saved to: {save_path}")

    # plt.show()

def plot_aero_curves(wing_name, all_case_data, mach_number):
    """Plots lift curve, moment curve, and drag polar."""
    if not all_case_data:
        print("No data to plot.")
        return
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Aerodynamic Characteristics\nWing Case: {wing_name.upper()}, M = {mach_number:.3f}', 
                 fontsize=16, y=1.05, fontweight='bold')
    
    # Extract data for plotting
    alphas = []
    cl_vfp = []
    cl_ibe = []
    cm_vfp = []
    cd_ibe = []
    
    for case_name, forces in all_case_data.items():
        alphas.append(case_name)
        cl_vfp.append(forces['CLTOT_VFP'])
        cl_ibe.append(forces['CLTOT_IBE'])
        cm_vfp.append(forces['CMTOT_VFP'])
        cd_ibe.append(forces['CDTOT_IBE'])
    
    # Sort all data by alpha
    sorted_data = sorted(zip(alphas, cl_vfp, cl_ibe, cm_vfp, cd_ibe))
    alphas, cl_vfp, cl_ibe, cm_vfp, cd_ibe = zip(*sorted_data)
    
    # Plot lift curve
    ax1.plot(alphas, cl_vfp, 'o-', label='VFP', color='blue', markerfacecolor='white')
    ax1.plot(alphas, cl_ibe, 's--', label='IBE', color='red', markerfacecolor='white')
    ax1.set_xlabel('Angle of Attack [deg]')
    ax1.set_ylabel('Lift Coefficient [-]')
    ax1.set_title('Lift Curve')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()
    
    # Plot moment curve
    ax2.plot(alphas, cm_vfp, 'o-', color='green', markerfacecolor='white')
    ax2.set_xlabel('Angle of Attack [deg]')
    ax2.set_ylabel('Moment Coefficient [-]')
    ax2.set_title('Moment Curve')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Plot drag polar
    ax3.plot(cd_ibe, cl_ibe, 'o-', color='purple', markerfacecolor='white')
    ax3.set_xlabel('Drag Coefficient [-]')
    ax3.set_ylabel('Lift Coefficient [-]')
    ax3.set_title('Drag Polar (IBE)')
    ax3.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if save_plots:
        # Create directory if it doesn't exist
        script_root = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(script_root, "results", wing_name)
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, f"{wing_name}_m{int(mach_number*100):03d}_aero_curves.{plot_file_format}")
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"Aero curves saved to: {save_path}")

    # plt.show()

def run_plots():
    script_root = os.path.dirname(os.path.abspath(__file__))
    wing_results_dir = os.path.join(script_root, "results", wing_name_to_plot)

    if not os.path.isdir(wing_results_dir):
        print(f"❌ ERROR: Results directory for wing '{wing_name_to_plot}' not found.")
    else:
        print(f"Analyzing results for wing: {wing_name_to_plot}")
        
        # Group data by Mach number
        mach_data = {}  # Dict of format {mach_number: {alpha: numpy_data}}
        mach_forces = {}  # Dict of format {mach_number: {alpha: forces}}
        
        for item in os.listdir(wing_results_dir):
            item_path = os.path.join(wing_results_dir, item)
            if os.path.isdir(item_path) and item not in ["geometry_master", "ANALYSIS_RESULTS"]:
                case_data = parse_case_name(item)
                if case_data:
                    mach = case_data['mach_val']
                    alpha = case_data['alpha_val']
                    forces_file_path = os.path.join(item_path, f"{case_data['full_name']}.forces")
                    
                    if os.path.exists(forces_file_path):
                        # Handle numpy data for spanwise plots
                        numpy_data = parse_forces_file_to_numpy(forces_file_path)
                        # numpy_data structure: array([[y_pos, cl, cd_wake, cd_te, cm], ...])
                        #   where: y_pos = spanwise position (y/s)
                        #         cl = section lift coefficient
                        #         cd_wake = section viscous drag coefficient (wake)
                        #         cd_te = section viscous drag coefficient (trailing edge)
                        #         cm = section moment coefficient
                        if numpy_data is not None:
                            if mach not in mach_data:
                                mach_data[mach] = {}
                            mach_data[mach][alpha] = numpy_data
                        
                        # Handle forces data for aero curves
                        forces = parse_integrated_forces(forces_file_path)
                        if forces:
                            if mach not in mach_forces:
                                mach_forces[mach] = {}
                            mach_forces[mach][alpha] = forces
        
        if mach_data:
            print(f"\nFound data for Mach numbers: {sorted(mach_data.keys())}")
            
            # Generate plots for each Mach number
            for mach_number in sorted(mach_data.keys()):
                print(f"\nGenerating plots for Mach {mach_number:.3f}")
                plot_spanwise_loading(wing_name_to_plot, mach_data[mach_number], mach_number)
                plot_aero_curves(wing_name_to_plot, mach_forces[mach_number], mach_number)
        
        else:
            print("\n❌ No valid .forces files were found to plot.")

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    run_plots()