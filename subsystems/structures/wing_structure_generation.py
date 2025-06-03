import numpy as np

import openvsp as vsp
import os
from design_variables import *
from vspfunctions import *
import scipy
import matplotlib.pyplot as plt


def wing_structure_generation(designvars: DesignParameters = None):
    """
    Generates the wing structure for the aircraft model using VSP.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - NCell: Number of cells for the wing structure.
    """
    cross_sectional_structure_along_span(designvars, 0.5)


def cross_sectional_structure_along_span(designvars: DesignParameters = None, spanwise_position: float = 0.0):
    """
    Generates the cross-sectional structure along the span of the wing.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - NCell: Number of cells for the wing structure.
    - spanwise_position: Position along the span where the cross-section is generated as a fraction of the total span (0.0 to 1.0).
    """
    outline, chord_length = cross_section(designvars, spanwise_position)
    split_index = np.argmin(outline[:, 0])
    upper_airfoil = outline[:split_index]
    lower_airfoil = outline[split_index:]


    for i in range(designvars.wing.wingsection.num_spars):
        spar_pos = designvars.wing.wingsection.spars[f"Spar{i+1}"]["x_pos_frac"] * chord_length
        y_0 = scipy.interpolate.interp1d(upper_airfoil[:, 0], upper_airfoil[:, 1], kind='linear')(spar_pos)
        y_1 = scipy.interpolate.interp1d(lower_airfoil[:, 0], lower_airfoil[:, 1], kind='linear')(spar_pos)
        spar_points = np.array([[spar_pos, y_0], [spar_pos, y_1]])
        plt.plot(spar_points[:, 0], spar_points[:, 1])
        # t_flange_1 = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_flange_1_mm"] # in mm
        # t_flange_2 = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_flange_2_mm"]
        # t_web = designvars.wing.wingsection.spars[f"Spar{i+1}"]["t_web_mm"]
        # t_flange_width = designvars.wing.wingsection.spars[f"Spar{i+1}"]["flange_width_mm"]

    for i in range(designvars.wing.wingsection.num_stringers):
        string_pos = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]["pos_along_airfoil_side"]
        top_or_bottom = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]['top_or_bottom_side']
        string_CS_area = designvars.wing.wingsection.stringers[f"Stringer{i+1}"]['crosssectionalarea_mm2']
        if top_or_bottom == "top":
            string_x = upper_airfoil[np.argmin(np.abs(upper_airfoil[:, 0]-string_pos*chord_length))][0]
            string_y = scipy.interpolate.interp1d(upper_airfoil[:, 0], upper_airfoil[:, 1], kind='linear')(string_x)
        elif top_or_bottom == "bottom":
            string_x = lower_airfoil[np.argmin(np.abs(lower_airfoil[:, 0] - string_pos * chord_length))][0]
            string_y = scipy.interpolate.interp1d(lower_airfoil[:, 0], lower_airfoil[:, 1], kind='linear')(string_x)
        plt.scatter(string_x, string_y, marker='o', color='r')

    plt.plot(outline[:, 0], outline[:, 1])
    plt.show()

#def generate_wing_structure_3D(designvars: DesignParameters = None):

