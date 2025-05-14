import math
import numpy as np

# Based on Part II "Preliminary Configuration Design and Integration of the Propulsion System" by Roskam
# For manned aircraft, use "5. Business Jet"
# For unmanned aircraft, use "8. Military Trainers"


########################## Chapter 6: Class I Method for Wing Planform Design and for Sizing and Locating Lateral Control Surfaces ##########################

dihedral = 2.5 # degrees
incidence = 1.0 # degrees
aspect_ratio = 8.0
sweep = 20 # degrees
taper_ratio = 0.4
max_speed = 545 #kts
wing_type = "low"
mach_crit = 0.92
wing_thickness = 0.14
tau_w = 1


#calculate wing fuel volume
V_WF = 0.54((S**2)/b)(wing_thickness)((1+taper_ratio*tau_w**(0.5)+taper_ratio**2*tau_w)/(1+taper_ratio)**2)




########################## Chapter 7: Class I Method for Verifying Clean Airplane C_L_max and for Sizing High Lift Devices ##########################

# not in scope of midterm report






########################## Chapter 8: Class I Method for Empennage Sizing and Disposition and for Control Surface Sizing and Disposition ##########################









########################## Chapter 9: Class I Method for Landing Gear Sizing and Disposition ##########################







########################## Chapter 10: Class I Weight and Balance Analysis ##########################







########################## Chapter 11: Class I Method for Stability and Control Analysis ##########################







########################## Chapter 12: Class I Method for Drag Polar Determination ##########################