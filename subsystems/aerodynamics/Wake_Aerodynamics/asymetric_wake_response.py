# Filename: cit2a_updated.py

# Calculation of state matrix and input matrix for calculation
# of asymmetric aircraft response to atmospheric turbulence.
# The system model is in the form:

#          .
#          x = Ax + Bu
# with x = [beta phi pb/2V rb/2V ug_ u_g* alpha_g alpha_g* beta_g betag*]^T

# The turbulence filters are derived using the approximated
# effective one-dimensional power spectral densities for u_g, alpha_g and
# beta_g.

# Data for cruise flight condition at FL400
# Minimal changes from Cessna Citation Ce-500 template

from math import*
import numpy
import pickle
#from design_variables import DesignParameters
# AIRCRAFT- AND FLIGHT CONDITION 'CRUISE FL400'.
V   = 240.0
S   = 9.44
b   = 10.65
mub = 79.6
KX2 = 0.012
KZ2 = 0.037
KXZ = 0.002

CL  = 0.281
I_xx = 1212.66      # kg*m²
I_yy = 8466.62      # kg*m²  
I_zz = 9219.268     # kg*m²
I_xz = 382.99       # kg*m²
mass = 3000         # kg

KX2 = I_xx / (mass * b * b)    # = 0.003564
KZ2 = I_zz / (mass * b * b)    # = 0.027094
KXZ = I_xz / (mass * b * b)    # = 0.001126
# TURBULENCE PARAMETERS APPROXIMATED POWER SPECTRAL DENSITIES
Lg        = 1   # Turbulence length scale [m]
B         = b/(2*Lg)
sigma     = 5     # Turbulence intensity [m/s]
sigmaug_V = sigma/V
sigmavg   = sigma
sigmabg   = sigmavg/V
sigmaag   = sigma/V

Iug0 = 0.0249*sigmaug_V**2
Iag0 = 0.0182*sigmaag**2

tau1 = 0.0991;      tau2 = 0.5545;      tau3 = 0.4159
tau4 = 0.0600;      tau5 = 0.3294;      tau6 = 0.2243

# AIRCRAFT ASYMMETRIC AERODYNAMIC DERIVATIVES 
CYb  =-1.0204;      Clb  =-0.07097;      Cnb  = 0.0140#Reduced Dihedral, Clb =-0.2497 to Clb =-0.1597, Cnb = 0.0140 is corrected
CYp  =-0.0131;      Clp  =-0.2561;      Cnp  =-0.148 # Cnp =-0.5163 to Cnp =-0.0508, more realistic
CYr  = 0.6475;      Clr  = 0.2868;      Cnr  =-0.3867
CYda = 0.0000;      Clda =-0.2349;      Cnda = 0.0286
CYdr = 0.3037;      Cldr = 0.0286;      Cndr =-0.1261

# Wing contribution corrections
Clpw = 0.8*Clp;    Cnpw = 0.9*Cnp
Clrw = 0.7*Clr;    Cnrw = 0.2*Cnr

CYfb = 0
Clfb = 0
Cnfb = 0

