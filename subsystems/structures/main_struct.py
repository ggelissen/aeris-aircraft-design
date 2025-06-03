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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from subsystems.structures.vspfunctions import calculate_cg, calculate_wet_areas
from vspfunctions import calculate_cg, calculate_wet_areas
from vspfunctions import print_all_params, plotSTL, create_fuselage, create_wing, create_V_tail, create_engines
matplotlib.use('Qt5Agg')
import openvsp as vsp
import vspfunctions
#import subsystems.structures.stanag as stanag
from design_variables import *
from wing_structure_generation import wing_structure_generation

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

    ### Calculate specifications
    calculate_cg(designvars)
    calculate_wet_areas(designvars)

    ### Set up structure
    wing_structure_generation(designvars)

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
        os.chdir(prev_cwd)



        # PLOTTING
        plotSTL(os.getcwd() + '/data/aircraft_model.stl')


if __name__ == "__main__":
    AERIS = DesignParameters()
    AERIS.load_from_yaml("design_config.yaml")
    struct_main(AERIS, show_3d=True)
