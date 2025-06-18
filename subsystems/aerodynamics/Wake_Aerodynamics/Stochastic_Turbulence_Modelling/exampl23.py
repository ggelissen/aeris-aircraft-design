# Exampl23     Calculate and plot the 2-dimensional Normal (Gaussian)
#              probability density function.

# Chapter 2 of the lecture notes ae4-304.

# Program revised August 1992, February 2004 [MM], October 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d

plt.close('all')

print('   Example 2.3')
print(' ')
print('   Calculate and plot the 2-dimensional Normal (Gaussian)')
print('   probability density function.')
print('   ')
print('   This program can produce Figures 2-17, 2-18 and 2-19 of')
print('   the lecture notes ae4-304.')

x = numpy.arange(-3,3+0.1,0.1); y = x


# Definition of distribution parameters
mx  = float(input('   Average value of stochastic variable x           : '))
sx  = float(input('   Standard deviation of x                          : '))
my  = float(input('   Average value of stochastic variable y           : '))
sy  = float(input('   Standard deviation of y                          : '))
Kxy = float(input('   Correlation coefficient between x and y, 0<Kxy<1 : '))

if abs(Kxy) > 0.99 or abs(Kxy) < 0:
   raise ValueError('  Correlation coefficient should be between 0 and 1')
   
   
fmax=1/(2*pi*sx*sy*sqrt(1-Kxy**2))
fxy = numpy.zeros((len(y), len(x)))

for i in range(len(x)):
    for j in range(len(y)):
        G=((x[i]-mx)**2/sx**2-2*Kxy*(x[i]-mx)*(y[j]-my)/(sx*sy)+(y[j]-my)**2/sy**2)
        G=G/(1-Kxy**2)
        fxy[j,i]=fmax*numpy.exp(-G/2)
        

# Plot p.d.f. surface 
x_m,y_m = numpy.meshgrid(x,y)

ax = plt.axes(projection='3d') # Note that surface can be dragged in plot window!
ax.plot_surface(x_m, y_m, fxy,
                cmap='viridis', edgecolor='none')
ax.set_title('The 2-dimensional Normal p.d.f.')
plt.show()