import os
import subprocess
import shutil
import numpy as np

# ==============================================================================
# 1. DEFINE SIMULATION PARAMETERS
# ==============================================================================
# --- Main Simulation Control ---
wing_name = "w2" # Base name for the wing
fpcon_source_dir = os.path.join(os.path.dirname(__file__), "vpwin_fpv20")
vfp_source_dir = os.path.join(os.path.dirname(__file__), "vpwin_vfphv20")

# Directory where your airfoil .DAT files are stored
#airfoil_source_dir = os.path.join(os.path.dirname(__file__), "airfoils")

# --- Angle of Attack Sweep ---
# List of angles of attack (in degrees) to simulate
alpha_sweep = [-1.0, 0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0]
# alpha_sweep = [0.5]

# --- Mach Sweep Settings ---
# Enable this to run an incremental Mach sweep for each angle of attack.
# This is highly recommended for high Mach numbers to improve convergence.
enable_mach_sweep = True
start_mach = 0.6       # The stable Mach number to begin the sweep from.
end_mach = 0.85         # The final target Mach number.
mach_increment = 0.02   # The step size for the Mach sweep.

# --- Flow Conditions (Used if Mach sweep is disabled) ---
Mach_freestream = 0.65 # Freestream Mach number
Re = 8500000 # Reynolds number based on mean geometric chord

# --- Wing Geometry ---
is_cranked = True # True for a cranked wing, False for a simple swept/tapered wing
A_g = 12.0 # Gross aspect ratio
crank_c0_taper_ratio = 0.5 # Taper ratio of the inner panel (crank chord / root chord)
tip_c0_taper_ratio = 0.294 # Taper ratio of the outer panel (tip chord / root chord)
eta_sc = 0.4 # Non-dimensional spanwise location of the crank (y_crank / s)
Lambda_lei = 32.0 # Inner panel leading-edge sweep (degrees)
Lambda_leo = 32.0 # Outer panel leading-edge sweep (degrees)

# --- Wing Sections, Twist, and Airfoils ---
NSECT1 = 2
section_data = [
    {'etas': 0.0, 'hsect': 0.0, 'xtwsec': 0.5, 'twsin': 3.0, 'airfoil': '0412vgk.dat'},
    {'etas': 0.4, 'hsect': 0.0, 'xtwsec': 0.5, 'twsin': 1.0, 'airfoil': '0412vgk.dat'},
    {'etas': 1.0, 'hsect': 0.0, 'xtwsec': 0.5, 'twsin': 0.0, 'airfoil': '0412vgk.dat'},
]

# --- Fuselage Parameters ---
has_fuselage = True
body_radius = 0.2
fuselage_length = 4.0
fore_body_length = 1.0
aft_body_length = 1.4
wing_root_le_pos = 1.6

# --- Viscous & Solver Parameters ---
XCM = 0.45
cl_cd_convergence = 'n'
NU = 3
NL = 3
upper_transition_data = [
    [0.272021, 0.02, 0.10, 0.000041],
    [0.898720, 0.02, 0.10, 0.000056],
    [2.186666, 0.02, 0.10, 0.000210],
]
lower_transition_data = [
    [0.272021, 0.02, 0.15, 0.000041],
    [0.898720, 0.02, 0.15, 0.000067],
    [2.186666, 0.02, 0.15, 0.000280],
]

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def generate_case_name(wing, mach, alpha, re):
    """Generates a standardized run name based on simulation parameters."""
    mach_str = f"m{int(mach * 100):02d}"
    alpha_str = f"a{str(abs(alpha)).replace('.', 'p')}"
    if alpha < 0:
        alpha_str = "am" + alpha_str[1:] # am for alpha minus

    re_in_millions = re / 1_000_000
    re_str = f"re{int(re_in_millions)}m"
    if re_in_millions != int(re_in_millions):
        re_str += str(int((re_in_millions - int(re_in_millions)) * 10))

    return f"{wing}_{mach_str}_{alpha_str}_{re_str}"

def setup_case_directory(base_dir, wing_name, run_name):
    """Creates a clean, self-contained directory for a single simulation case."""
    wing_results_dir = os.path.join(base_dir, "/subsystems/aerodynamics/vfp_analysis/results", wing_name)
    os.makedirs(wing_results_dir, exist_ok=True)
    
    case_run_dir = os.path.join(wing_results_dir, run_name)
    if os.path.exists(case_run_dir):
        shutil.rmtree(case_run_dir)
    
    try:
        shutil.copytree(vfp_source_dir, case_run_dir)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find source VFP directory: {e.filename}")
        return None
    return case_run_dir

