import pytest
import numpy as np
from numpy import nan, isnan
from math import sqrt
from unittest.mock import Mock, patch
import os
import sys

# In a real scenario, you would save your original code as 'mission_simulation.py'
# and this test file as 'test_mission_simulation.py' in the same directory.
# For this example, we assume the code from the artifact can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from old.Mission_Simulation import (
    atmosphere,
    ei_nox_dallara,
    fuelflow_to_emissionflow,
    emissions,
    turbofan_parametric_analysis,
    run_mission_simulation,
    DesignParameters,
)
@pytest.fixture
def mock_design_params():
    """
    Provides a mock DesignParameters object for the mission simulation.
    """
    # Mock the nested structure params.engine
    mock_engine = Mock()
    mock_engine.Bpr = 5.0
    mock_engine.prfan = 1.5
    mock_engine.prlpc = 2.0
    mock_engine.prhpc = 10.0
    mock_engine.etafan = 0.90
    mock_engine.etalpc = 0.88
    mock_engine.etahpc = 0.85
    mock_engine.etahpt = 0.92
    mock_engine.etalpt = 0.93
    mock_engine.etacom = 0.99
    mock_engine.etamechl = 0.99
    mock_engine.etamechh = 0.99
    mock_engine.prcom = 0.95
    mock_engine.prinlet = 0.98
    mock_engine.bleedto = 0.0
    mock_engine.power_tol = 0.0
    mock_engine.power_toh = 0.0
    mock_engine.cooling_l = 0.0
    mock_engine.cooling_h = 0.0
    mock_engine.lhv = 43.1e6
    mock_engine.T_TO = 7540.0
    mock_engine.cruise_thrust = 2000.0

    # Create the main mock object and attach the engine mock
    mock_params = Mock()
    mock_params.engine = mock_engine
    
    return mock_params

# --- Mocking Dependencies ---
# We create a pytest "fixture" to provide a mocked version of the gpr module.
# The 'autouse=True' means this mock will be active for all tests in this file.
@pytest.fixture(autouse=True)
def mock_gpr_for_tests():
    """
    Automatically mocks the 'gas_property_relations' (gpr) module for all tests.
    This fixture replaces the actual gpr module with a Mock object that returns
    predictable, simplified values, making the tests independent and repeatable.
    """
    mock_gpr_object = Mock()

    # Configure the mock to return plausible, consistent values for its functions
    mock_gpr_object.s_o_s.side_effect = lambda t, **kwargs: sqrt(1.4 * 287 * t) if not isnan(t) else nan
    mock_gpr_object.specific_enthalpy.side_effect = lambda t, **kwargs: 1005 * t if not isnan(t) else nan
    mock_gpr_object.prescribed_p_ratio.side_effect = lambda p_in, t_in, p_ratio, eta_pol, **kwargs: {
         "p_out": p_in * p_ratio if not (isnan(p_in) or isnan(p_ratio)) else nan,
         "t_out": t_in * p_ratio**(0.4/1.4/eta_pol) if not (isnan(t_in) or isnan(p_ratio) or isnan(eta_pol) or eta_pol==0) else nan,
         "h_out": 1005 * (t_in * p_ratio**(0.4/1.4/eta_pol)) if not (isnan(t_in) or isnan(p_ratio) or isnan(eta_pol) or eta_pol==0) else nan
    }
    mock_gpr_object.prescribed_delta_h.side_effect = lambda p_in, t_in, delta_h, **kwargs: {
        "p_out": p_in * 1.1,
        "t_out": t_in + delta_h / 1005 if not isnan(delta_h) else nan,
        "h_out": 1005 * (t_in + delta_h / 1005) if not isnan(delta_h) else nan
    }
    mock_gpr_object.gamma_gas.return_value = 1.4
    mock_gpr_object.r_gas.return_value = 287.0
    mock_gpr_object.t_total_to_static.side_effect = lambda tt, m, **kwargs: tt / (1 + 0.2 * m**2) if not (isnan(tt) or isnan(m)) else nan
    mock_gpr_object.prescribed_h.side_effect = lambda h, **kwargs: h / 1005 if not isnan(h) else nan

    # FIX: Uncomment the patch and use the correct path to your module
    with patch('old.Mission_Simulation.gpr', mock_gpr_object):
        yield mock_gpr_object

# --- Unit Test Functions ---

@pytest.mark.parametrize("altitude, expected_temp, expected_press", [
    (0, 288.15, 101325.0),      # Sea Level
    (11000, 216.65, 22632.1),   # Tropopause
    (20000, 216.65, 5474.89)    # Stratosphere
])
def test_atmosphere_model(altitude, expected_temp, expected_press):
    """
    Performs unit tests on the atmosphere model at various key altitudes.
    Uses @pytest.mark.parametrize to run the same test with different data sets.
    """
    assert atmosphere.temperature(altitude) == pytest.approx(expected_temp, abs=1e-2)
    assert atmosphere.pressure(altitude) == pytest.approx(expected_press, abs=1)

