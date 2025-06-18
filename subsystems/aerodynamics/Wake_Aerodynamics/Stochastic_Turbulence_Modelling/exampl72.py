# Filename : exampl72.m

# Calculation of covariance matrix of the (non-dimensional)
# motion variables.

# Steady-state (co)variances are calculated by solving the
# Lyapunov-equation AC+CA'+BWB'=0 or by integrating the power
# spectral density.

# Transient behaviour may be calculated with either the recursive
# relation C(k+1)=PHI C(k) PHI'+ GAMMA Wdis GAMMA' or using the
# impulse response method.

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2s import cit2s_fun


plt.close('all')


print('   Example 7.2')
print('   ')
print('   Calculation of covariance matrix of the (non-dimensional)')
print('   motion variables. Steady-state (co)variances are calculated')
print('   by solving the Lyapunov-equation AC+CA` +BWB` =0 or by')
print('   integrating the power spectral density. Transient behaviour')
print('   may be calculated with either the recursive relation')
print('   C(k+1)=PHI C(k) PHI` + GAMMA Wdis GAMMA`  or using the')
print('   impulse response method.')
print('   ')
print('   This program produces Figures 7-7 to 7-11 in the lecture')
print('   notes: Aircraft Responses to Atmospheric Turbulence.')

# COMPUTE A/C DYNAMICS
A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun()
    
# GET float(input PARAMETERS
Wc = float(input('   Give noise intensity                     (  1.0 ) : '))
dt = float(input('   Give sampling time interval dt           (  0.01) : '))
T  = float(input('   Give total time interval T_end           (150.0 ) : '))
Nf = int(input('   Give number of points in frequency axis  ( 200  ) : '))

# DEFINE NOISE INTENSITY
W  = Wc/dt    # discrete time covariance, remember?

# DEFINE TIME AXIS
t  = numpy.arange(0, T+dt, dt)
N = len(t)

#######################################################################
# COMPUTE THE STEADY-STATE SOLUTION
#######################################################################

#######################################################################
# Method 1. SOLVING THE LYAPUNOV-EQUATION
#######################################################################
print('                                                              ')
print('Method 1. SOLVING THE LYAPUNOV-EQUATION                       ')

Bin = B[:,2]
L   = cm.lyap(A,Bin*Wc*Bin.T)
# take only the part that belongs to the 4 states
L   = L[0:4,0:4]

print('                                                  ')
print('                                                  ')
print('   printlay solution Lyapunov equation             ')
print(L)
print('   Note: the diagonal elements are the variances: ')
print(numpy.diag(L).T)
    
#######################################################################
# Method 2. INTEGRATING THE ANALYTICAL POWER SPECTRAL DENSITIES
#######################################################################
print('                                                              ')
print('Method 2. INTEGRATING THE ANALYTICAL POWER SPECTRAL DENSITIES ')

# The motion variables u/V, alpha, theta and qc/V are the first four
# elements of the seventh order state vector.

# Input vector u=[0 0 w3]^T.
D = numpy.zeros((4,3))
C = numpy.hstack((numpy.eye(4), numpy.zeros((4, 3))))
iu = 2 # index of the input to be used

# DEFINE SISO SYSTEMS 
sys_uu = cm.ss(A, B[:,iu], C[0,:], D[0,iu])
sys_aa = cm.ss(A, B[:,iu], C[1,:], D[1,iu])
sys_tt = cm.ss(A, B[:,iu], C[2,:], D[2,iu])
sys_qq = cm.ss(A, B[:,iu], C[3,:], D[3,iu])


# DEFINE FREQUENCY AXIS
omega = numpy.logspace(-2,2,Nf)   
    
# COMPUTE FREQUENCY RESPONSES
mag_uu = cm.bode(sys_uu, omega, Plot = False)[0]
mag_aa = cm.bode(sys_aa, omega, Plot = False)[0]  
mag_tt = cm.bode(sys_tt, omega, Plot = False)[0]  
mag_qq = cm.bode(sys_qq, omega, Plot = False)[0]    

# COMPUTE POWER SPECTRA OF u/V, ALPHA, THETA AND qc/V
Suu = mag_uu**2
Saa = mag_aa**2
Stt = mag_tt**2
Sqq = mag_qq**2

