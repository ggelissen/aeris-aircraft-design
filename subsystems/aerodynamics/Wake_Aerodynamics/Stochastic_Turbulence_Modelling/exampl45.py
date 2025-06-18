# Exampl45.m

# Chapter 4 of the lecture notes ae4-304

# Calculates digitally the spectral densities of printlacement
# and acceleration as a result of runway surface irregularities.
# The results are compared with the analytical solutions as
# found in Example 3.3.

# Program revised August 1992, February 2004 [MM], December 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import scipy
import control.matlab as cm
from matplotlib import pyplot as plt
import MatlabFuncs

plt.close('all')

print('   Example 4.5')
print('   Compares the digitally calculated spectral densities of'    )
print('   printlacement and acceleration as a result of runway surface')
print('   irregularities with the analytical solutions found in'      )
print('   Example 3.3. The landing gear is modelled as a second order')
print('   1-DOF mass-spring-damper system, the float(input power spectral'  )
print('   density is taken from AGARD-R-632.'                         )
print('                                                              ')
print('   The output power spectral density is calculated with:'      )
print('                                                              ')
print('          Syy(w) = |H(w)|^2 * Suu(w)       (analytical)'       )
print('                                                              ')
print('   and it is computed using either the pwelch.m routine, or   ')
print('   using periodograms and then smoothed with smooth.m.        ')
print('                                                              ')
print('   The program also obtains estimates for the cross PSD'       )
print('   between u and y, Suy, and the frequency response between   ')
print('   colored noise (u) and the suspension printlacement.         ')
print('                                                              ')
print('   The power spectral density of the acceleration'             )
print('   is found with'                                              )
print('   '                                                           )
print('          Saa(w) = w^4 Syy(w)'                                 )
print('   '                                                           )
print('   This program produces Figures 4.22 and 4.23 of the lecture' )
print('   notes: Aircraft Responses to Atmospheric Turbulence.'       )

V  = float(input('   Enter ground speed V [m/s]           : '))
fs = float(input('   Enter sample frequency [Hz]          : '))
T  = float(input('   Enter time T_end    (s)              : '))
Wn = float(input('   Enter noise intensity                : '))

# create time axis
dt = 1/fs   # sampling time
N  = int(T/dt)   # number of samples
t  = numpy.arange(0, T, dt) # time axis

# create frequency axis
fres = fs/N           # frequency resolution in Hz
f    = fres*numpy.arange(1, int(N/2)+1) # frequency axis, in Hz
omega= f*2*pi         # frequency axis, in rad/s

#######################################################################
# RUNWAY RUMBLE
#######################################################################
# DEFINE DYNAMICS
# shaping filter parameters
tau1 = 0.4/V; tau2 = 7/V
# system dynamics
num = sqrt((6.3e-4)/V)   # 'runway rumble' shaping filter dynamics
den = [tau1*tau2, tau1+tau2, 1]
sys = cm.tf(num,den)

# frequency response, in rad/s
hrr = cm.frd(sys, omega).fresp; hrr = numpy.ndarray.flatten(hrr)

# CALCULATE 'runway rumble' SYSTEM RESPONSE TO WHITE NOISE
# create white noise input, intensity Wn
# because lsim 'internally' works as a discrete-time simulation, 
# the white noise intensity needs to scaled first (Chapter 5)
w = sqrt(Wn/dt)*numpy.random.randn(N)

# calculate runway rumble response to white noise
u = scipy.signal.lsim((num, den),w,t)[1]

#######################################################################
# SUSPENSION SYSTEM
#######################################################################
# DEFINE DYNAMICS
# landing gear parameters
m =   2290            # aircraft mass m [kg]           
c =  20000            # damping constant
k = 183000            # spring constant
# system dynamics
num = [c, k]           # 'suspension system' dynamics
den = [m, c, k]         
sys = cm.tf(num,den)
# frequency response, in rad/s
hss = cm.frd(sys, omega).fresp; hss = numpy.ndarray.flatten(hss)
# CALCULATE 'suspension system' SYSTEM RESPONSE TO 'runway rumble'
y = scipy.signal.lsim((num, den),u,t)[1]


