# Exampl53    Calculates covariance matrix as function of time for a
#             second order mass-spring-damper system perturbed by white
#             noise using the impulse response method.

# Chapter 5 of lecture notes ae4-304

# Program revised August 1992, February 2004 [MM], November 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt


plt.close('all')

print('   Example 5.3                                                ')
print('                                                              ')
print('   Calculation of the growth in time of the covariance        ')
print('   matrix of a second order mass-spring-damper system         ')
print('   perturbed by white noise using the impulse response method:')
print('                                                              ')
print('               _ t                                            ')
print('              |          T                                    ')
print('     C  (k) = | h(v).h(v)  dv                                 ')
print('      xx     _|                                               ')
print('            0                                                 ')
print('                                                              ')
print('   This program can produce Figure 5.9 of the lecture notes:  ')
print('   Aircraft Responses to Atmospheric Turbulence.              ')
print('                                                              ')
print('                                                              ')
print('   2nd Order Model Definition:                                ')
print('                                                              ')

# CT SYSTEM DYNAMICS
w0      = float(input('   Give undamped natural frequency [rad/s] : '))
zeta    = float(input('   Give damping ratio                      : '))

m = 1                          # mass
k = w0**2                       # spring constant
c = zeta*2*m*w0                # damping constan

A= numpy.asmatrix([[0, 1], [-k/m, -c/m]])  # state-space representation of second
B= numpy.asmatrix([[0], [1/m]])              # order system
C= numpy.asmatrix([[1, 0]])
D= numpy.asmatrix([[0]])
sys = cm.ss(A, B, C, D)

# DEFINE TIME AXIS
dt= 0.1; T = 15	                                # sample time 0.1 seconds
t = numpy.arange(0, T+dt, dt)	            # time axis
N = len(t)                              # number of samples

# COMPUTE CT SYSTEM IMPULSE RESPONSE
u = numpy.zeros(N)            # zero input
x0 = B                       # initial condition

h = cm.lsim(sys, u, t, x0)[0]

# SQUARE IMPULSE RESPONSE
hsq=h*h;                    # squared impulse response

# INTEGRATE THE SQUARED IMPULSE RESPONSE
# done rather crudely here

vary = numpy.zeros(N)
for i in range(0, N-1):
  vary[i+1] = vary[i] + hsq[i]*dt;	# integrated squared impulse response
  
  
# PLOT RESULTS
plt.figure()
plt.subplot(3,1,1)
plt.plot(t,h, linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('h (t)')
plt.title('Impulse Response')

plt.subplot(3,1,2)
plt.plot(t,hsq, linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('h^2 (t)')
plt.title('Squared Impulse Response')

plt.subplot(3,1,3)
plt.plot(t,vary, linestyle = '-')
plt.xlabel('time [s]')
plt.ylabel('Cx1x1 (t)')
plt.title('Variance')

plt.subplots_adjust(hspace=1)
plt.show()


