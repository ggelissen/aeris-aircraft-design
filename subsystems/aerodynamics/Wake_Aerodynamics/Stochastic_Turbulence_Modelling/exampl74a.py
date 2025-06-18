# Filename : exampl74a.m

# Calculation of analytical power spectral densities and variance of
# motion variables

# Chapter 7 of lecture notes ae4-304

# Revised: November 2014 [M Rodriguez], June 2021 [MM]
# - Python version by B. Englebert (September 2021)

from math import*
import numpy
import control.matlab as cm
from cit2s import cit2s_fun


if __name__ == "__main__":
    print('   Example 7.3                                                    ')
    print('   Calculation of analytical power spectral densities and variance')
    print('   motion variables                                               ')
    # GET AIRCRAFT DYNAMICS
    A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun()
        
    # DEFINE MISCELLANEOUS
    g  = 9.80665                       # gravitational acc [N/kg]
    
    # calculation of the frequency response of the normal acceleration factor
    # horizontal turbulence : u=2, vertical turbulence u=3.
    
    print('                                                                  ')
    print('   Input 2 for horizontal turbulence and 3 for vertical turbulence')
    print('   excitation                                                     ')


    u = int(input('   Input 2 or 3 : ')); u = u - 1 # zero based indexing

    # FREQUENCY AXIS
    Nomega = 300; w = numpy.logspace(-2,2,Nomega)
    
    # C and D MATRICES AND SYSTEMS
    D      = numpy.zeros((1, 3))
    Cu     = numpy.array([1, 0, 0, 0, 0, 0, 0]); sysu = cm.ss(A, B[:,u], Cu, D[:, u])
    Calpha = numpy.array([0, 1, 0, 0, 0, 0, 0]); sysalpha = cm.ss(A, B[:,u], Calpha, D[:, u])
    Ctheta = numpy.array([0, 0, 1, 0, 0, 0, 0]); systheta = cm.ss(A, B[:,u], Ctheta, D[:, u])
    Cq     = numpy.array([0, 0, 0, 1, 0, 0, 0]); sysq = cm.ss(A, B[:,u], Cq, D[:, u])
    Cug    = numpy.array([0, 0, 0, 0, 1, 0, 0]); sysug = cm.ss(A, B[:,u], Cug, D[:, u])
    Cag    = numpy.array([0, 0, 0, 0, 0, 1, 0]); sysag = cm.ss(A, B[:,u], Cag, D[:, u])
    
    
    Calphadot = A[1,:]
    Dalphadot = B[1,:]
    
    #% COMPUTE FREQUENCY RESPONSE FUNCTION AND PSD
    mag = cm.bode(sysu, w, Plot = False)[0]; Suu = mag * mag
    mag = cm.bode(sysalpha, w, Plot = False)[0]; Saa = mag * mag
    mag = cm.bode(systheta, w, Plot = False)[0]; Stt = mag * mag
    mag = cm.bode(sysq, w, Plot = False)[0]; Sqq = mag * mag
    mag = cm.bode(sysug, w, Plot = False)[0]; Sugug = mag * mag
    mag = cm.bode(sysag, w, Plot = False)[0]; Sagag = mag * mag
    
    # COMPUTE FREQ. RESPONSE of NZ
    sysalphadot = cm.ss(A, B[:,u], Calphadot, Dalphadot[:, u])
    Hadotw = cm.frd(sysalphadot, w).fresp; Hadotw = numpy.ndarray.flatten(Hadotw)
    Hqw =  cm.frd(sysq, w).fresp; Hqw = numpy.ndarray.flatten(Hqw)
    
    Hnz   = (V/g)*((V/c)*Hqw - Hadotw)
    mag   = abs(numpy.ndarray.flatten(Hnz))    
    Snznz = mag*mag
    
    Sxx = numpy.array([Suu, Saa, Stt, Sqq, Snznz, Sugug, Sagag]).T
    
    # COMPUTE VARIANCE THROUGH CRUDE INTEGRATION OF PSDs
    var = numpy.zeros(7)
    for j in range(len(var)):
      for i in range(0, Nomega-1):
        var[j]    = var[j]+(w[i+1]-w[i])*Sxx[i,j]
        
    var = var/pi
    print('                                                 ')
    print('   Compute variances for n and a_z:              ')            
    print('   Variance of nz: ', var[4]            )
    # Remember: var_az = E[(a*g)^2-mu_az]
    print('   Variance of az = g*nz: ', var[4]*g**2 ) 

