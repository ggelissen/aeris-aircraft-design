# Filename : examp81c.m

# Simulation of aircraft asymmetric response to atmospheric turbulence.

# Chapter 8 of lecture notes ae4-304

# Revised: November [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from matplotlib import pyplot as plt
from cit2a import cit2a_fun

plt.close('all')

print('   Example 8.1                                                    ')
print('                                                                  ')
print('   Simulation of the motion variables for asymmetric aircraft     ')
print('   motions.                                                       ')
print('                                                                  ')
print('   This program produces Figures 8-16 and 8-17 of the lecture notes:')
print('   Aircraft Responses to Atmospheric Turbulence.                  ')
print('                                                                  ')

# GET SYSTEM DYNAMICS
A, A1, A2, B, sigmaug_V, sigmabg, sigmaag, Lg, V, b = cit2a_fun()

# NOTE (see also cit2a.py) 

# THE CESSNA CITATION CE-500 IS NOT STABLE IN SPIRAL MODE (FOR THE cit2a.py 
# FLIGHT CONDITION), HENCE THE FEEDBACK CONTROLLER FOR PHI IS USED AS IN : 

#   delta_a = K_phi*phi (K_phi for THIS flight condition)

# THEREFORE, CONTROLLED AIRCRAFT SYSTEM MATRICES WILL BE USED FOR RESULTS;

#      A = A2

# TIME AXIS AND INPUT VECTOR DEFINITION

# TIME AXIS AND INPUT VECTOR DEFINITION
dt = 0.05; T  = 60; t = numpy.arange(0, T+dt, dt)
N = len(t)
nn = numpy.zeros((1,N))

# TURBULENCE INPUTS
u_g = numpy.random.randn(1,N)/sqrt(dt)    # sqrt(dt) because of lsim characteristics
v_g = numpy.random.randn(1,N)/sqrt(dt)
w_g = numpy.random.randn(1,N)/sqrt(dt)

#INPUT VECTORS
u1 = numpy.stack((nn, nn, u_g, nn, nn), axis = 1); u1 = u1[0].T
u2 = numpy.stack((nn, nn, nn, w_g, nn), axis = 1); u2 = u2[0].T
u3 = numpy.stack((nn, nn, nn, nn, v_g), axis = 1); u3 = u3[0].T
# DEFINE OUTPUT MATRICES
C = numpy.asmatrix([[1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  
     [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],    
     [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],    
     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]])  


D = numpy.zeros((4, 5))

sys = cm.ss(A2, B, C, D)

# RESPONSE to u_g
y1 = cm.lsim(sys,u1,t)[0]
# RESPONSE to w_g
y2 = cm.lsim(sys,u2,t)[0]
# RESPONSE to v_g
y3 = cm.lsim(sys,u3,t)[0]
# RESPONSE to all together (linear system!)
yt = y1+y2+y3

# PLOT RESULTS
beta_axis = [0, 60, -0.07,  0.07]
phi_axis  = [0, 60, -0.15,  0.15]
pb_axis   = [0, 60, -1e-2,  1e-2]
rb_axis   = [0, 60, -1e-2,  1e-2]

# RESPONSE TO u_g
print('                                              ')
print(' Response to u_g (see figures)                ')
plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y1[:,0])
plt.xlim(beta_axis[0:2]); plt.ylim(beta_axis[2:len(beta_axis)])
plt.xlabel('time, s'); plt.ylabel('beta [rad]')

plt.subplot(2,1,2); plt.plot(t,y1[:,1])
plt.xlim(phi_axis[0:2]); plt.ylim(phi_axis[2:len(phi_axis)])
plt.xlabel('time, s'); plt.ylabel('phi [rad]')

plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y1[:,2])
plt.xlim(pb_axis[0:2]); plt.ylim(pb_axis[2:len(pb_axis)])
plt.xlabel('time, s'); plt.ylabel('pb/2V [rad]')

plt.subplot(2,1,2); plt.plot(t,y1[:,3])
plt.xlim(rb_axis[0:2]); plt.ylim(rb_axis[2:len(rb_axis)])
plt.xlabel('time, s'); plt.ylabel('rb/2V [rad]')

# RESPONSE TO w_g
print('                                              ')
print(' Response to w_g (see figures)                ')
plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y2[:,0])
plt.xlim(beta_axis[0:2]); plt.ylim(beta_axis[2:len(beta_axis)])
plt.xlabel('time, s'); plt.ylabel('beta [rad]')

plt.subplot(2,1,2); plt.plot(t,y2[:,1])
plt.xlim(phi_axis[0:2]); plt.ylim(phi_axis[2:len(phi_axis)])
plt.xlabel('time, s'); plt.ylabel('phi [rad]')

plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y2[:,2])
plt.xlim(pb_axis[0:2]); plt.ylim(pb_axis[2:len(pb_axis)])
plt.xlabel('time, s'); plt.ylabel('pb/2V [rad]')

plt.subplot(2,1,2); plt.plot(t,y2[:,3])
plt.xlim(rb_axis[0:2]); plt.ylim(rb_axis[2:len(rb_axis)])
plt.xlabel('time, s'); plt.ylabel('rb/2V [rad]')

# RESPONSE TO w_g
print('                                              ')
print(' Response to v_g (see figures)                ')
plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y3[:,0])
plt.xlim(beta_axis[0:2]); plt.ylim(beta_axis[2:len(beta_axis)])
plt.xlabel('time, s'); plt.ylabel('beta [rad]')

plt.subplot(2,1,2); plt.plot(t,y3[:,1])
plt.xlim(phi_axis[0:2]); plt.ylim(phi_axis[2:len(phi_axis)])
plt.xlabel('time, s'); plt.ylabel('phi [rad]')

plt.figure() 
plt.subplot(2,1,1); plt.plot(t,y3[:,2])
plt.xlim(pb_axis[0:2]); plt.ylim(pb_axis[2:len(pb_axis)])
plt.xlabel('time, s'); plt.ylabel('pb/2V [rad]')

plt.subplot(2,1,2); plt.plot(t,y3[:,3])
plt.xlim(rb_axis[0:2]); plt.ylim(rb_axis[2:len(rb_axis)])
plt.xlabel('time, s'); plt.ylabel('rb/2V [rad]')

# RESPONSE TO all together
print('                                              ')
print(' Response to u_g, v_g and w_g combined (see figures) ')
plt.figure() 
plt.subplot(2,1,1); plt.plot(t,yt[:,0])
plt.xlim(beta_axis[0:2]); plt.ylim(beta_axis[2:len(beta_axis)])
plt.xlabel('time, s'); plt.ylabel('beta [rad]')

plt.subplot(2,1,2); plt.plot(t,yt[:,1])
plt.xlim(phi_axis[0:2]); plt.ylim(phi_axis[2:len(phi_axis)])
plt.xlabel('time, s'); plt.ylabel('phi [rad]')

plt.figure() 
plt.subplot(2,1,1); plt.plot(t,yt[:,2])
plt.xlim(pb_axis[0:2]); plt.ylim(pb_axis[2:len(pb_axis)])
plt.xlabel('time, s'); plt.ylabel('pb/2V [rad]')

plt.subplot(2,1,2); plt.plot(t,yt[:,3])
plt.xlim(rb_axis[0:2]); plt.ylim(rb_axis[2:len(rb_axis)])
plt.xlabel('time, s'); plt.ylabel('rb/2V [rad]')


plt.subplots_adjust(hspace=0.4)
plt.show()