# ==============================================================================
# 3. WORKFLOW FUNCTIONS
# ==============================================================================

def run_fpcon_once(base_dir, wing_name, airfoil_src_dir, mach_for_fpcon):
    """
    Generates master geometry files using fpcon.exe.
    This is run only once for the entire simulation sweep.
    """
    print("\n--- Step 1: Running FPCON to generate master geometry files ---")
    wing_results_dir = os.path.join("/root/DSEproject/subsystems/aerodynamics/vfp_analysis/results", wing_name)
    os.makedirs(wing_results_dir, exist_ok=True)
    
    fpcon_run_dir = os.path.join(wing_results_dir, "geometry_master")
    if os.path.exists(fpcon_run_dir):
        shutil.rmtree(fpcon_run_dir)
    
    try:
        shutil.copytree(fpcon_source_dir, fpcon_run_dir)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find source FPCON directory: {e.filename}")
        return None

    if not section_data:
        print("ERROR: 'section_data' list is empty. Cannot run FPCON.")
        return None

    nchange = 0
    unique_airfoils = {section_data[0]['airfoil']}
    changed_section_indices = []
    changed_airfoil_files = []

    for i in range(1, len(section_data)):
        current_airfoil = section_data[i]['airfoil']
        previous_airfoil = section_data[i-1]['airfoil']
        unique_airfoils.add(current_airfoil)
        if current_airfoil != previous_airfoil:
            nchange += 1
            changed_section_indices.append(i + 1)
            changed_airfoil_files.append(current_airfoil)

    root_airfoil = section_data[0]['airfoil']

    print(f"Determined NCHANGE = {nchange}")
    print(f"Changed section indices (NC values): {changed_section_indices}")
    print(f"Root airfoil: {root_airfoil}")
    print(f"Changed airfoil files for fpcon: {changed_airfoil_files}")
    
    try:
        for airfoil in unique_airfoils:
            src_path = os.path.join(airfoil_src_dir, airfoil)
            dest_path = os.path.join(fpcon_run_dir, airfoil)
            shutil.copy(src_path, dest_path)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find airfoil file: {e.filename}")
        print(f"Please ensure it exists in: {airfoil_src_dir}")
        return None
    
    nsect = len(section_data)
    local_nsect1 = nsect if not is_cranked else NSECT1

    input_file = f"{fpcon_run_dir}/fpcon_input.txt"
    with open(os.path.join(fpcon_run_dir, input_file), "w") as f:
        f.write("y\n" if is_cranked else "n\n")
        f.write(f"{A_g} {tip_c0_taper_ratio} {crank_c0_taper_ratio} {eta_sc}\n")
        f.write(f"{Lambda_lei} {Lambda_leo}\n")
        f.write(f"{nsect}\n")
        f.write(f"{local_nsect1}\n")
        f.write(f"{nchange}\n")
        
        for index in changed_section_indices:
            f.write(f"{index}\n")

        f.write(f"{root_airfoil}\n")
        for airfoil in changed_airfoil_files:
            f.write(f"{airfoil}\n")
            
        for data in section_data:
            f.write(f"{data['etas']} {data['hsect']} {data['xtwsec']} {data['twsin']}\n")
            
        f.write(f"{body_radius if has_fuselage else 0.0}\n")
        f.write(f"{wing_name}\n")
        f.write("n\n")
        # Use the provided Mach number for the initial FPCON run
        f.write(f"{mach_for_fpcon} {alpha_sweep[0]}\n")
    
    try:
        subprocess.run(f'wine "{fpcon_run_dir}/fpcon.exe" < {input_file}', shell=True, check=True)
        print("FPCON executed successfully.")
        return fpcon_run_dir
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FPCON execution failed. Return code: {e.returncode}")
        return None
    except FileNotFoundError:
        print(f"ERROR: 'fpcon.exe' not found in {fpcon_run_dir}.")
        return None


