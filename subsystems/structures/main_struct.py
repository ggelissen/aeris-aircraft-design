## Requirments:
# python=3.11
# numpy!=1.19.4
import os


# Before running, make sure to run:
# pip install -r requirements.txt

from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits import mplot3d
import matplotlib
import pyvista as pv
import numpy as np
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from subsystems.structures.vspfunctions import calculate_cg, calculate_wet_areas, calculate_fuel_capacity
from subsystems.structures.vspfunctions import calculate_cg, calculate_wet_areas
from subsystems.structures.vspfunctions import print_all_params, plotSTL, create_fuselage, create_wing, create_V_tail, create_engines
try:
    matplotlib.use('Qt5Agg')
except:
    matplotlib.use('Agg')
import openvsp as vsp
<<<<<<< HEAD
import subsystems.structures.vspfunctions
#import subsystems.structures.stanag as stanag
from design_variables import *
from subsystems.structures.wing_structure_generation import wing_structure_generation
=======

#import subsystems.structures.stanag as stanag
from design_variables import *
#from wing_structure_generation import generate_wing_structure_3D
from material_selection import run_material_selection_analysis
>>>>>>> origin/main

def struct_main(designvars: DesignParameters = None, show_3d: bool = True):

    # Step 1: Loading analysis
    


    # Step 2 Import geometric variables from Class I/II methods
    # span =
    # root_chord =
    # tip_chord =
    # sweep =

    # Step 3: Create a VSP model using the imported geometric variables
    vsp.ClearVSPModel()


    #### Add fuselage and change fuselage shape to make room for payload. This is done by changing the cross-sections of the fuselage.
    create_fuselage(designvars)

    ### Add wing
    create_wing(designvars)

    ### Add v_tail
    create_V_tail(designvars)

    ### Add engines
    create_engines(designvars)

    # Add fuel tank
    calculate_fuel_capacity(designvars)

    prev_cwd = os.getcwd()
    os.chdir(os.getcwd() + "/data")
    vsp.WriteVSPFile("aircraft_model2.vsp3")
    os.chdir(prev_cwd)

    ### Calculate specifications
    calculate_cg(designvars)
    calculate_wet_areas(designvars)

    ### Set up structure
<<<<<<< HEAD
    wing_structure_generation(designvars, plot=show_3d)
=======
    #wing_structure_generation(designvars)

    # Freeze geometry:

    vsp.UpdateGeom(designvars.wing.wingid)
    designvars.wing.b_w = vsp.GetParmVal(designvars.wing.wingid, "TotalSpan", "WingGeom")
    vsp.UpdateGeom(designvars.wing.wingid)
    vsp.SetComputationFileName(vsp.DEGEN_GEOM_CSV_TYPE, "data/DegenGeom.csv")
    vsp.SetSetFlag(designvars.wing.wingid, 8, True)
    vsp.ComputeDegenGeom(8, vsp.DEGEN_GEOM_CSV_TYPE)
    data = pd.read_csv("data/DegenGeom.csv", header=None, skiprows=10, nrows=2211)
    datanp = data.to_numpy()
    designvars.structurecoords = np.round(datanp, decimals=6)

    run_material_selection_analysis(designvars)
    #fuselage_cross_section(designvars, )


    # cross_sectional_structure_along_span(designvars, 0)
    # cross_sectional_structure_along_span(designvars, 0.871)
    # cross_sectional_structure_along_span(designvars, 0.9)
    # cross_sectional_structure_along_span(designvars, 0.95)
    #fuselage_cross_section(designvars, 0.5)

    #generate_wing_structure_3D(designvars, num_spanwise_points=1001)

>>>>>>> origin/main

    # Step 4: Simulate aircraft with loads

    # Step 5: Change Structural variables to optimise for mass


    # Step 6: Save progress and share optimised variables to other subsystems. Share aircraft 3D model to aerodynamics.
    vsp.Update()

    # Save as VSP3 file
    prev_cwd = os.getcwd()
    os.chdir(os.getcwd() + "/data")
    vsp.WriteVSPFile("aircraft_model.vsp3")
    os.chdir(prev_cwd)

    if show_3d:
        # Export to STL or other formats
        prev_cwd = os.getcwd()
        os.chdir(os.getcwd() + "/data")
        vsp.ExportFile("aircraft_model.stl", vsp.SET_ALL, vsp.EXPORT_STL)
        #vsp.ExportFile('aircraft_model.step', vsp.SET_ALL, vsp.EXPORT_STEP)
        vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
        for geom in vsp.FindGeoms():
            vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
        os.chdir(prev_cwd)



        # PLOTTING
        plotSTL(os.getcwd() + '/data/aircraft_model.stl')


if __name__ == "__main__":
    AERIS = DesignParameters()
    AERIS.load_from_yaml("design_config.yaml")
    struct_main(AERIS, show_3d=True)
