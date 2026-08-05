import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import math
import openvsp as vsp
from subsystems.structures.main_struct import struct_main
from scipy.interpolate import interp1d

sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

from config.design_variables import DesignParameters

#roskam page 383, chapter 10 part VI, 10.2.4

def angle_of_sideslip_beta(params: DesignParameters):

    C_Y_beta_w = -0.00573*params.wing.Gamma_w*180 / np.pi

    vsp.SetSetFlag(params.fuselage.fuseid, 17, True)
    vsp.ComputePlaneSlice(17, 50, vsp.vec3d(1, 0, 0), True)
    fuselage_area_distribution = np.asarray(vsp.GetDoubleResults(vsp.FindLatestResultsID('Slice'), 'Slice_Area'))
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
    lengthwise_points =  np.linspace(0, 10, len(fuselage_area_distribution))
    fuselage_area = interp1d(lengthwise_points, fuselage_area_distribution)
    x_1 = lengthwise_points[np.argmin(np.diff(fuselage_area_distribution))]
    x_0 = params.fuselage.l_f *(0.378 + 0.527*(x_1/params.fuselage.l_f))
    S_o = fuselage_area(x_0)
    z_w = -0.4 * params.fuselage.D_f #estimation because we can't get so specific
    z_f = params.fuselage.D_f 
    print(f"this is the x axis of the K_i plot: {z_w / params.fuselage.D_f}") #assumed that diameter at wing is max diameter
    K_i =     float(input("what is the value of K_i? p.384/416"))  #from plot on page 384
    C_Y_beta_f = -2*K_i*(S_o / params.wing.S_w) 
    
    b_v = params.empennage.b_v
    vsp.SetParmVal(params.empennage.tailid, 'Sweep_Location', "XSec_1", 0.0)
    ylemac_tail = vsp.GetParmVal(params.empennage.tailid, 'MAC', 'WingGeom') * vsp.GetParmVal(params.empennage.tailid, 'TotalProjectedSpan', 'WingGeom') / (2 * vsp.GetParmVal(params.empennage.tailid, 'Taper', 'XSec_1') * vsp.GetParmVal(params.empennage.tailid, 'Root_Chord', 'XSec_1'))

    xmac_vtail = vsp.GetParmVal(params.empennage.tailid, 'X_Rel_Location', 'XForm') + 0.25 * vsp.GetParmVal(params.empennage.tailid, 'MAC', 'WingGeom')  + np.tan(np.deg2rad(vsp.GetParmVal(params.empennage.tailid, 'Sweep', 'XSec_1'))) * ylemac_tail
    vsp.ComputePlaneSlice(17, 1, vsp.vec3d(1, 0, 0), False, start_bnd=xmac_vtail)
    fuselage_area_at_that_place = np.asarray(vsp.GetDoubleResults(vsp.FindLatestResultsID('Slice'), 'Slice_Area'))[0]
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
    two_r_1 = 2*np.sqrt(fuselage_area_at_that_place/np.pi) #from lucas: fuselage depth in region of vertical tail (at x_ac_mac of tail)
    print(f"this is the x axis of k_v plot: {b_v / two_r_1}")
    k_v = float(input("what is the value of k_v? p.385/417"))
    C_L_alpha_v = params.empennage.Cl_alpha #get eventually from tail sizing
    parameter_in_C_Y_beta_v = 0.724 + 3.06*((params.empennage.S_v / params.wing.S_w)/(1+ math.cos(params.wing.Lambda_025c_w)))+0.4* z_w / z_f + 0.009 * params.wing.A_w_target
    C_Y_beta_v = -k_v*(C_L_alpha_v)* parameter_in_C_Y_beta_v * (params.empennage.S_v / params.wing.S_w)

    C_Y_beta = C_Y_beta_w + C_Y_beta_f + C_Y_beta_v
    
    
    C_L_wf = params.performance.CL_cruise
    wing_sweep_contribution = float(input("what is the contribution of the wing sweep to the C_l_beta? p.393/425"))
    M_cos_Lambda_half = params.cruise_mach*math.cos(params.wing.Lambda_05_w)
    A_Sweep = params.wing.A_w_target / math.cos(params.wing.Lambda_05_w)
    print(f"this is the x axis of the compressibility sweep plot: {M_cos_Lambda_half, A_Sweep}")
    K_M_Lambda = float(input("what is the compressibility correction to sweep? p.394/426"))
    lf_b = params.fuselage.l_f / params.wing.b_w
    print(f"this is the x axis of the K_F plot: {lf_b, A_Sweep}")
    K_f = float(input("what is the fuselage correction to sweep? p.394/426") )
    aspect_ratio_contribution = float(input("what is the contribution of the aspect ratio to the C_l_beta? p.394/426"))
    wing_dihedral_effect = float(input("what is the contribution of the wing dihedral to the C_l_beta? p.395/427"))
    print(f"this is the x axis of the K__M_Gamma plot: {M_cos_Lambda_half, A_Sweep}")
    K_M_Gamma = float(input("what is the compressibility correction to the wing dihedral? p.396/428"))
    fuselage_effect_wing_height = -0.0005*params.wing.A_w_target*(params.fuselage.D_f / params.wing.b_w)**2
    delta_cl_beta_zw = 0.042*(params.wing.A_w_target)**0.5 * (z_w / params.wing.b_w)* (params.fuselage.D_f / params.wing.b_w)
    C_l_beta_wf = 57.3*(C_L_wf *(wing_sweep_contribution*K_M_Lambda*K_f + aspect_ratio_contribution) + params.wing.Gamma_w* wing_dihedral_effect * K_M_Gamma + wing_dihedral_effect + delta_cl_beta_zw)


    kappa_Gamma = float(input("what is kappa_Gamma (dihedral factor for roll stability)? Philips paper fig. 17"))
    kappa_l = float(input("what is kappa_l (planform factor for roll stability)? Philips paper fig. 17"))
    kappa_L = 0.04 #estimation according do Philips paper
    C_L_alpha_tail_airfoil = 2*np.pi
    C_L_alpha_Gamma0 = (C_L_alpha_tail_airfoil) / (1 + C_L_alpha_tail_airfoil / (np.pi*params.empennage.A_t))*(1 + kappa_L)
    C_l_beta_vtail = -((2*params.empennage.S_t*params.empennage.b_v) / (3*np.pi * params.wing.S_w * params.wing.b_w))*kappa_Gamma * kappa_l * C_L_alpha_Gamma0 * math.sin(params.empennage.vtail_dihedral) #ensure that this is the total area and span of v-tail
    
    C_l_beta = C_l_beta_wf + C_l_beta_vtail

    C_n_beta_w = 0


    vsp.ComputePlaneSlice(17, 1, vsp.vec3d(1, 0, 0), False, start_bnd=params.fuselage.l_f*0.25)
    fuselage_area_at_that_place = np.asarray(vsp.GetDoubleResults(vsp.FindLatestResultsID('Slice'), 'Slice_Area'))[0]
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
    h1 = 2 * np.sqrt(fuselage_area_at_that_place / np.pi) #get from lucas, diameter of fuselage at l_f / 4
    vsp.ComputePlaneSlice(17, 1, vsp.vec3d(1, 0, 0), False, start_bnd=params.fuselage.l_f * 0.75)
    fuselage_area_at_that_place = np.asarray(vsp.GetDoubleResults(vsp.FindLatestResultsID('Slice'), 'Slice_Area'))[0]
    vsp.DeleteGeom(vsp.FindGeom("MeshGeom", 0))  # Delete NewGeom which gets added after an export
    for geom in vsp.FindGeoms():
        vsp.SetSetFlag(geom, vsp.GetSetIndex("Shown"), True)
    h2 = 2 * np.sqrt(fuselage_area_at_that_place / np.pi) #get from lucas, diameter of fuselage at 3l_f/4
    print(f"This is needed for K_N: {np.sqrt(h1/h2)}")  #TODO: we need more
    K_N = float(input("what is K_N? p.397/431"))
    Re_L_f = (params.cruise_speed * params.fuselage.l_f) / params.cruise_viscosity #find cruise viscosity
    print(f"This is needed for K_R_l, the reynolds number of fuselage: {Re_L_f}")
    K_R_l = float(input("what is K_R_l? p.399/432"))
    vsp.SetIntAnalysisInput('Projection', 'DirectionType', [1])
    vsp.SetVec3dAnalysisInput('Projection', 'Direction', [vsp.vec3d(0, 1, 0)])
    resultsid = vsp.ExecAnalysis('Projection')
    S_B_S = vsp.GetDoubleResults(resultsid, 'Area')[0] #from lucas body side area
    C_n_beta_f = -57.3*K_N*K_R_l*((S_B_S*params.fuselage.l_f)/(params.wing.S_w*params.wing.b_w))
    
    C_n_beta_v = -C_Y_beta_v *(params.empennage.L_h * math.cos(params.cruise_aoa)+ params.empennage.z_v * math.sin(params.cruise_aoa))/params.wing.b_w


    C_n_beta = C_n_beta_w + C_n_beta_f + C_n_beta_v

    return C_Y_beta, C_l_beta, C_n_beta, C_Y_beta_v

