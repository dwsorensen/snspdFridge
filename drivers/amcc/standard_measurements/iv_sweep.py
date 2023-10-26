

# Ic measurement code
# Run add_path.py first

from amcc.instruments.lecroy_620zi import LeCroy620Zi
from amcc.instruments.agilent_33250a import Agilent33250a
from amcc.instruments.keithley_2400 import Keithley2400
from amcc.instruments.srs_sim928 import SIM928
import pyvisa as visa
import numpy as np
import time
import datetime
from matplotlib import pyplot as plt
from scipy.optimize import fmin
import scipy.io
import pickle as pickle

def setup_iv_sweep(lecroy, awg, vpp = 1, repetition_hz = 100, trigger_level = 0, num_datapoints = 10e3, trigger_slope = 'Positive', max_sweeps = 10e3):

    # Setup frequency generator to have heartbeat shape for Ic sweeping --'\,---
    awg.set_load('INF')
    awg.setup_ramp(freq=repetition_hz, vpp=vpp, voffset=0, symmetry_percent = 50)
    awg.set_output(True)

    lecroy.set_display_gridmode(gridmode = 'Dual')
    lecroy.set_vertical_scale(channel = 'C1', volts_per_div = vpp/8.0)
    lecroy.set_vertical_scale(channel = 'C2', volts_per_div = vpp/8.0)
    lecroy.set_horizontal_scale(0.1/repetition_hz)
    lecroy.set_memory_samples(num_datapoints)

    lecroy.set_trigger(source = 'C1', volt_level = trigger_level, slope = trigger_slope)
    lecroy.set_trigger_mode(trigger_mode = 'Normal')
    lecroy.set_coupling(channel = 'C1', coupling = 'DC1M') # CH1 is input voltage readout
    lecroy.set_coupling(channel = 'C2', coupling = 'DC1M') # CH2 is channel voltage readout
    lecroy.set_bandwidth(channel = 'C1', bandwidth = '20MHz')
    lecroy.set_bandwidth(channel = 'C2', bandwidth = '20MHz')

    lecroy.setup_math_wf_average(math_channel = 'F1', source = 'C1', num_sweeps = max_sweeps)
    lecroy.setup_math_wf_average(math_channel = 'F2', source = 'C2', num_sweeps = max_sweeps)

    lecroy.label_channel(channel = 'C1', label = 'AWG input waveform')
    lecroy.label_channel(channel = 'C2', label = 'Device voltage')

def downsample_average(arr, n):
    end =  n * int(len(arr)/n)
    return numpy.mean(arr[:end].reshape(-1, n), 1)

def run_iv_sweeps(lecroy, num_sweeps = 100, R = 10e3, R_shunt = None, downsample = 1):
    V1_channel = 'F1'  # Voltage applied to resistor
    V2_channel = 'F2'  # Voltage on device

    time.sleep(0.01)
    lecroy.clear_sweeps()
    time.sleep(0.1)
    while (lecroy.get_num_sweeps(channel = V1_channel) < num_sweeps):
        time.sleep(0.1)
    lecroy.set_trigger_mode('Stop')
    time.sleep(0.1)
    t1, v1 = lecroy.get_wf_data(channel=V1_channel)
    t2, v2 = lecroy.get_wf_data(channel=V2_channel)
    lecroy.set_trigger_mode('Normal')

    V = v2
    I = (v1-v2)/R
    
    if R_shunt is not None:
        I_shunt = v2/R_shunt
        I = I - I_shunt
    if downsample > 1:
        V = downsample_average(V, downsample)
        I = downsample_average(I, downsample)
    return V,I

