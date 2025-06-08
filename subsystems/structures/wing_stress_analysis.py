import numpy as np
import math as m
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from design_variables import DesignParameters
from wing_structure_generation import cross_sectional_structure_along_span
from ideal_cross_section_analysis import run_cross_section_analysis
from loading_diagrams import WingLoadingDiagrams


def perform_cross_section_analysis(designvars: DesignParameters = None, loading: WingLoadingDiagrams = None, spanwise_position: float = 0.0):
    """
    Performs cross-sectional analysis of the wing structure at a given spanwise position.

    Parameters:
    - designvars: DesignParameters object containing design variables.
    - spanwise_position: Position along the span where the cross-section is generated as a fraction of the total span (0.0 to 1.0).
    """
    
    spar_points_array, stringer_array, _, _, _, _ = cross_sectional_structure_along_span(designvars, spanwise_position, plot=False)
    results = run_cross_section_analysis(designvars, spar_points_array, stringer_array, loading["Mx"], loading["My"],
                                         loading["T"], loading["Vx"], loading["Vy"], designvars.wing.skin_thickness, plot=False)
    return results


def calculate_



if __name__ == "__main__":

    designvars = DesignParameters()
    wing_loading = WingLoadingDiagrams()
    wing_loading = wing_loading.run_analysis(PLOT=False)
    spanwise_position_lst = np.linspace(0.0, 1.0, 1000)

    cross_sectional_results = []
    for i, spanwise_position in enumerate(spanwise_position_lst):
        results = perform_cross_section_analysis(designvars, wing_loading[i], spanwise_position)
        cross_sectional_results.append(results)