def test_ei_nox_dallara_logic():
    """
    Unit test for the NOx Emission Index calculation.
    Checks the formula with a known data point.
    """
    # Use representative values for a mid-cruise condition
    pt_3 = 16 * 20000  # Combustor inlet pressure (Pa)
    tt_3 = 1200      # Combustor inlet temperature (K)
    h = 12192         # Altitude (m)
    
    expected_ei = (2+28.5*((pt_3/1000)/3100)**0.5 * np.exp((tt_3-825)/250))/1000
    
    calculated_ei = ei_nox_dallara(pt_3, tt_3, h)
    assert calculated_ei == pytest.approx(expected_ei, rel=1e-3)

def test_emissions_logic():
    """
    Unit test for the main 'emissions' function.
    Verifies correct calculation of emission mass and checks for NaN propagation.
    """
    mdot_f = 0.4  # kg/s fuel flow
    ei_nox = 0.012 # kg/kg NOx emission index
    dt = 30 * 60  # 30 minutes in seconds

    result = emissions(mdot_f, ei_nox, dt=dt)

    # Verify CO2 calculation (mdot_f * ei_co2 * dt)
    assert result["m_co2"] == pytest.approx(0.4 * 3.16 * 1800)
    # Verify NOx calculation (mdot_f * ei_nox * dt)
    assert result["m_nox"] == pytest.approx(0.4 * 0.012 * 1800)
    # Verify Water calculation (mdot_f * ei_h2o * dt)
    assert result["m_h2o"] == pytest.approx(0.4 * 1.26 * 1800)

    # Test that if fuel flow is NaN, all outputs are NaN
    nan_result = emissions(nan, ei_nox, dt=dt)
    assert isnan(nan_result["m_co2"])
    assert isnan(nan_result["m_nox"])
    assert isnan(nan_result["m_h2o"])

def test_turbofan_analysis_sanity():
    """
    Performs a sanity-check unit test on the turbofan_parametric_analysis.
    The goal is to ensure it runs without errors for a valid input set and
    that outputs are physically plausible, using the mocked gpr data.
    """
    # A typical set of parameters for a cruise condition
    params = {
        'mach_0': 0.85, 'ts_0': 218.8, 'ps_0': 20000,
        'bpr': 3.3, 'pr_fan': 1.9, 'pr_lpc': 1.2, 'pr_hpc': 5.65, 'tt_4': 1200.,
        'eta_fan': 0.92, 'eta_lpc': 0.90, 'eta_hpc': 0.88, 'eta_hpt': 0.92, 'eta_lpt': 0.94
    }
    
    # The function is called here; it will use the mocked gpr fixture automatically
    results = turbofan_parametric_analysis(**params)
    sf, tsfc, eta_thermal, eta_propulsive, eta_overall, _ = results

    # We don't check for exact values, as they depend on the mock.
    # We check that the results are valid numbers and are within a plausible range.
    assert not isnan(sf) and sf > 0
    assert not isnan(tsfc) and tsfc > 0
    assert not isnan(eta_overall) and 0 < eta_overall < 1.0, "Overall efficiency should be between 0 and 1"
    assert not isnan(eta_thermal) and 0 < eta_thermal < 1.0, "Thermal efficiency should be between 0 and 1"
    assert not isnan(eta_propulsive) and 0 < eta_propulsive < 1.0, "Propulsive efficiency should be between 0 and 1"

@patch('old.Mission_Simulation.turbofan_parametric_analysis')
def test_run_mission_simulation_integration(mock_tf_analysis, mock_design_params):
    """
    Tests the integration of the run_mission_simulation function,
    mocking the complex turbofan analysis part to ensure the loop and
    aggregation logic works correctly.
    """
    # Define a consistent, plausible return value for the mocked analysis function.
    # sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    # TSFC in kg/(N.s). 20 mg/Ns is 2e-5 kg/Ns
    mock_return_value = (500.0, 2e-5, 0.4, 0.7, 0.28, {"opr": 40.0, "tt_3": 650.0})
    mock_tf_analysis.return_value = mock_return_value

    # Run the full mission simulation with the mocked design parameters
    results = run_mission_simulation(mock_design_params)

    # 1. Check that the analysis was called for each of the 10 segments
    assert mock_tf_analysis.call_count == 10

    # 2. Check that the final TSFC list has an entry for each segment
    assert len(results["TSFC (kg/(Ns))"]) == 10
    
    # 3. Verify total fuel calculation based on the mock TSFC
    # This calculation is an approximation but validates the core logic
    total_thrust_newton_seconds = (
        (0.07 * 7540 * 10 * 60) +   # Warm-up
        (0.12 * 7540 * 10 * 60) +   # Taxi
        (7540 * 5 * 60) +           # Take-off
        (0.85 * 7540 * 20 * 60) +   # Climb
        (2000 * 400 * 60) +         # Cruise
        (2000 * 34 * 60) +          # Diversion Cruise
        (800 * 120 * 60) +          # Loiter
        (0.08 * 7540 * 15 * 60) +   # Descent
        (0.18 * 7540 * 5 * 60) +    # Landing
        (0.07 * 7540 * 15 * 60)     # Taxi & Shutdown
    )
    expected_total_fuel = total_thrust_newton_seconds * mock_return_value[1] # thrust * tsfc

    assert results["Total Fuel Used (kg)"] == pytest.approx(expected_total_fuel, rel=1e-2)