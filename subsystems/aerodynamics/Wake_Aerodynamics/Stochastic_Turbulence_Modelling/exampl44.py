# Exampl44.m

# Chapter 4 of lecture notes ae4-304

# Calculates digitally the spectral densities of printlacement and
# acceleration as a result of runway surface irregularities.
# The results are compared with the analytical solutions
# as found in Example 3.3.

# Program revised August 1992, February 2004 [MM], October 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import scipy
import control.matlab as cm
from matplotlib import pyplot as plt

plt.close('all')
s = cm.tf([1, 0], [1])

print('   Example 4.4')
print('   Compares the digitally calculated spectral densities')
print('   of displacement and acceleration as a result of runway')
print('   surface irregularities with the analytical solutions')
print('   found in Example 3.3. The landing gear is modelled as a')
print('   second order 1-DOF mass-spring-damper system, the input')
print('   power spectral density is taken from AGARD-R-632.')
print('   The output power spectral density is calculated with:')
print('   ')
print('           Syy(w) = |H(w)|^2 * Suu(w)       (analytical)')
print('           Syy(w) = conj(Y[k]).Y[k]/N       (numerical)')
print('   ')
print('   while the power spectral density for the acceleration')
print('   is found with')
print('   ')
print('          Saa(w) = w^4 Syy(w)')
print('   ')
print('   This program can produce Figures 4-20 and 4-21 of the lecture')
print('   notes: Aircraft Responses to Atmospheric Turbulence.')

V  = float(input('   Enter ground speed V [m/s]          : '))
fs = float(input('   Enter sample frequency [Hz]         : '))
T  = float(input('   Enter time T_end    (s)             : '))
Wn = float(input('   Enter noise intensity               : '))
m  = float(input('   Enter aircraft mass [kg]            : '))

dt = 1/fs     # sample time
N  = int(T/dt)    # Number of samples
t = numpy.arange(0,T,dt) # time axis

tau1=0.4/V; tau2=7/V

# LANDING GEAR PARAMETERS
c = 20000       # damping constant
k = 183000      # spring constant

# DIGITAL CALCULATION OF INPUT SIGNAL
# the shaping filter ('rumble' filter definition)
num1= (6.3e-4)/V; den1 = [tau1*tau2, tau1+tau2, 1];
sys = cm.tf(num1,den1)

# create CT white noise
w = sqrt(Wn)*numpy.random.randn(1,N)

# filter it before you use it as an input to Matlab's lsim
[B,A]= scipy.signal.butter(3,0.99)
w = scipy.signal.lfilter(B,A,w)

# Note that lsim 'internally' works in DT, so we need to 'scale' 
# the CT white noise intensity with dt, or the signal with sqrt(1/dt) 
# this explained in detail in Chapter 5 of the lecture notes
w = numpy.ndarray.flatten(w/sqrt(dt))

# Then compute response of the rumble filter to "white noise",
# this yields the colored noise signal u
u = scipy.signal.lsim((sqrt(num1), den1),w,t, interp = False)[1] # interp = False performs zoh, get 2nd index for output

# DIGITAL CALCULATION OF OUTPUT SIGNAL
# the suspension system (with known transfer function H(s))
num=[c, k]; den=[m, c, k]
sys = cm.tf(num,den)

# compute response of the suspension system to the
# colored noise u
y = scipy.signal.lsim((num, den),u,t, interp = False)[1] # interp = False performs zoh, get 2nd index for output

# plot the results
plt.figure()
plt.subplot(3,1,1)
plt.plot(t, w)
plt.xlabel('time [sec]')
plt.ylabel('w(t)') 
plt.title('White Noise w(t)')

plt.subplot(3,1,2)
plt.plot(t, u)
plt.xlabel('time [sec]')
plt.ylabel('u(t)') 
plt.title('Surface irregularity u(t)')

plt.subplot(3,1,3)
plt.plot(t, y)
plt.xlabel('time [sec]')
plt.ylabel('y(t)') 
plt.title('Suspension system output y(t)')

plt.subplots_adjust(hspace=1.2)

