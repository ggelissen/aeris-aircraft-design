import numpy as np
import math as m
import matplotlib.pyplot as plt
import sys
import os

# Import design variables class used to retrieve and store design parameters
from design_variables import DesignParameters

# Import main analysis functions from different disciplines
from class1.main_class_I import perform_class_I_analysis
from class2.main_class_II import perform_class_II_analysis
from subsystems.aerodynamics.main_aero import perform_aerodynamic_analysis
from subsystems.structures.main_struct import struct_main
from subsystems.propulsion.main_prop import perform_propulsion_analysis
from subsystems.flightperformance.main_flight import perform_flight_performance_analysis



def run_main_analysis(designvars: DesignParameters) -> dict:
    """
    Run the main analysis for the aircraft design, integrating various subsystems.

    Parameters:
    - designvars: An initial instance of DesignParameters containing the design variables.

    Returns:
    - A dictionary containing results from all analyses.
    """
    # Ensure the designvars object is initialized
    if not isinstance(designvars, DesignParameters):
        raise ValueError("designvars must be an instance of DesignParameters")
    
    # Create copy of designvars to avoid modifying the original object
    designvars = designvars.copy()
    
    # Step 1: Perform Class I analysis with the initial design variables
    # This will copy and update the designvars with results from Class I analysis
    class_I_results = perform_class_I_analysis(designvars)
    designvars_class1 = designvars.copy()
    for key, value in class_I_results.items():
        designvars_class1.update_parameters(key, value)
    
    # Step 2: Perform Class II analysis with the updated design variables
    # This will further refine the designvars based on Class II analysis
    # Note: The designvars object has been updated with results from Class I analysis
    class_II_results = perform_class_II_analysis(designvars_class1)
    designvars_class2 = designvars_class1.copy()
    for key, value in class_II_results.items():
        designvars_class2.update_parameters(key, value)

    # Step 3: Perform aerodynamic analysis
    aero_results = perform_aerodynamic_analysis(designvars_class2)
    designvars_aero = designvars_class2.copy()
    for key, value in aero_results.items():
        designvars_aero.update_parameters(key, value)

    # Step 4: Perform structural analysis
    struct_results = struct_main(designvars_aero, show_3d=False)
    designvars_struct = designvars_aero.copy()
    for key, value in struct_results.items():
        designvars_struct.update_parameters(key, value)

    # Step 5: Perform propulsion analysis
    prop_results = perform_propulsion_analysis(designvars_struct)
    designvars_prop = designvars_struct.copy()
    for key, value in prop_results.items():
        designvars_prop.update_parameters(key, value)   

    # Step 6: Perform flight performance analysis
    flight_results = perform_flight_performance_analysis(designvars_prop)
    designvars_flight = designvars_prop.copy()
    for key, value in flight_results.items():
        designvars_flight.update_parameters(key, value)

    designvars_final = designvars_flight.copy()
    
