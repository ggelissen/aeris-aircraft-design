# Exampl33.m

# Chapter 3

# Calculates power spectral densities of printlacement and
# acceleration as a result of runway surface irregularities.
# The landing gear is modelled as a second order 1-DOF
# mass-spring-damper system, the input power spectral
# density is taken from AGARD-R-632.
# The output power spectral density is calculated with

#          Syy(w) = |H(w)|^2 * Suu(w)

# while the power spectral density of the acceleration is found with

#          Saa(w) = w^4 Syy(w)

# Revised August 1992, February 2004 [MM], October 2014 [M Rodriguez],
#         June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt

plt.close('all')
s = cm.tf([1, 0], [1])

print('   Example 3.3')
print('   Calculates power spectral densities of displacement and')
print('   acceleration as a result of runway surface irregularities.')
print('   The landing gear is modelled as a second order 1-DOF')
print('   mass-spring-damper system, the input power spectral')
print('   density is taken from AGARD-R-632.')
print('   The output power spectral density is calculated with')
print('   ')
print('            Syy(w) = |H(w)|^2 * Suu(w)')
print('   ')
print('   while the power spectral density of the acceleration is')
print('   found with:')
print('   ')
print('            Saa(w) = w^4 Syy(w)')
print('   ')
print('   This program produces Figure 3.14 of the lecture notes:')
print('   Aircraft Responses to Atmospheric Turbulence.')

omega = numpy.logspace(-2,2,100)

# INPUT POWER SPECTRAL DENSITY OF 'RUNWAY RUMBLE'

# Ground speed. Can be changed.
V = float(input('   Enter ground speed V [m/s]  : '))

tau1=0.4/V; tau2=7/V

Suu = numpy.zeros(100)

for i in range(len(Suu)):
    Suu[i]=((6.3e-4)/V)/((1+(tau1*omega[i])**2)*(1+(tau2*omega[i])**2))
    
# LANDING GEAR DATA. TAKEN FROM DHC-2 'Beaver'
#
# aircraft mass. Can be changed.
m = float(input('   Enter aircraft mass m [kg]  : '))

c=20000	# damping constant. Can be changed.
k=183000	# spring constant. Can be changed.

# CALCULATION OF FREQUENCY RESPONSE USING TRANSFER FUNCTION H(s)
num=[c, k]; den=[m, c, k]
H = cm.tf(num,den); h = cm.frd(H, omega).fresp
h = numpy.ndarray.flatten(h)

# CALCULATION OF CROSS- AND AUTO POWER SPECTRAL DENSITIES
Suy = h*Suu
Syy = abs(h)**2*Suu
Saa = omega**4*Syy

# Plotting Results
plt.subplot(2,2,1)
plt.loglog(omega, Suy.real)
plt.xlabel("frequency, rad/s")
plt.ylabel("Re (Suy)")
plt.grid()
plt.title('Cross P.S.D.')

plt.subplot(2,2,2)
plt.semilogx(omega, Suy.imag)
plt.xlabel("frequency, rad/s")
plt.ylabel("Im (Suy)")
plt.grid()

plt.subplot(2,2,3)
plt.loglog(omega, Syy)
plt.xlabel("frequency, rad/s")
plt.ylabel('Syy, m^2/Hz')
plt.grid()
plt.title('Auto P.S.D. input')

plt.subplot(2,2,4)
plt.loglog(omega, Saa)
plt.xlabel("frequency, rad/s")
plt.ylabel('Saa, m^2/Hz')
plt.grid()
plt.title('Auto P.S.D. input')

plt.subplots_adjust(hspace=0.7, wspace=0.4)
plt.show()

