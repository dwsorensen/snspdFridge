# Change Spyder directory to C:\Users\vacnt\National Institute of Standards and Technology (NIST)\Sources and Detectors - Documents\CNT\code\labview\PPMS
import os
import sys
import time
import pandas as pd
from tqdm import tqdm
import datetime
from amcc.instruments.switchino import Switchino
from matplotlib import pyplot as plt
import numpy as np
from amcc.instruments.srs_sim970 import SIM970
from amcc.instruments.srs_sim928 import SIM928
import pyvisa as visa
#%%
# Close all open resources
rm = visa.ResourceManager() #closing with fresh kernel does not work and messes up connections
[i.close() for i in rm.list_opened_resources()]

#%% COnnect to PPMS python interface
dll_path = os.path.dirname(r'C:\Users\vacnt\PPMS_python_field\PPMS_control _path\\')
sys.path.append(dll_path)
from amcc.instruments.qdinstrument import QdInstrument
ppms = QdInstrument('DynaCool', '0.0.0.0', remote = False)


#%%Connect to electronics
vs = SIM928('ASRL10::INSTR', 2)
dmm = SIM970('ASRL10::INSTR', 3)
switch = Switchino('COM4')
#%%

dmm.set_impedance(gigaohm=False, channel = 1)
dmm.set_impedance(gigaohm=False, channel = 2)

def experiment_get_R_dut():
    v1 = dmm.read_voltage(channel = 1)
    v2 = dmm.read_voltage(channel = 2)
    i = (v1-v2)/R_series   
    try:
        R_dut = v2/i
    except ZeroDivisionError: #since if divide by zero occurs stops the whole script
        R_dut = np.nan   
    T = ppms.getTemperature()[1]
    data = dict(
        T = T,
        ibias = i,
        R_dut = R_dut,
        v1 = v1,
        v2 = v2,
        t = time.time()-time_start
        )
    return data

def experiment_get_R_dut_field():
    v1 = dmm.read_voltage(channel = 1)
    v2 = dmm.read_voltage(channel = 2)
    i = (v1-v2)/R_series
    try:
        R_dut = v2/i
    except ZeroDivisionError:
        R_dut = np.nan
    field = ppms.getField()[1]
    data = dict(
        T = T,
        field = field,
        R_dut = R_dut,
        v1 = v1,
        v2 = v2,
        t = time.time()-time_start
        )
    return data

def experiment_get_R_dut_4_probe_field():
    v1 = dmm.read_voltage(channel = 1)
    v2 = dmm.read_voltage(channel = 2)
    i = V/R_series
    try:
        R_dut = v2/i
    except ZeroDivisionError:
        R_dut = np.nan
    field = ppms.getField()[1]
    data = dict(
        T = T,
        field = field,
        R_dut = R_dut,
        v1 = v1,
        v2 = v2,
        t = time.time()-time_start
        )
    return data


#%% Run experiment for Tc check
vs.set_output(True)
V = 0.01
vs.set_voltage(V)
R_series = 100e3
target_temps = [2.5, 15, 2.5]
rate_K_per_min = 1
ports= [2]  # [3,6,10]
# Intialize variables
for port in ports:
    switch.select_port(port, switch = 1)
    time_start = time.time()
    data_list = []; n = 0; T = -1e9
    for n,target in enumerate(target_temps):
            ppms.setTemperature(target, rate_K_per_min)
            while abs(T-target) > 0.05:
                data = experiment_get_R_dut()
                data['step'] = n
                T = data['T']
                data_list.append(data)
                time.sleep(0.1)
    
    
    df = pd.DataFrame(data_list) 
    filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S Tc check' +str(port))
    df.to_csv(filename+'.csv')

    plt.figure()
    plt.plot(df['T'],df['R_dut'], marker = '.', label = port)
    plt.legend()
    plt.xlabel('Temp (K)')
    plt.ylabel('Resistance (Ohm)')
    plt.savefig(filename +'.png', dpi = 300)
    time.sleep(5)
    
    #set back to 2 k when finished
    # ppms.setTemperature(1.7,50)
    target = 300
    ppms.setTemperature(target,50)
    #time.sleep(0.5)
    #T = ppms.getTemperature()[1]
        
    #while abs(T-target) > 0.01:  
    #    T = ppms.getTemperature()[1]
    #    time.sleep(2)
    
vs.set_voltage(0)


#%%


#%%Tc check at different fields for critical field extraction, R vs T at fixed field
fields = [1.5e4,2e4,2.5e4,3e4, 3.5e4, 4e4, 4.5e4, 5e4, 6e4, 7e4, 8e4, 9e4,0]