# def pitch_rate_q(params: DesignParameters):
#     C_D_q = 0 

#     B = None #from luuks code when merged
#     x_w = params. #position of wing 0.25 c - x_cg of aircraft @lucas
#     C_L_alpha_w = params. #wing lift curve slope from mrugank
#     C_L_q_w_M0 = (0.5 + 2*x_w / params.wing.mac)*C_L_alpha_w
#     C_L_q_w = ((params.wing.A_w_target + 2*math.cos(params.wing.Lambda_025c_w))/(params.wing.A_w_target*B+2*math.cos(params.wing.Lambda_025c_w)))*C_L_q_w_M0
#     C_L_alpha_h =None #lift curve slope of tail
#     C_L_q_h = 2*C_L_alpha_h*params.empennage.Vh_v*params.empennage.V_h 
#     C_L_q = C_L_q_w + C_L_q_h 

#     K_w = 0.9 #assuming aspect ratio is higher than 10 so change if not, see p.426/459 roskam
#     C_m_q_w_M0 = -K_w*C_L_alpha_w * math.cos(params.wing.Lambda_025c_w)*((params.wing.A_w_target*(2*(x_w/params.wing.mac)**2 + 0.5*(x_w / params.wing.mac)))/(params.wing.A_w_target + 2*math.cos(params.wing.Lambda_025c_w)) + (params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(24*(params.wing.A_w_target + 6*math.cos(params.wing.Lambda_025c_w))) + 1/8)
#     C_m_q_w = C_m_q_w_M0*((params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(params.wing.A_w_target * B + 6 * math.cos(params.wing.Lambda_025c_w))+3/B)/((params.wing.A_w_target**3 * math.tan(params.wing.Lambda_025c_w)**2)/(params.wing.A_w_target + 6*math.cos(params.wing.Lambda_025c_w)+3))
    
