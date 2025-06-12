from subsystems.flightperformance.FlightSim import FlightSim

def calculate_Cm(C_m_ac,mass0,S,S_h,l_h,V_h_V,x_cg,x_w,c,C_N_w,C_N_h,z_cg,z_p, Cd0, AR, oswald, TSFC, C_L):
    '''
    C_m_ac = moment coefficient about aerodynamic center
    
    mass0 = take-off mass
    
    S = wing surface area
    
    S_h = horizontal tail surface area
    
    l_h = x_h - x_w = x_h - x_cg = distance between horizontal tail and wing
    
    V_h_V = airspeed of horizontal tail over total airspeed (Vh/V)
    
    x_cg = x coordinate of center of gravity, taken from nose of aircraft (in m!)
    
    x_w = x coordinate of wing, taken from nose of aircraft (in m!)
    
    c = mean aerodynamic chord of wing
    
    C_N_w = normal coefficient of wing (C_l of wing at take-off)
    
    C_N_h = normal coefficient of horizontal tail (C_l of tail at take-off)
    
    z_cg = z coordinate of center of gravity
    
    z_p = z coordinate of jet engine
    
    Returns (float, boolean) = calculated Cm, lower/higher than 0
    
    Returns True if aircraft can achieve positive moment coefficient (pitch-up) during take-off, False otherwise. 
    '''
    
    T, _, V = FlightSim().ground_run2(mass0*2,mass0, S, Cd0, AR, oswald, TSFC, C_L)
    rho = 1.225

    T_c = T / (0.5*rho*V**2*S)
    
    #print('Tc',T_c*(z_p - z_cg)/c)
    
    C_m = C_m_ac + C_N_w*(x_cg-x_w)/c - C_N_h*(V_h_V**2)*S_h*l_h/(S*c) - T_c*(z_p - z_cg)/c
    
    if C_m > 0:
        return C_m, True
    else:
        return C_m, False
    
if __name__ == "__main__":
    Cm, _ = calculate_Cm(1, 4000, 12, 4, 6, 1, 7, 6, 1, 1, 0, 1, 2)
    print('Cm',Cm)