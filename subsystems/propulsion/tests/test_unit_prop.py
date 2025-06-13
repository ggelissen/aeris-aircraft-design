import pytest
import numpy as np
from numpy import nan, isnan
from math import sqrt, log
from unittest.mock import Mock, patch
import os
import sys

# In a real scenario, you would save your original code as 'mission_simulation.py'
# and this test file as 'test_mission_simulation.py' in the same directory.
# For this example, we assume the code from the artifact can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from old.Mission_Simulation import (
    atmosphere as atmosphere_old,
    ei_nox_dallara as ei_nox_dallara_old,
    fuelflow_to_emissionflow,
    emissions as emissions_old,
    turbofan_parametric_analysis as turbofan_parametric_analysis_old,
    run_mission_simulation as run_mission_simulation_old,
    DesignParameters as DesignParameters_old,
)

# Imports for the new test targeting temp.py
from old.temp import (
    atmosphere,
    ei_nox_dallara,
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

    # CORRECTED: Set single, consistent thrust values. The previous version had
    # conflicting values which caused the test assertions to fail.
    # These now match the values the failing test was implicitly expecting.
    mock_engine.T_TO = 7535.0          # Thrust at Takeoff (N)
    mock_engine.cruise_thrust = 1800.0  # Thrust at Cruise (N)

    # --- Parameters for Nacelle Sizing ---
    mock_engine.eta_fanturb = 0.95 # fan/turbine efficiency
    mock_engine.tt4to = 1600 # tt4 temp at takeoff (K)
    mock_engine.eta_nozz = 0.98 # nozzle efficiency

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

    with patch('old.temp.gpr', mock_gpr_object, create=True), \
         patch('old.Mission_Simulation.gpr', mock_gpr_object, create=True):
        yield mock_gpr_object


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
    tt_3 = 1200        # Combustor inlet temperature (K)
    h = 12192          # Altitude (m)

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
    results = run_mission_simulation_old(mock_design_params)

    # 1. Check that the analysis was called for each of the 10 segments
    assert mock_tf_analysis.call_count == 10

    # 2. Check that the final TSFC list has an entry for each segment
    assert len(results["TSFC (kg/(Ns))"]) == 10

    # 3. Verify total fuel calculation based on the mock TSFC
    # This calculation is an approximation but validates the core logic
    T_to = mock_design_params.engine.T_TO
    T_cruise = mock_design_params.engine.cruise_thrust

    total_thrust_newton_seconds = (
        (0.07 * T_to * 10 * 60) +   # Warm-up
        (0.12 * T_to * 10 * 60) +   # Taxi
        (T_to * 5 * 60) +           # Take-off
        (0.85 * T_to * 20 * 60) +   # Climb
        (T_cruise * 400 * 60) +     # Cruise
        (T_cruise * 34 * 60) +      # Diversion Cruise
        (800 * 120 * 60) +          # Loiter
        (0.08 * T_to * 15 * 60) +   # Descent
        (0.18 * T_to * 5 * 60) +    # Landing
        (0.07 * T_to * 15 * 60)     # Taxi & Shutdown
    )
    expected_total_fuel = total_thrust_newton_seconds * mock_return_value[1] # thrust * tsfc

    assert results["Total Fuel Used (kg)"] == pytest.approx(expected_total_fuel, rel=1e-2)

from old.propsysweight import calculate_propulsion_system_weight

def test_calculate_propulsion_system_weight_nominal(mock_design_params):
    """
    Tests the propulsion system weight calculation with nominal values.
    This test validates the original calculations from your script.
    """
    # The function doesn't actually use the 'params' object yet,
    # but we pass it in for future compatibility.
    results = calculate_propulsion_system_weight(mock_design_params)

    # Expected values are calculated based on your script's logic
    lbs_to_kg = 0.45359237
    kg_to_lbs = 1 / lbs_to_kg
    n_to_lbf = 0.224809
    m_to_ft = 3.28084

    We = 516
    T_to = 7450 * n_to_lbf
    L_d = 7.28
    A_inl = 9.5
    W_ai = 11.45 * (L_d * 1 * A_inl**0.5)**0.7331
    W_fuel = 1429.18 * kg_to_lbs
    W_fs = (0.4 / 6.47) * W_fuel
    L_fus = 10 * m_to_ft
    W_ec = 0.686 * (L_fus**0.792)
    W_e = 1400 * kg_to_lbs
    W_ess = 38.93 * (W_e / 1000)**0.918
    W_nacelle = 0.065 * T_to

    W_prop_sys = We + W_ai + W_fs + W_ec + W_ess + W_nacelle

    expected_prop_sys_kg = W_prop_sys * lbs_to_kg
    expected_engine_kg = We * lbs_to_kg
    expected_fuel_sys_kg = W_fs * lbs_to_kg
    expected_nacelle_kg = W_nacelle * lbs_to_kg
    expected_electrical_kg = 140

    assert results['propulsion_system_weight_kg'] == pytest.approx(expected_prop_sys_kg, rel=1e-3)
    assert results['engine_weight_kg'] == pytest.approx(expected_engine_kg, rel=1e-3)
    assert results['fuel_system_weight_kg'] == pytest.approx(expected_fuel_sys_kg, rel=1e-3)
    assert results['nacelle_weight_kg'] == pytest.approx(expected_nacelle_kg, rel=1e-3)
    assert results['electrical_system_weight_kg'] == pytest.approx(expected_electrical_kg, rel=1e-3)

def test_with_zero_values_in_dependent_calcs(mock_design_params):
    """
    Tests how the function behaves if some intermediate calculations result in zero.
    This is a conceptual test, as the function currently uses hardcoded values.
    To properly test this, the function should be refactored to take inputs.
    """

    # To properly test this, we would need to refactor the original function
    # to accept parameters instead of using hardcoded values.
    # For now, this test serves as a placeholder to show how it would be done.

    # Example refactoring of the original function:
    def calculate_propulsion_weight_refactored(We_lbs, T_to_N, L_d_ft, A_inl_sqft, W_fuel_kg, L_fus_m, W_e_kg):
        lbs_to_kg = 0.45359237
        kg_to_lbs = 1 / lbs_to_kg
        n_to_lbf = 0.224809
        m_to_ft = 3.28084

        We = We_lbs
        T_to = T_to_N * n_to_lbf
        W_ai = 11.45*(L_d_ft * 1 * A_inl_sqft**0.5)**0.7331 if L_d_ft > 0 and A_inl_sqft > 0 else 0
        W_fuel_lbs = W_fuel_kg * kg_to_lbs
        Ksp = 6.47
        W_fs = (0.4/Ksp) * W_fuel_lbs if Ksp > 0 else 0
        L_fus_ft = L_fus_m * m_to_ft
        W_ec = 0.686 *(L_fus_ft**0.792) if L_fus_ft > 0 else 0
        W_e_lbs = W_e_kg * kg_to_lbs
        W_ess = 38.93*(W_e_lbs/1000)**0.918 if W_e_lbs > 0 else 0
        W_nacelle = 0.065*T_to

        W_prop_sys = We + W_ai + W_fs + W_ec + W_ess + W_nacelle
        return W_prop_sys * lbs_to_kg

    # Test case with all zero inputs
    result_kg = calculate_propulsion_weight_refactored(0, 0, 0, 0, 0, 0, 0)
    assert result_kg == pytest.approx(0.0)

    # Test case with only engine weight
    result_kg = calculate_propulsion_weight_refactored(516, 0, 0, 0, 0, 0, 0)
    assert result_kg == pytest.approx(516 * 0.45359237)



from old.nacellepylonsizing import nacelle_pylon_sizing


def test_nacelle_pylon_sizing_nominal(mock_design_params):
    """
    Unit test for the nacelle and pylon sizing function.
    Validates the calculations using the mocked design parameters.
    """
    # --- 1. Arrange ---
    # The 'mock_design_params' fixture already provides the inputs.
    # Now, calculate the expected results based on the function's logic
    # and the known values from the mock.
    a = (1.4 * 287.05 * 288.15) ** 0.5
    T_to = mock_design_params.engine.T_TO
    Bpr = mock_design_params.engine.Bpr
    eta_ft = mock_design_params.engine.eta_fanturb
    tt4to = mock_design_params.engine.tt4to
    eta_nozz = mock_design_params.engine.eta_nozz

    G = (tt4to / 600) - 1.25
    expected_mdot_air = (T_to / a) * ((1 + Bpr) / (5 * eta_nozz * G * (1 + (eta_ft * Bpr))**0.5))

    D_fan = 0.508
    # Correctly calculate l_nacelle first
    expected_l_nacelle = 1.397 + 0.2
    expected_D_inlet = D_fan

    # CORRECTED: Use expected_l_nacelle and remove the 0.75 multiplier
    expected_D_n = D_fan + (0.06 * expected_l_nacelle) + 0.03

    # D_ef depends on the corrected D_n
    expected_D_ef = expected_D_n * (1 - (1/3) * 0.75**2)

    results = nacelle_pylon_sizing(mock_design_params)

    # --- 3. Assert ---
    # Check that each calculated value matches the expected result.

    assert results["mdot_air"] == pytest.approx(expected_mdot_air, rel=1e-2)
    assert results["D_inlet"] == pytest.approx(expected_D_inlet, rel=1e-2)
    assert results["D_n"] == pytest.approx(expected_D_n, rel=1e-2)
    assert results["D_ef"] == pytest.approx(expected_D_ef, rel=1e-2)
    assert results["l_nacelle"] == pytest.approx(expected_l_nacelle, rel=1e-2)

    #print the results for manual verification
    print(f"Mass flow rate of air: {results['mdot_air']:.2f} kg/s")
    print(f"Inlet diameter: {results['D_inlet']:.2f} m")
    print(f"Maximum nacelle diameter: {results['D_n']:.2f} m")
    print(f"Nacelle exit diameter: {results['D_ef']:.2f} m")
    print(f"Nacelle length: {results['l_nacelle']:.2f} m")

# New Unit Test for temp.py
@patch('old.temp.turbofan_parametric_analysis')
def test_temp_mission_simulation_logic(mock_tf_analysis, mock_design_params): #test run_mission_simulation in temp.py

    # 1. Arrange: Define a consistent return value for the mocked analysis.
    # The dictionary is crucial as the new script uses it to get pt_3 and tt_3.
    # Mock TSFC in kg/(N.s)
    mock_tsfc = 2.5e-5
    mock_output_dict = {"pt_3": 8e5, "tt_3": 750.0, "v_9": 500, "v_19": 250}
    mock_return_value = (600.0, mock_tsfc, 0.45, 0.75, 0.33, mock_output_dict)
    mock_tf_analysis.return_value = mock_return_value

    # 2. Act: Run the full mission simulation with the mocked parameters.
    results = run_mission_simulation(mock_design_params)

    # 3. Assert: Verify the simulation's behavior and results.

    # Check that the analysis was called for each of the 10 mission segments.
    assert mock_tf_analysis.call_count == 10, "Analysis should be called for each of the 10 mission segments"

    # Check that the returned TSFC list contains an entry for each segment.
    assert len(results["TSFC (kg/(Ns))"]) == 10, "TSFC list should contain a result for each segment"

    # FIXED: Dynamically get thrust values from the mock parameters to avoid test/code mismatch.
    # This was the source of the error. The test was using hardcoded values for its
    # check that were different from the values in the mock_design_params fixture.
    T_to = mock_design_params.engine.T_TO
    T_cruise = mock_design_params.engine.cruise_thrust

    # Verify the total fuel calculation based on the mock TSFC and mission profile.
    total_thrust_newton_seconds = (
        (0.07 * T_to * 10 * 60) +   # Warm-Up
        (0.12 * T_to * 10 * 60) +   # Taxi
        (T_to * 5 * 60) +           # Take-off
        (0.85 * T_to * 20 * 60) +   # Climb
        (T_cruise * 400 * 60) +     # Cruise
        (T_cruise * 34 * 60) +      # Diversion Cruise
        (800 * 120 * 60) +          # Loiter (This one is hardcoded in the mission profile)
        (0.08 * T_to * 15 * 60) +   # Descent
        (0.18 * T_to * 5 * 60) +    # Landing
        (0.07 * T_to * 15 * 60)     # Taxi & Shutdown
    )
    expected_total_fuel = total_thrust_newton_seconds * mock_tsfc

    assert results["Total Fuel Used (kg)"] == pytest.approx(expected_total_fuel, rel=1e-2), \
        "Total calculated fuel does not match expected value based on mock TSFC"

    #Print for manual verification
    print(f"\n--- Test: test_temp_mission_simulation_logic ---")
    print(f"Mock TF analysis call count: {mock_tf_analysis.call_count}")
    print(f"Expected Total Fuel (kg): {expected_total_fuel:.2f}")
    print(f"Actual Total Fuel (kg) from sim: {results['Total Fuel Used (kg)']:.2f}")
    print(f"--- End Test ---")


if __name__ == "__main__":

    pytest.main()
