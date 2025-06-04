import os
from subprocess import Popen, PIPE

path = os.path.dirname(os.path.abspath(__file__))

p = Popen(f'{path}\\datcom.exe', stdin=PIPE) #NOTE: no shell=True here
p.communicate(str.encode(f"{path}\\aeris.INP"))