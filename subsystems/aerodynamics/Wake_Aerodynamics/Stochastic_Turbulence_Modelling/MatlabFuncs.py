# MatlabFuncs   Contains functions present in Matlab but not in Python
# by B. Englebert (September 2021)

import numpy
import scipy.linalg as spla


# UNBIASED AUTO PRODUCT FUNCTION
def xcorr(x, mode = None):
    r= numpy.correlate(x, x, mode = "full")
    if mode == None or mode == "unbiased":
        L = (len(r)-1)/2; Larr = numpy.arange(-L,L+1) # Max number of lags
        Nm = [len(x)-abs(i) for i in Larr]
        
        for i in range(len(r)):
            r[i] = r[i]/Nm[i]
    elif mode  == "biased":
        N = len(x)
        r = r/N
        
    return r
    

# UNBIASED AUTO COVARIANCE FUNCTION
def xcov(x, mode = None):
    c = xcorr(x - numpy.mean(x), mode)
    
    return c

# SMOOTHING FUNCTION
def smooth(a,WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size 
    if WSZ%2 == 0:
        WSZ = WSZ - 1 # Window size needs to be odd, this is the same operation as in Matlab
    
    out0 = numpy.convolve(a,numpy.ones(WSZ,dtype=int),'valid')/WSZ    
    r = numpy.arange(1,WSZ-1,2)
    start = numpy.cumsum(a[:WSZ-1])[::2]/r
    stop = (numpy.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    
    return numpy.concatenate((start , out0, stop))
