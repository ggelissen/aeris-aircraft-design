# Filename : exampl82.m

# Calculation of the PSD functions for the controlled and uncontrolled
# aircraft. Also, numerical integration of the PSD is performed in order 
# to determine the variances of phi for both cases. In this code figures
# 8.18 and 8.19 are generated.

# Chapter 8 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2a import cit2a_fun

plt.close('all')

print('   Example 8.2                                                    ')
print('                                                                  ')
print('   Calculation of the power spectral density of the roll angle    ')
print('   due to asymmetric vertical turbulence.                         ')
print('                                                                  ')
print('   The effect of an autopilot which keeps the roll-angle constant ')
print('   is also investigated.                                          ')
print('                                                                  ')
print('   This program produces Figures 8-18 and 8-19 of the lecture     ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.           ')
print('                                                                  ')

# GET SYSTEM DYNAMICS
# NOTE: A  represents the UNCONTROLLED SYSTEM
#       A2 represents the CONTROLLED SYSTEM with gain as in lecture notes
A, A1, A2, B, sigmaug_V, sigmabg, sigmaag, Lg, V, b = cit2a_fun()

# FREQUENCY VECTOR
omega = numpy.logspace(-2,2,200);

# DEFINE C AND D MATRICES
C = numpy.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0]).reshape(1, 10)
D = numpy.array([0, 0, 0, 0, 0]).reshape(1, 5)

# CALCULATION OF THE POWER SPECTRAL DENSITY FUNCTION OF PHI DUE TO
# VERTICAL TURBULENCE

# Uncontrolled aircraft
sys = cm.ss(A, B[:, 3], C, D[:, 3])
mag = cm.bode(sys,omega, Plot = False)[0]
Sphi = mag*mag

# Controlled aircraft
syst = cm.ss(A2, B[:, 3], C, D[:, 3])
mag = cm.bode(syst,omega, Plot = False)[0]
Sphit = mag*mag

plt.figure()
plt.loglog(omega,Sphi, linestyle = '-', label = r'$S_{u_{\phi\phi}}$') 
plt.loglog(omega,Sphit,linestyle = '--', label = r'$S_{c_{\phi\phi}}$')
plt.xlabel('omega [rad/s]'); plt.ylabel('Sphi [rad2]')
plt.legend()

# CALCULATION OF THE COVARIANCE MATRIX
dt   = 0.05; T = 300; t = numpy.arange(0, T + dt, dt)
N = len(t)

Wdis = 1/dt   # discrete-time intensity of white noise

# Calculation of discrete time system matrices for the 
# uncontrolled and controlled aircraft
sysd = cm.c2d(sys,dt)   
Phi = sysd.A; Gamma = sysd.B

sysdt = cm.c2d(syst,dt)   
Phit = sysdt.A; Gammat = sysdt.B

# Initial covariance matrices
Cxx  = numpy.zeros((10,10))
Cxxt = numpy.zeros((10,10))
Cx2x2 = numpy.zeros((N,1))
Cx2x2t = numpy.zeros((N,1))

# Store only variance of phi
for k in range(1, N):
   Cxx       = Phi*Cxx*Phi.T + Gamma*Wdis*Gamma.T
   Cxxt      = Phit*Cxxt*Phit.T + Gammat*Wdis*Gammat.T
   Cx2x2[k]  = Cxx[1,1]
   Cx2x2t[k] = Cxxt[1,1]
   
# PLOT RESULTS
plt.figure()
plt.subplot(2,1,1)
plt.plot(t,Cx2x2);  plt.xlabel('time [s]'); plt.ylabel('variance phi')
plt.title('Uncontrolled aircraft')

plt.subplot(2,1,2)
plt.plot(t,Cx2x2t); plt.xlabel('time [s]'); plt.ylabel('variance phi')
plt.title('Controlled aircraft')

plt.subplots_adjust(hspace=0.4)
plt.show()

# CHECK: CALCULATION OF THE VARIANCE BY NUMERICALLY INTEGRATING THE 
#        POWER SPECTRAL DENSITY FUNCTION OF THE ROLL ANGLE PHI.
dw      = numpy.diff(omega)
varphi  = sum(Sphi[0:len(dw)].T*dw)/pi
print('                                                                  ')
print(' Variance of phi for the uncontrolled aircraft: ', varphi)

varphit  = sum(Sphit[0:len(dw)].T*dw)/pi
print(' Variance of phi for the controlled aircraft: ', varphit)