# PLOT POWER SPECTRA
plt.figure()
plt.subplot(2,2,1) 
plt.loglog(omega,Suu); plt.xlabel('omega [rad/sec]'); plt.ylabel('Suu [rad^2/Hz]')
plt.subplot(2,2,2)
plt.loglog(omega,Saa); plt.xlabel('omega [rad/sec]'); plt.ylabel('Saa [rad^2/Hz]')
plt.subplot(2,2,3) 
plt.loglog(omega,Stt); plt.xlabel('omega [rad/sec]'); plt.ylabel('Stt [rad^2/Hz]')
plt.subplot(2,2,4) 
plt.loglog(omega,Sqq); plt.xlabel('omega [rad/sec]'); plt.ylabel('Sqq [rad^2/Hz]')

plt.subplots_adjust(wspace=0.4)
plt.show()

# NUMERICAL INTEGRATION OF PSD's
do = numpy.diff(omega).T   # compute "difference vector" in omega
                     # i.e., omega(k+1)-omega(k);
# then perform (very crude) integration
var = numpy.zeros(4)

var[0] = sum(do*Suu[0:Nf-1])
var[1] = sum(do*Saa[0:Nf-1])
var[2] = sum(do*Stt[0:Nf-1])
var[3] = sum(do*Sqq[0:Nf-1])

print('   Numerical integration of PSD yields the variances: ')
var = var/pi
print(var )
print('   Note that when we have more frequency points the   ')
print('   integration will become more accurate and the      ')
print('   variances will approximate the Lyapunov solution.  ')

hh = numpy.ones(N)
var1 = var[0]*hh; var2 = var[1]*hh; var3 = var[2]*hh; var4 = var[3]*hh

#######################################################################
# CALCULATION OF GROWTH IN TIME OF COVARIANCE MATRIX
#######################################################################
print('                                              ')
print('CALCULATION OF GROWTH IN TIME OF COVARIANCE MATRIX')
#######################################################################
# Method 1. BY RECURSIVE CALCULATION 
#
#    Cxx(k+1) = PHI Cxx(k) PHI' + GAMMA Wdis GAMMA'
#######################################################################

# Discretize the system matrices
sys = cm.ss(A, B[:, iu], C, D[:, iu].reshape((4, 1)))
sysd = cm.c2d(sys,dt)
Phi = sysd.A; Gamma = sysd.B

# Initial conditions
Cxx = numpy.zeros((7,7))    

# Discrete Solution of response equation
print('                                                           ')
print('      Method 1. Computing response by recursive calculation')
print('                                                           ')
hh=2

Cx1x1 = numpy.zeros(N)
Cx1x2 = numpy.zeros(N)
Cx1x3 = numpy.zeros(N)
Cx1x4 = numpy.zeros(N)

Cx2x2 = numpy.zeros(N)
Cx2x3 = numpy.zeros(N)
Cx2x4 = numpy.zeros(N)

Cx3x3 = numpy.zeros(N)
Cx3x4 = numpy.zeros(N)

Cx4x4 = numpy.zeros(N)

for k in range(1, N):
    Cxx = Phi*Cxx*Phi.T + Gamma*W*Gamma.T
    
    Cx1x1[k] = Cxx[0,0]; Cx1x2[k] = Cxx[0,1]; Cx1x3[k] = Cxx[0,2]; Cx1x4[k] = Cxx[0,3]
    Cx2x2[k] = Cxx[1,1]; Cx2x3[k] = Cxx[1,2]; Cx2x4[k] = Cxx[1,3]
    Cx3x3[k] = Cxx[2,2]; Cx3x4[k] = Cxx[2,3]
    Cx4x4[k] = Cxx[3,3]
    
    if hh > 100:
        hh=1 
        print('step' , k+1)
        
    hh=hh+1; 
print('ready')

I = numpy.ones(N)

Css11 = L[0,0]*I
Css12 = L[0,1]*I
Css13 = L[0,2]*I
Css14 = L[0,3]*I

Css22 = L[1,1]*I
Css23 = L[1,2]*I
Css24 = L[1,3]*I

