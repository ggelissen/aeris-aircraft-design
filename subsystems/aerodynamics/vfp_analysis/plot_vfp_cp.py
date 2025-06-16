import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import seaborn as sns

# ==============================================================================
# 1. DEFINE PLOTTING PARAMETERS
# ==============================================================================
# This script should be placed in the root project folder.

# --- Main Control ---
# Specify the name of the wing you want to plot the results for.
wing_name_to_plot = "w8"

# --- Plotting Options ---
save_plots = True
plot_file_format = 'png'
iso_levels = 50 # Number of contour levels for the isobar plot

# ==============================================================================
# 2. PARSING FUNCTION
# ==============================================================================

def parse_case_name(case_name):
    """Parses a run folder name to extract wing_name, mach, alpha, and re identifiers."""
    try:
        match = re.match(r"(.+?)(m\d+)(am?[\d_p]+)(re\d+m?\d*)", case_name)
        if match:
            wing_id, mach_id, alpha_id, re_id = match.groups()
            if alpha_id.startswith('am'):
                alpha_val = -float(alpha_id[2:].replace('p', '.'))
            else:
                alpha_val = float(alpha_id[1:].replace('p', '.'))
            return {"alpha_val": alpha_val, "full_name": case_name}
    except Exception as e:
        print(f"Warning: Could not parse folder name '{case_name}': {e}")
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

def plot_interactive_isobars(wing_name, all_case_data):
    """Plots surface isobars with buttons to cycle through angles of attack."""
    if not all_case_data: print("No data for isobar plot."); return

    sorted_alphas = sorted(all_case_data.keys())
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), sharey=True)
    plt.subplots_adjust(bottom=0.2, right=0.88)
    
    # Use a dictionary for the index to make it mutable inside callbacks
    state = {'alpha_idx': 0}

    def draw_isobars(alpha_idx):
        alpha = sorted_alphas[alpha_idx]
        ax1.clear(); ax2.clear()
        df = all_case_data[alpha]
        
        num_points = df['YPHYS'].value_counts().iloc[0]
        df['surface'] = ['lower' if i < num_points//2 else 'upper' for i in df.groupby('YPHYS').cumcount()]
        upper_surface, lower_surface = df[df['surface'] == 'upper'], df[df['surface'] == 'lower']
        
        cp_min, cp_max = df['CP'].min(), df['CP'].max()
        levels = np.linspace(cp_min, cp_max, iso_levels)
        
        # Using RdYlBu which is both perceptually uniform and colorblind-friendly
        # The '_r' reverses it so red=high pressure, blue=low pressure
        colormap = plt.cm.RdYlBu_r
        
        contour1 = ax1.tricontourf(upper_surface['XPHYS'], upper_surface['YPHYS'], 
                                  upper_surface['CP'], levels=levels, 
                                  cmap=colormap, extend='both')
        ax1.tricontour(upper_surface['XPHYS'], upper_surface['YPHYS'], 
                      upper_surface['CP'], levels=levels, 
                      colors='k', linewidths=0.3, alpha=0.3)
        ax1.set_title('Upper Surface'); ax1.set_xlabel('Chordwise Position (x)'); ax1.set_ylabel('Spanwise Position (y)')
        ax1.set_aspect('equal', adjustable='box')

        contour2 = ax2.tricontourf(lower_surface['XPHYS'], lower_surface['YPHYS'], 
                                  lower_surface['CP'], levels=levels, 
                                  cmap=colormap, extend='both')
        ax2.tricontour(lower_surface['XPHYS'], lower_surface['YPHYS'], 
                      upper_surface['CP'], levels=levels, 
                      colors='k', linewidths=0.3, alpha=0.3)
        ax2.set_title('Lower Surface'); ax2.set_xlabel('Chordwise Position (x)')
        ax2.set_aspect('equal', adjustable='box')

        fig.suptitle(f'Surface Pressure Isobars ($C_p$) at α = {alpha:.2f}°\n{wing_name.upper()}', fontsize=16, fontweight='bold')
        return contour1

    contour_plot = draw_isobars(state['alpha_idx'])
    cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
    fig.colorbar(contour_plot, cax=cbar_ax, label='$C_p$')

    # --- Button Logic ---
    def next_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] + 1) % len(sorted_alphas)
        draw_isobars(state['alpha_idx'])
        fig.canvas.draw_idle()

    def prev_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] - 1 + len(sorted_alphas)) % len(sorted_alphas)
        draw_isobars(state['alpha_idx'])
        fig.canvas.draw_idle()

    ax_prev = plt.axes([0.35, 0.05, 0.1, 0.04])
    btn_prev = Button(ax_prev, '◄ Prev α')
    btn_prev.on_clicked(prev_alpha)

    ax_next = plt.axes([0.55, 0.05, 0.1, 0.04])
    btn_next = Button(ax_next, 'Next α ►')
    btn_next.on_clicked(next_alpha)

    if save_plots:
        save_path = os.path.join(os.getcwd(), "results", wing_name, f"{wing_name}_isobar_plot.{plot_file_format}")
        plt.savefig(save_path, dpi=300); print(f"Isobar plot saved to: {save_path}")
    plt.show()

