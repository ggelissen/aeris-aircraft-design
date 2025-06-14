import os
import sys
import pytest

# It's a good practice to add the project root to the Python path
# to ensure that all modules can be imported correctly.
# This assumes the test is run from the root of the DSEGroup17 directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

@pytest.fixture
def data_object():
    """
    This is a pytest fixture. It creates and returns an initialized
    Data object that will be used in the test functions. Fixtures help
    to avoid code duplication and manage test setup.
    """
    # Moved the import inside the fixture to prevent potential circular import issues.
    from design_variables import Data
    return Data()

def test_mission_simulation_run(data_object):
    """
    Tests the full mission simulation and verifies key performance outputs.
    This test ensures that the propulsion system analysis runs without errors
    and that the calculated values are physically reasonable.

    Args:
        data_object: The Data object instance provided by the pytest fixture.
    """
    # Import the correct PropulsionSystem class from the mainprop module.
    from subsystems.propulsion.mainprop import PropulsionSystem

    # Instantiate the PropulsionSystem with the data object.
    propulsion_system = PropulsionSystem(data_object)

    # Execute the main analysis method for the propulsion system.
    propulsion_system.run_prop_analysis(data_object)

    # --- Verification and Assertions ---

    # 1. Check if the output values have been added to the data object.
    #    These assertions are based on the attributes set in mainprop.py.
    assert hasattr(data_object, 'mass_fuel'), "Total fuel mass should be calculated."
    assert hasattr(data_object, 'w_prop_sys'), "Total propulsion system weight (force) should be calculated."
    assert hasattr(data_object, 'NOx_cruise'), "Cruise NOx emissions should be calculated."
    assert hasattr(data_object, 'NOx_TO'), "Take-off NOx emissions should be calculated."
    
    # Note: engine_weight and tsfc_cruise are calculated in sub-modules but not
    # directly exposed on the data object by the current run_prop_analysis method.
    # For a more detailed test, consider modifying mainprop.py to expose these values.

    # 2. Assert that key output values are positive and non-zero.
    assert data_object.mass_fuel > 0, "Total fuel mass must be positive."
    assert data_object.w_prop_sys > 0, "Total propulsion system weight must be positive."
    assert data_object.NOx_cruise > 0, "Cruise NOx index must be positive."
    assert data_object.NOx_TO > 0, "Take-off NOx index must be positive."

    # 3. Check for plausible ranges (example values).
    # These checks help to catch errors that might not cause a crash but produce
    # unrealistic results.
    
    # The total propulsion system weight should be a reasonable fraction of the MTOW.
    if hasattr(data_object, 'mtow') and data_object.mtow > 0:
        # Convert prop system weight from Newtons to mass in kg for comparison.
        prop_sys_mass = data_object.w_prop_sys / 9.80665
        prop_weight_fraction = prop_sys_mass / data_object.mtow
        assert 0.05 < prop_weight_fraction < 0.25, "Propulsion system weight fraction seems outside the plausible range."

    # 4. Check that fuel weight is less than MTOW
    assert data_object.mass_fuel < data_object.mtow, "Fuel mass cannot be more than MTOW."

    # The print statements are still useful for debugging during test runs.
    # Pytest captures and displays this output when a test fails.
    print("\nPropulsion System Test Results (Pytest):")
    print(f"  - Total Fuel Mass: {data_object.mass_fuel:.2f} kg")
    print(f"  - Total Propulsion System Weight: {data_object.w_prop_sys / 9.80665:.2f} kg")
    print(f"  - Cruise NOx Index: {data_object.NOx_cruise:.4f}")
    print(f"  - Take-off NOx Index: {data_object.NOx_TO:.4f}")