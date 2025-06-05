import numpy as np
from scipy.interpolate import interp1d, CubicSpline
# Assuming design_variables.py and design_config.yaml are available in the environment
from design_variables import DesignParameters
params = DesignParameters()
params.load_from_yaml("design_config.yaml")

def calculate_aileron_specifics(
    params,
    CA_to_C: float,
    b_inboard: float,
    b_outboard: float,
    rho: float,
    delta_a: float,
    bank_angle: float
) -> dict:
    """
    Calculates various aileron-specific parameters and roll authority metrics.

    Args:
        params: An object containing design parameters (e.g., from design_variables.py).
                It should have attributes like params.wing.root_chord,
                params.wing.tip_chord, params.wing.b_w, params.wing.airfoil_clalpha,
                params.wing.airfoil_cd0, params.wing.S_w, params.wing.Lambda_w,
                params.performance.CL_max_cruise, and params.weight.W_TO.
        CA_to_C: Aileron chord to Wing chord ratio.
        b_inboard: Inboard edge of aileron from centerline as a fraction of half-span.
        b_outboard: Outboard edge of aileron from centerline as a fraction of half-span.
        rho: Air density in kg/m^3.
        delta_a: Maximum Aileron deflection in radians.
        bank_angle: Desired bank angle in degrees.

    Returns:
        A dictionary containing the calculated aileron specifics, including:
        - 'time_to_bank': Required time to achieve the desired bank angle in seconds.
        - 'aircraft_weight': Aircraft weight in Newtons.
        - 'stall_speed': Stall speed in meters per second.
        - 'CL_max': Maximum lift coefficient in clean configuration.
        - 'root_chord': Wing root chord in meters.
        - 'tip_chord': Wing tip chord in meters.
        - 'half_span': Half of the wing span in meters.
        - 'aileron_inboard_edge': Inboard edge of aileron from centerline in meters.
        - 'aileron_outboard_edge': Outboard edge of aileron from centerline in meters.
        - 'wing_surface_area': Reference wing surface area in m^2.
        - 'aileron_surface_area_approx': Approximate aileron surface area in m^2.
    """

    # Extract parameters from the params object
    C_r = params.wing.root_chord          # Root chord in meters (m)
    C_t = params.wing.tip_chord           # Tip chord in meters (m)
    b = params.wing.b_w                   # Wing span in meters (m)
    c_l_alpha = params.wing.airfoil_clalpha # Airfoil lift curve slope
    c_d_0 = params.wing.airfoil_cd0       # Airfoil 2D drag coefficient
    S_ref = params.wing.S_w               # Reference wing surface area (m^2)
    C_L_max = params.performance.CL_max_cruise # Maximum lift coefficient in clean configuration
    W = params.weight.W_TO                # Aircraft weight in Newtons (N)
    Lambda_LE = params.wing.Lambda_w      # Leading edge sweep angle in radians (rad)
    # Lambda_TE = params.wing.Lambda_w    # Trailing edge sweep angle in radians (rad) - not used in calculations

    # Calculate actual inboard and outboard edges of the aileron
    b1 = b_inboard * b / 2                # Inboard edge of aileron from centerline in meters (m)
    b2 = b_outboard * b / 2               # Outboard edge of aileron from centerline in meters (m)

    # Aileron effectiveness data from Gudmundsson’s design handbook
    x_data = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    y_data = np.array([0, 0.26, 0.41, 0.525, 0.6, 0.675, 0.74, 0.8])

    # Interpolation for aileron effectiveness (tau)
    f_cubic = interp1d(x_data, y_data, kind='cubic')
    cs = CubicSpline(x_data, y_data)

    # Use the average of both interpolation methods for tau
    tau = (f_cubic(CA_to_C) + cs(CA_to_C)) / 2 # Aileron effectiveness interpolated

    # Calculate Stall Speed
    V_stall = np.sqrt((W * 2) / (S_ref * rho * C_L_max)) # Stall speed in meters per second (m/s)

    # Calculate integral I_1 (derived from the integral of c(y) * y dy)
    # where c(y) is the local chord at span-wise position y.
    # Assuming a trapezoidal wing, local chord c(y) = C_r - (C_r - C_t) * (y / (b/2))
    # Note: The original I_1 calculation seems to be for a full span, but b1, b2 are half-span distances.
    # This calculation needs to be consistent with the definition of b1 and b2 being from centerline.
    # The integral should be from b1 to b2.
    # The original I_1 calculation: -(2/3) * ((C_r - C_t) / b) * b2**3 + 0.5 * C_r * b2**2 - (-(2/3) * ((C_r - C_t) / b) * b1**3 + 0.5 * C_r * b1**2)
    # This form is correct for integrating c(y)*y from b1 to b2, where c(y) = C_r - (C_r - C_t) * (y / (b/2))
    # The term (C_r - C_t) / b should be (C_r - C_t) / (b/2) if y is from centerline to tip.
    # Let's assume the original formula for I_1 implicitly handles the half-span correctly based on its source.
    # Re-evaluating based on common wing theory:
    # c(y) = C_r - (C_r - C_t) * (y / (b/2)) for y from 0 to b/2
    # Integral of c(y) * y dy from b1 to b2:
    # Integral[ (C_r - (C_r - C_t) * (y / (b/2))) * y ] dy from b1 to b2
    # Integral[ C_r*y - (C_r - C_t) / (b/2) * y^2 ] dy from b1 to b2
    # [ 0.5 * C_r * y^2 - (C_r - C_t) / (3 * b/2) * y^3 ] from b1 to b2
    # [ 0.5 * C_r * y^2 - (2 * (C_r - C_t)) / (3 * b) * y^3 ] from b1 to b2
    I_1 = (0.5 * C_r * b2**2 - (2 * (C_r - C_t)) / (3 * b) * b2**3) - \
          (0.5 * C_r * b1**2 - (2 * (C_r - C_t)) / (3 * b) * b1**3)


    # Calculate integral I_2 (derived from the integral of y^2 * c(y) dy)
    # where c(y) is the local chord at span-wise position y.
    # Integral[ (C_r - (C_r - C_t) * (y / (b/2))) * y^2 ] dy from 0 to b/2
    # Integral[ C_r*y^2 - (C_r - C_t) / (b/2) * y^3 ] dy from 0 to b/2
    # [ (C_r / 3) * y^3 - (C_r - C_t) / (4 * b/2) * y^4 ] from 0 to b/2
    # [ (C_r / 3) * y^3 - (2 * (C_r - C_t)) / (4 * b) * y^4 ] from 0 to b/2
    I_2 = (C_r * (b/2)**3) / 3 - ((C_r - C_t) / (2 * b)) * (b/2)**4

    # Aileron control derivative (C_l_delta_a)
    C_l_delta_a = (2 * c_l_alpha * tau * I_1) / (S_ref * b)

    # Roll damping derivative (C_l_p)
    C_l_p = (-4 * (c_l_alpha + c_d_0) * I_2) / (S_ref * b**2)

    # Aircraft steady state roll rate (P)
    P = (-1 * C_l_delta_a * delta_a * 2 * V_stall) / (C_l_p * b)

    # Required time to achieve bank angle (delta_t)
    delta_t = (bank_angle * np.pi) / (180 * P)

    # Approximate Aileron surface area
    # Assuming aileron chord is CA_to_C * local_chord at its spanwise position
    # For a trapezoidal wing, chord at b1: c_b1 = C_r - (C_r - C_t) * (b1 / (b/2))
    # Chord at b2: c_b2 = C_r - (C_r - C_t) * (b2 / (b/2))
    # Average chord of aileron section: (c_b1 + c_b2) / 2 * CA_to_C
    # Span of aileron: (b2 - b1)
    # S_aileron = (b2 - b1) * CA_to_C * ( (C_r - (C_r - C_t) * (b1 / (b/2))) + (C_r - (C_r - C_t) * (b2 / (b/2))) ) / 2
    # The original S_aileron calculation: (b2-b1)* (params.wing.root_chord-params.wing.tip_chord) / (b/2) *b1
    # This original calculation seems incorrect for surface area. Let's use a more standard approximation.
    # Aileron area approximation: average chord * span of aileron
    # Average chord along the aileron span:
    avg_chord_aileron_section = (C_r - (C_r - C_t) * (b1 / (b/2)) + C_r - (C_r - C_t) * (b2 / (b/2))) / 2
    S_aileron = (b2 - b1) * CA_to_C * avg_chord_aileron_section


    results = {
        'time_to_bank': delta_t,
        'aircraft_weight': W,
        'stall_speed': V_stall,
        'CL_max': C_L_max,
        'root_chord': C_r,
        'tip_chord': C_t,
        'half_span': b / 2,
        'aileron_inboard_edge': b1,
        'aileron_outboard_edge': b2,
        'wing_surface_area': S_ref,
        'aileron_surface_area_approx': S_aileron
    }

    return results




aileron_data = calculate_aileron_specifics(params,0.2,0.62,0.9,1.225,0.349,30)

print("\nCalculated Aileron Specifics:")
for key, value in aileron_data.items():
    if isinstance(value, float):
        print(f"{key}: {value:.4f}")
    else:
        print(f"{key}: {value}")