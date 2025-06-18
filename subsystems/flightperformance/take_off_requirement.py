from design_variables import DesignParameters
from subsystems.flightperformance.FlightSim import FlightSim

def calculate_Cm(C_m_ac,mass0,S,S_h,l_h,V_h_V,x_cg,x_w,c,C_N_h,z_cg,z_p, Cd0, AR, oswald, TSFC, C_L, X_TO):
    '''
    Returns (float, boolean) = calculated Cm, lower/higher than 0
    
    Returns True if aircraft can achieve positive moment coefficient (pitch-up) during take-off, False otherwise. 
    
    Parameters:
    C_m_ac: moment coefficient about aerodynamic center
    mass0: take-off mass [kg]
    S: wing surface area
    S_h: horizontal tail surface area
    l_h: x_h - x_w = x_h - x_cg = distance between horizontal tail and wing
    V_h_V: airspeed of horizontal tail over total airspeed (Vh/V)
    x_cg: x coordinate of center of gravity, taken from nose of aircraft (in m!)
    x_w: x coordinate of wing, taken from nose of aircraft (in m!)
    c: mean aerodynamic chord of wing
    C_N_w: normal coefficient of wing (C_l of wing at take-off)
    C_N_h: normal coefficient of horizontal tail (C_l of tail at take-off)
    z_cg: z coordinate of center of gravity
    z_p: z coordinate of jet engine
    cd0: zero-lift drag coefficient
    AR: wing aspect ratio
    oswald: oswald efficiency factor of wing
    TSFC: Thrust specific fuel consumption of engine
    '''
    
    T, _, V = FlightSim().ground_run2(mass0*2,mass0, S, Cd0, AR, oswald, TSFC, C_L, X_TO)
    rho = 1.225
    
    #print('Tc',T_c*(z_p - z_cg)/c)
    print("engine",2*T/(rho*(V**2)*S)*((z_cg - z_p)/c))
    C_m = C_m_ac + C_L*(x_cg-x_w)/c - C_N_h*(V_h_V**2)*S_h*l_h/(S*c) + 2*T/(rho*(V**2)*S)*((z_cg - z_p)/c)
    
    if C_m > 0:
        return C_m, True
    else:
        return C_m, False
    
if __name__ == "__main__": # pragma: no cover
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')
    Cm, _ = calculate_Cm(params.fuselage.C_m_ac, params.weight.W_TO/9.81, params.wing.S_w, params.empennage.S_h, 3.7439, 0.95, 5.4176, 5.256, params.wing.mac, params.empennage.CL_h, 0, 1.442, params.wing.C_D0, params.wing.A_w_target, params.wing.e, params.engine.cruise_tsfc_SI, params.performance.CL_max_TO, 1500)
    print('Cm',Cm)