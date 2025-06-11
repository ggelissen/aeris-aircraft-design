import pytest
import numpy as np
from numpy import nan, isnan
from math import sqrt
from unittest.mock import Mock, patch

# Assume the code to be tested is in a file named `mission_simulation.py`
# If your file has a different name, you'll need to adjust the import.

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
    params = Mock(spec=DesignParameters)
    params.engine.Bpr = 5.0
    params.engine.prfan = 1.5
    params.engine.prlpc = 2.0
    params.engine.prhpc = 10.0
    params.engine.etafan = 0.90
    params.engine.etalpc = 0.88
    params.engine.etahpc = 0.85
    params.engine.etahpt = 0.92
    params.engine.etalpt = 0.93
    params.engine.etacom = 0.99
    params.engine.etamechl = 0.99
    params.engine.etamechh = 0.99
    params.engine.prcom = 0.95
    params.engine.prinlet = 0.98
    params.engine.bleedto = 0.0
    params.engine.power_tol = 0.0
    params.engine.power_toh = 0.0
    params.engine.cooling_l = 0.0
    params.engine.cooling_h = 0.0
    params.engine.lhv = 43.1e6
    params.engine.T_TO = 7540.0
    return params


# --- Verification Tests ---

def test_atmosphere_sea_level():
    """
    Verifies atmosphere model at sea level (h=0).
    """
    assert atmosphere.temperature(0) == pytest.approx(288.15)
    assert atmosphere.pressure(0) == pytest.approx(101325.0)
    assert atmosphere.saturation_vapor_pressure(288.15) == pytest.approx(1705.54)
    # Using default relative humidity of 0.6
    assert atmosphere.specific_humidity(0) == pytest.approx(6.33, abs=1e-2)

def test_atmosphere_tropopause():
    """
    Verifies atmosphere model at the tropopause (h=11000m).
    """
    assert atmosphere.temperature(11000) == pytest.approx(216.65)
    assert atmosphere.pressure(11000) == pytest.approx(22632.1, abs=1e-1)
    # Humidity should be very low at this altitude
    assert atmosphere.specific_humidity(11000) == pytest.approx(0.12, abs=1e-2)

def test_ei_nox_dallara_calculation():
    """
    Verifies the NOx Emission Index calculation with a known data point.
    """
    # Test case: Mid-cruise like conditions
    pt_3 = 10 * 101325  # 10 atm
    tt_3 = 600  # K
    h = 11000  # m
    # Expected specific humidity at 11km is ~0.12 g/kg
    # Calculation: (0.0986 * (10)**0.4 * exp((600/194.4) - (0.12/53.2))) / 1000
    expected_ei = (2+28.5*((pt_3/1000)/3100)**0.5 * np.exp((tt_3-825)/250))/1000.
    assert ei_nox_dallara(pt_3, tt_3, h) == pytest.approx(expected_ei, rel=1e-3)

def test_emissions_calculation():
    """
    Verifies the emissions dictionary calculation for a given fuel flow.
    """
    mdot_f = 0.5  # kg/s
    ei_nox = 0.015  # kg/kg
    dt = 120  # seconds

    result = emissions(mdot_f, ei_nox, dt=dt)

    # Check CO2
    assert result["mdot_co2"] == pytest.approx(0.5 * 3.16)
    assert result["m_co2"] == pytest.approx(0.5 * 3.16 * 120)
    # Check NOx
    assert result["mdot_nox"] == pytest.approx(0.5 * 0.015)
    assert result["m_nox"] == pytest.approx(0.5 * 0.015 * 120)
    # Check NaN propagation
    nan_result = emissions(nan, ei_nox, dt=dt)
    assert isnan(nan_result["m_co2"])
    assert isnan(nan_result["m_nox"])

def test_fuelflow_to_emissionflow():
    """
    Verifies the simple multiplication in fuelflow_to_emissionflow.
    """
    assert fuelflow_to_emissionflow(0.5, 0.02) == pytest.approx(0.01)
    assert isnan(fuelflow_to_emissionflow(nan, 0.02))
    assert isnan(fuelflow_to_emissionflow(0.5, nan))