Css33 = L[2,2]*I
Css34 = L[2,3]*I

Css44 = L[3,3]*I

#######################################################################
# Method 2. USING THE IMPULSE RESPONSE METHOD
#######################################################################
print('                                                 ')
print('      Method 2. Using the impulse response method')
print('                                                 ')
# ZERO INPUT, INITIAL CONDITION EQUALS B (for input 3 in this case)

u = numpy.zeros((N,3)); x0 = B[:,2]
sys = cm.ss(A, B, C, D)
# CALCULATION OF IMPULSE RESPONSES
h = cm.lsim(sys,u,t,x0)[0]

# PLOT IMPULSE RESPONSE
plt.figure()
plt.subplot(2,1,1)
plt.plot(t,h[:,0]); plt.xlabel('Time [sec]'); plt.ylabel('h u w3(t)')
plt.subplot(2,1,2)
plt.plot(t,h[:,1]); plt.xlabel('Time [sec]'); plt.ylabel('h alpha w3(t)')


plt.figure()
plt.subplot(2,1,1)
plt.plot(t,h[:,2]); plt.xlabel('Time [sec]'); plt.ylabel('h theta w3(t)')
plt.subplot(2,1,2)
plt.plot(t,h[:,3]); plt.xlabel('Time [sec]'); plt.ylabel('h qc/V w3(t)')

plt.subplots_adjust(hspace=0.4)
plt.show()

# CALCULATION OF PRODUCT MATRIX OF IMPULSE RESPONSES
h11 = h[:,0]*h[:,0]
h12 = h[:,0]*h[:,1]
h13 = h[:,0]*h[:,2]
h14 = h[:,0]*h[:,3]

h22 = h[:,1]*h[:,1]
h23 = h[:,1]*h[:,2]
h24 = h[:,1]*h[:,3]

h33 = h[:,2]*h[:,2]
h34 = h[:,2]*h[:,3]

h44 = h[:,3]*h[:,3]

# PLOT (CROSS) PRODUCTS OF IMPULSE RESPONSES
print('                                           ')
print(' PLOT (CROSS) PRODUCTS OF IMPULSE RESPONSES')
print('                                           ')

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,h11); plt.xlabel('Time [sec]'); plt.ylabel('h1*h1(t)')
plt.subplot(2,2,2)
plt.plot(t,h12); plt.xlabel('Time [sec]'); plt.ylabel('h1*h2(t)')
plt.subplot(2,2,4)
plt.plot(t,h22); plt.xlabel('Time [sec]'); plt.ylabel('h2*h2(t)')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,h13); plt.xlabel('Time [sec]'); plt.ylabel('h1*h3(t)')
plt.subplot(2,2,2)
plt.plot(t,h14); plt.xlabel('Time [sec]'); plt.ylabel('h1*h4(t)')
plt.subplot(2,2,3)
plt.plot(t,h23); plt.xlabel('Time [sec]'); plt.ylabel('h2*h3(t)')
plt.subplot(2,2,4)
plt.plot(t,h24); plt.xlabel('Time [sec]'); plt.ylabel('h2*h4(t)')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,h33); plt.xlabel('Time [sec]'); plt.ylabel('h3*h3(t)')
plt.subplot(2,2,2)
plt.plot(t,h34); plt.xlabel('Time [sec]'); plt.ylabel('h3*h4(t)')
plt.subplot(2,2,4)
plt.plot(t,h44); plt.xlabel('Time [sec]'); plt.ylabel('h4*h4(t)')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

# INTEGRATION OF PRODUCT MATRIX OF IMPULSE RESPONSES
var11 = numpy.zeros(N)
var12 = numpy.zeros(N)
var13 = numpy.zeros(N)
var14 = numpy.zeros(N)

var22 = numpy.zeros(N)
var23 = numpy.zeros(N)
var24 = numpy.zeros(N)

var33 = numpy.zeros(N)
var34 = numpy.zeros(N)

var44 = numpy.zeros(N)

dth11 = dt*h11
dth12 = dt*h12
dth13 = dt*h13
dth14 = dt*h14

