import os
from subprocess import Popen, PIPE

p = Popen('C:\\Users\\Luuk\\Documents\\DSEGITHUB\\DSEGroup17\\subsystems\\flightperformance\\datcom.exe', stdin=PIPE) #NOTE: no shell=True here
#p.communicate(os.linesep.join(["aeris.INP"]))