def run_vfp_case(case_run_dir, master_fpcon_dir, current_run_name, current_mach, current_alpha, is_continuation, prev_run_name, prev_case_dir):
    """Runs a single VFP case, either initial or continuation."""
    print(f"\n{'='*20} RUNNING CASE: {current_run_name} (M={current_mach}, A={current_alpha}) {'='*20}")
    
    try:
        # --- Prepare Inputs ---
        shutil.copy(os.path.join(master_fpcon_dir, "GEO.DAT"), os.path.join(case_run_dir, "geo.dat"))
        shutil.copy(os.path.join(master_fpcon_dir, "MAP.DAT"), os.path.join(case_run_dir, "map.dat"))

        if has_fuselage:
            input_file_fuse = "fuse_input.txt"
            with open(os.path.join(case_run_dir, input_file_fuse), "w") as f:
                f.write(f"{current_mach}\n") # Use current Mach for fusegen
                f.write(f"{fuselage_length} {fore_body_length} {aft_body_length}\n")
                f.write(f"{wing_root_le_pos}\n")
            subprocess.run(f'wine "vfpfusegenv2.exe" < {input_file_fuse}', shell=True, check=True, cwd=case_run_dir)

            input_file_body = "body_input.txt"
            with open(os.path.join(case_run_dir, input_file_body), "w") as f:
                f.write("y\n")
                f.write(f"{current_run_name}\n")
                f.write(f"{cl_cd_convergence}\n")
                f.write(f"{current_alpha} {XCM}\n")
                f.write(f"{Re}\n")
                f.write(f"{NU}\n")
                f.write(f"{NL}\n")
                for data in upper_transition_data:
                    f.write(f"{data[0]} {data[1]} {data[2]} {data[3]}\n")
                for data in lower_transition_data:
                    f.write(f"{data[0]} {data[1]} {data[2]} {data[3]}\n")
            subprocess.run(f'wine "vfptvkbodyv8.exe" < {input_file_body}', shell=True, check=True, cwd=case_run_dir)
            shutil.copy(os.path.join(case_run_dir, "FLOWdmmean.dat"), os.path.join(case_run_dir, "fort.15"))
        else:
            print("ERROR: Wing-only flow file generation not implemented.")
            return False

        shutil.copy(os.path.join(case_run_dir, "map.dat"), os.path.join(case_run_dir, "fort.14"))
        shutil.copy(os.path.join(case_run_dir, "geo.dat"), os.path.join(case_run_dir, "fort.10"))

        if is_continuation and prev_case_dir and prev_run_name:
            print(f"This is a continuation run. Using dump files from: {prev_run_name}")
            found_valid_dump = False
            for i in [11, 21, 50, 51, 52, 55]:
                dump_file_name = f"{prev_run_name}.fort{i}"
                src_path = os.path.join(prev_case_dir, dump_file_name)
                if os.path.exists(src_path):
                    shutil.copy(src_path, os.path.join(case_run_dir, f"fort.{i}"))
                    found_valid_dump = True
            
            if not found_valid_dump:
                print("Warning: No valid dump files found from previous run.")
                print("This might be normal for the first case or when switching from negative to positive alpha.")
                is_continuation = False
        else:
            if is_continuation:
                print("Warning: Continuation requested but no previous case data available.")
            is_continuation = False
        
        # --- Run Core Solver ---
        print(f"\n--- Running VFP Core Solver for M={current_mach}, alpha={current_alpha} ---")
        # Here you would typically generate the FLOWVIS.DAT file based on current_mach and current_alpha
        # For simplicity, this example assumes vfphe.exe can take these as command line arguments or reads a pre-made file.
        # A more robust implementation would write a FLOWVIS.DAT file here.
        subprocess.run('wine "vfphe.exe"', shell=True, check=True, cwd=case_run_dir)
        print("VFP core solver finished successfully.")

        # --- Post-Process and archive results with standard names ---
        print("\n--- Post-Processing and Archiving Results ---")
        for src, dest_suffix in {'fort.16': 'vis', 'fort.18': 'forces', 'fort.19': 'cp'}.items():
            if os.path.exists(os.path.join(case_run_dir, src)):
                shutil.move(os.path.join(case_run_dir, src), os.path.join(case_run_dir, f"{current_run_name}.{dest_suffix}"))
        
        shutil.copy(os.path.join(case_run_dir, "geo.dat"), os.path.join(case_run_dir, f"{current_run_name}.geo"))
        shutil.copy(os.path.join(case_run_dir, "fort.15"), os.path.join(case_run_dir, f"{current_run_name}.dat"))

        if os.path.exists(os.path.join(case_run_dir, "fort.70")):
            shutil.copy(os.path.join(case_run_dir, "fort.70"), os.path.join(case_run_dir, "flow70.dat"))
            shutil.copy(os.path.join(case_run_dir, "fort.71"), os.path.join(case_run_dir, "flow71.dat"))
            subprocess.run('wine "f137b1.exe"', shell=True, check=True, cwd=case_run_dir)
            if os.path.exists(os.path.join(case_run_dir, "wavedrg73.dat")):
                shutil.copy(os.path.join(case_run_dir, "wavedrg73.dat"), os.path.join(case_run_dir, f"{current_run_name}wavedrg73.dat"))
            print("Wave drag calculation complete.")
        else:
            print("Wave drag inputs (fort.70) not found, skipping for this case.")
        
        for i in [11, 21, 50, 51, 52, 55]:
            if os.path.exists(os.path.join(case_run_dir, f"fort.{i}")):
                shutil.copy(os.path.join(case_run_dir, f"fort.{i}"), os.path.join(case_run_dir, f"{current_run_name}.fort{i}"))

        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR during VFP case run for {current_run_name}: {e}")
        return False

