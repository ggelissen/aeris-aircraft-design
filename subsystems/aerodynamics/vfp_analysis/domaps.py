import os
import subprocess
import shutil
import matplotlib.pyplot as plt
import numpy as np
import re

# ==============================================================================
# 1. DEFINE CRANKED WING STUDY PARAMETERS
# ==============================================================================
# --- Main Simulation Control ---
# This wing_name MUST match the one used to generate the initial geometry
# so the script can find the 'geometry_master' folder.
wing_name = "w11-multi-airfoil" 

# Location of the VFP/FPCON executables (find.exe, maponly.exe, gridproc.exe)
# Assumes executables are in a subdirectory named 'vpwin_fpv20' relative to the script.
vfp_tools_source_dir = os.path.join(os.path.dirname(__file__), "vpwin_fpv20")

# --- Grid Study Parameters for Cranked Wing ---
# As per ESDU 02014a, Section 7.4, we vary MBAR and B16(2).
mbar_values_to_test = [8, 16, 24]
b16_2_values_to_test = [0.01, 0.15, 0.50]

# YSLOP1 is a key parameter for cranked wings. Set a single value for the study.
YSLOP1_val = 1.728 

# Define the approximate non-dimensional (eta) location of the crank.
# This is used to center the zoomed-in plot.
crank_eta_location = 0.4

# These are standard values, typically not changed for this type of study.
M_val = 38
MOB_val = 8.5 # Number of grid intervals outboard of the tip

# ==============================================================================
# 2. HELPER AND WORKFLOW FUNCTIONS
# ==============================================================================

def prepare_study_directory(base_dir, wing_name, tools_src_dir):
    """
    Creates a clean directory for the grid study, copies the baseline
    GEO.DAT and MAP.DAT from the 'geometry_master' folder, and also
    copies the required VFP executables.
    """
    study_dir = os.path.join(base_dir, "results", f"{wing_name}_cranked_grid_study")
    geometry_master_dir = os.path.join(base_dir, "results", wing_name, "geometry_master")

    print(f"--- Looking for baseline geometry in: {geometry_master_dir} ---")
    if not os.path.isdir(geometry_master_dir):
        print(f"ERROR: Baseline geometry directory not found. Please run the initial geometry generation first.")
        return None
    
    # Create the new study directory
    if os.path.exists(study_dir): shutil.rmtree(study_dir)
    os.makedirs(study_dir)
    print(f"Created study directory: {study_dir}")

    # Copy required executables
    try:
        for item in ['FIND.exe', 'MAPONLY.exe', 'GRIDPROC.exe']:
            shutil.copy(os.path.join(tools_src_dir, item), study_dir)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find a required tool executable: {e.filename}")
        return None
    
    # Copy the baseline GEO.DAT and MAP.DAT files
    for f in ["GEO.DAT", "MAP.DAT"]:
        try:
            shutil.copy(os.path.join(geometry_master_dir, f), study_dir)
        except FileNotFoundError as e:
            print(f"ERROR: Could not find baseline file: {e.filename}")
            return None
    print("Copied baseline GEO.DAT and MAP.DAT.")
        
    return study_dir

