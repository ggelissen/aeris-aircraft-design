import openvsp as vsp
from design_variables import *
from subsystems.structures.main_struct import struct_main


def aerodynamic_analysis(designvars : DesignParameters = None):
    return panel_openvsp(designvars) + parasite_drag_2D(designvars)

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