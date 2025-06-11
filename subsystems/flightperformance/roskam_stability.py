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

def angle_of_sideslip_beta(params: DesignParameters):

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
    
    
    C_L_wf = #cruise lift coefficient of aircraft
    wing_sweep_contribution = input("what is the contribution of the wing sweep to the C_l_beta? p.393/425")
    M_cos_Lambda_half = params.cruise_mach*math.cos(params.wing.Lambda_05_w)
    A_Sweep = params.wing.A_w_target / math.cos(params.wing.Lambda_05_w)
    print(f"this is the x axis of the compressibility sweep plot: {M_cos_Lambda_half, A_Sweep}")
    K_M_Lambda = input("what is the compressibility correction to sweep? p.394/426")
    lf_b = params.fuselage.l_f / params.wing.b_w
    print(f"this is the x axis of the K_F plot: {lf_b, A_Sweep}")
    K_f = input("what is the fuselage correction to sweep? p.394/426")    
    aspect_ratio_contribution = input("what is the contribution of the aspect ratio to the C_l_beta? p.394/426")
    wing_dihedral_effect = input("what is the contribution of the wing dihedral to the C_l_beta? p.395/427")
    print(f"this is the x axis of the K__M_Gamma plot: {M_cos_Lambda_half, A_Sweep}")
    K_M_Gamma = input("what is the compressibility correction to the wing dihedral? p.396/428")
    fuselage_effect_wing_height = -0.0005*params.wing.A_w_target*(params.fuselage.D_f / params.wing.b_w)**2
    delta_cl_beta_zw = 0.042*(params.wing.A_w_target)**0.5 * (z_w / params.wing.b_w)* (params.fuselage.D_f / params.wing.b_w)
    wing_twist_correction = input("what is the contribution of the wing twist to the C_l_beta? p.396/428")
    #wing twist correction very confused on page 397/429
    #what is root-section zero-lift line and tip-section zero lift line?
    C_l_beta_wf = 57.3*(C_L_wf *(wing_sweep_contribution*K_M_Lambda*K_f + aspect_ratio_contribution) + params.wing.Gamma_w* wing_dihedral_effect * K_M_Gamma + wing_dihedral_effect + delta_cl_beta_zw + wing_twist_correction)


    # C_l_beta_h = C_l_beta_hf * ((params.empennage.S_h*params.empennage.b_h) / (params.wing.S_w*params.wing.b_w)) #what is horizontal tail span
    kappa_Gamma = input("what is kappa_Gamma (dihedral factor for roll stability)? Philips paper fig. 17")
    kappa_l = input("what is kappa_l (planform factor for roll stability)? Philips paper fig. 17")
    kappa_L = 0.04 #estimation according do Philips paper
    C_L_alpha_tail_airfoil = 2*np.pi
    C_L_alpha_Gamma0 = (C_L_alpha_tail_airfoil) / (1 + C_L_alpha_tail_airfoil / (np.pi*params.empennage.A_t))*(1 + kappa_L)
    C_l_beta_vtail = -((2*params.empennage.S_t*params.empennage*b_v) / (3*np.pi * params.wing.S_w * params.wing.b_w))*kappa_Gamma * kappa_l * C_L_alpha_Gamma0 * math.sin(params.empennage.vtail_dihedral) #ensure that this is the total area and span of v-tail
    
    C_l_beta = C_l_beta_wf + C_l_beta_vtail

    C_n_beta_w = 0

    h1 = #get from lucas, diameter of fuselage at l_f / 4
    h2 = #get from lucas, diameter of fuselage at 3l_f/4
    print(f"This is needed for K_N: {np.sqrt(h1/h2)}")
    K_N = input("what is K_N? p.397/431")
    Re_L_f = (params.cruise_speed * params.fuselage.l_f) / params.cruise_viscosity #find cruise viscosity
    print(f"This is needed for K_R_l, the reynolds number of fuselage: {Re_L_f}")
    K_R_l = input("what is K_R_l? p.399/432")
    S_B_S = #from lucas body side area
    C_n_beta_f = -57.3*K_N*K_R_l*((S_B_S*params.fuselage.l_f)/(params.wing.S_w*params.wing.b_w))
    
    C_n_beta_v = -C_Y_beta_v *(params.empennage.L_h * math.cos(params.cruise_aoa)+ params.empennage.z_v * math.sin(params.cruise_aoa))/params.wing.b_w


    C_n_beta = C_n_beta_w + C_n_beta_f + C_n_beta_v

    return C_Y_beta, C_l_beta, C_n_beta, C_Y_beta_v

def pitch_rate_q(params: DesignParameters):
    C_D_q = 0 

    B = #from luuks code when merged
    x_w = #position of wing 0.25 c - x_cg of aircraft
    C_L_alpha_w = #wing lift curve slope from mrugank
    C_L_q_w_M0 = (0.5 + 2*x_w / params.wing.mac)*C_L_alpha_w
    C_L_q_w = ((params.wing.A_w_target + 2*math.cos(params.wing.Lambda_025c_w))/(params.wing.A_w_target*B+2*math.cos(params.wing.Lambda_025c_w)))*C_L_q_w_M0
    C_L_alpha_h = #lift curve slope of tail
    C_L_q_h = 2*C_L_alpha_h*params.empennage.Vh_v*params.empennage.V_h #check that V_h is volume coefficient
    C_L_q = C_L_q_w + C_L_q_h 

    K_w = 0.9 #assuming aspect ratio is higher than 10 so change if not, see p.426/459 roskam
    C_m_q_w_M0 = -K_w*C_L_alpha_w * math.cos(params.wing.Lambda_025c_w)*((params.wing.A_w_target*(2*(x_w/params.wing.mac)**2 + 0.5*(x_w / params.wing.mac)))/(params.wing.A_w_target + 2*math.cos(params.wing.Lambda_025c_w)) + (params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(24*(params.wing.A_w_target + 6*math.cos(params.wing.Lambda_025c_w))) + 1/8)
    C_m_q_w = C_m_q_w_M0*((params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(params.wing.A_w_target * B + 6 * math.cos(params.wing.Lambda_025c_w))+3/B)/((params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(params.wing.A_w_target + 6*math.cos(params.wing.Lambda_025c_w)+3))
    
    x_ac_h = #distance between LEMAC to quarter chord of tail
    C_m_q_h = -2*C_L_alpha_h*params.empennage.Vh_v*params.empennage.V_h*(x_ac_h - params.cg.x_cg) #TODO check that this cg works

    C_m_q = C_m_q_w + C_m_q_h

    return C_L_q, C_m_q, C_D_q

def yaw_rate_r(params: DesignParameters, C_Y_beta_v):
    C_Y_r = -2* C_Y_beta_v * (params.empennage.L_h * math.cos(params.cruise_aoa) + params.empennage.z_v * math.sin(params.cruise_aoa)) / params.wing.b_w'

    C_L_w = #wing lift coefficient at cruise
    parameter_for_C_l_r_w = 
    parameter2_for_C_l_r_w = input("what is the parameter from fig 10.41 p.428/462 roskam?")
    C_l_r_w = C_L_w * parameter_for_C_l_r_w + parameter2_for_C_l_r_w * params.wing.Gamma_w
    
    C_l_r_v = -(2/params.wing.b_w**2)*(params.empennage.L_h*math.cos(params.cruise_aoa)+params.empennage.z_v*math.sin(cruise_aoa))*(params.empennage.z_v*math.cos(params.cruise_aoa - params.empennage.L_v*math.sin(params.cruise_aoa))*C_Y_beta_v)
    
    C_l_r = C_l_r_w + C_l_r_v

    return C_Y_r, C_l_r