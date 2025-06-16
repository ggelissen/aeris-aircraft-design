import os
import subprocess
import shutil

# ==============================================================================
# 1. DEFINE SIMULATION PARAMETERS
# ==============================================================================
# --- Main Simulation Control ---
wing_name = "w14" # Base name for the wing
fpcon_source_dir = os.path.join(os.path.dirname(__file__), "vpwin_fpv20")
vfp_source_dir = os.path.join(os.path.dirname(__file__), "vpwin_vfphv20")
# Directory where your airfoil .DAT files are stored
airfoil_source_dir = os.path.join(os.path.dirname(__file__), "airfoils")

# --- Angle of Attack Sweep ---
# List of angles of attack (in degrees) to simulate
alpha_sweep = [0.0, 0.5, 1.0, 1.5, 2.0]

# --- Flow Conditions ---
Mach_freestream = 0.65 # Freestream Mach number
Re = 9500000 # Reynolds number based on mean geometric chord

# --- Wing Geometry ---
is_cranked = True # True for a cranked wing, False for a simple swept/tapered wing
A_g = 12.0 # Gross aspect ratio
crank_c0_taper_ratio = 0.5 # Taper ratio of the inner panel (crank chord / root chord)
tip_c0_taper_ratio = 0.294 # Taper ratio of the outer panel (tip chord / root chord)
eta_sc = 0.4 # Non-dimensional spanwise location of the crank (y_crank / s)
Lambda_lei = 35.0 # Inner panel leading-edge sweep (degrees)
Lambda_leo = 35.0 # Outer panel leading-edge sweep (degrees)