#     x_ac_h = None#distance between LEMAC to quarter chord of tail, @lucas
#     C_m_q_h = -2*C_L_alpha_h*params.empennage.Vh_v*params.empennage.V_h*(x_ac_h - params.cg.x_cg) #TODO check that this cg works

#     C_m_q = C_m_q_w + C_m_q_h

#     return C_L_q, C_m_q, C_D_q

def yaw_rate_r(params: DesignParameters, C_Y_beta_v):
    C_Y_r = -2* C_Y_beta_v * (params.empennage.L_h * math.cos(params.cruise_aoa) + params.empennage.z_v * math.sin(params.cruise_aoa)) / params.wing.b_w

    C_L_w = params.performance.CL_cruise
    parameter_for_C_l_r_w = None
    parameter2_for_C_l_r_w = input("what is the parameter from fig 10.41 p.428/462 roskam?")
    C_l_r_w = C_L_w * parameter_for_C_l_r_w + parameter2_for_C_l_r_w * params.wing.Gamma_w
    
    C_l_r_v = -(2/params.wing.b_w**2)*(params.empennage.L_h*math.cos(params.cruise_aoa)+params.empennage.z_v*math.sin(params.cruise_aoa))*(params.empennage.z_v*math.cos(params.cruise_aoa - params.empennage.L_v*math.sin(params.cruise_aoa))*C_Y_beta_v)
    
    C_l_r = C_l_r_w + C_l_r_v

    return C_Y_r, C_l_r

