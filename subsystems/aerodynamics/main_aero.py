import openvsp as vsp
from design_variables import *
from subsystems.structures.main_struct import struct_main
import subprocess
import os
import numpy as np
import shutil

# RUN IN DOCKER: https://hub.docker.com/r/lhuirne/dsewithaero . Use launch.json (ask google what that means)

def send_command(command, proc):
    proc.stdin.write(command + '\n')
    proc.stdin.flush()
    output = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        output.append(line)
        if line.strip() == "":  # crude end detection
            break
    return ''.join(output)

def aerodynamic_analysis(designvars : DesignParameters = None):
    cur_cwd = os.getcwd()
    os.chdir(os.path.join(cur_cwd, "data"))
    speed_mach = 0.85  # Mach number for the analysis
    aoa = 2  # Angle of attack in degrees
    eta_crank = vsp.GetParmVal(designvars.wing.wingid, 'Span', 'XSec_1') / (vsp.GetParmVal(designvars.wing.wingid, 'Span', 'XSec_1') + vsp.GetParmVal(designvars.wing.wingid, 'Span', 'XSec_2'))
    chord_root = vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),1), 'Root_Chord'))
    re_at_chord_root = 4000000  # Reynolds number at root chord
    with open("EXIN1.DAT", "w") as f:
        f.write("y\n")
        f.write(f"   {vsp.GetParmVal(designvars.wing.wingid,'TotalAR', 'WingGeom')}      {vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),2), 'Tip_Chord'))/vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),1), 'Root_Chord'))}      {vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),1), 'Tip_Chord'))/vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),1), 'Root_Chord'))}      {eta_crank}    \n")
        f.write(f"   {np.rad2deg(designvars.wing.Lambda_0_w)}       {np.rad2deg(designvars.wing.Lambda_0_w)}    \n")
        f.write("           3\n")
        f.write("           2\n")
        f.write("           0\n")
        f.write("Airfoil.dat \n")
        f.write("  0.0000000E+00  0.0000000E+00  0.0000000E+00  0.0000000E+00\n")
        f.write(f"  {eta_crank}      0.0000000E+00  0.0000000E+00  0.0000000E+00\n")
        f.write("   1.000000      0.0000000E+00  0.0000000E+00  0.0000000E+00\n")
        f.write(f"  {designvars.fuselage.D_f/vsp.GetParmVal(vsp.GetXSecParm(vsp.GetXSec(vsp.GetXSecSurf(designvars.wing.wingid,0),1), 'Root_Chord'))}    \n")
        f.write("TESTRUNNER                                                                      \n")
        f.write("y\n")
        f.write(f"  {speed_mach}       {aoa}    \n")
    with open("EXIN1.DAT", "w") as f:
        f.write("y\n")
        f.write(f"   8      0.3      0.5      0.4    \n")
        f.write(f"   35       35    \n")
        f.write("           3\n")
        f.write("           2\n")
        f.write("           0\n")
        f.write("nac0012.dat \n")
        f.write("  0.0000000E+00  0.0000000E+00  0.5000000E+00  4.0000000E+00\n")
        f.write(f"  0.4      0.0000000E+00  0.5000000E+00  2.0000000E+00\n")
        f.write("   1.000000      0.0000000E+00  0.0000000E+00  0.0000000E+00\n")
        f.write(f"  0.2    \n")
        f.write("TESTRUNNER2                                                                   \n")
        f.write("n\n")
        f.write(f" 0.75       2    \n")

    print('Start fpcon')
    subprocess.Popen("wine /root/DSEproject/subsystems/aerodynamics/fpcon.exe  < EXIN1.DAT", shell=True)
    print('Generated files')
    shutil.copy('GEO.DAT', 'test.geo')
    shutil.copy('GEO.DAT', 'geo.dat')
    shutil.copy('MAP.DAT', 'test2.map')
    # Start a persistent shell subprocess
    # proc = subprocess.Popen(
    #     ['/bin/bash'],  # Use 'cmd.exe' on Windows
    #     stdin=subprocess.PIPE,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True,  # Ensure text mode (str instead of bytes)
    #     bufsize=1
    # )
    print('Starting vpf things')
    with open("EXIN2.DAT", "w") as f:
        f.write(f"{speed_mach}\n")
        f.write(f"{vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} {vsp.GetParmVal(designvars.fuselage.fuseid, 'XLocPercent', 'XSec_1')*vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} {vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root - vsp.GetParmVal(designvars.fuselage.fuseid, 'XLocPercent', 'XSec_3')*vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} \n")
        f.write(f'{(designvars.wing.xpos - np.tan(designvars.wing.Lambda_0_w) * designvars.fuselage.D_f/2)/chord_root}  \n')
    with open("EXIN2.DAT", "w") as f:
        f.write(f"0.75\n")
        f.write(f"{vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} {vsp.GetParmVal(designvars.fuselage.fuseid, 'XLocPercent', 'XSec_1')*vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} {vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root - vsp.GetParmVal(designvars.fuselage.fuseid, 'XLocPercent', 'XSec_3')*vsp.GetParmVal(designvars.fuselage.fuseid, 'Length', 'Design')/chord_root} \n")
        f.write(f'{(designvars.wing.xpos - np.tan(designvars.wing.Lambda_0_w) * designvars.fuselage.D_f/2)/chord_root}  \n')

    #subprocess.Popen('wine /root/DSEproject/subsystems/aerodynamics/vpwin_vfphv20/vfpfusegenv2.exe < EXIN2.DAT', shell=True)
    print("Starting vfptvkbodyv8")
    with open("EXIN3.DAT", "w") as f:
        f.write("y\n")
        f.write("Testrun \n")
        f.write('y\n')
        f.write(f'{aoa}, 0.0\n')
        f.write(f'{re_at_chord_root}\n')
        f.write("3\n")
        f.write("3\n")
        f.write(f"0, {designvars.wing.simulation_parms['Transition_location_for_effective_aoa_0.03_upper_surface']}, {np.min([designvars.wing.simulation_parms['Transition_location_for_effective_aoa_0.03_upper_surface'] + 0.05, 1.0])}, {designvars.wing.simulation_parms['momentum_thickness_jump_for_effective_aoa_0.03_upper_surface']} \n")
        f.write(f"{eta_crank}, {designvars.wing.simulation_parms['Transition_location_for_effective_aoa_0.03_upper_surface']}, {np.min([designvars.wing.simulation_parms['Transition_location_for_effective_aoa_0.03_upper_surface'] + 0.05, 1.0])}, {designvars.wing.simulation_parms['momentum_thickness_jump_for_effective_aoa_0.03_upper_surface']} \n")
        f.write(f'1.0, {designvars.wing.simulation_parms["Transition_location_for_effective_aoa_-1.655_upper_surface"]}, {np.min([designvars.wing.simulation_parms["Transition_location_for_effective_aoa_-1.655_upper_surface"] + 0.05, 1.0])}, {designvars.wing.simulation_parms["momentum_thickness_jump_for_effective_aoa_-1.655_upper_surface"]} \n')
        f.write(f'0, {designvars.wing.simulation_parms["Transition_location_for_effective_aoa_0.03_lower_surface"]}, {np.min([designvars.wing.simulation_parms["Transition_location_for_effective_aoa_0.03_lower_surface"] + 0.05, 1.0])}, {designvars.wing.simulation_parms["momentum_thickness_jump_for_effective_aoa_0.03_lower_surface"]} \n')
        f.write(f'{eta_crank}, {designvars.wing.simulation_parms["Transition_location_for_effective_aoa_0.03_lower_surface"]}, {np.min([designvars.wing.simulation_parms["Transition_location_for_effective_aoa_0.03_lower_surface"] + 0.05, 1.0])}, {designvars.wing.simulation_parms["momentum_thickness_jump_for_effective_aoa_0.03_lower_surface"]} \n')
        f.write(f'1.0, {designvars.wing.simulation_parms["Transition_location_for_effective_aoa_-1.655_lower_surface"]}, {np.min([designvars.wing.simulation_parms["Transition_location_for_effective_aoa_-1.655_lower_surface"] + 0.05, 1.0])}, {designvars.wing.simulation_parms["momentum_thickness_jump_for_effective_aoa_-1.655_lower_surface"]} \n')

    subprocess.Popen('wine /root/DSEproject/subsystems/aerodynamics/vpwin_vfphv20/visflow.exe < EXIN3.DAT', shell=True)
    shutil.copy('VISFLOW.DAT', 'flowfile.dat')
    # subprocess.Popen('wine /root/DSEproject/subsystems/aerodynamics/vpwin_vfphv20/vfptvkbodyv8.exe < EXIN3.DAT', shell=True)
    # print("finished vfptvkbodyv8")
    # shutil.copy('FLOWdmmean.DAT', 'flowfile.dat')
    # shutil.copy('test.geo', 'fort.10')
    # shutil.copy('test2.map', 'fort.14')
    # shutil.copy('flowfile.dat', 'fort.15')
    # print('Starting Aero run')
    subprocess.Popen('wine /root/DSEproject/subsystems/aerodynamics/vpwin_vfphv20/vfphe.exe', shell=True)
    # Move files
    print('Moving/Copying...')
    shutil.move("fort.16", "testflowfile.flow")
    shutil.move("fort.17", "testflowfile.conv")
    shutil.move("fort.22", "test.mapout")
    shutil.move("fort.18", "testflowfile.forces")
    shutil.move("fort.19", "testflowfile.cp")
    shutil.move("fort.20", "testflowfile.vis")
    shutil.move("fort.24", "testflowfile.sum")
    shutil.copy("fort.11", "testflowfile.fort11")
    shutil.copy("fort.15", "testflowfile.fort15")
    shutil.copy("fort.21", "testflowfile.fort21")
    shutil.copy("fort.50", "testflowfile.fort50")
    shutil.copy("fort.51", "testflowfile.fort51")
    shutil.copy("fort.52", "testflowfile.fort52")
    shutil.copy("fort.55", "testflowfile.fort55")
    shutil.copy("fort.70", "flow.70")
    shutil.copy("fort.71", "flow.71")
    print('Start wave drag aero')
    subprocess.Popen('wine /root/DSEproject/subsystems/aerodynamics/vpwin_vfphv20/f137b1.exe', shell=True)
    shutil.copy("wavedrg73.dat", f"testflowfilewavedrg73.dat")
    shutil.copy("wavedrg74.dat", f"testflowfilewavedrg74.dat")
    shutil.copy("wavedrg75.dat", f"testflowfilewavedrg75.dat")
    shutil.copy("wavedrg76.dat", f"testflowfilewavedrg76.dat")
 
    print('Finished aero') 



    


    os.chdir(cur_cwd)
    #return panel_openvsp(designvars) + parasite_drag_2D(designvars)

