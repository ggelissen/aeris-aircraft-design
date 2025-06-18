# Exampl43.m

# Chapter 4 of lecture notes ae4-304

# Digital calculation of covariance function and
# auto power spectral density.

# Program revised 1995, February 2004 [MM], October 2014 [M Rodriguez],
# June 2021 [MM] - - Python version by B. Englebert (August 2021)

from math import*
import numpy
import MatlabFuncs
from matplotlib import pyplot as plt

plt.close('all')

print('   Example 4.3')
print('   Digital calculation of covariance function and')
print('   auto power spectral density of a stochastic signal x(t).')
print('   ')
print('   This program can produce Figures 4-14 to 4-19 of the lecture')
print('   notes: Aircraft Responses to Atmospheric Turbulence.')
print('   ')

fs    = float(input('   Enter sample frequency f (Hz)   : '))
T     = float(input('   Enter time T_end    (s)         : '))

dt=1/fs; N=T*fs; t= numpy.arange(dt, T+dt, dt)

x     = float(input('   Enter function definition x(t)= : '))
ni   = float(input('   Enter noise intensity           : '))


# generate DT white noise sequence
x  = x + sqrt(ni)*numpy.random.randn(1,int(N))
x = numpy.ndarray.flatten(x)

# compute the auto covariance function
Cxx = MatlabFuncs.xcov(x,'biased')
  
# compute the Fast Fourier Transform
X = numpy.fft.fft(x)

# calculate the DT power spectral density estimate
Sxx= (X*numpy.conj(X)/N).real  

# define the frequency axis
f=  (fs/N)*numpy.arange(0,N/2,1)

fg = numpy.zeros(int(N/2))
Sx = numpy.zeros(int(N/2))

# properly assign positive and negative frequencies
for i in range(1,int(N/2)):
    fg[i-1]     =  -f[int(N/2)-i]
    Sx[i-1]     = Sxx[int(N/2)-i] 

f = numpy.hstack((fg, f))
Sxx = numpy.hstack((Sx, Sxx[0:int(N/2)]))

# reference for white noise PSD
Refw= ni*numpy.ones(int(N/2))

# PLOTTING THE RESULTS
plt.figure()
plt.subplot(2,1,1)
plt.plot(t, x)
plt.xlabel('time [s]')
plt.ylabel('x (t)')
plt.title('SIGNAL')

plt.subplot(2,1,2)
plt.plot(t-T/2, Cxx[int(2*N/4)+1:int(6*N/4)+1])
plt.xlabel('tau [s]')
plt.ylabel('Cxx (tau)')
plt.title('Auto Covariance Function')

plt.subplots_adjust(hspace=0.7)

plt.figure()
plt.subplot(2,1,1)
plt.plot(f, Sxx)
plt.xlabel('frequency [Hz]')
plt.ylabel('Sxx')
plt.title('Auto Power Spectral Density (linear scales)')

plt.subplot(2,1,2)
plt.loglog(f[int(N/2):int(N-1)], Sxx[int(N/2):int(N-1)])
plt.loglog(f[int(N/2):int(N-1)+1], Refw, linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Sxx')
plt.title('Auto Power Spectral Density (loglog Scales)')

plt.subplots_adjust(hspace=0.7)
plt.show()