def plot_interactive_cp(wing_name, all_case_data):
    """Creates an interactive plot of Cp vs x/c with buttons for alpha and a slider for span station."""
    if not all_case_data: print("No data for interactive Cp plot."); return

    sorted_alphas = sorted(all_case_data.keys())
    initial_df = all_case_data[sorted_alphas[0]]
    y_stations = sorted(initial_df['YPHYS'].unique())
    
    fig, ax = plt.subplots(figsize=(10, 8))
    plt.subplots_adjust(bottom=0.25)
    
    line_upper, = ax.plot([], [], 'o-', label='Upper Surface', markerfacecolor='white')
    line_lower, = ax.plot([], [], 's-', label='Lower Surface', markerfacecolor='white')
    ax.invert_yaxis(); ax.grid(True); ax.legend(loc='best')
    ax.set_xlim([0, 1]); ax.set_xlabel('Non-dimensional Chord (x/c)'); ax.set_ylabel('Pressure Coefficient ($C_p$)')
    
    # State dictionary to hold the current index for alpha
    state = {'alpha_idx': 0}

    # --- UI Elements ---
    ax_prev = plt.axes([0.35, 0.15, 0.1, 0.04])
    btn_prev = Button(ax_prev, '◄ Prev α')
    
    ax_next = plt.axes([0.55, 0.15, 0.1, 0.04])
    btn_next = Button(ax_next, 'Next α ►')
    
    ax_y_slider = plt.axes([0.2, 0.08, 0.65, 0.03])
    y_slider = Slider(ax=ax_y_slider, label='y-station', valmin=min(y_stations), valmax=max(y_stations), valinit=y_stations[0], valstep=y_stations)

    def update_plot(event=None):
        alpha = sorted_alphas[state['alpha_idx']]
        y = y_slider.val
        
        df = all_case_data[alpha]
        station_df = df[np.isclose(df['YPHYS'], y)]
        
        if 'surface' not in station_df.columns:
            n = len(station_df)
            station_df = station_df.copy()
            station_df['surface'] = ['lower'] * (n // 2) + ['upper'] * (n - n // 2)

        upper, lower = station_df[station_df['surface'] == 'upper'], station_df[station_df['surface'] == 'lower']
        
        line_upper.set_data(upper['X/C'], upper['CP'])
        line_lower.set_data(lower['X/C'], lower['CP'])
        ax.relim(); ax.autoscale_view(scalex=False)
        ax.set_title(f'Chordwise Pressure Distribution for {wing_name.upper()}\nα = {alpha:.2f}°, y = {y:.3f}')
        fig.canvas.draw_idle()

    def next_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] + 1) % len(sorted_alphas)
        update_plot()

    def prev_alpha(event):
        state['alpha_idx'] = (state['alpha_idx'] - 1 + len(sorted_alphas)) % len(sorted_alphas)
        update_plot()

    btn_next.on_clicked(next_alpha)
    btn_prev.on_clicked(prev_alpha)
    y_slider.on_changed(update_plot)
    
    update_plot() # Initial plot draw
    
    if save_plots:
        save_path = os.path.join(os.getcwd(), "results", wing_name, f"{wing_name}_interactive_cp_plot.{plot_file_format}")
        plt.savefig(save_path, dpi=300); print(f"Interactive Cp plot saved to: {save_path}")

    plt.show()

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
        
        all_case_data = {}
        for item in os.listdir(wing_results_dir):
            if os.path.isdir(os.path.join(wing_results_dir, item)) and item not in ["geometry_master", "ANALYSIS_RESULTS"]:
                case_data = parse_case_name(item)
                if case_data:
                    cp_file_path = os.path.join(wing_results_dir, item, f"{case_data['full_name']}.cp")
                    if os.path.exists(cp_file_path):
                        df = parse_cp_file(cp_file_path)
                        if df is not None and not df.empty:
                            all_case_data[case_data['alpha_val']] = df
                        else:
                            print(f"Warning: Could not extract data from '{os.path.basename(cp_file_path)}'.")
        
        if all_case_data:
            plot_interactive_isobars(wing_name_to_plot, all_case_data)
            plot_interactive_cp(wing_name_to_plot, all_case_data)
        else:
            print("\n❌ No valid .cp files were found to plot.")
