from pyvisa import pyvisa as visa
import numpy as np
from matplotlib import pyplot as plt
from time import sleep
from instruments.srs_sim928 import *



vsource = SIM928(4, 'GPIB0::4')
vsource.reset()
vsource.set_output(True)
R_gate = 100e3

