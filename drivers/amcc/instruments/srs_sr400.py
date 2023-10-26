import pyvisa as visa
import numpy as np
from time import sleep
from matplotlib import pyplot as plt

class SR400(object):
    """Python class for SRS counter, written by Adam McCaughan
    Use like c = SR400('GPIB0::3')"""
    
    