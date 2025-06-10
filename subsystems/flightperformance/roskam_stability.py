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

