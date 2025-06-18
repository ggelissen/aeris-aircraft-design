# Exampl22   Calculates the signal, the auto product function, the
#            auto-covariance function and the auto correlation function
#            of an arbitrary signal.

# Chapter 2 of the lecture notes ae4-304.

# Program revised August 1992, February 2004 [MM], October 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (July 2021)

from math import*
import numpy
from matplotlib import pyplot as plt
import MatlabFuncs

plt.close('all')

print('   Example 2.2                                          ')
print('                                                        ')
print('   Calculates signal, auto product-, -covariance- and   ')
print('   -correlation function of a stochastic signal x(t).   ')
print('                                                        ')
print('   This program can produce Figures 2.14 and 2.16 of the')
print('   lecture notes ae4-304.                               ')


# create time axis
T     = float(input('   Enter total time interval T       : '))
dt    = float(input('   Enter sampling time interval dt   : '))

t = numpy.arange(-T/2,T/2+dt,dt)
N = len(t)

# create signal
x     = float(input('   Enter function definition x(t) =  : '))
ni   = float(input('   Enter noise intensity             : '))

x = x + sqrt(ni)*numpy.random.randn(1,N)
x = numpy.ndarray.flatten(x)

print('                                    '      )
print('   Signal mean     = ', numpy.mean(x)      )
print('   Signal variance = ', numpy.cov(x)       )
print('   Signal std.dev. = ', sqrt(numpy.cov(x)) )

# compute variables of interest
r = MatlabFuncs.xcorr(x, mode = "unbiased") # auto product function
c = MatlabFuncs.xcov(x, mode = "unbiased") # auto covariance function
k =  [i/(numpy.std(x)**2) for i in c]  # auto correlation function

# plot results
plt.figure()
plt.subplot(2,1,1)
plt.plot(t+T/2, x)
plt.xlabel("time")
plt.ylabel("x(t)")
plt.title("Signal")

plt.subplot(2,1,2)
plt.plot(t, r[int((T/2)/dt):int(3*(T/2)/dt+1)])
plt.xlabel("tau")
plt.ylabel("Rxx(tau)")
plt.title("Auto product function")

plt.subplots_adjust(hspace=0.7)

plt.figure()
plt.subplot(2,1,1)
plt.plot(t, c[int((T/2)/dt):int(3*(T/2)/dt+1)])
plt.xlabel("tau")
plt.ylabel("Cxx(tau)")
plt.title("Auto covariance function")

plt.subplot(2,1,2)
plt.plot(t, k[int((T/2)/dt):int(3*(T/2)/dt+1)])
plt.xlabel("tau")
plt.ylabel("Kxx(tau)")
plt.title("Auto correlation function")

plt.subplots_adjust(hspace=0.7)
plt.show()