# --- Wing Sections, Twist, and Airfoils ---
# NSECT: Total number of control sections. This is determined automatically
#        from the length of the 'section_data' list below.
# NSECT1: The control section number corresponding to the crank.
#         For a simple swept wing (is_cranked=False), this is equal to NSECT.
#         For a cranked wing, it is the index (1-based) of the crank section.
NSECT1 = 2
#
# section_data: A list defining each control section of the wing from root to tip.
# Each entry is a dictionary with the following keys:
#   'etas': Non-dimensional spanwise location (y/s). Must go from 0.0 to 1.0.
#   'hsect': Vertical position of the twist axis (z/c0).
#   'xtwsec': Chordwise location of the twist axis (x/c, from 0 to 1).
#   'twsin': Twist angle in degrees (positive is nose-up).
#   'airfoil': The filename of the airfoil .DAT file for this section.
section_data = [
    {'etas': 0.0, 'hsect': 0.0, 'xtwsec': 0.5, 'twsin': 4.0, 'airfoil': '0412vgk.dat'},
    {'etas': 0.4, 'hsect': 0.0, 'xtwsec': 0.5, 'twsin': 2.0, 'airfoil': '0412vgk.dat'},
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
    mach_str = f"m{str(int(mach * 100))}"
    alpha_str = f"a{str(abs(alpha)).replace('.', 'p')}"
    if alpha < 0:
        alpha_str = "am" + alpha_str[1:] # am for alpha minus

    re_in_millions = re / 1_000_000
    re_str = f"re{int(re_in_millions)}m"
    if re_in_millions != int(re_in_millions):
        re_str += str(int((re_in_millions - int(re_in_millions)) * 10))

    return f"{wing}{mach_str}{alpha_str}{re_str}"

def setup_case_directory(base_dir, wing_name, run_name):
    """Creates a clean, self-contained directory for a single simulation case."""
    wing_results_dir = os.path.join(base_dir, "results", wing_name)
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

def run_fpcon_once(base_dir, wing_name, airfoil_src_dir):
    """
    Generates master geometry files using fpcon.exe.
    This is run only once for the entire alpha sweep. It now handles multiple
    airfoils by calculating NCHANGE and providing the correct sequence of
    inputs to the fpcon executable.
    """
    print("\n--- Step 1: Running FPCON to generate master geometry files ---")
    wing_results_dir = os.path.join(base_dir, "results", wing_name)
    os.makedirs(wing_results_dir, exist_ok=True)
    
    fpcon_run_dir = os.path.join(wing_results_dir, "geometry_master")
    if os.path.exists(fpcon_run_dir):
        shutil.rmtree(fpcon_run_dir)
    
    try:
        shutil.copytree(fpcon_source_dir, fpcon_run_dir)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find source FPCON directory: {e.filename}")
        return None

    # --- Prepare airfoil files and determine NCHANGE and NC values ---
    # NCHANGE: Number of sections where the airfoil differs from the one inboard.
    # NC values: The 1-based indices of the sections where the change occurs.
    # fpcon expects: NCHANGE, then NC1, NC2..., then root airfoil file, 
    # then the NCHANGE subsequent airfoil files for the sections where changes occur.
    
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
            changed_section_indices.append(i + 1) # Add the 1-based index
            changed_airfoil_files.append(current_airfoil)

    root_airfoil = section_data[0]['airfoil']

    print(f"Determined NCHANGE = {nchange}")
    print(f"Changed section indices (NC values): {changed_section_indices}")
    print(f"Root airfoil: {root_airfoil}")
    print(f"Changed airfoil files for fpcon: {changed_airfoil_files}")
    
    # Copy all unique airfoil files to the run directory
    try:
        for airfoil in unique_airfoils:
            src_path = os.path.join(airfoil_src_dir, airfoil)
            dest_path = os.path.join(fpcon_run_dir, airfoil)
            shutil.copy(src_path, dest_path)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find airfoil file: {e.filename}")
        print(f"Please ensure it exists in: {airfoil_src_dir}")
        return None
    
    # --- Generate fpcon input file ---
    nsect = len(section_data)
    local_nsect1 = nsect if not is_cranked else NSECT1

    input_file = "fpcon_input.txt"
    with open(os.path.join(fpcon_run_dir, input_file), "w") as f:
        f.write("y\n" if is_cranked else "n\n")
        f.write(f"{A_g} {tip_c0_taper_ratio} {crank_c0_taper_ratio} {eta_sc}\n")
        f.write(f"{Lambda_lei} {Lambda_leo}\n")
        f.write(f"{nsect}\n")
        f.write(f"{local_nsect1}\n")
        f.write(f"{nchange}\n")
        
        # Write the NC values (1-based indices of changed sections)
        for index in changed_section_indices:
            f.write(f"{index}\n")

        # Write the airfoil filenames: root first, then the NCHANGE changed files.
        f.write(f"{root_airfoil}\n")
        for airfoil in changed_airfoil_files:
            f.write(f"{airfoil}\n")
            
        # Write the section properties (etas, hsect, xtwsec, twsin)
        for data in section_data:
            f.write(f"{data['etas']} {data['hsect']} {data['xtwsec']} {data['twsin']}\n")
            
        f.write(f"{body_radius if has_fuselage else 0.0}\n")
        f.write(f"{wing_name}\n")
        f.write("n\n")
        f.write(f"{Mach_freestream} {alpha_sweep[0]}\n")
    
    # --- Execute FPCON ---
    try:
        # Removed capture_output=True to allow console output to be displayed in real-time
        subprocess.run(f'"fpcon.exe" < {input_file}', shell=True, check=True, cwd=fpcon_run_dir)
        print("FPCON executed successfully.")
        return fpcon_run_dir
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FPCON execution failed. Return code: {e.returncode}")
        return None
    except FileNotFoundError:
        print(f"ERROR: 'fpcon.exe' not found in {fpcon_run_dir}. Please check your fpcon_source_dir.")
        return None


def run_vfp_case(case_run_dir, master_fpcon_dir, current_run_name, current_alpha, is_continuation, prev_run_name, prev_case_dir):
    """Runs a single VFP case, either initial or continuation."""
    print(f"\n{'='*20} RUNNING CASE: {current_run_name} {'='*20}")
    
    try:
        # --- Prepare Inputs ---
        shutil.copy(os.path.join(master_fpcon_dir, "GEO.DAT"), os.path.join(case_run_dir, "geo.dat"))
        shutil.copy(os.path.join(master_fpcon_dir, "MAP.DAT"), os.path.join(case_run_dir, "map.dat"))

        if has_fuselage:
            input_file_fuse = "fuse_input.txt"
            with open(os.path.join(case_run_dir, input_file_fuse), "w") as f:
                f.write(f"{Mach_freestream}\n")
                f.write(f"{fuselage_length} {fore_body_length} {aft_body_length}\n")
                f.write(f"{wing_root_le_pos}\n")
            # Removed capture_output=True
            subprocess.run(f'"vfpfusegenv2.exe" < {input_file_fuse}', shell=True, check=True, cwd=case_run_dir)

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
            # Removed capture_output=True
            subprocess.run(f'"vfptvkbodyv8.exe" < {input_file_body}', shell=True, check=True, cwd=case_run_dir)
            shutil.copy(os.path.join(case_run_dir, "FLOWdmmean.dat"), os.path.join(case_run_dir, "fort.15"))
        else:
            print("ERROR: Wing-only flow file generation not implemented.")
            return False

        shutil.copy(os.path.join(case_run_dir, "map.dat"), os.path.join(case_run_dir, "fort.14"))
        shutil.copy(os.path.join(case_run_dir, "geo.dat"), os.path.join(case_run_dir, "fort.10"))

        if is_continuation:
            print(f"This is a continuation run. Using dump files from: {prev_run_name}")
            for i in [11, 21, 50, 51, 52, 55]:
                dump_file_name = f"{prev_run_name}.fort{i}"
                src_path = os.path.join(prev_case_dir, dump_file_name)
                if os.path.exists(src_path):
                    shutil.copy(src_path, os.path.join(case_run_dir, f"fort.{i}"))
        
        # --- Run Core Solver ---
        print(f"\n--- Running VFP Core Solver for alpha = {current_alpha} ---")
        # Removed capture_output=True
        subprocess.run('"vfphe.exe"', shell=True, check=True, cwd=case_run_dir)
        print("VFP core solver finished successfully.")

        # --- Post-Process and archive results with standard names ---
        print("\n--- Post-Processing and Archiving Results ---")
        for src, dest_suffix in {'fort.16': 'vis', 'fort.18': 'forces', 'fort.19': 'cp'}.items():
            if os.path.exists(os.path.join(case_run_dir, src)):
                shutil.move(os.path.join(case_run_dir, src), os.path.join(case_run_dir, f"{current_run_name}.{dest_suffix}"))
        
        shutil.copy(os.path.join(case_run_dir, "geo.dat"), os.path.join(case_run_dir, f"{current_run_name}.geo"))
        shutil.copy(os.path.join(case_run_dir, "fort.15"), os.path.join(case_run_dir, f"{current_run_name}.dat"))

        # --- Run Wave Drag and archive results ---
        if os.path.exists(os.path.join(case_run_dir, "fort.70")):
            shutil.copy(os.path.join(case_run_dir, "fort.70"), os.path.join(case_run_dir, "flow70.dat"))
            shutil.copy(os.path.join(case_run_dir, "fort.71"), os.path.join(case_run_dir, "flow71.dat"))
            # Removed capture_output=True
            subprocess.run('"f137b1.exe"', shell=True, check=True, cwd=case_run_dir)
            if os.path.exists(os.path.join(case_run_dir, "wavedrg73.dat")):
                shutil.copy(os.path.join(case_run_dir, "wavedrg73.dat"), os.path.join(case_run_dir, f"{current_run_name}wavedrg73.dat"))
            print("Wave drag calculation complete.")
        else:
            print("Wave drag inputs (fort.70) not found, skipping for this case.")
        
        # Archive dump files for next continuation run
        for i in [11, 21, 50, 51, 52, 55]:
            if os.path.exists(os.path.join(case_run_dir, f"fort.{i}")):
                shutil.copy(os.path.join(case_run_dir, f"fort.{i}"), os.path.join(case_run_dir, f"{current_run_name}.fort{i}"))

        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR during VFP case run for {current_run_name}: {e}")
        return False

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    script_root = os.path.dirname(os.path.abspath(__file__))
    
    # Run FPCON once to generate the master geometry files (GEO.DAT, MAP.DAT)
    master_fpcon_dir = run_fpcon_once(script_root, wing_name, airfoil_source_dir)
    
    if not master_fpcon_dir:
        print("\n❌ Initial FPCON run failed. Aborting sweep.")
    else:
        previous_run_name = None
        previous_case_dir = None
        
        # Loop through the specified angles of attack
        for i, current_alpha in enumerate(alpha_sweep):
            current_run_name = generate_case_name(wing_name, Mach_freestream, current_alpha, Re)
            is_continuation_run = (i > 0)
            
            case_run_dir = setup_case_directory(script_root, wing_name, current_run_name)
            
            if not case_run_dir:
                print(f"Aborting sweep due to directory setup failure for {current_run_name}.")
                break
            
            # Run the VFP simulation for the current angle of attack
            if run_vfp_case(case_run_dir, master_fpcon_dir, current_run_name, current_alpha, is_continuation_run, previous_run_name, previous_case_dir):
                print(f"\n✅ Case complete for alpha = {current_alpha}. Results are in: {case_run_dir}")
                previous_run_name = current_run_name
                previous_case_dir = case_run_dir
            else:
                print(f"\n❌ Simulation failed for alpha = {current_alpha}. Aborting sweep.")
                break
        
        print("\nAlpha sweep finished.")

