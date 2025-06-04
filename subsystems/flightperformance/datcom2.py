import os
from subprocess import Popen, PIPE


path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'datcom.out'))

with open(f"{path}\\datcom.out", "r") as f:
    data = f.readlines()