def run_grid_variation(study_dir, mbar, b16_2, yslop1):
    """
    Runs the grid generation process for a single combination of parameters.
    This function prepares input files, runs the Fortran executables,
    and saves the resulting grid files. It ensures the original MAP.DAT
    is restored after each run.
    """
    case_name = f"mbar{mbar}_b16_2_{b16_2:.2f}".replace('.', 'p')
    print(f"\n--- Processing variation: {case_name} ---")

    # Define paths to working files
    working_map = os.path.join(study_dir, "MAP.DAT")
    working_map_new = os.path.join(study_dir, "mapnew.dat")
    working_map_backup = os.path.join(study_dir, "MAP.DAT.bak")
    range_file = os.path.join(study_dir, "RANGE.DAT")
    mbarb2_file = os.path.join(study_dir, "mbarb2.dat")

    if not os.path.exists(working_map):
        print(f"ERROR: MAP.DAT not found in {study_dir}")
        return None

    # Create a backup of the original MAP.DAT to be restored later
    shutil.copy2(working_map, working_map_backup)

    try:
        # --- Prepare all input files for FIND.exe ---

        # Create RANGE.DAT with correct line endings
        with open(range_file, "w", newline='\r\n') as f:
            f.write(f"{M_val}\r\n")
            f.write(f"{mbar}\r\n")
            f.write(f"{b16_2}\r\n")
            f.write(f"{MOB_val}\r\n")
            f.write(f"{yslop1}\r\n")
        
        # Create mbarb2.dat with fixed-width formatting.
        with open(mbarb2_file, "w", newline='\r\n') as f:
            f.write(f"{mbar:5d}{b16_2:10.6f}\r\n")

        # Create mapnew.dat as a copy of MAP.DAT *before* running FIND.exe.
        shutil.copy2(working_map, working_map_new)
        
        # --- Run the Fortran Executables ---
        subprocess.run('FIND.exe', shell=True, cwd=study_dir, check=True, capture_output=True, text=True)
        
        if not os.path.exists(working_map_new):
             print(f"   ERROR: FIND.exe did not create/modify mapnew.dat. Aborting this case.")
             return None
        
        # Replace the original MAP.DAT with the newly generated one for the next steps
        os.remove(working_map)
        os.rename(working_map_new, working_map)
        
        subprocess.run('MAPONLY.exe', shell=True, cwd=study_dir, check=True, capture_output=True, text=True)
        subprocess.run('GRIDPROC.exe', shell=True, cwd=study_dir, check=True, capture_output=True, text=True)
        
        # --- Save and Rename Results ---
        generated_files = {}
        for filename in ["AVY.DAT", "GRIDBIT2.DAT", "GRIDBIT4.DAT"]:
            original_path = os.path.join(study_dir, filename)
            if os.path.exists(original_path):
                renamed_path = os.path.join(study_dir, f"{case_name}_{filename.split('.')[0]}.dat")
                os.rename(original_path, renamed_path)
                generated_files[filename.split('.')[0]] = renamed_path
        
        print(f"   Successfully generated files for {case_name}")
        return generated_files

    except subprocess.CalledProcessError as e:
        print(f"   ERROR: Execution failed for '{e.cmd}' in directory '{study_dir}'")
        print(f"   Return Code: {e.returncode}")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        return None
    except Exception as e:
        print(f"   An unexpected error occurred: {e}")
        return None
    finally:
        # --- Restore original MAP.DAT and cleanup temporary files ---
        # This block ensures the original MAP.DAT is restored after every run,
        # whether it succeeded or failed.
        if os.path.exists(working_map_backup):
            # Overwrite the current MAP.DAT (which is the modified one) with the original.
            shutil.copy2(working_map_backup, working_map)
            os.remove(working_map_backup)
            
        for temp_file in [mbarb2_file, range_file, working_map_new]:
             if os.path.exists(temp_file):
                 os.remove(temp_file)

def plot_spanwise_comparison(study_dir, all_variations_data):
    """
    Plots yG vs j, showing the effects of varying MBAR and B16(2) separately.
    This replicates the style of Figure 16 from ESDU 02014a.
    """
    print("\n--- Plotting spanwise grid distribution comparisons ---")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 16), sharex=True)

    # Plot 1: Vary MBAR, keep B16(2) constant
    fixed_b16_2 = b16_2_values_to_test[1] 
    ax1.set_title(f'Effect of MBAR (B16(2) = {fixed_b16_2})', fontsize=14)
    for data in all_variations_data:
        if np.isclose(data['b16_2'], fixed_b16_2):
            label = f"MBAR = {data['mbar']}"
            avy_path = data.get('AVY')
            if avy_path and os.path.exists(avy_path):
                avy_data = np.loadtxt(avy_path, usecols=(0, 1))
                ax1.plot(avy_data[:, 0], avy_data[:, 1], marker='o', linestyle='-', markersize=3, label=label)

    # Plot 2: Vary B16(2), keep MBAR constant
    fixed_mbar = mbar_values_to_test[1] 
    ax2.set_title(f'Effect of B16(2) (MBAR = {fixed_mbar})', fontsize=14)
    for data in all_variations_data:
        if data['mbar'] == fixed_mbar:
            label = f"B16(2) = {data['b16_2']:.2f}"
            avy_path = data.get('AVY')
            if avy_path and os.path.exists(avy_path):
                avy_data = np.loadtxt(avy_path, usecols=(0, 1))
                ax2.plot(avy_data[:, 0], avy_data[:, 1], marker='o', linestyle='-', markersize=3, label=label)
            
    for ax in [ax1, ax2]:
        ax.set_ylabel('Spanwise Position ($y_G$)', fontsize=12)
        ax.legend()
        ax.grid(True)
    ax2.set_xlabel('Grid Line Index (j)', fontsize=12)
    
    plt.tight_layout(pad=3.0)
    plot_filename = os.path.join(study_dir, 'spanwise_grid_comparison.png')
    plt.savefig(plot_filename, dpi=300)
    print(f"Spanwise comparison plot saved to: {plot_filename}")
    plt.close(fig)

