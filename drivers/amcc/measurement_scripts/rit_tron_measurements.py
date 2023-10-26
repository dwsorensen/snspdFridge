# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 11:11:56 2023

@author: qittlab
"""
#%%
import numpy as np
from matplotlib import pyplot as plt
import pickle
import scipy
from scipy.signal import hilbert
from scipy.signal import gausspulse
from scipy.signal import hilbert
from scipy.signal import gausspulse
from scipy.signal import butter, filtfilt
from scipy.signal import freqs
import sys
import pandas as pd
import time
from tqdm import tqdm
import datetime

#NEcessary instruments, ie scope and AWG
import pyvisa as visa
from amcc.instruments.tektronix_awg610 import TektronixAWG610
from amcc.instruments.lecroy_620zi import LeCroy620Zi
 
#%% Setup TektronixAWG520 + Lecroy for measurement
awgw = TektronixAWG610('GPIB0::23::INSTR')
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % '192.168.1.100')

# Setup scope - CH1 = carrier pulse, CH2 = marker trigger
lecroy.reset()
lecroy.set_coupling(channel = 'C1', coupling = 'DC1M') 
lecroy.set_coupling(channel = 'C2', coupling = 'DC1M')
lecroy.set_coupling(channel = 'C3', coupling = 'DC1M') 
lecroy.set_coupling(channel = 'C4', coupling = 'DC1M')
lecroy.set_bandwidth(channel = 'C1', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C2', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C3', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C4', bandwidth = '20MHz')
lecroy.set_trigger_mode(trigger_mode = 'Normal')
lecroy.set_display_gridmode(gridmode = 'Dual')
lecroy.set_trigger(source = 'C1', volt_level = 0.05)
lecroy.set_vertical_scale(channel = 'C1', volts_per_div = 0.1)
lecroy.set_vertical_scale(channel = 'C2', volts_per_div = 0.5)
lecroy.set_horizontal_scale(1e-6)

# lecroy.setup_math_wf_average(math_channel = 'F1', source = 'C1', num_sweeps = 10000)
t = [0,.5,.75,1]
v = [0,0,1,0]
gate_data = np.interp(np.linspace(0,1,4096), t, v)
t = [0,0.25,.5,.75,1]
v = [0,0,1,1,0]
channel_data = np.interp(np.linspace(0,1,4096), t, v)
marker_data = np.zeros_like(channel_data)
marker_data[int(len(channel_data)/2):] = 1
plt.plot(channel_data)
plt.plot(gate_data)
plt.plot(marker_data)

awgw.create_waveform(voltages = channel_data.tolist(), filename = 'temp1.wfm', clock = 1e6, marker1_data = marker_data.tolist(), auto_fix_sample_length = True, normalize_voltages=True)
awgw.create_waveform(voltages = gate_data.tolist(), filename = 'temp2.wfm', clock = 1e6, marker1_data = marker_data.tolist(), auto_fix_sample_length = True, normalize_voltages=True)

awgw.load_file('temp1.wfm', channel = 1)
awgw.load_file('temp2.wfm', channel = 2)
awgw.set_clock(1e5)
awgw.set_vhighlow(vlow = 0, vhigh = 0.2, channel = 1)
awgw.set_vhighlow(vlow = 0, vhigh = 0.5, channel = 2)
lecroy.set_memory_samples(num_samples = 100e3)
# awgw.set_trigger_mode(continuous_mode=True)
awgw.set_trigger_mode(trigger_mode=True)
awgw.set_trigger_source(internal=True, internal_interval=50e-3)
awgw.set_output(True)

#%% Quick sample mode changes
lecroy.set_sample_mode(sequence = True, num_segments = 1000)
lecroy.set_sample_mode(sequence = True, num_segments = 10)
lecroy.set_sample_mode(sequence = False)
lecroy.set_trigger_mode('Normal')

#%% Quick scale adjustment
lecroy.find_vertical_scale(channel = 'C1')
lecroy.find_vertical_scale(channel = 'C2')
lecroy.find_vertical_scale(channel = 'C3')
lecroy.find_vertical_scale(channel = 'C4')

#%%
def downsample_and_average(arr, n):
    end =  n * int(len(arr)/n)
    return np.mean(arr[:end].reshape(-1, n), 1)

#%%
Rbias = 10e3
Rgate = 100e3
Rload = 50
Igate_max = 3e-6
downsample = 40

lecroy.set_sample_mode(sequence = True, num_segments = 100)
Ibias_list = [0,5e-6,10e-6,15e-6,20e-6,25e-6,30e-6,35e-6]
# Ibias_list = [35e-6]
data_list = []

for Ibias in tqdm(Ibias_list):
    
    # Set channel bias level
    awgw.set_vhighlow(vlow = 0, vhigh = Ibias*Rbias/2, channel = 1)
    
    # Set gate sweep maximum
    awgw.set_vhighlow(vlow = 0, vhigh = Igate_max*Rgate/2, channel = 2)
    
    # Get data
    time.sleep(0.5)
    lecroy.clear_sweeps()
    lecroy.set_trigger_mode('Single')
    while lecroy.get_trigger_mode() == 'Single':
        time.sleep(0.5)
    t1,v1 = lecroy.get_wf_data(channel = 'C1', downsample = downsample)
    t2,v2 = lecroy.get_wf_data(channel = 'C2', downsample = downsample)
    t3,v3 = lecroy.get_wf_data(channel = 'C3', downsample = downsample)
    t4,v4 = lecroy.get_wf_data(channel = 'C4', downsample = downsample)
    
    data = dict(
            Ibias = Ibias,
            Rbias = Rbias,
            Rgate = Rgate,
            Rload = Rload,
            t1 = t1,
            v1 = v1,
            t2 = t2,
            v2 = v2,
            t3 = t3,
            v3 = v3,
            t4 = t4,
            v4 = v4,
            )
    data_list.append(data)


filename = datetime.datetime.now().strftime(f'%Y-%m-%d %H-%M-%S tron measurements - Rload={Rload:.1e} Ohm')
pickle.dump({'data':data_list}, open(filename + '.pickle', 'wb'))
# pickle.dump(fig, open(filename + '.fig.pickle', 'wb'))

#%%
n = 1
plt.plot(t1[n],v1[n])
plt.plot(t2[n],v2[n])
plt.plot(t3[n],v3[n])
plt.plot(t4[n],v4[n])
plt.legend(['v1 (~Ibias)', 'v2 (~Igate)','v3 (Vchannel)','v4 (Vgate)',])
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')

#%%

for n in range(100): plt.plot(data[5]['t4'][n], data[5]['v4'][n])
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')


#%% Example code for loading
import pickle
from matplotlib import pyplot as plt

with open("2023-01-06 15-13-51 tron measurements - Rload=1e6 Ohm.pickle", "rb") as input_file:
    data = pickle.load(input_file)['data']

# Each of the 8 elements of the `data` list correspond to a different Ibias value
# corresponding to [0,5e-6,10e-6,15e-6,20e-6,25e-6,30e-6,35e-6] amps of current
# So to select IB=10uA, we do

data_IB_10uA = data[2]
v3 = data_IB_10uA['v3'] # 100x traces of v3 voltage
t3 = data_IB_10uA['t3'] # 100x traces of v3 time
for n in range(100):
    plt.plot(t3[n],v3[n])