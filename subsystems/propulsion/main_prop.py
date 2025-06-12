from old.Mission_Simulation import run_mission_simulation
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from design_variables import DesignParameters  # Assuming this is defined in design_variables.py



if __name__ == "__main__":
    params = DesignParameters()  # Assuming DesignParameters is defined in design_variables.py
    params.load_from_yaml("design_config.yaml")  # Load design parameters from a YAML file
    mission_results = run_mission_simulation(params)
    print("Mission Simulation Results:")
    print(mission_results)
    
    # Note: The actual implementation of run_mission_simulation should be defined in the Mission_Simulation module.
    # This is just a placeholder to demonstrate how to call it.