def test_turbofan_analysis_sanity_check():
    """
    Runs a sanity check on the turbofan analysis to ensure it produces
    non-NaN results for a reasonable cruise condition.
    """
    params = {
        'mach_0': 0.85, 'ts_0': 216.65, 'ps_0': 18753.9,
        'bpr': 5.0, 'pr_fan': 1.5, 'pr_lpc': 1.8, 'pr_hpc': 12.0, 'tt_4': 1300.0,
        'eta_fan': 0.9, 'eta_lpc': 0.88, 'eta_hpc': 0.85, 'eta_hpt': 0.92, 'eta_lpt': 0.93
    }
    
    results = turbofan_parametric_analysis(**params)
    sf, tsfc, eta_th, eta_pr, eta_ov, _ = results

    # The primary goal is to ensure the function runs and produces numbers.
    # The exact values depend heavily on the mocked gpr.
    assert not isnan(sf) and sf > 0
    assert not isnan(tsfc) and tsfc > 0
    assert not isnan(eta_ov) and 0 < eta_ov < 1.0


def test_turbofan_analysis_static_case():
    """
    Tests the turbofan analysis at sea-level static conditions (Mach 0).
    """
    params = {
        'mach_0': 0.0, 'ts_0': 288.15, 'ps_0': 101325,
        'bpr': 5.0, 'pr_fan': 1.5, 'pr_lpc': 1.8, 'pr_hpc': 12.0, 'tt_4': 1400.0,
        'eta_fan': 0.9, 'eta_lpc': 0.88, 'eta_hpc': 0.85, 'eta_hpt': 0.92, 'eta_lpt': 0.93
    }
    
    results = turbofan_parametric_analysis(**params)
    sf, tsfc, eta_th, eta_pr, eta_ov, _ = results

    assert not isnan(sf) and sf > 0
    assert not isnan(tsfc) and tsfc > 0
    # Propulsive efficiency should be 0 at M=0, so overall efficiency is 0
    assert eta_pr == 0.0
    assert eta_ov == 0.0


@patch('mission_simulation.turbofan_parametric_analysis')
def test_run_mission_simulation_integration(mock_tf_analysis, mock_design_params):
    """
    Tests the integration of the run_mission_simulation function,
    mocking the complex turbofan analysis part.
    """
    # Define a consistent, plausible return value for the mocked analysis function.
    # sf, tsfc, eta_thermal, eta_propulsive, eta_overall, output_dict
    # TSFC in kg/(N.s). 20 mg/Ns is 2e-5 kg/Ns
    mock_return_value = (500.0, 2e-5, 0.4, 0.7, 0.28, {"opr": 40.0, "tt_3": 650.0})
    mock_tf_analysis.return_value = mock_return_value

    # Run the full mission simulation
    results = run_mission_simulation(mock_design_params)

    # --- Verification ---
    # 1. Check that the mocked analysis function was called for each segment.
    # The mission has 8 segments.
    assert mock_tf_analysis.call_count == 8

    # 2. Verify total fuel calculation.
    # We can calculate the expected total fuel based on our mock TSFC.
    # Note: This is an approximation as thrust varies, but it verifies the logic.
    total_thrust_newton_seconds = (
        (0.07 * 7540 * 10 * 60) +  # Warm-up
        (0.12 * 7540 * 10 * 60) +  # Taxi
        (7540 * 5 * 60) +         # Take-off
        (0.85 * 7540 * 20 * 60) + # Climb
        (0.30 * 7540 * 400 * 60) +# Cruise
        (0.08 * 7540 * 15 * 60) + # Descent
        (0.18 * 7540 * 5 * 60) +  # Landing
        (0.07 * 7540 * 15 * 60)   # Taxi & Shutdown
    )
    expected_total_fuel = total_thrust_newton_seconds * mock_return_value[1] # thrust * tsfc

    assert results["Total Fuel Used (kg)"] == pytest.approx(expected_total_fuel, rel=1e-3)
    
    # 3. Verify that the final TSFC list has an entry for each segment
    assert len(results["TSFC (kg/(Ns))"]) == 8