def roll_rate_derivates(params: DesignParameters, CyBv):
    zv = input(f"Z distance from airplane c.g. to vertical tail a.c.") # TODO: PUT IN DESIGN_VARIABLES
    lv = input(f"X distance from airplane c.g. to vertical tail a.c.") # TODO: PUT IN DESIGN_VARIABLES
    z = input("vertical distance between the airplane center of gravity and the wing root quarter chord point") # TODO: PUT IN DESIGN_VARIABLES
    M = 0.7
    beta = (1-M**2)**0.5
    #cla = params.wing.CLA_A_h
    cla0 = params.wing.CLA_A_h_M0
    clam = cla0 /beta
    cla0_t = params.empennage.Cl_alpha_M0
    clam_t = cla0_t/beta
    kappa_w = clam*beta*2*np.pi
    kappa_t = clam_t*beta*2*np.pi
    alpha = params.cruise_aoa /180 *math.pi
    
    deltaB = np.arctan(np.tan(params.wing.Lambda_025c_w/beta))
    BA_K = beta/kappa_w * params.wing.A_w_target
    A = params.wing.A_w_target
    BClp_K_CL_0 = input(f"roll damping parameter at zero lift which is obtained from figure 10.35 pag. 418/450 using sweep_b = {deltaB} and BA/K = {BA_K} and lamba = {params.wing.lambda_w}")
    ClaCL = params.wing.CLA_A_h # input("the wing lift-curve slope at any lift coefficient. It is obtained as the local slope of the wing CL versus alpha curve as obtained from 8.1.3.5 or from 8.1.4.4")
    ClaCl_0 = 2*np.pi*A / (2+(((A**2)*(beta**2)*(kappa_w**2))*(1+(np.tan(params.wing.Lambda_025c_w)/beta)**2)+4)**0.5)  #input("the wing lift-curve slope at zero lift as obtained from eq (8.22)")
    gamma = params.wing.Gamma_w
    zw = input("vertical distance of wing from fuselage c.g. (smaller than 0 for high wing) (ask Julie/Lucas)")
    paramater1 = (1 - (4*zw / params.wing.b_w)*math.sin(gamma) + 12 * (zw / params.wing.b_w)**2 * math.sin(gamma)**2)
    
    ClpCdlCl2 = input(f"The drag-due-to-lift roll damping parameter as found from figure 10.36 at lamba_c/4 = {params.wing.Lambda_025c_w} and A = {params.wing.A_w_target}")
    C_L = params.performance.CL_cruise
    paramater2 = ClpCdlCl2 * C_L**2 - 0.125*params.wing.C_D0
    Clpw = BClp_K_CL_0*(kappa_w/beta) * (ClaCL / ClaCl_0) * paramater1 + paramater2
    
    # for h:
    # -----------
    deltaB = np.arctan(np.tan(params.empennage.Lambda_t_025c/beta))
    BA_K = beta/kappa_t * params.empennage.A_t_h
    A = params.empennage.A_t_h
    BClp_K_CL_0 = input(f"roll damping parameter at zero lift which is obtained from figure 10.35 pag. 418/450 using sweep_b = {deltaB} and BA/K = {BA_K} and lamba = {0}")
    ClaCL = params.empennage.Cl_alpha #  input("the wing lift-curve slope at any lift coefficient. It is obtained as the local slope of the wing CL versus alpha curve as obtained from 8.1.3.5 or from 8.1.4.4")
    ClaCl_0 = 2*np.pi*A / (2+(((A**2)*(beta**2)*(kappa_t**2))*(1+(np.tan(params.wing.Lambda_025c_w)/beta)**2)+4)**0.5) #  input("the wing lift-curve slope at zero lift as obtained from eq (8.22)")
    #gamma = params.wing.Gamma_w
    #zw = input("vertical distance of wing from fuselage c.g. (smaller than 0 for high wing)")
    paramater1 = 1 # gamma = 0 
    
    ClpCdlCl2 = input(f"The drag-due-to-lift roll damping parameter as found from figure 10.36 at lamba_c/4 = {params.empennage.Lambda_t_025c} and A = {params.empennage.A_t_h}")
    C_Lh = params.empennage.CL_h
    paramater2 = ClpCdlCl2 * C_Lh**2 - 0.125*params.empennage.cd0
    Clp_h = BClp_K_CL_0*(kappa_t/beta) * (ClaCL / ClaCl_0) * paramater1 + paramater2
    # ----------
    
    b_h = params.empennage.b_v
    Clph = 0.5*Clp_h * (params.empennage.S_h/params.wing.S_w)*(b_h/params.wing.b_w)**2
    Clpv = 2/(params.wing.b_w**2)*abs((zv*math.cos(alpha)-lv*math.sin(alpha))*(zv*math.cos(alpha)-lv*math.sin(alpha)-zv))*CyBv
    
    Clp = Clpw + Clph + Clpv
    
    Clp_gamma_0_cl_0 = (kappa_w/beta)*((beta*Clp)/kappa_w) # at C_L = 0
    Cyp = 2*CyBv(zv*math.cos(alpha)-lv*math.sin(alpha)-zv)/params.wing.b_w + 3*math.sin(params.wing.Gamma_w) * (1- (4*z/params.wing.b_w)*math.sin(params.wing.Gamma_w))*Clp_gamma_0_cl_0
    
    
    qcsweep = params.wing.Lambda_025c_w
    B = (1-M**2*math.cos(qcsweep)**2)**0.5
    A = params.wing.A_w_target
    CnpClCl_0_M_0 = -1/6 * ((A+6*(math.cos(qcsweep))*(0.25 * (math.tan(qcsweep)/A)+(math.tan(qcsweep))**2/12))/(A+4*math.cos(qcsweep))) # x/c was assumed to be quarter chord = 0.25
    CnpClCl_0 = (A+4*math.cos(qcsweep)/(A*B+4*math.cos(qcsweep))) * ((A*B + 0.5*(A*B+math.cos(qcsweep))*(math.tan(qcsweep)**2))/(A + 0.5*(A+math.cos(qcsweep))*(math.tan(qcsweep)**2))) * CnpClCl_0_M_0
    
    # #Cnpet = input("wing twist contribution as given by Figures 10.37 (pag. 420/452)") # twist = 0
    # bf = input("span of the flaps [m]")
    # deltaCnpadfdf = input(f"contribution due to symmetrical flap deflection as found from Figure 10.38 (pag. 423/455) with A = {params.wing.A_w_target}, bf/b = {bf/params.wing.b_w}")
    # deltacl = input(f"deltacl determined from 8.1.2.1 for the type of flap used ")
    # cla = input("cla is the airfoil (flaps-up) lift-curve-slope as found from 8.1.1.2")

    # adf = deltacl/(cla)
    Cnpw = CnpClCl_0 * C_L # + (deltaCnpadfdf)*adf
    
    Cnpv = -(2/params.wing.b_w**2)*(lv*math.cos(alpha)+zv*math.sin(alpha))*(zv*math.cos(alpha)-lv*math.sin(alpha)-zv)*CyBv
    
    Cnp = Cnpw + Cnpv
    
    return Cyp, Clp, Cnp, zv, lv

