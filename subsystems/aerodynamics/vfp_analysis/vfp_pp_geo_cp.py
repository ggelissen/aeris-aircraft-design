import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from mpl_toolkits.mplot3d import Axes3D # Import for 3D plotting
import seaborn as sns

# ==============================================================================
# 1. DEFINE PLOTTING PARAMETERS
# ==============================================================================
# This script should be placed in the root project folder.

# --- Main Control ---
# Specify the name of the wing you want to plot the results for.
wing_name_to_plot = "w11-multi-airfoil"

# --- Plotting Options ---
save_plots = True
plot_file_format = 'png'
iso_levels = 30 # Number of contour levels for the isobar plot
# ** NEW **: Set to True to generate the 3D airfoil stack plot
plot_airfoil_stack_view = True 

# ==============================================================================
# 2. PARSING FUNCTION
# ==============================================================================

def parse_case_name(case_name):
    """Parses a run folder name to extract wing_name, mach, alpha, and re identifiers."""
    try:
        # Updated pattern to handle underscores between components
        pattern = r"(.+?)_(m\d+(?:\.\d+)?)_(a[m]?\d+(?:_?\d+)?(?:p\d+)?)_(re\d+(?:m\d+)?)"
        match = re.match(pattern, case_name)
        
        if match:
            wing_id, mach_id, alpha_id, re_id = match.groups()
            
            # Fix Mach number parsing (divide by 100 instead of 10)
            mach_val = float(mach_id[1:]) / 100  # Convert m50 to 0.50, m86 to 0.86
            
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


def parse_cp_file(file_path):
    """Parses a VFP .cp file to extract surface data for the entire wing."""
    all_station_data = []
    try:
        with open(file_path, 'r') as f: lines = f.readlines()
        last_block_start = 0
        for i, line in enumerate(reversed(lines)):
            if "LEV= " in line:
                last_block_start = len(lines) - 1 - i
                break
        
        current_station_y, current_station_lines = None, []
        for line in lines[last_block_start:]:
            if 'J=' in line and 'YAVE=' in line:
                if current_station_lines and current_station_y is not None:
                    df = pd.read_csv(pd.io.common.StringIO("".join(current_station_lines)),
                                     delim_whitespace=True, header=None, names=["X/C", "Z/C", "CP", "P/H", "M", "Q", "PHI(I=L)", "Y/YTIP", "XPHYS", "ZPHYS", "VT", "VALP"])
                    df['YPHYS'] = current_station_y
                    all_station_data.append(df)
                current_station_y = float(re.search(r"YAVE=\s*([\d\.\-]+)", line).group(1))
                current_station_lines = []
            elif current_station_y is not None and line.strip() and not line.strip().startswith('*'):
                current_station_lines.append(line)
        if current_station_lines and current_station_y is not None:
            df = pd.read_csv(pd.io.common.StringIO("".join(current_station_lines)),
                             delim_whitespace=True, header=None, names=["X/C", "Z/C", "CP", "P/H", "M", "Q", "PHI(I=L)", "Y/YTIP", "XPHYS", "ZPHYS", "VT", "VALP"])
            df['YPHYS'] = current_station_y
            all_station_data.append(df)

        if not all_station_data: return None
        full_wing_df = pd.concat(all_station_data, ignore_index=True)
        for col in ["X/C", "Z/C", "CP", "XPHYS", "YPHYS", "ZPHYS"]:
            full_wing_df[col] = pd.to_numeric(full_wing_df[col], errors='coerce')
        return full_wing_df.dropna(subset=["X/C", "Z/C", "CP", "XPHYS", "YPHYS", "ZPHYS"])
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}"); return None

# ==============================================================================
# 3. PLOTTING FUNCTIONS
# ==============================================================================

sns.set_style("whitegrid")
plt.rcParams.update({'font.family': 'serif', 'axes.spines.top': False, 'axes.spines.right': False})

