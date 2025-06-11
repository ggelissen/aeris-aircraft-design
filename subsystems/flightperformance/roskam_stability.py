import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import math

sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

from design_variables import DesignParameters

#roskam page 383, chapter 10 part VI, 10.2.4

def angle_of_sideslip(params: DesignParameters):

    C_Y_beta_w = -0.00573*params.wing.Gamma_w*180 / np.pi

    x_1 = #from lucas
    x_0 = params.fuselage.l_f *(0.378 + 0.527*(x_1/params.fuselage.l_f))
    S_o =  #from lucas
    z_w = -0.4 * params.fuselage.D_f #estimation because we can't get so specific
    z_f = params.fuselage.D_f 
    print(f"this is the x axis of the K_i plot: {z_w / params.fuselage.D_f}") #assumed that diameter at wing is max diameter
    input("what is the value of K_i? p.384/416")
    K_i = #from plot on page 384
    C_Y_beta_f = -2*K_i*(S_o / params.wing.S_w) 

    b_v = params.empennage.b_v
    two_r_1 = #from lucas: fuselage depth in region of vertical tail (at x_ac_mac of tail)
    print(f"this is the x axis of k_v plot: {b_v / two_r_1}")
    k_v = input("what is the value of k_v? p.385/417")
    C_L_alpha_v = #get eventually from tail sizing
    parameter_in_C_Y_beta_v = 0.724 + 3.06*((params.empennage.S_v / params.wing.S_w)/(1+ math.cost(params.wing.Lambda_025c_w)))+0.4* z_w / z_f + 0.009 * params.wing.A_w_target
    C_Y_beta_v = -k_v*(C_L_alpha_v)* parameter_in_C_Y_beta_v * (params.empennage.S_v / params.wing.S_w)

    C_Y_beta = C_Y_beta_w + C_Y_beta_f + C_Y_beta_v
    
    C_l_beta_wf = 57.3*()
    
    C_l_beta = C_l_beta_wf + C_l_beta_h _ C_l_beta_v

    return C_Y_beta, C_l_beta



def roll_rate_derivates(params: DesignParameters):
    zv = input(f"zv is read from figure 10.27")
    lv = input(f"lv is read from figure 10.27")
    z = input("vertical distance between the airplane center of gravity and the wing root quarter chord point")
    beta = (1-M**2)**0.5
    kappa = 
    Clp_gamma_0_cl_0 = (kappa/beta)*((beta*Clp)/kappa) # at C_L = 0
    
    Cyp = 2*CyBv(zv*math.cos(alpha)-lv*math.sin(alpha)-zv)/params.wing.b_w + 3*math.sin(params.wing.Gamma_w) * (1- (4*z/params.wing.b_w)*math.sin(params.wing.Gamma_w))*Clp_gamma_0_cl_0
    
    BClp_K_CL_0 = input("roll damping parameter at zero lift which is obtained from figure 10.35 pag. 418/450")
    ClaCL = input("the wing lift-curve slope at any lift coefficient. It is obtained as the local slope of the wing CL versus alpha curve as obtained from 8.1.3.5 or from 8.1.4.4")
    ClaCl_0 = input("the wing lift-curve slope at zero lift as obtained from eq (8.22)")
    gamma = input("gamma(?) defined in figure 10.7")
    zw = input("zw defined in figure 10.9")
    paramater1 = (1 - (4*zw / params.wing.b_w)*math.sin(gamma) + 12 * (zw / params.wing.b_w)**2 * math.sin(gamma)**2)
    ClpCdlCl2 = input("The drag-due-to-lift roll damping parameter as found from figure 10.36")
    C_L = input("wing C_L")
    paramater2 = ClpCdlCl2 * C_L**2 - 0.125*params.wing.C_D0
    Clpw = BClp_K_CL_0*(kappa/beta) * (ClaCL / ClaCl_0) * paramater1 + paramater2
    Clp_h = input("the roll-damping derivative of the horizontal tail based on its own reference geometry. It is obtained from Eq 10.52 with appropiate substitution of horizontal tail parameters for wing parameters")
    b_h = input("span of horizontal tail (b_h)")
    Clph = 0.5*Clp_h * (params.empennage.S_h/params.wing.S_w)*(b_h/params.wing.b_w)**2
    Clpv = 2/(params.wing.b_w**2)*abs((zv*math.cos(alpha)-lv*math.sin(alpha))*(zv*math.cos(alpha)-lv*math.sin(alpha)-zv))*CyBv
    
    Clp = Clpw + Clph + Clpv
    
    qcsweep = input("sweep at quarter chord (/\_c/4)")
    B = (1-M**2*cos(qcsweep)**2)**0.5
    A = params.wing.A_w_actual
    CnpClCl_0_M_0 = -1/6 * ()
    CnpClCl_0 = (A+4*math.cos(qcsweep)/(A*B+4*math.cos(qcsweep))) * ((A*B + 0.5*(A*B+math.cos(qcsweep))*(math.tan(qcsweep)**2))/(A + 0.5*(A+math.cos(qcsweep))*(math.tan(qcsweep)**2))) * CnpClCl_0_M_0
    
    Cnpv = -(2/params.wing.b_w**2)*(lv*math.cos(alpha)+zv*math.sin(alpha))*(zv*math.cos(alpha)-lv*math.sin(alpha)-zv)*CyBv
    
    Cnp = Cnpw + Cnpv
    