def yaw_moment_due_to_yaw_rate_CNR(params: DesignParameters, CyBv, zv, lv):
    c = params.wing.mac
    x_lemac = params.cg.x_ac_w - c/4
    x = ((params.VSP.x_cg_vsp - x_lemac)/c - (params.cg.x_ac_w-x_lemac)/c)
    CnrCL2 = input(f"Figure 10.44 pag. 433/465 with A={params.wing.A_w_target}, Lamba_c/4={params.wing.Lambda_025c_w}, x/c = {x/c}")
    CLw = params.performance.CL_cruise
    CnrCdo = input(f"found from Figure 10.45 pag. 434/466 with A={params.wing.A_w_target}, Lamba_c/4={params.wing.Lambda_025c_w}, x/c = {x/c}")
    Cd0 = params.wing.C_D0
    Cnrw = CnrCL2 *CLw**2 + CnrCdo * Cd0
    
    alpha = params.cruise_aoa /180 * math.pi
    Cnrv = (2/(params.wing.S_w**2))*((lv*math.cos(alpha)+zv*math.sin(alpha))**2)*CyBv
    
    Cnr = Cnrw + Cnrv
    return Cnr

# def speed_derivatives(params: DesignParameters):
#     C_L_u = (params.cruise_mach**2*(math.cos(params.wing.Lambda_025c_w))**2 * params.performance.CL_cruise)/(1-params.cruise_mach**2*(math.cos(params.wing.Lambda_025c_w))**2)
#     C_m_u = None

if __name__ == '__main__':
    AERIS = DesignParameters()
    AERIS.load_from_yaml("design_config.yaml")
    struct_main(AERIS, show_3d=False)
    C_Y_beta, C_l_beta, C_n_beta, C_Y_beta_v = angle_of_sideslip_beta(AERIS)
    C_Y_r, C_l_r = yaw_rate_r(AERIS, C_Y_beta_v)
    Cyp, Clp, Cnp, zv, lv = roll_rate_derivates(AERIS, C_Y_beta_v)  # CyBv needs to be calculated first
    Cnr = yaw_moment_due_to_yaw_rate_CNR(AERIS, C_Y_beta_v, zv, lv)  # CyBv, zv, lv need to be calculated first
    # pitch_rate_q(AERIS)  # This function is not fully implemented yet
    # speed_derivatives(AERIS)  # This function is not fully implemented yet()
    print(f"C_Y_beta: {C_Y_beta}, C_l_beta: {C_l_beta}, C_n_beta: {C_n_beta}, C_Y_beta_v: {C_Y_beta_v}")
    print(f"Cyp: {Cyp}, Clp: {Clp}, Cnp: {Cnp}, zv: {zv}, lv: {lv}")
    print(f"Cnr: {Cnr}, C_Y_r: {C_Y_r}, C_l_r: {C_l_r}")


