# Exampl51  shows the response of a CT first order linear system to a white
#           noise input signal and examine the statistical properties
#           of the response for a large number of realizations.

#           Check the outcome with the result that can be
#           analytically obtained through Tables 3.5 and 3.6.

# Chapter 5 of lecture notes ae4-304.

# (c) MM 2004 Revised: November 2014, [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (August 2021)

from math import*
import numpy
import scipy
import control.matlab as cm
from matplotlib import pyplot as plt

plt.close('all')


print('   Example 5.1                                                     ')
print('                                                                   ')  
print('   Simulation of a continuous time first order system response     ')
print('   to a white noise input signal and examine the mean and          ')
print('   standard deviation of the response for a large number           ')
print('   of realizations                                                 ')
print('                                                                   ')
print('   The outcome can be verified with the result obtained            ')
print('   analytically using Tables 3.5 and 3.6                           ')
print('                                                                   ')
print('   This program can produce Figure 5.2 of the lecture              ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.            ')
print('                                                                   ')


# SYSTEM DYNAMICS
#
# Assume we have a CT system, a first order low-pass filter K/(1+s tau)
#
K   = 2.00         # system gain     [-]
tau = 0.50         # system time lag [s]

num = K; den = [tau, 1]    # system dynamics in rational polynomial form

sys = cm.tf(num,den)       # Matlab LTI system

# TIME DEFINITION
fs = 100            #sample rate [Hz], 100 Hz is very common.
dt = 1/fs          # sample time [s]
t  = numpy.arange(0, 60+dt, dt)       # 60 seconds of data
NT = len(t)     # the number of time samples

#WHITE NOISE DEFINITION
Wn = 2                   # intensity of the white noise

w  = sqrt(Wn)*numpy.random.randn(NT)  # random, normally distributed white 
                            #noise with intensity Wn
                             
                             
# COMPUTE SYSTEM TIME RESPONSE

# REPEAT THE SYSTEM RESPONSE N TIMES AND LOOK AT VARIANCES
# OF INPUT AND OUTPUT SIGNALS
# DO NOT FORGET TO SKIP THE TRANSIENT PART OF THE RESPONSE!
N = 500   # the number of realizations

Var_in      = numpy.zeros(N)
Var_out     = numpy.zeros(N)
Var_out_e   = numpy.zeros(N)

# skip the first part of the response, because of the transient
# in this case this only depends on the value of tau, but let's be
# safe and skip the first 33% anyway
stationary_part = numpy.arange((floor(NT/3)+1), NT+1)

for kk in range(len(Var_in)):
    #
    # create white noise input
    w = sqrt(Wn)*numpy.random.randn(NT)
    # compute system output - TAKES A WHILE TO RUN FOR ALL N REALIZATIONS
    y = scipy.signal.lsim((num, den),w/sqrt(dt),t, interp = False)[1] # interp = False performs zoh, get 2nd index for output. Correct: DIVISION of Wn by dt!
    y_e = scipy.signal.lsim((num, den),w,t, interp = False)[1] # interp = False performs zoh, get 2nd index for output.  Wrong: NO DIVISION of Wn by dt!
    # compute variance of input and output
    Var_in[kk]  = numpy.cov(w[stationary_part[0]:stationary_part[-1]])
    Var_out[kk] = numpy.cov(y[stationary_part[0]:stationary_part[-1]])
    Var_out_e[kk] = numpy.cov(y_e[stationary_part[0]:stationary_part[-1]])
    
# NOW, NOTE THAT WE ARE INTERESTED IN THE VARIANCE OF
# THE WHITE NOISE INPUT SIGNAL AND THE VARIANCE OF THE SYSTEM
# OUTPUT SIGNAL. FOR EACH REALIZATION, THESE ARE DIFFERENT:
# THEY CAN BE CONSIDERED STOCHASTIC VARIABLES THEMSELVES!!!
# AND THE MEANS SHOULD IN PRINCIPLE (for a large number of
# realizations N) BE IDENTICAL TO THE ANALYTICAL VALUES
# REPRESENTING THE ENSEMBLE.

