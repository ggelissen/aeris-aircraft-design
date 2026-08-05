import sys 
import os 
import numpy as np
# Ensure correct paths for imports - adjust if your project structure differs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.unit_conversions import * # Assuming this is available
from config.design_variables import DesignParameters # For loading initial T_TO if needed

def fuselage_exhaust_cone_analysis():
    # 2. Create an instance of the DesignParameters class.
    #    This object will contain all the nested parameter objects, including 'fuselage'.
    aircraft = DesignParameters()

    # 3. Now you can access the fuselage object and its attributes directly.
    fuselage_length = aircraft.fuselage.l_f
    max_diameter = aircraft.fuselage.D_f
    nose_length = aircraft.fuselage.l_n
    cross_sections = aircraft.fuselage.crosssections

    # 4. You can now use these variables in your new script.
    print(f"Aircraft Fuselage Length: {fuselage_length} m")
    print(f"Maximum Fuselage Diameter: {max_diameter} m")

    # You can also access nested data like the dimensions of a specific cross-section
    section_2_width = cross_sections['crosssection_2']['Dimensions']['Width']
    print(f"Width of fuselage cross-section 2: {section_2_width} m")

    # You can also pass the fuselage object itself to other functions
    def analyze_fuselage(fuselage_params):
        print("\n--- Running Fuselage Analysis ---")
        print(f"Analyzing a fuselage with length-to-diameter ratio of: {fuselage_params.lf_df:.2f}")


    # Access the 'Width' from the 'Dimensions' of 'crosssection_3'
    cs3_width = aircraft.fuselage.crosssections['crosssection_3']['Dimensions']['Width']

    print(f"The width of fuselage cross-section 3 is: {cs3_width} m")

    eng_nozz_diameter = 0.49   # Example nozzle diameter in meters
    distance_to_edge = cs3_width/2 - eng_nozz_diameter/2  # Distance from the edge of the fuselage to the nozzle edge
    print(f"Distance from the edge of fuselage to engine nozzle edge: {distance_to_edge} m")

    #do the distance from edge of fuselage to engine nozzle edge over tan(10 degrees)
    # This is to ensure the engine exhaust cone does not interfere with the v-tail
    x_eng = distance_to_edge / np.tan(np.radians(15)) 
    print(f"Maximum distance the engine can to be placed from end of v-tail: {x_eng} m")

    return {
        'distance_to_edge': distance_to_edge,
        'x_eng': x_eng
    }

if __name__ == "__main__":
    print("Fuselage Exhaust Cone Analysis Results:")
    results = fuselage_exhaust_cone_analysis()