for field in fields:
    
    ppms.setField(field,100)
    time.sleep(3)
    f = ppms.getField()[1]
    
    while abs(field-f) > 10: #Wait for field to settle before taking data
        f = ppms.getField()[1]
        print('not ready')
        time.sleep(5)
        
    #set bias/ temperature conditions
    V = 0.1
    vs.set_voltage(V)
    R_series = 10e3
    target_temps = [1.7,5]
    rate_K_per_min = 0.5
    ports= [1]  # [3,6,10]
    
    #Start temp sweep, this only collects points in up ramp!
    for port in ports:
        switch.select_port(port, switch = 1)
        time_start = time.time()
        data_list = []; n = 0; T = -1e9
        for n,target in enumerate(target_temps):
                ppms.setTemperature(target, rate_K_per_min)
                while abs(T-target) > 0.01:
                    data = experiment_get_R_dut()
                    data['step'] = n
                    T = data['T']
                    data_list.append(data)
                    time.sleep(0.1)
        
        
        df = pd.DataFrame(data_list) 
        filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S WSi Tc check_' +str(field)+'Oe')
        df.to_csv(filename+'.csv')
    
        plt.figure()
        plt.plot(df['T'],df['R_dut'], marker = '.', label = port)
        plt.legend()
        plt.xlabel('Temp (K)')
        plt.ylabel('Resistance (Ohm)')
        plt.savefig(filename +'.png', dpi = 300)
       
        time.sleep(5)
        
    vs.set_voltage(0)
    #After sweep is done go back to 1.7 K
    time.sleep(5)
    ppms.setTemperature(1.7,50)
    time.sleep(10)
    
    T = ppms.getTemperature()[1]
    target = 1.7
    
    while abs(T-target) > 0.01: 
        T = ppms.getTemperature()[1]
        print('not ready')
        time.sleep(1)
    print('ready!')

# When done set bias to zero and ramp back up to 300 k/ set field back to 0
vs.set_voltage(0)
ppms.setField(0,100)
ppms.setTemperature(300, 50)

         
#%% Run experiment for Hc check
V = 1
vs.set_voltage(V)
R_series = 97e3
target_field = [0,6e4,0]
rate_oe_per_sec = 220
T = ppms.getTemperature()[1]
#ports=[10]
# Intialize variables
#for port in ports:
#switch.select_port(port, switch = 1)
time_start = time.time()
data_list = []; n = 0; field = 0
for n,target in enumerate(target_field):
        ppms.setField(target, rate_oe_per_sec)
        while abs(field-target) > 10:
            data = experiment_get_R_dut_field()
            data['step'] = n
            field = data['field']
            data_list.append(data)
            time.sleep(0.1)
vs.set_voltage(0)
#%%
df = pd.DataFrame(data_list) 
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S Hc2 check_N8')
df.to_csv(filename+'.csv')
plt.figure()
plt.plot(df['field'],df['R_dut'], marker = '.', label = 'N8')
plt.legend()
plt.xlabel('Field (Oe)')
plt.ylabel('Resistance (ohm)')
plt.savefig(filename +'.png')
#%% Run experiment for critical field 4 probe
V = 1
vs.set_voltage(V)
R_series = 97e3
target_field = [0,6e4,0]
rate_oersted_per_sec = 220
T = ppms.getTemperature()[1]
#ports=[10]
# Intialize variables
#for port in ports:
#switch.select_port(port, switch = 1)
time_start = time.time()
data_list = []; n = 0; field = 0
for n,target in enumerate(target_field):
        ppms.setField(target, rate_oersted_per_sec)
     
        while abs(field-target) > 10:
            data = experiment_get_R_dut_4_probe_field()
            data['step'] = n
            field = data['field']
            data_list.append(data)
            time.sleep(0.1)
vs.set_voltage(0)

df = pd.DataFrame(data_list) 
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S Hc check_N8')
df.to_csv(filename+'.csv')
plt.figure()
plt.plot(df['field'],df['R_dut'], marker = '.', label = 'S8')
plt.legend()
plt.xlabel('Field (Oe)')
plt.ylabel('Resistance (Ohm)')
plt.savefig(filename +'.png')


#%%
fig, axs = plt.subplots(2,1, sharex = True)
axs[0].semilogy(df.t, df['T'], label = 'PPMS internal sensor')
axs[0].semilogy(df.t,  lakeshore_rx102a_thermometer(df.R_dut), label = 'RX-102A probe')
axs[0].legend()
# axs[0].xlabel('Time (s)')
axs[0].set_ylabel('Temp (K)')
axs[1].plot(df.t,  df['T']- lakeshore_rx102a_thermometer(df.R_dut), label = 'Difference')
axs[1].legend()
axs[1].set_xlabel('Time (s)')
axs[1].set_ylabel('Difference in temp (K)')