# CALCULATION OF AIRCRAFT ASYMMETRIC STABILITY DERIVATIVES
yb   = (V/b)*CYb/(2*mub)
yphi = (V/b)*CL/(2*mub) 
yp   = (V/b)*CYp/(2*mub) 
yr   = (V/b)*(CYr-4*mub)/(2*mub) 
ybg  = yb 
ydr  = (V/b)*CYdr/(2*mub) 
den  = b*4*mub*(KX2*KZ2-KXZ**2)/V 
lb   = (Clb*KZ2+Cnb*KXZ)/den 
lp   = (Clp*KZ2+Cnp*KXZ)/den 
lr   = (Clr*KZ2+Cnr*KXZ)/den 
lda  = (Clda*KZ2+Cnda*KXZ)/den 
ldr  = (Cldr*KZ2+Cndr*KXZ)/den 
lug  = (-Clrw*KZ2-Cnrw*KXZ)/den 
lbg  = lb 
lag  = (Clpw*KZ2+Cnpw*KXZ)/den 
nb   = (Clb*KXZ+Cnb*KX2)/den 
np   = (Clp*KXZ+Cnp*KX2)/den 
nr   = (Clr*KXZ+Cnr*KX2)/den 
nda  = (Clda*KXZ+Cnda*KX2)/den 
ndr  = (Cldr*KXZ+Cndr*KX2)/den 
nug  = (-Clrw*KXZ-Cnrw*KX2)/den 
nbg  = nb 
nag  = (Clpw*KXZ+Cnpw*KX2)/den 
aug1 =-(V/Lg)**2*(1/(tau1*tau2)) 
aug2 =-(tau1+tau2)*(V/Lg)/(tau1*tau2) 
aag1 =-(V/Lg)**2*(1/(tau4*tau5)) 
aag2 =-(tau4+tau5)*(V/Lg)/(tau4*tau5) 
abg1 =-(V/Lg)**2 
abg2 =-2*(V/Lg) 
bug1 = tau3*sqrt(Iug0*V/Lg)/(tau1*tau2) 
bug2 = (1-tau3*(tau1+tau2)/(tau1*tau2))*sqrt(Iug0*(V/Lg)**3)/(tau1*tau2) 
bag1 = tau6*sqrt(Iag0*V/Lg)/(tau4*tau5) 
bag2 = (1-tau6*(tau4+tau5)/(tau4*tau5))*sqrt(Iag0*(V/Lg)**3)/(tau4*tau5) 
bbg1 = sigmabg*sqrt(3*V/Lg) 
bbg2 = (1-2*sqrt(3))*sigmabg*sqrt((V/Lg)**3) 

# STATE MATRIX A
A = numpy.asmatrix([[yb, yphi, yp,    yr, 0,    0,    0,    0,    ybg,  0],
               [0,  0,    2*V/b, 0,  0,    0,    0,    0,    0,    0], 
               [lb, 0,    lp,    lr, lug,  0,    lag,  0,    lbg,  0],
               [nb, 0,    np,    nr, nug,  0,    nag,  0,    nbg,  0],
               [0,  0,    0,     0,  0,    1,    0,    0,    0,    0],
               [0,  0,    0,     0,  aug1, aug2, 0,    0,    0,    0],
               [0,  0,    0,     0,  0,    0,    0,    1,    0,    0],
               [0,  0,    0,     0,  0,    0,    aag1, aag2, 0,    0],
               [0,  0,    0,     0,  0,    0,    0,    0,    0,    1],
               [0,  0,    0,     0,  0,    0,    0,    0,    abg1, abg2]])

# INPUT MATRIX B
B = numpy.asmatrix([[0,   ydr, 0,    0,    0],
               [0,   0,   0,    0,    0],
               [lda, ldr, 0,    0,    0],
               [nda, ndr, 0,    0,    0],
               [0,   0,   bug1, 0,    0],
               [0,   0,   bug2, 0,    0],
               [0,   0,   0,    bag1, 0],
               [0,   0,   0,    bag2, 0],
               [0,   0,   0,    0,    bbg1],
               [0,   0,   0,    0,    bbg2]])


# SHOW EIGENVALUES OF THE UNCONTROLLED SYSTEM
print("Eigenvalues of uncontrolled system:")
print(numpy.linalg.eig(A)[0])


# check for yourself that the spiral mode is not stable, the
# corresponding pole lies in the right-half plane (s = 0.0764).

# THE CESSNA CITATION CE-500 IS NOT STABLE IN SPIRAL MODE (FOR THE cit2a.py 
# FLIGHT CONDITION), HENCE THE FEEDBACK CONTROLLER TO THE AILERON FOR PHI IS 
# USED AS IN : 

#   delta_a = K_phi*phi     :  (K_phi for THIS flight condition)

# THEREFORE, CONTROLLED AIRCRAFT SYSTEM MATRICES WILL BE USED FOR RESULTS;

#       A = At 

# NO ALTERATIONS MADE FOR cit1a.py !

# NOTE: SPIRAL MODE IS JUST STABLE WITH K_phi ENTERED BELOW
Kphi = -0.025
K    = numpy.array([0, Kphi, 0, 0, 0, 0, 0, 0, 0, 0])
A1   = A-B[:,0]*K
# SHOW EIGENVALUES OF THIS CONTROLLED SYSTEM
#print(numpy.linalg.eig(A1)[0])