def run_simulation():
    script_root = '/root/DSEproject'
    
    mach_list = []
    if enable_mach_sweep:
        # Create a list of Mach numbers for the sweep, rounded to 2 decimal places
        raw_mach_list = np.arange(start_mach, end_mach + mach_increment, mach_increment)
        mach_list = [round(m, 2) for m in raw_mach_list]
        # Ensure the final Mach number is included with proper rounding
        if not np.isclose(mach_list[-1], round(end_mach, 2)):
            mach_list.append(round(end_mach, 2))
        mach_for_fpcon = round(end_mach, 2)
    else:
        mach_list = [round(Mach_freestream, 2)]
        mach_for_fpcon = round(Mach_freestream, 2)

    # Run FPCON once to generate the master geometry files
    airfoil_source_dir = os.path.join(script_root, 'subsystems/aerodynamics/vfp_analysis/airfoils')
    master_fpcon_dir = run_fpcon_once(script_root, wing_name, airfoil_source_dir, mach_for_fpcon)
    
    if not master_fpcon_dir:
        print("\n❌ Initial FPCON run failed. Aborting all sweeps.")
    else:
        # Loop through each angle of attack
        for alpha_idx, current_alpha in enumerate(alpha_sweep):
            print(f"\n{'='*25} STARTING SWEEP FOR ALPHA = {current_alpha:.2f} deg {'='*25}")
            previous_run_name = None
            previous_case_dir = None
            
            # Loop through the Mach numbers for the current angle of attack
            for mach_idx, current_mach in enumerate(mach_list):
                current_run_name = generate_case_name(wing_name, current_mach, current_alpha, Re)
                
                # The very first run of the entire script is not a continuation.
                # All subsequent runs (whether for a new Mach or a new Alpha) are continuations.
                is_continuation_run = not (alpha_idx == 0 and mach_idx == 0)
                
                case_run_dir = setup_case_directory(script_root, wing_name, current_run_name)
                
                if not case_run_dir:
                    print(f"Aborting sweep due to directory setup failure for {current_run_name}.")
                    break # Break from the Mach loop
                
                # Run the VFP simulation for the current point
                # NOTE: A more complete script would generate a FLOWVIS.DAT file here
                # based on current_mach, current_alpha, and is_continuation_run status.
                # This example assumes vfphe.exe can handle this implicitly or a file is pre-made.
                if run_vfp_case(case_run_dir, master_fpcon_dir, current_run_name, current_mach, current_alpha, is_continuation_run, previous_run_name, previous_case_dir):
                    print(f"\n✅ Case complete for M={current_mach:.3f}, alpha={current_alpha:.2f}. Results are in: {case_run_dir}")
                    previous_run_name = current_run_name
                    previous_case_dir = case_run_dir
                else:
                    print(f"\n❌ Simulation failed for M={current_mach:.3f}, alpha={current_alpha:.2f}. Aborting remaining sweeps.")
                    # To prevent further failed runs, we can exit all loops.
                    master_fpcon_dir = None # Prevents further alpha sweeps
                    break # Break from the Mach loop
            
            if not master_fpcon_dir:
                break # Break from the Alpha loop
        
        print("\nAll simulation sweeps finished.")

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    run_simulation()
