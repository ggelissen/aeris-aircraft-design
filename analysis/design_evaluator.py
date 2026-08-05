import numpy as np
import math as m
import copy
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.design_variables import DesignParameters
from class1.main_class_I import perform_class_I_analysis
from class2.main_class_II import perform_class_II_analysis
from subsystems.aerodynamics.main_aero import analyse_aerodynamics
from subsystems.flightperformance.main_flight import analyse_flight_performance
from subsystems.propulsion.old.main_prop import analyse_propulsion
from subsystems.structures.main_struct import analyse_structures


def evaluate_design(current_params: DesignParameters):
    """
    Evaluates the design parameters by performing various subsystem analyses, and calculates objectives and constraints.
    
    Parameters:
        current_params (DesignParameters): An instance of DesignParameters containing the design variables.
    
    Returns:
        DesignParameters: The updated design parameters object containing the results of the analyses.
    """
    
    # 0. Create a copy of the current parameters to avoid modifying the original object
    params = copy.deepcopy(current_params)
    params.is_feasible = True

    # 1. Perform Class I analysis
    class1_results = perform_class_I_analysis(params)

    # 2. Perform Class II analysis
    class2_results = perform_class_II_analysis(params)

    # 3. Perform Aerodynamics analysis
    aero_results = analyse_aerodynamics(params)

    # 4. Perform Flight Performance analysis
    flight_results = analyse_flight_performance(params)

    # 5. Perform Propulsion analysis
    prop_results = analyse_propulsion(params)

    # 6. Perform Structures analysis
    struct_results = analyse_structures(params)

    # 7. Calculate objectives and constraints

    # Objective: .....

    # Constraint: Lift >= Total Weight at Cruise
    if aero_results['lift'] < flight_results['total_weight']:
        params.is_feasible = False
        print("Design is infeasible: Lift is less than Total Weight at Cruise.")

    # Constraint: Thrust >= Drag at Cruise
    if prop_results['thrust'] < aero_results['drag']:
        params.is_feasible = False
        print("Design is infeasible: Thrust is less than Drag at Cruise.")

    # Constraint: Minimum Range
    if flight_results['range'] < params.cruise_range:
        params.is_feasible = False
        print("Design is infeasible: Range is less than the required cruise range.")
    
    return params