#######################################################################
# ANALYTICAL EXPRESSIONS FOR POWER SPECTRAL DENSITIES
#######################################################################
# Note that these spectra are continuous-time, as our system dynamics
# above are defined as continuous-time transfer functions H(s). So when
# comparing these analytical spectra with what we will calculate with
# the simulated time series, which are discrete time, we need to multiply
# the spectra that we estimate with dt (Chapter 4).
# And also note that these analytical spectra are computed as a function
# of frequency in rad/s (omega).

# white noise has a spectrum that equals Wn at all frequencies
Swwanal = numpy.zeros(int(N/2))

for i in range(len(Swwanal)):
  Swwanal[i] = Wn

# the colored noise has an auto-spectrum that equals Wn * |Hrr|^2
# with Hr the runway rumble frequency response

hrrmag  = abs(hrr) 
Suuanal = hrrmag**2*Swwanal

# the suspension system has an auto-spectrum that equals Suuanal * |Hss|^2
# with Hss the suspension system frequency response

hssmag  = abs(hss)
Syyanal = hssmag**2*Suuanal

# the analytical cross PSD between u and y equals Hss * Suuanal
Suyanal = hss*Suuanal

# the auto PSD of the acceleration comes from double differentiating
# the position, which in the frequency domain becomes
Saaanal = omega**4*Syyanal

#######################################################################
# CALCULATE THE RAW PERIODOGRAMS
#######################################################################
# white noise PSD estimate
WN  = numpy.fft.fft(w,N)
Sww = (WN*numpy.conj(WN)/N).real  
Sww = Sww[0:int(N/2)]      # only take positive frequencies

# runway rumble PSD estimate
U  = numpy.fft.fft(u,N)
Suu = (U*numpy.conj(U)/N).real  
Suu = Suu[0:int(N/2)]      # only take positive frequencies

# suspension system PSD estimate
Y  = numpy.fft.fft(y,N)
Syy = (Y*numpy.conj(Y)/N).real  
Syy = Syy[0:int(N/2)]      # only take positive frequencies

# cross PSD function Suy estimate
Suy = (Y*numpy.conj(U))/N 
Suy = Suy[0:int(N/2)]      # only take positive frequencies

# acceleration PSD estimate
Saa = omega**4*Syy

# correct for the fact that we want estimates of continuous-time
# spectra, so multiply with dt (Chapter 4)
Sww = Sww*dt
Suu = Suu*dt
Suy = Suy*dt
Syy = Syy*dt
Saa = Saa*dt

#######################################################################
# CALCULATE THE SMOOTHED PERIODOGRAMS USING pwelch.m
#######################################################################
# To properly use pwelch (or any algorithm for that matter) we first
# need to state some of the algorithm's properties:
#  - it gives us the estimate of the discrete-time spectrum, 
#    but already multiplied with dt
#  - it returns the frequency in Hz, starting with the zero frequency,
#    so we need to 'align' the frequency axis with our frequency axis
#  - we can only compute autospectra with pwelch
#  - it uses windows (here 100 samples) and overlap between these
#    windows (here set at 10 samples)
#  - with one-sided the spectrum estimate needs to be divided by 2
#    to also take into account the negative frequencies

# smoothed periodogram of the white noise signal
fw, Swwspct = scipy.signal.welch(w, fs, window = numpy.arange(0, 100), nfft = N, noverlap = 10, return_onesided = True, detrend = False)
Swwspct = Swwspct/2        # adjust power for negative frequencies
Swwspct = Swwspct[1:int(N/2)+1] # get rid of the zero frequency, to align

#smoothed periodogram of runway rumble response
fw, Suuspct = scipy.signal.welch(u, fs, window = numpy.arange(0, 100), nfft = N, noverlap = 10, return_onesided = True, detrend = False)
Suuspct = Suuspct/2        # adjust power for negative frequencies
Suuspct = Suuspct[1:int(N/2)+1] # get rid of the zero frequency, to align

# smoothed periodogram of suspension system response
fw, Syyspct = scipy.signal.welch(y, fs, window = numpy.arange(0, 100), nfft = N, noverlap = 10, return_onesided = True, detrend = False)
Syyspct = Syyspct/2        # adjust power for negative frequencies
Syyspct = Syyspct[1:int(N/2)+1] # get rid of the zero frequency, to align

# smoothed periodogram of acceleration
Saaspct = omega**4*Syyspct