def exampl74a_fun():
    # DEFINE MISCELLANEOUS
    g  = 9.80665                       # gravitational acc [N/kg]
    A, At, B, sigmaug_V, sigmaag, Lg, V, c = cit2s_fun()
    u = int(input('   Input 2 or 3 : ')); u = u - 1 # zero based indexing

    # FREQUENCY AXIS
    Nomega = 300; w = numpy.logspace(-2,2,Nomega)
    
    # C and D MATRICES AND SYSTEMS
    D      = numpy.zeros((1, 3))
    Cu     = numpy.array([1, 0, 0, 0, 0, 0, 0]); sysu = cm.ss(A, B[:,u], Cu, D[:, u])
    Calpha = numpy.array([0, 1, 0, 0, 0, 0, 0]); sysalpha = cm.ss(A, B[:,u], Calpha, D[:, u])
    Ctheta = numpy.array([0, 0, 1, 0, 0, 0, 0]); systheta = cm.ss(A, B[:,u], Ctheta, D[:, u])
    Cq     = numpy.array([0, 0, 0, 1, 0, 0, 0]); sysq = cm.ss(A, B[:,u], Cq, D[:, u])
    Cug    = numpy.array([0, 0, 0, 0, 1, 0, 0]); sysug = cm.ss(A, B[:,u], Cug, D[:, u])
    Cag    = numpy.array([0, 0, 0, 0, 0, 1, 0]); sysag = cm.ss(A, B[:,u], Cag, D[:, u])
    
    
    Calphadot = A[1,:]
    Dalphadot = B[1,:]
    
    #% COMPUTE FREQUENCY RESPONSE FUNCTION AND PSD
    mag = cm.bode(sysu, w, Plot = False)[0]; Suu = mag * mag
    mag = cm.bode(sysalpha, w, Plot = False)[0]; Saa = mag * mag
    mag = cm.bode(systheta, w, Plot = False)[0]; Stt = mag * mag
    mag = cm.bode(sysq, w, Plot = False)[0]; Sqq = mag * mag
    mag = cm.bode(sysug, w, Plot = False)[0]; Sugug = mag * mag
    mag = cm.bode(sysag, w, Plot = False)[0]; Sagag = mag * mag
    
    # COMPUTE FREQ. RESPONSE of NZ
    sysalphadot = cm.ss(A, B[:,u], Calphadot, Dalphadot[:, u])
    Hadotw = cm.frd(sysalphadot, w).fresp; Hadotw = numpy.ndarray.flatten(Hadotw)
    Hqw =  cm.frd(sysq, w).fresp; Hqw = numpy.ndarray.flatten(Hqw)
    
    Hnz   = (V/g)*((V/c)*Hqw - Hadotw)
    mag   = abs(numpy.ndarray.flatten(Hnz))    
    Snznz = mag*mag
    
    Sxx = numpy.array([Suu, Saa, Stt, Sqq, Snznz, Sugug, Sagag]).T
    
    # COMPUTE VARIANCE THROUGH CRUDE INTEGRATION OF PSDs
    var = numpy.zeros(7)
    for j in range(len(var)):
      for i in range(0, Nomega-1):
        var[j]    = var[j]+(w[i+1]-w[i])*Sxx[i,j]
        
    var = var/pi
    print('                                                 ')
    print('   Compute variances for n and a_z:              ')            
    print('   Variance of nz: ', var[4]            )
    # Remember: var_az = E[(a*g)^2-mu_az]
    print('   Variance of az = g*nz: ', var[4]*g**2 ) 
    
    return u, w, V, c, Sxx, A, B