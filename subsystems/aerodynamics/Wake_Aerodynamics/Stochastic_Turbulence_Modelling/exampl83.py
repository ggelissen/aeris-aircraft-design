# Filename : exampl83.m

# Computation of analytical PSDs and time-simulation of aircraft 
# asymmetric response to atmospheric turbulence.

# Chapter 8 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2a import cit2a_fun

plt.close('all')

print('   Example 8.3                                                    ')
print('                                                                  ')
print('   This example compares analytically obtained auto power         ')
print('   spectral densities with experimentally obtained                ')
print('   periodograms of the asymmetric motion variables.               ')
print('                                                                  ')
print('   This program produces Figures 8-20 and 8-21 of the lecture     ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.           ')
print('                                                                  ')

# GET SYSTEM DYNAMICS
A, A1, A2, B, sigmaug_V, sigmabg, sigmaag, Lg, V, b = cit2a_fun()

# NOTE (see also cit2a.py) 

# THE CESSNA CITATION CE-500 IS NOT STABLE IN SPIRAL MODE (FOR THE cit2a.py 
# FLIGHT CONDITION), HENCE THE FEEDBACK CONTROLLER FOR PHI IS USED AS IN : 

#   delta_a = K_phi*phi (K_phi for THIS flight condition)

# THEREFORE, CONTROLLED AIRCRAFT SYSTEM MATRICES WILL BE USED FOR RESULTS;

#      A = A2

# DEFINE OUTPUT MATRICES
C = numpy.mat([[1, 0, 0, 0, 0, 0, 0, 0, 0, 0],   # beta
     [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],    # phi
     [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],    # pb/2V
     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],    # rb/2V
     [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]])   # betag

D = numpy.zeros((5, 5))

# DEFINE FREQUENCY VECTOR
w = numpy.logspace(-2,2,300)

# COMPUTE ANALYTIC POWER SPECTRAL DENSITIES
# RESPONSE TO HORIZONTAL LATERAL TURBULENCE
iu = 4 # input index

sys = cm.ss(A2, B[:, iu], C[0,:], D[0, iu])
temp = cm.bode(sys, w, Plot = False)[0]
Sbeta  = temp*temp

sys = cm.ss(A2, B[:, iu], C[1,:], D[1, iu])
temp = cm.bode(sys, w, Plot = False)[0]
Sphi  = temp*temp

sys = cm.ss(A2, B[:, iu], C[2,:], D[2, iu])
temp = cm.bode(sys, w, Plot = False)[0]
Spp  = temp*temp

sys = cm.ss(A2, B[:, iu], C[3,:], D[3, iu])
temp = cm.bode(sys, w, Plot = False)[0]
Srr  = temp*temp

sys = cm.ss(A2, B[:, iu], C[4,:], D[4, iu])
temp = cm.bode(sys, w, Plot = False)[0]
Sbetag = temp*temp

Sxx = numpy.array([Sbeta, Sphi, Spp, Srr, Sbetag]).T

# COMPUTE PSDS USING TIME DOMAIN DATA

# SET TIME AXIS
dt = 0.01; T = 60; t = numpy.arange(0, T + dt, dt) 
N = len(t)

# In this case responses to lateral gust vg are calculated (fifth input):
# no asymmetric vertical and longitudinal turbulence: u_g = w_g = 0.
v_g = numpy.random.randn(1,N)/sqrt(dt)   # sqrt(dt) because of lsim

nn = numpy.zeros((1,N))
u = numpy.stack((nn, nn, nn, nn, v_g), axis = 1); u = u[0].T

# COMPUTE SYSTEM RESPONSE
sys = cm.ss(A2,B,C,D)
y     = cm.lsim(sys,u,t)[0]

beta  = y[:,0]
phi   = y[:,1]
pbtV  = y[:,2]
rbtV  = y[:,3]
betag = y[:,4]

# PLOT TIME RESPONSES
print('                                                                  ')
print('   Aircraft response to atmospheric turbulence                    ')

plt.figure()
plt.suptitle('Aircraft response to atmospheric turbulence')
plt.subplot(2,2,1); plt.plot(t,beta); plt.xlabel('time, s'); plt.ylabel('beta')
plt.subplot(2,2,2); plt.plot(t,phi);  plt.xlabel('time, s'); plt.ylabel('phi')
plt.subplot(2,2,3); plt.plot(t,pbtV); plt.xlabel('time, s'); plt.ylabel('pb/2V')
plt.subplot(2,2,4); plt.plot(t,rbtV); plt.xlabel('time, s'); plt.ylabel('rb/2V')


plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

plt.figure()
plt.title('Beta response to atmospheric turbulence')
plt.plot(t,betag); plt.xlabel('time, s'); plt.ylabel('betag')
plt.show()

# COMPUTE PERIODOGRAM AND ESTIMATE PSD
# PERIODOGRAM
BETA  = dt*numpy.fft.fft(beta)
PHI   = dt*numpy.fft.fft(phi)
P     = dt*numpy.fft.fft(pbtV)
R     = dt*numpy.fft.fft(rbtV)
BETAg = dt*numpy.fft.fft(betag)

# PSD ESTIMATE
Pbeta  = ((1/T)* BETA*numpy.conj(BETA)).real
Pphi   = ((1/T)* PHI*numpy.conj(PHI)).real
Pp     = ((1/T)* P*numpy.conj(P)).real
Pr     = ((1/T)* R*numpy.conj(R)).real
Pbetag = ((1/T)* BETAg*numpy.conj(BETAg)).real

# DEFINE FREQUENCY VECTOR
fs = 1/dt                                 # sample frequency
omega = 2*pi*fs*numpy.arange(0, int(N/2))/N

# PLOT ANALYTIC AND ESTIMATED PSDS IN ONE PLOT
print('                                                                  ')
print('   Plot analytic and estimated PSD functions                      ')

plt.figure()
plt.subplot(2,2,1);
plt.loglog(w,Sxx[:,0],linestyle = '--')
plt.loglog(omega,Pbeta[0:round(N/2)]) 
plt.xlabel('omega [rad/s]'); plt.ylabel('Sbeta')

plt.subplot(2,2,2);
plt.loglog(w,Sxx[:,1],linestyle = '--')
plt.loglog(omega,Pphi[0:round(N/2)]) 
plt.xlabel('omega [rad/s]'); plt.ylabel('Sphi')

plt.subplot(2,2,3);
plt.loglog(w,Sxx[:,2],linestyle = '--')
plt.loglog(omega,Pp[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Spp')

plt.subplot(2,2,4);
plt.loglog(w,Sxx[:,3],linestyle = '--')
plt.loglog(omega,Pr[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Srr')
plt.suptitle('Plot analytic and estimated PSD functions')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)

plt.figure()
plt.loglog(w,Sxx[:,4],linestyle = '--', label = 'Analytic PSD')
plt.loglog(omega, Pbetag[0:round(N/2)], label = 'Estimated PSD')
plt.xlabel('omega [rad/s]'); plt.ylabel('Sbetag [rad2]')
plt.legend()
plt.title(' PSD for beta')

plt.show()