#######################################################################
# A SIMPLER ALTERNATIVE TO SMOOTH THE RAW PERIODOGRAMS
#######################################################################
# Basically we smoothen the periodogram in the frequency domain
# with a 'moving average' (the algorithm's default) of 100 samples

Swws = MatlabFuncs.smooth(Sww,100)
Suus = MatlabFuncs.smooth(Suu,100)
Syys = MatlabFuncs.smooth(Syy,100)
Saas = MatlabFuncs.smooth(Saa,100)

# Suy is complex
Suys = MatlabFuncs.smooth(Suy,100)
Suyrs= MatlabFuncs.smooth(Suy.real,100)  # smooth real part of Suy
Suyis= MatlabFuncs.smooth(Suy.imag,100)  # smooth imaginary part of Suy

#######################################################################
# ESTIMATE THE suspension dynamics FREQUENCY RESPONSE FUNCTION
#######################################################################
# We can now obtain estimates of the frequency response function
# of the suspension system dynamics, in two ways

# 1) using the raw periodograms
hss_raw = Suy/Suu
mss_raw = abs(hss_raw)
pss_raw = (180/pi)*numpy.angle(hss_raw)

# 2) using the smoothed periodograms with pwelch
hss_sm  = Suys/Suus
mss_sm  = abs(hss_sm)
pss_sm  = (180/pi)*numpy.angle(hss_sm)

# the analytic frequency response
mss_anal = abs(hss)
pss_anal = (180/pi)*numpy.angle(hss)

#######################################################################
# PLOTTING THE RESULTS
#######################################################################
# FIRST THE AUTOSPECTRA and the smoothed ways to compute them

plt.figure()
plt.subplot(2, 2, 1)
plt.loglog(f,Swwspct)
plt.loglog(f,Swws, linestyle = '-', color = 'r')
plt.loglog(f,Swwanal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Sww(f)')
plt.title('PSD White Noise \n and Smoothed PSDs')

plt.subplot(2, 2, 2)
plt.loglog(f,Suuspct)
plt.loglog(f,Suus, linestyle = '-', color = 'r')
plt.loglog(f,Suuanal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Suu(f)')
plt.title('PSD Forming Filter Output \n and Smoothed PSDs')

plt.subplot(2, 2, 3)
plt.loglog(f,Syyspct)
plt.loglog(f,Syys, linestyle = '-', color = 'r')
plt.loglog(f,Syyanal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Syy(f)')
plt.title('PSD Damper Output \n and Smoothed PSDs')

plt.subplot(2, 2, 4)
plt.loglog(f,Saaspct)
plt.loglog(f,Saas, linestyle = '-', color = 'r')
plt.loglog(f,Saaanal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Saa(f)')
plt.title('PSD Acceleration \n and Smoothed PSDs')

plt.subplots_adjust(hspace=0.7, wspace=1.1)

# THEN THE crossSPECTRUM, in two ways (raw & smoothed vs. analytic)
# note that we take the absolute values of the real and imaginary parts
# as these may be very small and negative
plt.figure()
plt.subplot(2, 2, 1)
plt.loglog(f,abs(Suy.real))
plt.loglog(f,abs(Suyrs), linestyle = '-', color = 'r')
plt.loglog(f,abs(Suyanal.real), linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Real Suy(f)')
plt.title('Real part cross PSDs Suy')

plt.subplot(2, 2, 2)
plt.loglog(f,abs(Suy.imag))
plt.loglog(f,abs(Suyis), linestyle = '-', color = 'r')
plt.loglog(f,abs(Suyanal.imag), linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('Imag Suy(f)')
plt.title('Imaginary part cross PSDs Suy')

plt.subplot(2, 2, 3)
plt.loglog(f,mss_raw)
plt.loglog(f,mss_sm, linestyle = '-', color = 'r')
plt.loglog(f,mss_anal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('|Hyu|')
plt.title('Frequency response function Hyu (gain)')

plt.subplot(2, 2, 4)
plt.semilogx(f,pss_raw)
plt.semilogx(f,pss_sm, linestyle = '-', color = 'r')
plt.semilogx(f,pss_anal, linestyle = '--', color = 'g')
plt.xlabel('frequency [Hz]')
plt.ylabel('<Hyu, deg')
plt.title('Frequency response function Hyu (phase)')


plt.subplots_adjust(hspace=0.7, wspace=1.1)
plt.show()



