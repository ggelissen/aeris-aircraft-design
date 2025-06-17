
# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *



VA_EAS = 81.137
VA_TAS = equivalent_to_true_air_speed(VA_EAS, 0.3059685, 1.225)
print(VA_TAS)
VA_EAS =  63.159
VA_TAS = equivalent_to_true_air_speed(VA_EAS, 0.3059685, 1.225)
print(VA_TAS)



