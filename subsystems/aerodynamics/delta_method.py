# delta_method.py
# CORRECTED VERSION - Fixes the interpolation logic.
import numpy as np
import matplotlib.pyplot as plt

# --- Data remains the same ---
DELTA_M_SWEEP_X = np.array([0.0, 6.958, 12.660, 18.530, 23.495, 27.566, 30.0, 32.693, 36.753, 40.814, 45.396, 49.444, 53.490, 58.067, 60.0])
DELTA_M_SWEEP_Y = np.array([0.0, 0.0018, 0.0057, 0.0124, 0.0228, 0.0338, 0.04, 0.0491, 0.0630, 0.0769, 0.0952, 0.1126, 0.1309, 0.1505, 0.1600])
DELTA_M_AR_X = np.array([0.0, 0.054621, 0.143022, 0.196048, 0.257086, 0.326169, 0.367924, 0.420933, 0.480375, 0.533401])
DELTA_M_AR_Y = np.array([0.0, 0.008081, 0.019579, 0.027000, 0.036415, 0.046519, 0.053236, 0.061309, 0.070064, 0.077485])
ADVANCED_AIRFOIL_DATA = {
    0.8: {'x': [0.1810, 0.3117], 'y': [-0.3154, -0.5627]}, 0.7: {'x': [0.1810, 0.3120], 'y': [-0.2947, -0.5446]},
    0.6: {'x': [0.1816, 0.3120], 'y': [-0.2702, -0.5201]}, 0.5: {'x': [0.1810, 0.3117], 'y': [-0.2572, -0.5097]},
    0.4: {'x': [0.1810, 0.3117], 'y': [-0.2430, -0.5020]}, 0.3: {'x': [0.1810, 0.3112], 'y': [-0.2275, -0.4942]},
    0.2: {'x': [0.1816, 0.3112], 'y': [-0.2171, -0.4825]}, 0.1: {'x': [0.1813, 0.3117], 'y': [-0.2068, -0.4735]}
}

def _get_delta_m_sweep(sweep_deg):
    return np.interp(sweep_deg, DELTA_M_SWEEP_X, DELTA_M_SWEEP_Y)

def _get_delta_m_ar(aspect_ratio):
    if aspect_ratio == 0: return np.inf
    return np.interp(1.0 / aspect_ratio, DELTA_M_AR_X, DELTA_M_AR_Y)

def _get_tc_from_mdd2d(mdd2d, cl_des):
    """
    CORRECTED 2D interpolation to find t/c from required 2D Mdd.
    The key fix is using [::-1] to reverse both arrays, which preserves
    the mapping while making the lookup axis monotonic.
    """
    required_y = mdd2d**2 - 1
    cl_keys = sorted(ADVANCED_AIRFOIL_DATA.keys())

    if not (cl_keys[0] <= cl_des <= cl_keys[-1]): return 0

    upper_cl_key = min(key for key in cl_keys if key >= cl_des)
    lower_cl_key = max(key for key in cl_keys if key <= cl_des)

    def get_x_for_y(y_target, curve_data):
        # The y-data from the chart is descending. To use np.interp, the lookup
        # array must be ascending. We reverse both arrays with [::-1] to achieve this
        # while keeping the (x,y) pairs correctly mapped.
        return np.interp(y_target, curve_data['y'][::-1], curve_data['x'][::-1])

    if upper_cl_key == lower_cl_key:
        required_x = get_x_for_y(required_y, ADVANCED_AIRFOIL_DATA[cl_des])
    else:
        x_at_lower_cl = get_x_for_y(required_y, ADVANCED_AIRFOIL_DATA[lower_cl_key])
        x_at_upper_cl = get_x_for_y(required_y, ADVANCED_AIRFOIL_DATA[upper_cl_key])
        interp_fraction = (cl_des - lower_cl_key) / (upper_cl_key - lower_cl_key)
        required_x = x_at_lower_cl + interp_fraction * (x_at_upper_cl - x_at_lower_cl)
    
    return required_x**(1.5)

def calculate_tc_from_delta_method(target_cruise_mach, aspect_ratio, sweep_deg, cl_des):
    """
    Calculates the achievable thickness-to-chord ratio using the Delta Method.
    """
    try:
        total_correction = _get_delta_m_sweep(sweep_deg) + _get_delta_m_ar(aspect_ratio)
        required_mdd2d = target_cruise_mach - total_correction
        if required_mdd2d <= 0: return 0
        t_c = _get_tc_from_mdd2d(required_mdd2d, cl_des)
        return t_c if t_c > 0.05 else 0
    except (ValueError, IndexError):
        return 0
    

# --- Plotting Section ---
# --- Example Usage ---
if __name__ == '__main__':
    ar_test = 11.0 # 1/AR = 0.0909
    sweep_test = 30.0
    cl_test = 0.5
    mach_test = 0.85
    
    tc_result = calculate_tc_from_delta_method(mach_test, ar_test, sweep_test, cl_test)
    
    print("--- Example Run with Updated Data ---")
    print(f"For M={mach_test}, AR={ar_test}, Sweep={sweep_test}°, CL={cl_test}:")
    print(f"The achievable t/c is: {tc_result:.4f} or {tc_result*100:.2f}%")
        
    # Create a figure with 3 subplots
    fig, axs = plt.subplots(3, 1, figsize=(8, 18))
    fig.suptitle('Visual Validation of Digitized Delta Method Charts', fontsize=16)

    # Plot 1: Sweep Correction
    axs[0].plot(DELTA_M_SWEEP_X, DELTA_M_SWEEP_Y, 'o-', label='Digitized Data')
    axs[0].set_title('Figure 4 (Top): Sweep Correction')
    axs[0].set_xlabel('Sweep Angle, Λ_c/4 (deg)')
    axs[0].set_ylabel('Correction, ΔM')
    axs[0].grid(True)
    axs[0].legend()

    # Plot 2: Aspect Ratio Correction
    axs[1].plot(DELTA_M_AR_X, DELTA_M_AR_Y, 'o-', label='Digitized Data', color='green')
    axs[1].set_title('Figure 4 (Bottom): Aspect Ratio Correction')
    axs[1].set_xlabel('Inverse Aspect Ratio (1/AR)')
    axs[1].set_ylabel('Correction, ΔM')
    axs[1].grid(True)
    axs[1].legend()

    # Plot 3: Advanced Airfoil Performance
    axs[2].set_title('Figure 3: Advanced Airfoil Performance')
    for cl, data in ADVANCED_AIRFOIL_DATA.items():
        axs[2].plot(data['x'], data['y'], 'o-', label=f'CL_DES = {cl}')
    axs[2].set_xlabel('(t/c)^(2/3)')
    axs[2].set_ylabel('M_dd^2 - 1')
    axs[2].grid(True)
    axs[2].legend()
    axs[2].invert_yaxis() # The original chart has a descending y-axis

    # Show the plots
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.show()