dth22 = dt*h22
dth23 = dt*h23
dth24 = dt*h24

dth33 = dt*h33
dth34 = dt*h34

dth44 = dt*h44

for i in range(0, N-1):
    var11[i+1] = var11[i]+dth11[i]
    var12[i+1] = var12[i]+dth12[i]
    var13[i+1] = var13[i]+dth13[i]
    var14[i+1] = var14[i]+dth14[i]
    
    var22[i+1] = var22[i]+dth22[i]
    var23[i+1] = var23[i]+dth23[i]
    var24[i+1] = var24[i]+dth24[i]
    
    var33[i+1] = var33[i]+dth33[i]
    var34[i+1] = var34[i]+dth34[i]
    
    var44[i+1] = var44[i]+dth44[i]
    
# PLOT VARIANCES FROM IMPULSE RESPONSE METHOD
print(' PLOT VARIANCES FROM IMPULSE RESPONSE METHOD ')
print('                                             ')

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Css11,linestyle = '--'); plt.plot(t,var11); plt.xlabel('time [s]'); plt.ylabel('Cx1x1')
plt.subplot(2,2,2)
plt.plot(t,Css12,linestyle = '--'); plt.plot(t,var12); plt.xlabel('time [s]'); plt.ylabel('Cx1x2')
plt.subplot(2,2,4)
plt.plot(t,Css22,linestyle = '--'); plt.plot(t,var22); plt.xlabel('time [s]'); plt.ylabel('Cx2x2')


plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Css13,linestyle = '--'); plt.plot(t,var13); plt.xlabel('time [s]'); plt.ylabel('Cx1x3')
plt.subplot(2,2,2)
plt.plot(t,Css14,linestyle = '--'); plt.plot(t,var14); plt.xlabel('time [s]'); plt.ylabel('Cx1x4')
plt.subplot(2,2,3)
plt.plot(t,Css23,linestyle = '--'); plt.plot(t,var23); plt.xlabel('time [s]'); plt.ylabel('Cx2x3')
plt.subplot(2,2,4)
plt.plot(t,Css24,linestyle = '--'); plt.plot(t,var24); plt.xlabel('time [s]'); plt.ylabel('Cx2x4')


plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Css33,linestyle = '--'); plt.plot(t,var33); plt.xlabel('time [s]'); plt.ylabel('Cx3x3')
plt.subplot(2,2,2)
plt.plot(t,Css34,linestyle = '--'); plt.plot(t,var34); plt.xlabel('time [s]'); plt.ylabel('Cx3x4')
plt.subplot(2,2,4)
plt.plot(t,Css44,linestyle = '--'); plt.plot(t,var44); plt.xlabel('time [s]'); plt.ylabel('Cx4x4')


# PLOT RESULTS FROM RECURSIVE EQUATION WITH STEADY-STATE DASHED
print(' PLOT RESULTS FROM RECURSIVE EQUATION WITH STEADY-STATE DASHED')
print('                                                              ')

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Cx1x1); plt.plot(t,Css11,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx1x1')
plt.subplot(2,2,2)
plt.plot(t,Cx1x2); plt.plot(t,Css12,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx1x2')
plt.subplot(2,2,4)
plt.plot(t,Cx2x2); plt.plot(t,Css22,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx2x2')


plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Cx1x3); plt.plot(t,Css13,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx1x3')
plt.subplot(2,2,2)
plt.plot(t,Cx1x4); plt.plot(t,Css14,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx1x4')
plt.subplot(2,2,3)
plt.plot(t,Cx2x3); plt.plot(t,Css23,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx2x3')
plt.subplot(2,2,4)
plt.plot(t,Cx2x4); plt.plot(t,Css24,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx2x4')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

plt.figure()
plt.subplot(2,2,1)
plt.plot(t,Cx3x3); plt.plot(t,Css33,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx3x3')
plt.subplot(2,2,2)
plt.plot(t,Cx3x4); plt.plot(t,Css34,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx3x4')
plt.subplot(2,2,4)
plt.plot(t,Cx4x4); plt.plot(t,Css44,linestyle = '--'); plt.xlabel('time [s]'); plt.ylabel('Cx4x4')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()