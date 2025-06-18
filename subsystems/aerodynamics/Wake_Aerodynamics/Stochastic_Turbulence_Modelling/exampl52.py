# Exampl52  Calculates covariance matrix as function of time for a
#           second order mass-spring-damper system perturbed by white 
#           noise, using the discrete-time recursive calculation method.

# Chapter 5 of lecture notes ae4-304

# Program revised August 1992, February 2004 [MM], November 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import scipy
import control.matlab as cm
from matplotlib import pyplot as plt
import MatlabFuncs

plt.close('all')

print('   Example 5.2                                                     ')
print('                                                                   ')  
print('   Calculation of the growth in time of the covariance             ')
print('   matrix of a second order mass-spring-damper system              ')
print('   perturbed by white noise. The covariance matrix C               ')
print('   is calculated in time with:                                     ')
print('                                                                   ')
print('                            T                               T      ')
print('   C  (k+1) = PHI(k) C  (k) PHI (k)   +   GAMMA(k) C  (k) GAMMA (k)')
print('    xx                xx                            ww             ')
print('                                                                   ')
print('   This program can produce Figures 5.4 to 5.8 of the lecture      ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.            ')
print('                                                                   ')
print('                                                                   ')
print('   2nd Order Model Definition:                                     ')
print('                                                                   ')

# CT SYSTEM DYNAMICS
w0      = float(input('   Give undamped natural frequency [rad/s]     : '))
zeta    = float(input('   Give damping ratio                          : '))

m = 1; k = w0**2
c = zeta*2*m*w0

A= numpy.mat([[0, 1], [-k/m, -c/m]])  # state-space representation of second
B= numpy.mat([[0], [1/m]])              # order system
C= numpy.mat([[1, 0]])
D= numpy.mat([[0]])
sys = cm.ss(A, B, C, D)

# DEFINE TIME AXIS
dt= 0.01	                                # sample time 0.1 seconds
t = numpy.arange(dt, 15+dt, dt)	            # time axis
N = int(15/dt)                              # number of samples

# DISCRETIZE SYSTEM MATRICES
sysd = cm.c2d(sys,dt)   # discretizing using MATLAB c2d command
Phi = sysd.A; Gamma = sysd.B

# DEFINE WHITE NOISE CHARACTERISTICS
Wc      = float(input('   Enter CT white noise intensity              : '))
answ    = input('   Stepwise change of noise intensity ? (y/n)  :')

W       = numpy.zeros(N)

if answ =='y':
  Q     = float(input('   Enter Q (0<Q<1)                             : '))
  answ1 = input('   Noise intensity W=0 after t=T(1-Q) (y/n)    :')
  answ2 = input('   Noise intensity W=2*Wc after t=T(1-Q) (y/n) :')
  M=Q*N
  
  W[0:int(N-M)+1]= Wc/dt             # always apply equation (5.45)
  
  for i in range(int(N-M), N):
      if answ1 == 'y':
          W[i]=0
      if answ2 == 'y':
          W[i]=2*Wc/dt
          
if answ == 'n':
    for i in range(0, N):
        W[i] = Wc/dt 
        
# DEFINE INITIAL CONDITIONS
Cx1x1 = numpy.zeros(N)
Cx1x2 = numpy.zeros(N)
Cx2x2 = numpy.zeros(N)

Cx1x1[0]= float(input('   Give initial value of Cyy(1,1)              : '))
Cx1x2[0]= float(input('   Give initial value of Cyy(1,2)=C(2,1)       : '))
Cx2x2[0]= float(input('   Give initial value of Cyy(2,2)              : '))
Cxx= numpy.mat([[Cx1x1[0], Cx1x2[0]], [Cx1x2[0], Cx2x2[0]]])

# DISCRETE SOLUTION Cxx(k+1)=Phi*Cxx(k)*Phi' + Gamma*W*Gamma';
for i in range(0, N-1):
  Cxx        = Phi*Cxx*Phi.T+Gamma*W[i]*Gamma.T
  Cx1x1[i+1] = Cxx[0,0] 
  Cx1x2[i+1] = Cxx[1,0] 
  Cx2x2[i+1] = Cxx[1,1]
  
ref = numpy.zeros(N)

# PLOT RESULTS
plt.figure()
plt.subplot(3,1,1)
plt.plot(t,Cx1x1, linestyle = '-')
plt.plot(t,ref,linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('Cx1x1 (t)')

plt.subplot(3,1,2)
plt.plot(t,Cx1x2, linestyle = '-')
plt.plot(t,ref,linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('Cx1x2 (t)')

plt.subplot(3,1,3)
plt.plot(t,Cx2x2, linestyle = '-')
plt.plot(t,ref,linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('Cx2x2 (t)')

plt.subplots_adjust(hspace=0.8)
plt.show()