# TRANSFORM ALL TO THE FREQUENCY DOMAIN
U = numpy.fft.fft(u,N)
W = numpy.fft.fft(w,N)
Y = numpy.fft.fft(y,N)

# ESTIMATE THE DT POWER SPECTRA (PERIODOGRAM)
Suucalc = (U*numpy.conj(U)/N).real
Swwcalc = (W*numpy.conj(W)/N).real
Syycalc = (Y*numpy.conj(Y)/N).real

Suycalc = numpy.conj(U[0:N])*Y[0:N]/N

# COMPUTE THE CT POWER SPECTRA
Suucalc = dt*Suucalc
Swwcalc = dt*Swwcalc
Syycalc = dt*Syycalc
Suycalc = dt*Suycalc

# define frequency axis
freqHz = (fs/N)*numpy.arange(1,N/2+1,1)
omega  = 2*pi*freqHz

Swwanal = numpy.zeros(len(freqHz))
Suuanal = numpy.zeros(len(freqHz))

# ANALYTICAL EXPRESSIONS FOR INPUT POWER SPECTRAL DENSITIES
for i in range(len(freqHz)):
    Swwanal[i] = Wn
    Suuanal[i] = num1/((1+tau1**2*omega[i]**2)*(1+tau2**2*omega[i]**2))*Swwanal[i]

    
#compute the accelerations
Saacalc = omega**4*Syycalc[0:int(N/2)]


# ANALYTICAL EXPRESSIONS FOR OUTPUT POWER SPECTRAL DENSITIES
h = cm.frd(sys, omega).fresp; h = numpy.ndarray.flatten(h)
maganal   = abs(h) 
phaseanal = 180*numpy.angle(h)/pi

Suyanal = h*numpy.ndarray.flatten(Suuanal)
Syyanal = maganal**2*Suuanal
Saaanal = omega**4*Syyanal

# ESTIMATION OF FREQUENCY RESPONSE FUNCTION FROM
# POWER SPECTRAL DENSITY RATIO
hcalc = Suycalc/Suucalc

magcalc   = abs(hcalc)  
phasecalc = 180*numpy.angle(hcalc)/pi

# PLOT THE RESULTS
plt.figure()
plt.subplot(2,2,1)
plt.loglog(freqHz,Swwanal)
plt.loglog(freqHz,Swwcalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Sww')
plt.title('PSD White Noise')

plt.subplot(2,2,2)
plt.loglog(freqHz,Suuanal)
plt.loglog(freqHz,Suucalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Suu')
plt.title('PSD Forming Filter Output')

plt.subplot(2,2,3)
plt.loglog(freqHz,abs(Suyanal.real))
plt.loglog(freqHz,abs(Suycalc[0:int(N/2)].real),linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Re (Suy)')
plt.title('Cross PSD w-u')

plt.subplot(2,2,4)
plt.semilogx(freqHz,Suyanal.imag)
plt.semilogx(freqHz,Suycalc[0:int(N/2)].imag,linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Im (Suy)')
plt.title('Cross PSD w-u')

plt.subplots_adjust(hspace=0.7, wspace=0.7)

plt.figure()
plt.subplot(2,2,1)
plt.loglog(freqHz,Syyanal)
plt.loglog(freqHz,Syycalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Syy')
plt.title('PSD Model Output')

plt.subplot(2,2,2)
plt.loglog(freqHz,Saaanal)
plt.loglog(freqHz,Saacalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('Saa')
plt.title('PSD Normal Acceleration')

plt.subplot(2,2,3)
plt.loglog(freqHz,maganal)
plt.loglog(freqHz,magcalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('gain (H)')
plt.title('Frequency Response Function')

plt.subplot(2,2,4)
plt.semilogx(freqHz,phaseanal)
plt.semilogx(freqHz,phasecalc[0:int(N/2)],linestyle = '--')
plt.xlabel('frequency [Hz]')
plt.ylabel('phase angle (H)')
plt.title('Frequency Response Function')

plt.subplots_adjust(hspace=0.7, wspace=0.7)
plt.show()
