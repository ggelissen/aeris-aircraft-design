# Filename : exampl73.m

# Calculates the power spectral density of the normal acceleration.

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2s import cit2s_fun


plt.close('all')


print('   Example 7.3                                                  ')
print('                                                                ')
print('   Calculation of the power spectral density of the normal      ')
print('   acceleration due to longitudinal and vertical turbulence.    ')
print('   Also, the effect of a lagfree autopilot will be investigated.')
print('                                                                ')
print('   This program produces Figures 7-12 and 7-13 of the lecture   ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.         ')

# GET A/C DYNAMICS
A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun()
    
    
# DEFINE FREQUENCY AXES
N = 1000 
omega = numpy.logspace(-3,3,N)                 # frequency axis

# MISCELLANEOUS
D = numpy.zeros((1, 3))
g = 9.80665                              # gravitational acc [N/kg]

# HORIZONTAL TURBULENCE
iu = 1 # index of the input to be used

# CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
Cn = A[2, :] - A[1, :] 
Dn = B[2, iu] - B[1, iu]
Hn = cm.ss(A, B[:,iu], V/g*Cn, Dn)
# COMPUTE FREQUENCY RESPONSE FUNCTION
mag = cm.bode(Hn,omega, Plot = False)[0]

Snn = mag*mag

# VERTICAL TURBULENCE
iu = 2 # index of the input to be used

# CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
Cn = A[2, :] - A[1, :] 
Dn = B[2, iu] - B[1, iu]
Hn = cm.ss(A, B[:,iu], V/g*Cn, Dn)

# COMPUTE FREQUENCY RESPONSE FUNCTION
mag = cm.bode(Hn,omega, Plot = False)[0]
Snn1 = mag*mag

# VERTICAL TURBULENCE AIRCRAFT WITH PITCH ATTITUDE HOLD SYSTEM
iu = 2 # index of the input to be used

# CALCULATION OF THE LOAD FACTOR: n = V/g*(theta_dot-alpha_dot)
Cn = At[2, :] - At[1, :] 
Dn = B[2, iu] - B[1, iu]
Hn = cm.ss(At, B[:,iu], V/g*Cn, Dn)


# COMPUTE FREQUENCY RESPONSE FUNCTION
mag = cm.bode(Hn,omega, Plot = False)[0]
Snnt1 = mag*mag

# PLOT POWER SPECTRAL DENSITIES
plt.figure()
plt.loglog(omega,Snnt1,linestyle = '--', label = 'Pitch attitude hold')
plt.loglog(omega,Snn1, label = 'Elevator fixed')
plt.xlabel('omega [rad/s]'); plt.ylabel('Snn')
plt.legend()
plt.title('Power Spectral Density of Normal Acceleration')

plt.figure()
plt.loglog(omega,Snn,linestyle = '--', label = 'Horizontal turbulence')
plt.loglog(omega,Snn1, label = 'Vertical turbulence')
plt.xlabel('omega [rad/s]'); plt.ylabel('Snn')
plt.legend()
plt.title('Power Spectral Density of Normal Acceleration')

plt.show()

# CALCULATION OF VARIANCES USING VERY CRUDE INTEGRATION
print('                                                     ')
print('  CALCULATION OF THE VARIANCES OF n AND az:          ')
print('                                                     ')

dw = numpy.diff(omega)
dw = numpy.hstack((dw, numpy.array([0])))  # make vector length equal to N again

print(' ');
print(' Variance of n due to horizontal turbulence')
varn    = sum(Snn.T*dw)/pi;
print(varn)

print(' Variance of az due to horizontal turbulence')
varaz   = (sum(Snn.T*dw)*g**2)/pi          # Remember: var_z = E[(n*g)^2-mu_z]
print(varaz)

print(' Variance of n due to vertical turbulence')
varn1   = sum(Snn1.T*dw)/pi
print(varn1)

print(' Variance of az due to vertical turbulence')
varaz1  = sum(Snn1.T*dw)*g**2/pi
print(varaz1)

print(' Variance of n due to vertical turbulence for aircraft')
print(' with pitch attitude hold system')
varnt1  = sum(Snnt1.T*dw)/pi
print(varnt1)

print(' Variance of az due to vertical turbulence for aircraft')
print(' with pitch attitude hold system')
varazt1 = sum(Snnt1.T*dw)*g**2/pi;
print(varazt1)