import pytest
import os
import sys
import yaml
from numpy import isnan

# --- Path Setup ---
# This ensures the test can find the Mission_Simulation file.
# Adjust the number of '..' if your directory structure is different.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from old.Mission_Simulation import run_mission_simulation, DesignParameters

# --- Test Setup: Create a realistic config file for the test ---

@pytest.fixture(scope="module")
def real_design_config_file():
    """
    This fixture creates a real 'design_config.yaml' file for the system test to use.
    Using a fixture ensures the file is created before tests run and can be cleaned up after.
    The scope="module" means this file is created only once for all tests in this file.
    """
    config_data = {
        'engine': {
            'Bpr': 5.0, 'prfan': 1.5, 'prlpc': 2.0, 'prhpc': 10.0,
            'etafan': 0.90, 'etalpc': 0.88, 'etahpc': 0.85, 'etahpt': 0.92, 'etalpt': 0.93,
            'etacom': 0.99, 'etamechl': 0.99, 'etamechh': 0.99, 'prcom': 0.95,
            'prinlet': 0.98, 'bleedto': 0.0, 'power_tol': 0.0, 'power_toh': 0.0,
            'cooling_l': 0.0, 'cooling_h': 0.0, 'lhv': 43.1e6, 'T_TO': 7540.0,
            'cruise_thrust': 2000.0
        }
    }
    config_path = "design_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    
    # Provide the path to the test function
    yield config_path
    
    # Teardown: Clean up the created file after the test run
    os.remove(config_path)

@pytest.fixture
def real_design_params(real_design_config_file):
    """
    Loads the design parameters from the YAML file created by the fixture.
    This provides a real, fully populated DesignParameters object to the test.
    """
    params = DesignParameters()
    params.load_from_yaml(real_design_config_file)
    return params


# --- System Test Function ---

def test_mission_simulation_end_to_end(real_design_params):
    """
    SYSTEM TEST: Executes the entire mission simulation from end-to-end with no mocks.
    
    This test verifies the complete workflow of the application by:
    1. Loading real parameters from a config file.
    2. Running the full simulation, including the actual `turbofan_parametric_analysis`
       and its dependency on the real `gas_property_relations` module.
    3. Asserting that the final, aggregated results are within a plausible and
       expected range.
       
    This contrasts with integration tests, which mock internal components to check
    the "wiring," and unit tests, which check a single function's logic.
    """
    # We expect the test might fail if the actual gpr module isn't available.
    # A real CI/CD pipeline would ensure it is. For now, we can mark it as
    # expected to fail if the module is known to be missing in the test environment.
    try:
        import gas_property_relations as gpr
    except ImportError:
        pytest.fail(
            "SYSTEM TEST FAILED: The 'gas_property_relations' module could not be imported. "
            "This is required for an end-to-end system test."
        )

    # --- 1. Execution ---
    # Run the simulation with the real, loaded parameters. No mocks are used.
    results = run_mission_simulation(real_design_params)

    # --- 2. Verification ---
    # We check the final, high-level outputs for plausibility.
    # These are not exact values, but sanity checks on the overall system behavior.

    # Check that the results dictionary contains the expected keys.
    assert "Total Fuel Used (kg)" in results
    assert "TSFC (kg/(Ns))" in results

    # Retrieve the final calculated total fuel.
    total_fuel = results["Total Fuel Used (kg)"]

    # Assert that the fuel is a valid, positive number.
    assert total_fuel is not None
    # FIX: Added a detailed message to explain why this assertion might fail.
    assert not isnan(total_fuel), \
        "The simulation resulted in NaN for Total Fuel. This indicates a calculation error in one or more mission segments."
    assert total_fuel > 0, "Total fuel used should be a positive value."

    # Assert that the total fuel is within a reasonable, expected range.
    # This range would be determined from benchmark runs or known aircraft performance.
    # For this example, we'll use a broad but reasonable range.
    # NOTE: You would adjust this range based on expected results from your model.
    expected_min_fuel = 40000  # kg
    expected_max_fuel = 90000  # kg
    assert expected_min_fuel < total_fuel < expected_max_fuel, \
        f"Total fuel used ({total_fuel:.2f} kg) is outside the expected range of {expected_min_fuel}-{expected_max_fuel} kg."

    # Assert that the list of TSFC values is populated for all segments that succeeded.
    # In a full run, some segments might fail, so we check that the list is not empty.
    tsfc_results = results["TSFC (kg/(Ns))"]
    assert len(tsfc_results) > 0, "The TSFC results list should not be empty after a full run."
    
    # Check that all calculated TSFC values are plausible positive numbers.
    for tsfc in tsfc_results:
        assert not isnan(tsfc) and tsfc > 0