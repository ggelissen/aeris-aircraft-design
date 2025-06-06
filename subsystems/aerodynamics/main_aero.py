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
    # vsp.SetIntAnalysisInput()
    # vsp.SetDoubleAnalysisInput()
    # vsp.SetVec3dAnalysisInput()
    # vsp.SetStringAnalysisInput()

    # Execute analysis
    vsp.ExecAnalysis("VSPAEROSweep")
    results = vsp.FindLatestResultsID("VSPAEROSweep")

    # Print results
    vsp.PrintResults(results)
    # vsp.GetDoubleResults()

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