def plot_airfoil_stack(wing_name, all_case_data, mach_number=None):
    """Plots a 3D view of the airfoil stack."""
    if not all_case_data: print("No data for airfoil stack plot."); return

    sorted_alphas = sorted(all_case_data.keys())
    state = {'alpha_idx': 0}

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    plt.subplots_adjust(bottom=0.2)

    def draw_stack(alpha_idx):
        ax.clear()
        alpha = sorted_alphas[alpha_idx]
        df = all_case_data[alpha]
        
        for y_station, station_df in df.groupby('YPHYS'):
            # --- FIX: Filter out wake points (where X/C > 1) before plotting ---
            surface_df = station_df[(station_df['X/C'] >= 0) & (station_df['X/C'] <= 1.01)] # Use 1.01 to ensure closed trailing edge
            ax.plot(surface_df['XPHYS'], surface_df['YPHYS'], surface_df['ZPHYS'], color='k', linewidth=0.8)

        ax.set_xlabel('X (Chord)')
        ax.set_ylabel('Y (Span)')
        ax.set_zlabel('Z (Height)')
        ax.set_title(f'Wing Geometry Airfoil Stack\n{wing_name.upper()} at α = {alpha:.2f}°' + (f"\nMach {mach_number:.2f}" if mach_number is not None else ""), fontsize=14)
        ax.view_init(elev=30, azim=-125) 
        # Use 'auto' aspect ratio for better scaling with wing-like geometries
        ax.set_aspect('auto') 
        
    def next_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] + 1) % len(sorted_alphas)
        draw_stack(state['alpha_idx'])
        fig.canvas.draw_idle()

    def prev_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] - 1 + len(sorted_alphas)) % len(sorted_alphas)
        draw_stack(state['alpha_idx'])
        fig.canvas.draw_idle()

    ax_prev = plt.axes([0.35, 0.05, 0.1, 0.04]); btn_prev = Button(ax_prev, '◄ Prev α'); btn_prev.on_clicked(prev_alpha)
    ax_next = plt.axes([0.55, 0.05, 0.1, 0.04]); btn_next = Button(ax_next, 'Next α ►'); btn_next.on_clicked(next_alpha)

    draw_stack(state['alpha_idx'])

    if save_plots:
        mach_folder = f"mach_{mach_number:.2f}".replace('.', 'p')
        save_dir = os.path.join(os.getcwd(), "results", wing_name, mach_folder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{wing_name}_airfoil_stack_plot.{plot_file_format}")
        plt.savefig(save_path, dpi=300)
        print(f"Airfoil stack plot saved to: {save_path}")
    # plt.show()


def plot_interactive_isobars(wing_name, all_case_data, mach_number=None):
    """Plots surface isobars with buttons to cycle through angles of attack."""
    if not all_case_data: print("No data for isobar plot."); return

    sorted_alphas = sorted(all_case_data.keys())
    state = {'alpha_idx': 0}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), sharey=True)
    plt.subplots_adjust(bottom=0.2, right=0.88)
    
    def draw_isobars(alpha_idx):
        alpha = sorted_alphas[alpha_idx]
        ax1.clear(); ax2.clear()
        df = all_case_data[alpha]
        
        num_points = df['YPHYS'].value_counts().iloc[0]
        df['surface'] = ['lower' if i < num_points//2 else 'upper' for i in df.groupby('YPHYS').cumcount()]
        upper_surface, lower_surface = df[df['surface'] == 'upper'], df[df['surface'] == 'lower']
        
        cp_min, cp_max = df['CP'].min(), df['CP'].max()
        levels = np.linspace(cp_min, cp_max, iso_levels)
        
        contour1 = ax1.tricontourf(upper_surface['XPHYS'], upper_surface['YPHYS'], upper_surface['CP'], levels=levels, cmap='viridis', extend='both')
        ax1.tricontour(upper_surface['XPHYS'], upper_surface['YPHYS'], upper_surface['CP'], levels=levels, colors='k', linewidths=0.5, alpha=0.5)
        ax1.set_title('Upper Surface'); ax1.set_xlabel('Chordwise Position (x)'); ax1.set_ylabel('Spanwise Position (y)')
        ax1.set_aspect('equal', adjustable='box')

        contour2 = ax2.tricontourf(lower_surface['XPHYS'], lower_surface['YPHYS'], lower_surface['CP'], levels=levels, cmap='viridis', extend='both')
        ax2.tricontour(lower_surface['XPHYS'], lower_surface['YPHYS'], lower_surface['CP'], levels=levels, colors='k', linewidths=0.5, alpha=0.5)
        ax2.set_title('Lower Surface'); ax2.set_xlabel('Chordwise Position (x)')
        ax2.set_aspect('equal', adjustable='box')

        fig.suptitle(f'Surface Pressure Isobars ($C_p$) at α = {alpha:.2f}°\n{wing_name.upper()}' + (f"\nMach {mach_number:.2f}" if mach_number is not None else ""), fontsize=16, fontweight='bold')
        return contour1

    contour_plot = draw_isobars(state['alpha_idx'])
    cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
    fig.colorbar(contour_plot, cax=cbar_ax, label='$C_p$')

    def next_alpha(event): state['alpha_idx'] = (state['alpha_idx'] + 1) % len(sorted_alphas); draw_isobars(state['alpha_idx']); fig.canvas.draw_idle()
    def prev_alpha(event): state['alpha_idx'] = (state['alpha_idx'] - 1 + len(sorted_alphas)) % len(sorted_alphas); draw_isobars(state['alpha_idx']); fig.canvas.draw_idle()

    ax_prev = plt.axes([0.35, 0.05, 0.1, 0.04]); btn_prev = Button(ax_prev, '◄ Prev α'); btn_prev.on_clicked(prev_alpha)
    ax_next = plt.axes([0.55, 0.05, 0.1, 0.04]); btn_next = Button(ax_next, 'Next α ►'); btn_next.on_clicked(next_alpha)

    if save_plots:
        mach_folder = f"mach_{mach_number:.2f}".replace('.', 'p')
        save_dir = os.path.join(os.getcwd(), "results", wing_name, mach_folder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{wing_name}_isobar_plot.{plot_file_format}")
        plt.savefig(save_path, dpi=300)
        print(f"Isobar plot saved to: {save_path}")
    # plt.show()

def plot_interactive_cp(wing_name, all_case_data, mach_number=None):
    """Creates an interactive plot of Cp vs x/c with buttons for alpha and a slider for span station."""
    if not all_case_data: print("No data for interactive Cp plot."); return

    sorted_alphas = sorted(all_case_data.keys())
    initial_df = all_case_data[sorted_alphas[0]]
    y_stations = sorted(initial_df['YPHYS'].unique())
    
    fig, ax = plt.subplots(figsize=(10, 8)); plt.subplots_adjust(bottom=0.3)
    line_upper, = ax.plot([], [], 'o-', label='Upper Surface', markerfacecolor='white')
    line_lower, = ax.plot([], [], 's-', label='Lower Surface', markerfacecolor='white')
    ax.invert_yaxis(); ax.grid(True); ax.legend(loc='best')
    ax.set_xlim([0, 1]); ax.set_xlabel('Non-dimensional Chord (x/c)'); ax.set_ylabel('Pressure Coefficient ($C_p$)')
    
    state = {'alpha_idx': 0}
    ax_prev = plt.axes([0.35, 0.15, 0.1, 0.04]); btn_prev = Button(ax_prev, '◄ Prev α')
    ax_next = plt.axes([0.55, 0.15, 0.1, 0.04]); btn_next = Button(ax_next, 'Next α ►')
    ax_y_slider = plt.axes([0.2, 0.08, 0.65, 0.03]); y_slider = Slider(ax=ax_y_slider, label='y-station', valmin=min(y_stations), valmax=max(y_stations), valinit=y_stations[0], valstep=y_stations)

    def update_plot(event=None):
        alpha, y = sorted_alphas[state['alpha_idx']], y_slider.val
        df = all_case_data[alpha]
        station_df = df[np.isclose(df['YPHYS'], y)]
        if 'surface' not in station_df.columns:
            n = len(station_df); station_df = station_df.copy(); station_df['surface'] = ['lower'] * (n // 2) + ['upper'] * (n - n // 2)
        upper, lower = station_df[station_df['surface'] == 'upper'], station_df[station_df['surface'] == 'lower']
        line_upper.set_data(upper['X/C'], upper['CP']); line_lower.set_data(lower['X/C'], lower['CP'])
        ax.relim(); ax.autoscale_view(scalex=False)
        ax.set_title(f'Chordwise Pressure Distribution for {wing_name.upper()}\nα = {alpha:.2f}°, y = {y:.3f}' + (f" | Mach {mach_number:.2f}" if mach_number is not None else ""))
        fig.canvas.draw_idle()

    def next_alpha(event): state['alpha_idx'] = (state['alpha_idx'] + 1) % len(sorted_alphas); update_plot()
    def prev_alpha(event): state['alpha_idx'] = (state['alpha_idx'] - 1 + len(sorted_alphas)) % len(sorted_alphas); update_plot()

    btn_next.on_clicked(next_alpha); btn_prev.on_clicked(prev_alpha); y_slider.on_changed(update_plot)
    update_plot()
    
    if save_plots:
        mach_folder = f"mach_{mach_number:.2f}".replace('.', 'p')
        save_dir = os.path.join(os.getcwd(), "results", wing_name, mach_folder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{wing_name}_interactive_cp_plot.{plot_file_format}")
        plt.savefig(save_path, dpi=300)
        print(f"Interactive Cp plot saved to: {save_path}")
    # plt.show()

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    script_root = os.path.dirname(os.path.abspath(__file__))
    wing_results_dir = os.path.join(script_root, "results", wing_name_to_plot)

    if not os.path.isdir(wing_results_dir):
        print(f"❌ ERROR: Results directory for wing '{wing_name_to_plot}' not found.")
    else:
        print(f"Analyzing results for wing: {wing_name_to_plot}")
        
        # Organize data by Mach number
        mach_data = {}  # Dictionary to store cases by Mach number
        
        for item in os.listdir(wing_results_dir):
            if os.path.isdir(os.path.join(wing_results_dir, item)) and item not in ["geometry_master", "ANALYSIS_RESULTS"]:
                case_data = parse_case_name(item)
                if case_data:
                    cp_file_path = os.path.join(wing_results_dir, item, f"{case_data['full_name']}.cp")
                    if os.path.exists(cp_file_path):
                        df = parse_cp_file(cp_file_path)
                        if df is not None and not df.empty:
                            # Initialize dictionary for this Mach number if it doesn't exist
                            if case_data['mach_val'] not in mach_data:
                                mach_data[case_data['mach_val']] = {}
                            mach_data[case_data['mach_val']][case_data['alpha_val']] = df
                        else:
                            print(f"Warning: Could not extract data from '{os.path.basename(cp_file_path)}'.")
        
        if mach_data:
            print(f"\nFound data for {len(mach_data)} Mach number(s)")
            for mach_number, cases in sorted(mach_data.items()):
                print(f"\nProcessing Mach {mach_number:.2f} ({len(cases)} cases)")
                if plot_airfoil_stack_view:
                    plot_airfoil_stack(wing_name_to_plot, cases, mach_number)
                plot_interactive_isobars(wing_name_to_plot, cases, mach_number)
                plot_interactive_cp(wing_name_to_plot, cases, mach_number)
        else:
            print("\n❌ No valid .cp files were found to plot.")
