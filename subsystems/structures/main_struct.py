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
from vspfunctions import print_all_params, plotSTL, create_fuselage, create_wing, create_V_tail, create_engines
matplotlib.use('Qt5Agg')
import openvsp as vsp
import vspfunctions
import subsystems.structures.stanag as stanag
from design_variables import *

def struct_main(designvars: DesignParameters = None):

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


    # Step 4: Simulate aircraft with loads

    # Step 5: Change Structural variables to optimise for mass

    # Step 6: Save progress and share optimised variables to other subsystems. Share aircraft 3D model to aerodynamics.

    vsp.Update()

    # Save as VSP3 file
    prev_cwd = os.getcwd()
    os.chdir(os.getcwd() + "/data")
    vsp.WriteVSPFile("aircraft_model.vsp3")
    os.chdir(prev_cwd)

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
    struct_main(AERIS)
