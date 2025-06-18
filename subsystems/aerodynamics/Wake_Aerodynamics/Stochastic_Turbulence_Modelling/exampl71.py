# Filename : examp71.m

# Simulation of aircraft symmetric response to atmospheric turbulence.

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [mm]
# - Python version by B. Englebert (August 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2s import cit2s_fun


plt.close('all')

print('   Example 7.1                                            ')
print('                                                          ')
print('   Simulation of symmetric gust response of the           ')
print('   Cessna Ce-500 "Citation" at an airspeed of 59.9 [m/s], ')
print('   CRUISE condition.                                      ')
print('                                                          ')
print('   This program produces Figure 7-6 of the lecture notes: ')
print('   Aircraft Responses to Amospheric Turbulence.           ')


# COMPUTE A/C DYNAMICS
A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun()

# TIME AXIS INPUT VECTOR DEFINITION
dt = float(input('   Give sampling time interval dt             (0.01) : '))
T  = 60
t = numpy.arange(0, T + dt, dt)
N = len(t)

# INPUT VECTOR DEFINITION
nn = numpy.zeros((N, 1))                    # zero input elevator
w1 = numpy.random.randn(N, 1)/sqrt(dt)      # scaled input hor. turbulence,
                                            # note the sqrt(dt) because of lsim
w3 = numpy.random.randn(N, 1)/sqrt(dt)      # scaled input vert. turbulence,
                                            # note the sqrt(dt) because of lsim
u  = numpy.hstack((nn, nn, w3))             # input vector definition (vertical
                                            # turbulence only, can be changed).

# SIMULATION OF MOTION VARIABLES
C = numpy.eye(7); D = numpy.zeros((7, 3))
sys = cm.ss(A, B, C, D)

y = cm.lsim(sys, u, t)[0]

# PLOTTING RESULTS
plt.figure()

plt.subplot(4, 1, 1)
plt.plot(t,y[:,0])
plt.xlabel('time [s]') 
plt.ylabel('u/V [-]')
plt.title('airspeed deviation')

plt.subplot(4, 1, 2)
plt.plot(t,y[:,1]*180/pi)
plt.xlabel('time [s]')
plt.ylabel('alpha [deg]')
plt.title('angle of attack')

plt.subplot(4, 1, 3)
plt.plot(t,y[:,2]*180/pi)
plt.xlabel('time [s]')
plt.ylabel('theta [deg]')
plt.title('pitch angle')

plt.subplot(4, 1, 4)
plt.plot(t,y[:,3]*180/pi)
plt.xlabel('time [s]')
plt.ylabel('qc/V [deg]')
plt.title('pitch rate')

plt.subplots_adjust(hspace=1.7)
plt.show()