def panel_openvsp(designvars : DesignParameters = None):
    """Perform aerodynamic panel analysis using OpenVSP.
    Output: Aerodynamic loads distribution along span"""

    # add geometries to a set (set 15) that will be used for panel analysis
    vsp.Update()
    vsp.SetSetFlag(designvars.wing.wingid, 15, True)
    vsp.SetSetFlag(designvars.fuselage.fuseid, 15, True)
    vsp.SetSetFlag(designvars.control_surface.vtailid, 15, True)
    vsp.SetSetFlag(designvars.engine.engine_id, 15, True)

    # Activate standard vspaero settings
    vsp.SetAnalysisInputDefaults("VSPAEROSweep")

    # Print possible inputs
    vsp.PrintAnalysisDocs("VSPAEROSweep")

    # Set analysis inputs

    vsp.SetIntAnalysisInput("VSPAEROSweep", "AnalysisMethod", [vsp.PANEL]) # Set analysis mode to PANEL method instead of VLM
    vsp.SetIntAnalysisInput("VSPAEROSweep", "GeomSet", [15]) # Apply analysis to set 15 as defined above
    vsp.SetIntAnalysisInput("VSPAEROSweep", "RefFlag", [1])  # 1 for wing reference area, 0 for manually entered area
    vsp.SetIntAnalysisInput("VSPAEROSweep", "MACFlag", [1])  # 1 for wing mean aerodynamic chord, 0 average chord as reference chord
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ScurveFlag", [0])  # 0 for no Stot, 1 for Scurve as reference areea. Scurve takes into account possible wing to fuselage blending if that is set up in openvsp but this is not the case
    vsp.SetStringAnalysisInput("VSPAEROSweep", "WingID", [designvars.wing.wingid]) # Wing used to calculate reference areas/lengths
    vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry", [vsp.SYM_XZ])
    vsp.SetIntAnalysisInput("VSPAEROSweep", "Precondition", [vsp.PRECON_MATRIX])  # choose preconditioner
    vsp.SetIntAnalysisInput("VSPAEROSweep", "KTCorrection", [1])  # Use KT correction for panel method
    vsp.SetIntAnalysisInput("VSPAEROSweep", "2DFEMFlag", [0])  # 0 for no 2D FEM, 1 for using 2D FEM for panel method
    vsp.SetIntAnalysisInput("VSPAEROSweep", "FixedWakeFlag", [0])  # 0 for no fixed wake, 1 for fixed wake
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ClmaxToggle", [vsp.CLMAX_OFF])  # Use panel wake for panel method

    # Set cg for moment coefficents calculation
    vsp.SetIntAnalysisInput("VSPAEROSweep", "CGGeomSet", [15])  # Use the same set as above for CG calculation
    vsp.SetIntAnalysisInput("VSPAEROSweep", "NumMassSlic", [20])  # number of cross sectional slices to use for CG calculation
    vsp.SetIntAnalysisInput("VSPAEROSweep", "MassSliceDir", [vsp.X_DIR]) # Use X direction for CG calculation
    #TODO: Set CG location, probably not really needed

    # Flow conditions
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [0.0])  # Start angle of attack in degrees
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd", [10.0])  # End angle of attack in degrees
    vsp.SetIntAnalysisInput("VSPAEROSweep", "AlphaNpts", [11])  # Number of angles of attack to calculate
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "BetaStart", [0.0])  # Start sideslip angle in degrees
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "BetaEnd", [0.0])  # End sideslip angle in degrees
    vsp.SetIntAnalysisInput("VSPAEROSweep", "BetaNpts", [1])  # Number of sideslip angles to calculate
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", [0.85])  # Mach number
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachEnd", [0.85])  # End Mach number
    vsp.SetIntAnalysisInput("VSPAEROSweep", "MachNpts", [1])  # Number of Mach numbers to calculate
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "ReCref", [8.0e6])  # Start Reynolds number
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "ReCrefEnd", [8.0e6])  # End Reynolds number
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ReCrefNpts", [1])  # Number of Reynolds numbers to calculate





    # vsp.SetIntAnalysisInput()
    # vsp.SetDoubleAnalysisInput()
    # vsp.SetVec3dAnalysisInput()
    # vsp.SetStringAnalysisInput()

    # Execute analysis
    results  = vsp.ExecAnalysis("VSPAEROSweep")


    # Print results
    vsp.PrintResults(results)
    print(vsp.GetStringResults(results, "ResultsVec"))

    return 0


def parasite_drag_2D(designvars : DesignParameters = None):
    """
    Calculate the parasite drag using 2D airfoil data and use it to create spanwise parasite drag distribution.
    """
    # Placeholder for 2D airfoil data calculation
    return 0

if __name__ == '__main__':
    AERIS = DesignParameters()
    AERIS.load_from_yaml("design_config.yaml")
    struct_main(AERIS, show_3d=False)
    aerodynamic_analysis(AERIS)

