# Exampl54  Calculates covariance matrix of a second order mass-spring-damper
#           system perturbed by white noise, using the Monte Carlo
#           method (ensemble average = average over all realizations)

# Chapter 5 of lecture notes ae4-304

# Program revised August 1992, February 2004 [MM], November 2014 [M
# Rodriguez], June 2021 [MM] - Python version by B. Englebert (August 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt


plt.close('all')

print('   Example 5.4                                                ')
print('                                                              ')
print('   Calculation of the Covariance matrix of a second order     ')
print('   mass-spring-damper system perturbed by white noise using   ')
print('   Monte Carlo Method.                                        ')
print('   The covariance matrix C is calculated with:                ')
print('                                                              ')
print('             1   N                    T                       ')
print('      C   = --- SUM (x(i)-m )(x(i)-m )                        ')
print('       xx   N-1 i=1        x        x                         ')
print('                                                              ')
print('   This program can produce Figures 5.10-5.12 in the lecture  ')
print('   notes: Aircraft Responses to Atmospheric Turbulence.       ')
print('                                                              ')
print('   2nd order dynamic model Definition:                        ')
print('                                                              ')

# CT SYSTEM DYNAMICS
w0      = float(input('   Give undamped natural frequency [rad/s] : '))
zeta    = float(input('   Give damping ratio                      : '))

m = 1                          # mass
k = w0**2                       # spring constant
c = zeta*2*m*w0                # damping constan

A= numpy.mat([[0, 1], [-k/m, -c/m]])  # state-space representation of second
B= numpy.mat([[0], [1/m]])              # order system
C= numpy.mat([[1, 0]])
D= numpy.mat([[0]])
sys = cm.ss(A, B, C, D)

# SET TIME AXIS
dt   =  float(input('   Give sampling time interval dt              : '))
T    =  float(input('   Give total time interval T                  : '))

t = numpy.arange(0, T, dt)	        # time axis
N = int(T/dt)                       # number of samples

# COMPUTE DT EQUIVALENT
sysd = cm.c2d(sys,dt)   # discretizing using MATLAB c2d command
Phi = sysd.A; Gamma = sysd.B

# DEFINE CT WHITE NOISE CHARACTERISTICS
Wc   =  float(input('   Give CT white noise intensity               : '))

Wd = Wc/dt     # NOTE: divide by sample time dt, this was not done 
                # correctly in the lecture notes ae4-404, May 1998
                # and earlier!! (Figures 5.8, 5.9 
                # and 5.10 are now correct)

# DEFINE # of EXPERIMENTS (MONTE CARLO METHOD)
NN   =  int(input('   Give number of experiments                  : '))

w = sqrt(Wd)*numpy.random.randn(N,NN)   # generate realizations of the random noise

# Initialize variables
x1 = numpy.zeros((N,NN))
x2 = numpy.zeros((N,NN))
x = numpy.vstack((x1[0,:], x2[0,:]))
w1 = numpy.zeros((2,1))
xx = numpy.zeros((2,1))

for j in range(0, NN):
  for l in range(0, 2):
    xx[l,0] = x[l,j]


  for i in range(0, N-1):
    for k in range(0, 2):
      w1[k,0] = Gamma[k,0]*w[i,j]           # response to noise                    

    
    xx = Phi*xx + w1;                              
    x1[i+1,j] = xx[0,0]
    x2[i+1,j] = xx[1,0]
    
mean1 = numpy.zeros(N)
mean2 = numpy.zeros(N)

for i in range(0, N):
  for j in range(0, NN):
    mean1[i] = mean1[i] + x1[i,j]
    mean2[i] = mean2[i] + x2[i,j]
    
mean1 = (1/NN)*mean1
mean2 = (1/NN)*mean2
    
Cx1x1 = numpy.zeros(N)
Cx1x2 = numpy.zeros(N)
Cx2x2 = numpy.zeros(N)

for i in range(0, N):
  for j in range(0, NN):
    Cx1x1[i] = Cx1x1[i] +(x1[i,j]-mean1[i])*(x1[i,j]-mean1[i])
    Cx1x2[i]  = Cx1x2[i] +(x1[i,j]-mean1[i]) *(x2[i,j]-mean2[i])
    Cx2x2[i]  = Cx2x2[i] +(x2[i,j]-mean2[i]) *(x2[i,j]-mean2[i])

  
  Cx1x1[i]  =Cx1x1[i] /(NN-1)
  Cx1x2[i] = Cx1x2[i] /(NN-1)
  Cx2x2[i]  = Cx2x2[i] /(NN-1)

# ANALYTICAL CALCULATIONS
Cy1y1 = numpy.zeros(N)
Cy1y2 = numpy.zeros(N)  
Cy2y2 = numpy.zeros(N)    
  
Cy1y1[0] = Cx1x1[0]; Cy1y2[0] = Cx1x2[0]; Cy2y2[0] = Cx2x2[0]

Cyy = numpy.zeros((2,2))
for i in range(0, N-1):
    Cyy = Phi*Cyy*Phi.T + Gamma*Wd*Gamma.T
    Cy1y1[i+1] = Cyy[0,0]
    Cy1y2[i+1] = Cyy[0,1]
    Cy2y2[i+1] = Cyy[1,1]

# PLOT RESULTS
plt.figure()
plt.subplot(2,1,1)
plt.plot(t,mean1)
plt.xlabel('time (s)')
plt.ylabel('mean1(t)')

plt.subplot(2,1,2)
plt.plot(t,mean2)
plt.xlabel('time (s)')
plt.ylabel('mean2(t)')

# SHOW ANALYTICAL CALCULATIONS AND "MONTE-CARLO" DATA
plt.figure()
plt.subplot(3,1,1)
plt.plot(t,Cx1x1,linestyle = '--')
plt.plot(t,Cy1y1)
plt.xlabel('time (s)')
plt.ylabel('Cx1x1(t)')

plt.subplot(3,1,2)
plt.plot(t,Cx1x2,linestyle = '--')
plt.plot(t,Cy1y2)
plt.xlabel('time (s)')
plt.ylabel('Cx1x2(t)')

plt.subplot(3,1,3)
plt.plot(t,Cx2x2,linestyle = '--')
plt.plot(t,Cy2y2)
plt.xlabel('time (s)')
plt.ylabel('Cx2x2(t)')

plt.show()
