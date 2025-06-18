# Filename : exampl62.m

# Simulation of atmospheric turbulence using Dryden model

# Chapter 6 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (August 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt

plt.close('all')

print('   Example 6.2                                                ')
print('   Simulation of vertical gust velocity using Dryden model.   ')
print('                                                              ')
print('   This example produces Figure 6-19 of the lecture notes:    ')
print('   Aircraft Responses to Atmospheric Turbulence.              ')

sigma = float(input('   Enter turbulence intensity sigma [m/s]  (0.282) : '))
Lg1   = float(input('   Enter turbulence scale length Lg1 [m]   (  150) : '))
Lg2   = float(input('   Enter turbulence scale length Lg2 [m]   ( 1500) : '))
V     = float(input('   Enter airspeed V [m/s]                  (   35) : '))

# Define time basis
dt = 0.1; T = 120
t  = numpy.arange(0, T+dt, dt)
N = len(t)

# White noise input
w = numpy.random.randn(N)/sqrt(dt);  # note: divide by sqrt(dt), with dt the sample time
                                     # because of lsim characteristics

# Forming filter characteristics equation (6.41)
rat = V/Lg1

A = numpy.asmatrix([[0, 1], [-rat**2, -2*rat]])
B = sigma*numpy.asmatrix([[sqrt(3*rat)], [(1-2*sqrt(3))*sqrt((rat**3))]])
C = numpy.asmatrix([[1, 0]])
D = numpy.asmatrix([[0]])
sys = cm.ss(A, B, C, D)

# Output turbulence velocity
wg = cm.lsim(sys,w,t)[0]

# Forming filter characteristics equation (6.41)
rat = V/Lg2

A = numpy.asmatrix([[0, 1], [-rat**2, -2*rat]])
B = sigma*numpy.asmatrix([[sqrt(3*rat)], [(1-2*sqrt(3))*sqrt((rat**3))]])
C = numpy.asmatrix([[1, 0]])
D = numpy.asmatrix([[0]])
sys = cm.ss(A, B, C, D)

# Output turbulence velocity
wgg = cm.lsim(sys,w,t)[0]

# Plot the results
plt.figure()
plt.subplot(2,1,1)
plt.plot(t,w)
plt.xlabel('time [s]')
plt.ylabel('w')
plt.title('White Noise Filter Input')


plt.subplot(2,1,2)
plt.plot(t,wg, label = ' '.join(['Lg = ', str(Lg1) ,'m']))
plt.plot(t,wgg, linestyle = '--', label = ' '.join(['Lg = ', str(Lg2) ,'m']))
plt.xlabel('time [s]')
plt.ylabel('wg [m/s]')
plt.title('Vertical Gust Velocity')
plt.legend(loc = 'upper right')

plt.subplots_adjust(hspace=0.8)
plt.show()