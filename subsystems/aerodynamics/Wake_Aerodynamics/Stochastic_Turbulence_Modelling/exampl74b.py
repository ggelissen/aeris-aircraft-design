# Filename : exampl74b.m

# Calculation of the output spectral densities using the
# MATLAB FFT algorithm

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM}
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from exampl74a import exampl74a_fun


plt.close('all')

print('   Example 7.4                                                ')
print('                                                              ')
print('   This program calculates the periodograms of time-domain    ')
print('   data using the FFT algorithm. The experimentally    ')
print('   obtained PSD will be compared with the analytically derived')
print('   PSD of the motion variables.                               ')
print('                                                              ')
print('   This program produces Figures 7-14 to 7-17 of the lecture  ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.       ')
print('                                                              ')

# DEFINE MISCELLANEOUS
g  = 9.80665                       # gravitational acc [N/kg]

# RUN EXAMPL74A 
u, w, V, c, Sxx, A, B = exampl74a_fun()

# DEFINE TIME AXIS
dt = 0.05; fs = 1/dt
T  = 200;  t = numpy.arange(0, T + dt, dt); N = len(t)

# CREATE ZERO INPUT SIGNAL
delta = numpy.zeros(N)

# CREATE NORMAL WHITE NOISE SIGNALS 
#  if Vertical turbulence   (u=3) : w1 = 0
#  if Horizontal turbulence (u=2) : w3 = 0

if u == 1:
   w1 = numpy.random.randn(N)/sqrt(dt)   # sqrt(dt) because of lsim 
   w3 = numpy.zeros(N)
else:
   w1 = numpy.zeros(N)
   w3 = numpy.random.randn(N)/sqrt(dt)  # sqrt(dt) because of lsim 

inpsig  = numpy.array([delta, w1, w3]).T

# DEFINE C and D MATRICES
C = numpy.asmatrix([[1, 0, 0, 0, 0, 0, 0],   # u/V
     [0, 1, 0, 0, 0, 0, 0],    # alpha
     [0, 0, 1, 0, 0, 0, 0],    # theta
     [0, 0, 0, 1, 0, 0, 0],    # qc/V
     [0, 0, 0, 0, 1, 0, 0],    # u_g/V
     [0, 0, 0, 0, 0, 1, 0]])  # alpha_g

D = numpy.zeros((6,3))
sys = cm.ss(A, B, C, D)

# COMPUTE TIME RESPONSE
y  = cm.lsim(sys,inpsig,t)[0]

hatu   = y[:,0]
alpha  = y[:,1]
theta  = y[:,2]
qcV    = y[:,3]
hatug  = y[:,4]
alphag = y[:,5]

# Add a trailing zero for alpha array. Because we use the routine
# diff(w) which fills a vector of length(w)-1 with w(i+1)-w(i) for i=1 to
# length(w).

alphanz = alpha
alphanz = numpy.hstack((alphanz, numpy.array([0])))

# Calculation of the normal load factor nz according to: 
nz = (V/g)*( (V/c)*qcV-numpy.diff(alphanz)/dt )
nz[-1] = nz[-2]

# PLOT TIME RESPONSES
plt.figure()
plt.subplot(3,2,1)
plt.plot(t,hatu);  plt.xlabel('Time [s]'); plt.ylabel('u/V [-]')
plt.subplot(3,2,2)
plt.plot(t,alpha); plt.xlabel('Time [s]'); plt.ylabel('alpha [rad]')
plt.subplot(3,2,3)
plt.plot(t,theta); plt.xlabel('Time [s]'); plt.ylabel('theta [rad]')
plt.subplot(3,2,4)
plt.plot(t,qcV);   plt.xlabel('Time [s]'); plt.ylabel('qc/V [rad]')
plt.subplot(3,2,5)
plt.plot(t,nz);    plt.xlabel('Time [s]'); plt.ylabel('nz')
plt.subplot(3,2,6)
if u == 1:
    plt.plot(t,hatug); plt.xlabel('Time [s]'); plt.ylabel('ug/V [-]')
else:
    plt.plot(t,alphag); plt.xlabel('Time [s]'); plt.ylabel('alphag [rad]')
    
plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()

# FFT ALL SIGNALS
U      = dt*numpy.fft.fft(hatu)
ALPHA  = dt*numpy.fft.fft(alpha)
THETA  = dt*numpy.fft.fft(theta)
QCV    = dt*numpy.fft.fft(qcV)
NZ     = dt*numpy.fft.fft(nz)
Ug     = dt*numpy.fft.fft(hatug)
ALPHAg = dt*numpy.fft.fft(alphag)

((1/T)* U*numpy.conj(U)/N).real

# COMPUTE PSDs
Pu      = ((1/T)* U*numpy.conj(U)).real
Palpha  = ((1/T)* ALPHA*numpy.conj(ALPHA)).real
Ptheta  = ((1/T)* THETA*numpy.conj(THETA)).real
PqcV    = ((1/T)* QCV*numpy.conj(QCV)).real
Pnz     = ((1/T)* NZ*numpy.conj(NZ)).real
Pug     = ((1/T)* Ug*numpy.conj(Ug)).real
Palphag = ((1/T)* ALPHAg*numpy.conj(ALPHAg)).real

#DEFINE FREQUENCY VECTOR FOR PLOTTING
omega = 2*pi*fs*numpy.arange(0, int(N/2))/N

# PLOT PSDs
plt.figure()
plt.subplot(3,2,1) 
plt.loglog(w,Sxx[:,0], linestyle = '--'); plt.loglog(omega,Pu[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Suu [rad2/Hz]')

plt.subplot(3,2,2)
plt.loglog(w,Sxx[:,1], linestyle = '--'); plt.loglog(omega,Palpha[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Saa [rad2/Hz]')

plt.subplot(3,2,3)
plt.loglog(w,Sxx[:,2], linestyle = '--'); plt.loglog(omega,Ptheta[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Stt [rad2/Hz]')

plt.subplot(3,2,4)
plt.loglog(w,Sxx[:,3], linestyle = '--'); plt.loglog(omega,PqcV[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Sqq [rad2/Hz]')

plt.subplot(3,2,5)
plt.loglog(w,Sxx[:,4], linestyle = '--'); plt.loglog(omega,Pnz[0:round(N/2)])
plt.xlabel('omega [rad/s]'); plt.ylabel('Snznz [/Hz]')

if u == 1:
    plt.subplot(3,2,6)
    plt.loglog(w,Sxx[:,5], linestyle = '--'); plt.loglog(omega,Pug[0:round(N/2)])
    plt.xlabel('omega [rad/s]'); plt.ylabel('Sugug [rad2/Hz]')

else:
    plt.subplot(3,2,6)
    plt.loglog(w,Sxx[:,5], linestyle = '--'); plt.loglog(omega,Palphag[0:round(N/2)])
    plt.xlabel('omega [rad/s]'); plt.ylabel('Sagag [rad2/Hz]')

plt.subplots_adjust(hspace=0.4, wspace = 0.4)
plt.show()



