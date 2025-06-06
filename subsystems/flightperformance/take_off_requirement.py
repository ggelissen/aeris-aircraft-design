from subsystems.flightperformance.FlightSim import FlightSim

def calculate_Cm(C_m_ac,mass0,S,S_h,l_h,V_h,x_cg,x_w,c,C_N_w,C_N_h):
    '''
    C_m_ac = moment coefficient about aerodynamic center
    mass0 = take-off mass
    S = wing surface area
    S_h = horizontal tail surface area
    l_h = x_h - x_w = x_h - x_cg
    V_h = airspeed over horizontal tail
    x_cg = x coordinate of center of gravity, taken from nose of aircraft (in m!)
    x_w = x coordinate of wing, taken from nose of aircraft (in m!)
    c = mean aerodynamic chord of wing
    C_N_w = normal coefficient of wing (C_l of wing at take-off)
    C_N_h = normal coefficient of horizontal tail (C_l of tail at take-off)
    
    Returns True if aircraft can achieve positive moment coefficient (pitch-up) during take-off, False otherwise. 
    '''
    
    T, _, V = FlightSim().ground_run2(mass0*2,mass0)
    
    rho = 1.225

    T_c = T / (0.5*rho*V**2*S)
    
    C_m = C_m_ac + C_N_w*(x_cg-x_w)/c + C_N_h*((V_h/V)**2)*S_h*l_h/(S*c) - T_c 
    
    if C_m > 0:
        return True
    else:
        return False