def plot_planform_grid(study_dir, variation_data, crank_eta_location):
    """
    Plots the planform grid with zoomed-in views of the root and crank.
    This version dynamically determines the crank's physical location for accurate zooming.
    """
    case_name = f"mbar{variation_data['mbar']}_b16_2_{variation_data['b16_2']:.2f}".replace('.', 'p')
    print(f"--- Plotting enhanced planform grid for {case_name} ---")
    
    avy_path = variation_data.get('AVY')
    gridbit2_path = variation_data.get('GRIDBIT2')
    gridbit4_path = variation_data.get('GRIDBIT4')

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax_full, ax_root, ax_crank) = plt.subplots(1, 3, figsize=(24, 8))
    fig.suptitle(f'Planform Grid for {case_name}', fontsize=16, y=0.98)

    # Helper function to plot grid lines from a file onto a given axis
    def plot_gridbit_on_ax(ax, file_path, color, lw):
        if not (file_path and os.path.exists(file_path)): return
        
        with open(file_path, 'r') as f:
            points = []
            for line in f:
                try:
                    # Split line and convert first two elements to float
                    coords = list(map(float, line.split()[:2]))
                    if len(coords) == 2:
                        points.append(coords)
                except (ValueError, IndexError):
                    # Plot segment when a blank line or invalid data is encountered
                    if points:
                        np_points = np.array(points)
                        ax.plot(np_points[:, 0], np_points[:, 1], color=color, linewidth=lw)
                        points = []
            # Plot any remaining points after the loop
            if points:
                np_points = np.array(points)
                ax.plot(np_points[:, 0], np_points[:, 1], color=color, linewidth=lw)

    # Plot on all three axes
    for ax in [ax_full, ax_root, ax_crank]:
        plot_gridbit_on_ax(ax, gridbit2_path, 'k', 0.8) # Streamwise lines
        plot_gridbit_on_ax(ax, gridbit4_path, 'gray', 0.6) # Spanwise lines

    # --- Configure Full View ---
    ax_full.set_title('Full Planform')
    ax_full.set_xlabel('x (Chordwise)')
    ax_full.set_ylabel('y (Spanwise)')
    ax_full.set_aspect('equal', adjustable='box')
    ax_full.grid(True)

    # --- Configure Root Zoom ---
    ax_root.set_title('Zoom: Wing Root')
    ax_root.set_xlabel('x (Chordwise)')
    ax_root.set_ylabel('')
    ax_root.set_aspect('equal', adjustable='box')
    ax_root.grid(True)
    ax_root.set_xlim(-0.2, 0.4)
    ax_root.set_ylim(-0.1, 0.5)

    # --- Configure Crank Zoom ---
    # Calculate the physical crank location for accurate zooming
    y_tip = 1.0  # Default fallback value
    if avy_path and os.path.exists(avy_path):
        avy_data = np.loadtxt(avy_path, usecols=(1,)) # Only need yG (spanwise position)
        if avy_data.size > 0:
            y_tip = np.max(avy_data) # The max yG is the semispan
    
    crank_y_location = crank_eta_location * y_tip
    zoom_half_width = 0.15 * y_tip  # Zoom window is 30% of the semispan

    ax_crank.set_title('Zoom: Wing Crank')
    ax_crank.set_xlabel('x (Chordwise)')
    ax_crank.set_ylabel('')
    ax_crank.set_aspect('equal', adjustable='box')
    ax_crank.grid(True)
    ax_crank.set_ylim(crank_y_location - zoom_half_width, crank_y_location + zoom_half_width)
    ax_crank.set_xlim(0.2, 0.9) 

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plot_filename = os.path.join(study_dir, f'planform_grid_enhanced_{case_name}.png')
    plt.savefig(plot_filename, dpi=300)
    plt.close(fig) 

# ==============================================================================
# 3. MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    script_root = os.path.dirname(os.path.abspath(__file__))
    
    study_dir = prepare_study_directory(script_root, wing_name, vfp_tools_source_dir)
    
    if study_dir:
        all_variations_data = []
        for mbar in mbar_values_to_test:
            for b16_2 in b16_2_values_to_test:
                generated_files = run_grid_variation(study_dir, mbar, b16_2, YSLOP1_val)
                if generated_files:
                    # Store parameters alongside the generated file paths
                    variation_info = generated_files.copy()
                    variation_info['mbar'] = mbar
                    variation_info['b16_2'] = b16_2
                    all_variations_data.append(variation_info)
        
        if all_variations_data:
            # Plot 1: Comparison of spanwise distributions
            plot_spanwise_comparison(study_dir, all_variations_data)
            
            # Plot 2: Detailed planform grid for every case
            for variation_data in all_variations_data:
                plot_planform_grid(study_dir, variation_data, crank_eta_location)
            
            print("\nAll plotting complete.")
        else:
            print("\nNo grid variation files were generated. Cannot plot results.")
    else:
        print("\nAborting study due to setup failure.")

