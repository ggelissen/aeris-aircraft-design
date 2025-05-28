import numpy as np

#ADVANCED AIRCRAFT DESIGN
#   - PROPULSION INTEGRATION
#       - L.17 PROPELLER SLIPSTREAM EFFECTS: Not relevant
#       - L.18 Engine Intakes: Relevant
#       - L.19 Exhaust & Thrust reversers: Relevant
#       - L.20 Wing integration: Relevant

#High-speed design requirements:
    #MFR (mass flow ratio) <=1
    #Super velocities outside intake critical
    #Cross section engine flow indep. inlet shape
    #Mass flow varies w/ engine setting, altitude & airspeed
    #Intake area closely to req. mass flow
    #Extern. cowling shd. prevent shock waves
    
#Design conditions:
    #Stream tube diameter <= throat diameter
    #Typical mach 0.85: thicker engine
    #Typical mach 0.98: Thin lip/low external curvature
    
#Low-speed design requirements:  
    #MFR > 1.0
    #Highest super velocities near throat area
    #Velocity distribution over throat area ot uniform
    #M_TH > 0.8 -> large decrease in tot. press. recov. & efficiency
    #Max. M_TH is crit. at low speed due req. engine mass flow largest @ take-off & init. climb
    #Ave. limited M_TH < 0.8 to prevent shock waves


#One dimensional isentropic flow relation:
#Note:  High mf (given A_TH) leads to high throat Mach numbers
#       M_TH <= 1
#       If M_TH > 0.8 -> shock waves/total press. loss

m_dot = 0
T_T = 0
p_T = 0
M_TH = 0
gamma = 1.4
R = 287
A_INF = 0
A_HL = 0

MFR = A_INF / A_HL
A_TH = m_dot * np.sqrt(T_T) / p_T * (M_TH*(1+(gamma-1)/2*M_TH**2)**((gamma+1)/(2*(1-gamma)))*np.sqrt(gamma/R))**(-1)

#Fuselage-mounted: align intake with local flow (upwash)

#Nozzle function: 
#   - Convert energy into kinetic energy through expansion
m_e_dot = 0
V_e = 0
V_INF = 0
A_e = 0 # exhaust area
p_e = 0
p_0 = 0 # back pressure

T = m_e_dot * (V_e - V_INF) + A_e * (p_e - p_0)

#Exhaust efficiency coefficients:
F_actual = 0
m_dot_actual = 0
V_actual = F_actual / m_dot_actual
V_ideal = 0
m_dot_ideal = 0
C_V = V_actual / V_ideal
C_D = m_dot_actual / m_dot_ideal

#Nozzle thrust coefficient:
C_T = C_V * C_D
#Turbofan:
F_actual_fancore = 0
F_ideal_fan = 0
F_ideal_core = 0
C_T_tf = F_actual_fancore / (F_ideal_fan + F_ideal_core)

#Case: un-choked nozzle, p_0/p_T > 0.528 (cold flow) or p_T / p_0 < 1.89
p_T = 0 # stagnation pressure
V_ideal = np.sqrt(2*gamma*R*T_T/(gamma-1)*(1-(p_0/p_T)**((gamma-1)/gamma)))
m_dot_ideal = A_e * p_T * np.sqrt(2*gamma/(gamma-1)*1/(R*T_T)*((p_0/p_T)**(2/gamma)-(p_0/p_T)**((gamma+1)/gamma)))

#Case: choked nozzle, p_0/p_T < 0.528 (cold flow) or