# FOR EFFECT OF K_phi ON AIRCRAFT RESPONSES, ONE OTHER K_phi IS USED
Kphi = -0.1
K    = numpy.array([0, Kphi, 0, 0, 0, 0, 0, 0, 0, 0])
A2   = A-B[:,0]*K
# % SHOW EIGENVALUES OF THIS CONTROLLED SYSTEM
print(numpy.linalg.eig(A2)[0])

# Save variables to file
save_vars = {"A": A, "A1": A1, "A2": A2, "B": B,
            "sigmaug_V": sigmaug_V, "sigmabg": sigmabg,
            "sigmaag": sigmaag, "Lg": Lg, "V": V, "b": b}

file = open("dumpfile.txt", 'wb')
pickle.dump(save_vars, file)
file.close()
    
# Load variables from file
with open('dumpfile.txt', 'rb') as f:
    dict_vars = pickle.load(f)
    for key in dict_vars.keys():
        globals()[key] = dict_vars[key]

# Define the asymmetric aircraft dynamics function
def cit2a_fun():
    V   = 240.0
    S   = 9.44
    b   = 10.65
    mub = 79.6
    KX2 = 0.012
    KZ2 = 0.037
    KXZ = 0.002
    CL  = 0.281

    I_xx = 1212.66     # Moment of inertia about x-axis (kg*m^2)
    I_yy = 8466.62     # Moment of inertia about y-axis (kg*m^2)
    I_zz = 9219.268     # Moment of inertia about z-axis (kg*m^2)
    I_xz = 382.99     # Product of inertia xz-plane (kg*m^2)
    CL  = 0.281

    I_xx = 1212.66      # kg*m²
    I_yy = 8466.62      # kg*m²  
    I_zz = 9219.268     # kg*m²
    I_xz = 382.99       # kg*m²
    mass = 3000         # kg

    KX2 = I_xx / (mass * b * b)    # = 0.003564
    KZ2 = I_zz / (mass * b * b)    # = 0.027094
    KXZ = I_xz / (mass * b * b)    # = 0.001126
    Lg        = 150
    B         = b/(2*Lg)
    sigma     = 1
    sigmaug_V = sigma/V
    sigmavg   = sigma
    sigmabg   = sigmavg/V
    sigmaag   = sigma/V

    Iug0 = 0.0249*sigmaug_V**2
    Iag0 = 0.0182*sigmaag**2

    tau1 = 0.0991;      tau2 = 0.5545;      tau3 = 0.4159
    tau4 = 0.0600;      tau5 = 0.3294;      tau6 = 0.2243

    CYb  =-1.0204;      Clb  =-0.1597;      Cnb  = 0.140#Reduced Dihedral, Clb =-0.2497 to Clb =-0.1597
    CYp  =-0.0131;      Clp  =-0.2561;      Cnp  =-0.05163 # Cnp =-0.5163 to Cnp =-0.0508, more realistic
    CYr  = 0.6475;      Clr  = 0.2868;      Cnr  =-0.3867
    CYda = 0.0000;      Clda =-0.2349;      Cnda = 0.0286
    CYdr = 0.3037;      Cldr = 0.0286;      Cndr =-0.1261
    
    Clpw = 0.8*Clp;    Cnpw = 0.9*Cnp
    Clrw = 0.7*Clr;    Cnrw = 0.2*Cnr

    CYfb = 0
    Clfb = 0
    Cnfb = 0

        
    Clpw = 0.8*Clp;    Cnpw = 0.9*Cnp
    Clrw = 0.7*Clr;    Cnrw = 0.2*Cnr

    CYfb = 0
    Clfb = 0
    Cnfb = 0

    yb   = (V/b)*CYb/(2*mub)
    yphi = (V/b)*CL/(2*mub) 
    yp   = (V/b)*CYp/(2*mub) 
    yr   = (V/b)*(CYr-4*mub)/(2*mub) 
    ybg  = yb 
    ydr  = (V/b)*CYdr/(2*mub) 
    den  = b*4*mub*(KX2*KZ2-KXZ**2)/V 
    lb   = (Clb*KZ2+Cnb*KXZ)/den 
    lp   = (Clp*KZ2+Cnp*KXZ)/den 
    lr   = (Clr*KZ2+Cnr*KXZ)/den 
    lda  = (Clda*KZ2+Cnda*KXZ)/den 
    ldr  = (Cldr*KZ2+Cndr*KXZ)/den 
    lug  = (-Clrw*KZ2-Cnrw*KXZ)/den 
    lbg  = lb 
    lag  = (Clpw*KZ2+Cnpw*KXZ)/den 
    nb   = (Clb*KXZ+Cnb*KX2)/den 
    np   = (Clp*KXZ+Cnp*KX2)/den 
    nr   = (Clr*KXZ+Cnr*KX2)/den 
    nda  = (Clda*KXZ+Cnda*KX2)/den 
    ndr  = (Cldr*KXZ+Cndr*KX2)/den 
    nug  = (-Clrw*KXZ-Cnrw*KX2)/den 
    nbg  = nb 
    nag  = (Clpw*KXZ+Cnpw*KX2)/den 
    aug1 =-(V/Lg)**2*(1/(tau1*tau2)) 
    aug2 =-(tau1+tau2)*(V/Lg)/(tau1*tau2) 
    aag1 =-(V/Lg)**2*(1/(tau4*tau5)) 
    aag2 =-(tau4+tau5)*(V/Lg)/(tau4*tau5) 
    abg1 =-(V/Lg)**2 
    abg2 =-2*(V/Lg) 
    bug1 = tau3*sqrt(Iug0*V/Lg)/(tau1*tau2) 
    bug2 = (1-tau3*(tau1+tau2)/(tau1*tau2))*sqrt(Iug0*(V/Lg)**3)/(tau1*tau2) 
    bag1 = tau6*sqrt(Iag0*V/Lg)/(tau4*tau5) 
    bag2 = (1-tau6*(tau4+tau5)/(tau4*tau5))*sqrt(Iag0*(V/Lg)**3)/(tau4*tau5) 
    bbg1 = sigmabg*sqrt(3*V/Lg) 
    bbg2 = (1-2*sqrt(3))*sigmabg*sqrt((V/Lg)**3) 

    A = numpy.asmatrix([[yb, yphi, yp,    yr, 0,    0,    0,    0,    ybg,  0],
                [0,  0,    2*V/b, 0,  0,    0,    0,    0,    0,    0], 
                [lb, 0,    lp,    lr, lug,  0,    lag,  0,    lbg,  0],
                [nb, 0,    np,    nr, nug,  0,    nag,  0,    nbg,  0],
                [0,  0,    0,     0,  0,    1,    0,    0,    0,    0],
                [0,  0,    0,     0,  aug1, aug2, 0,    0,    0,    0],
                [0,  0,    0,     0,  0,    0,    0,    1,    0,    0],
                [0,  0,    0,     0,  0,    0,    aag1, aag2, 0,    0],
                [0,  0,    0,     0,  0,    0,    0,    0,    0,    1],
                [0,  0,    0,     0,  0,    0,    0,    0,    abg1, abg2]])

    B = numpy.asmatrix([[0,   ydr, 0,    0,    0],
                [0,   0,   0,    0,    0],
                [lda, ldr, 0,    0,    0],
                [nda, ndr, 0,    0,    0],
                [0,   0,   bug1, 0,    0],
                [0,   0,   bug2, 0,    0],
                [0,   0,   0,    bag1, 0],
                [0,   0,   0,    bag2, 0],
                [0,   0,   0,    0,    bbg1],
                [0,   0,   0,    0,    bbg2]])

    Kphi = -0.025
    K    = numpy.array([0, Kphi, 0, 0, 0, 0, 0, 0, 0, 0])
    A1   = A-B[:,0]*K

    Kphi = -0.1
    K    = numpy.array([0, Kphi, 0, 0, 0, 0, 0, 0, 0, 0])
    A2   = A-B[:,0]*K

    return A, A1, A2, B, sigmaug_V, sigmabg, sigmaag, Lg, V, b