# Filename : exampl61.m

# Calculation of correlation coefficients of turbulence
# velocities according to Batchelor using Dryden correlation
# functions at two points A and B.

# Chapter 6 of lecture notes ae4-304

# Revised November 2014 [M Rodriguez], June 2021 [MM] 
# - Python version by B. Englebert (August 2021)

from math import*
import numpy
from matplotlib import pyplot as plt

plt.close('all')

print('   Example 6.1');
print('   Calculates the correlation coefficient between velocity    ')
print('   vectors at two points as a function of the longitudinal    ')
print('   scale length L according to Batchelor using Dryden         ')
print('   correlation functions f(.) and g(.).                       ')
print('                                                              ')
print('   This program produces Figure 6-17 of the lecture notes:    ')
print('   Aircraft Responses to Atmospheric Turbulence.              ')

x1 = float(input('   Give x-separation [m] between the two points (-40) : '))
x2 = float(input('   Give y-separation [m] between the two points ( 20) : '))
x3 = float(input('   Give z-separation [m] between the two points (-10) : '))

xi = numpy.array([x1, x2, x3])

print('   ')
print('   Velocity directions:')
print('   1 --- Longitudinal')
print('   2 --- Lateral')
print('   3 --- Normal')
print('   ')

uA = int(input('   Give velocity direction 1st point              (3) : '))
uB = int(input('   Give velocity direction 2nd point              (3) : '))

if uA < 1 or uA > 3 or uB < 1 or uB > 3:
    raise ValueError('Make a choice 1, 2 or 3')
    
# Turbulence velocity directions for calculation of correlation;
# 1: longitudinal
# 2: lateral
# 3: normal
    
if uA == uB:
   delta = 1 
else:
   delta = 0

Lg = numpy.logspace(1,4,50);		# running Lg from 10-10000m

# Specific functions f(xi) and g(xi) according to Dryden;
f = numpy.exp(-numpy.linalg.norm(xi)/Lg)
g = f*(1-numpy.linalg.norm(xi)/(2*Lg))

# Correlation according to Batchelor;
K = ((f-g)/numpy.linalg.norm(xi)**2)*xi[uA-1]*xi[uB-1]+delta*g

# PLOTTING RESULTS
plt.figure()
plt.semilogx(Lg,K)
plt.xlabel('scale length of turbulence Lg [m]')
plt.ylabel('correlation coefficient K')
plt.grid()
plt.show()