# REMEMBER: AVERAGING OVER THE REALIZATIONS MEANS THAT WE
#       ARE ESTIMATING THE ENSEMBLE AVERAGE. WHEN THE
#       NUMBER OF REALIZATIONS INCREASES (N -> infinity)
#       THE ESTIMATIONS SHOULD CONVERGE TO THE ENSEMBLE
#       AVERAGE. IT CAN BE SHOWN THAT THE ESTIMATOR
#       FOR THE MEAN AND THE ESTIMATOR FOR THE VARIANCE
#       ARE UNBIASED AND ASYMPTOTICALLY RIGHT
    
mean_var_in    = numpy.mean(Var_in)
mean_var_out   = numpy.mean(Var_out)
mean_var_out_e = numpy.mean(Var_out_e)
var_var_in     = numpy.var(Var_in) 
var_var_out    = numpy.var(Var_out)
var_var_out_e  = numpy.var(Var_out_e)


# THE ANALYTICAL VALUE OF THE SYSTEM OUTPUT SIGNAL VARIANCE
# CAN BE OBTAINED WITH TABLE 3.5

# For this system it is equal to:
#       K^2
#    W*-----       with: W   : the CT white noise intensity
#      2*tau             K   : the system gain
#                        tau : the system lag time constant

var_out_analytic = Wn*K*K/(2*tau)

# THE ANALYTICAL VALUE OF THE WHITE NOISE INPUT VARIANCE
# JUST EQUALS THE INTENSITY
var_in_analytic = Wn

# PLOT THE RESULTS
plt.figure()
plt.subplot(3,1,1)
plt.plot(numpy.arange(1, N+1, 1), Var_in, label = 'estimated')
# show the mean +- var of the average over 
# all realizations in green
plt.plot(numpy.array([1, N]), mean_var_in*numpy.array([1, 1]),color = 'g', label = 'mean')             
plt.plot(numpy.array([1, N]), mean_var_in*numpy.array([1, 1])+var_var_in, color = 'g', linestyle = '--', label = 'variance')  
# show the analytical value (the ensemble average) in red
plt.plot(numpy.array([1, N]), var_in_analytic*numpy.array([1, 1]),color = 'r', label = 'analytic')        
# plot the other var line here, otherwise it is 
# redundant in the legend
plt.plot(numpy.array([1, N]), mean_var_in*numpy.array([1, 1])-var_var_in, color = 'g', linestyle = '--')
plt.title('variance of CT white noise input signal')
plt.ylabel('var(w)')
plt.xlabel('realization')
plt.legend(loc='right') 


plt.subplot(3,1,2)
plt.plot(numpy.arange(1, N+1, 1), Var_out_e, label = 'estimated')
# show the mean +- var of the average over 
# all realizations in green
plt.plot(numpy.array([1, N]), mean_var_out_e*numpy.array([1, 1]),color = 'g', label = 'mean')             
plt.plot(numpy.array([1, N]), mean_var_out_e*numpy.array([1, 1])+var_var_out_e, color = 'g', linestyle = '--', label = 'variance')  
# show the analytical value (the ensemble average) in red
plt.plot(numpy.array([1, N]), var_out_analytic*numpy.array([1, 1]),color = 'r', label = 'analytic')        
# plot the other var line here, otherwise it is 
# redundant in the legend
plt.plot(numpy.array([1, N]), mean_var_out_e*numpy.array([1, 1])-var_var_out_e, color = 'g', linestyle = '--')
plt.title('variance of system output signal no dt')
plt.ylabel('var(y)')
plt.xlabel('realization')
plt.legend(loc='right') 

plt.subplot(3,1,3)
plt.plot(numpy.arange(1, N+1, 1), Var_out, label = 'estimated')
# show the mean +- var of the average over 
# all realizations in green
plt.plot(numpy.array([1, N]), mean_var_out*numpy.array([1, 1]),color = 'g', label = 'mean')             
plt.plot(numpy.array([1, N]), mean_var_out*numpy.array([1, 1])+var_var_out, color = 'g', linestyle = '--', label = 'variance')  
# show the analytical value (the ensemble average) in red
plt.plot(numpy.array([1, N]), var_out_analytic*numpy.array([1, 1]),color = 'r', label = 'analytic')        
# plot the other var line here, otherwise it is 
# redundant in the legend
plt.plot(numpy.array([1, N]), mean_var_out*numpy.array([1, 1])-var_var_out, color = 'g', linestyle = '--')
plt.title('variance of system output signal')
plt.ylabel('var(y)')
plt.xlabel('realization')
plt.legend(loc='right') 

plt.subplots_adjust(hspace=0.8)
plt.show()
