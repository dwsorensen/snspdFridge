#%%============================================================================
# Instrument setup
#==============================================================================
import numpy as np
import time
from tqdm import tqdm
import datetime
import pyvisa as visa
import itertools
import pandas as pd
from amcc.instruments.agilent_81567 import Agilent81567
from amcc.instruments.agilent_53131a import Agilent53131a
from amcc.instruments.switchino import Switchino
from amcc.instruments.jds_ha9 import JDSHA9
from amcc.instruments.srs_sim928 import SIM928
from amcc.instruments.srs_sim970 import SIM970
from matplotlib import pyplot as plt
from amcc.instruments.lecroy_620zi import LeCroy620Zi

##% Close all open resources
rm = visa.ResourceManager()
print(rm.list_resources())
[i.close() for i in rm.list_opened_resources()]

# COnnect to PPMS python interface
import os
import sys
dll_path = os.path.dirname(r'C:\Users\vacnt\PPMS_python_field\PPMS_control _path\\')
sys.path.append(dll_path)
from amcc.instruments.qdinstrument import QdInstrument
ppms = QdInstrument('DynaCool', '0.0.0.0', remote = False)


def parameter_combinations(parameters_dict):
    for k,v in parameters_dict.items():
        try: v[0]
        except: parameters_dict[k] = [v]
        if type(v) is str:
            parameters_dict[k] = [v]
    value_combinations = list(itertools.product(*parameters_dict.values()))
    keys = list(parameters_dict.keys())
    return [{keys[n]:values[n] for n in range(len(keys))} for values in value_combinations]


def run_experiment(experiment_fun, parameter_dict):
    # Create combinations and manipulate them as needed
    parameter_dict_list = parameter_combinations(parameter_dict)
    
    # Run each parameter set as a separate experiment
    data_list = []
    for p_d in tqdm(parameter_dict_list):
        data_list.append(experiment_fun(**p_d))
    
    # Convert list of data-dictionaries to DataFrame
    df = pd.DataFrame(data_list)
    return df


#%% Define our experiments
 
def set_temperature_ppms(temperature):
    current_temp = ppms.getTemperature()[1]
    if abs(temperature - current_temp) > 25e-3: # if not close in temperature
        ppms.setTemperature(temperature, rate = 10)
        time.sleep(10)
        while ppms.getTemperature()[2] != 1: # when == 1, the temperature is "stable" in DynaCool
            time.sleep(0.5)
        print(f'Temperature set to {temperature:0.2f}K, now at {ppms.getTemperature()[1]:0.2f}K')
        current_temp = ppms.getTemperature()[1]
    return current_temp


def experiment_counter(
    vtrig,
    count_time,
    ibias,
    rbias,
    att_db,
    delay,
    port,
    temperature,
    portmap = None,
    **kwargs
    ):
    current_temp = set_temperature_ppms(temperature)
    
    if port != switch.get_current_port():
        vs.set_voltage(0)
        vs.set_output(True)
        switch.select_port(port)
        time.sleep(0.25)
    
    vbias = ibias*rbias
    vs.set_voltage(vbias)
    counter.set_trigger(trigger_voltage = vtrig, slope_positive = (vtrig>0), channel = 1)
    
    if att_db == np.inf:
        att.set_beam_block(True)
        att_db = 9999
    else:
        att.set_beam_block(False)
        att.set_attenuation(att_db)
    time.sleep(delay)

    counts = counter.timed_count(counting_time=count_time)
    v1 = dmm.read_voltage(1)
    v2 = dmm.read_voltage(2)
    ibias_meas = (v1-v2)/rbias
    
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    data = dict(
        port = port,
        device = device,
        voltage_source_V = vbias,
        voltage_source_applied_V = v1,
        voltage_snspd_measure_V = v2,
        rbias = rbias,
        ibias_nominal = ibias,
        ibias_meas = ibias_meas,
        counts = counts,
        vtrig = vtrig,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        temperature = current_temp,
        **kwargs
    )

    return data

#================================================================
# IV Curves, Single and Steady State
#================================================================

def iv_sweep(
        port,
        t_delay,
        rbias,
        ibias,
        temperature,
        portmap = None,
        **kwargs,
        ):
    
    current_temp = set_temperature_ppms(temperature)
    
    #select port first
    if switch.get_current_port(switch = 1) != port:
        switch.select_port(port = port, switch = 1)
        vs.set_voltage(0)
        time.sleep(1)
        
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    # set voltage, wait t_delay, then take measurement
    vbias = rbias*ibias
    vs.set_voltage(vbias)
    time.sleep(t_delay)
    v1 = dmm.read_voltage(channel = 1)
    v2 = dmm.read_voltage(channel = 2)
    
    data = dict(
        port = port,
        device = device,
        rbias = rbias,
        ibias = ibias,
        voltage_source_V = vbias,
        voltage_source_applied_V = v1,
        voltage_snspd_measure_V = v2,
        current_measure_A = (v1-v2)/rbias,
        time = time.time(),
        temperature = current_temp,
        **kwargs,
        )
    return data

#%% Setup instruments

# #Lecroy scope
# lecroy_ip = '192.168.1.100'
# lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)

#Laser attenuator
att = JDSHA9('GPIB0::11::INSTR')
att.reset()
att.set_wavelength(1550)
att.set_beam_block(True)
att.set_attenuation(0)

# Setup counter
counter = Agilent53131a('GPIB0::12::INSTR')
counter.reset()
counter.set_impedance(ohms = 50)
counter.set_coupling(dc = True)
counter.setup_timed_count()
counter.set_trigger(trigger_voltage = 0.05, slope_positive = True, channel = 1)

# Setup voltage source
vs = SIM928('GPIB0::15::INSTR', 1)
dmm = SIM970('GPIB0::15::INSTR', 7)
vs.set_output(True)
vs.set_voltage(0)
dmm.set_range(autorange = False, voltage_max = 20, channel = 1)
dmm.set_range(autorange = False, voltage_max = 20, channel = 2)
 
# Setup switch
switch = Switchino('ASRL4::INSTR')


#%% Information about device

portmap = None
portmap = {
    1 : '4.A.3',
    2 : '4.A.6',
    3 : '4.A.9',
    4 : '4.A.12',
    5 : '4.B.3',
    6 : '4.B.6',
    7 : '4.B.9',
    8 : '4.B.12',
    }


additonal_info = {}
additional_info = dict(
    sample_name = 'TV5.2',
    study = 'SCE-219',
    wafer = 16,
    # die_location = '(1,1)',
    sub_die = 4,
    wavelength = 1550,
    )



#%% IV Sweep

# Initial calculations
didt = 100e-9/100e-3 # Fix the ramp rate
dt = 200e-3 # Set the time between measurements to get `di`
i = np.arange(0, 15e-6, didt*dt)


# Set up experiment parameters
parameter_dict = dict(
    temperature = [2,2.5,3,3.5],
    port =  [1,2,3,4,5,6,7,8],
    rbias = 100e3,
    ibias = i,#np.concatenate((i,i[::-1],-i,-i[::-1])),
    t_delay = dt,
    portmap = portmap,
    **additional_info,
    )


# Initialization
att.set_beam_block(True)
vs.set_output(True); vs.set_voltage(0)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = iv_sweep,
    parameter_dict = parameter_dict,
    )


# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S IV curves')
df.to_csv(filename +  '.csv')


# Plot
fig, axs = plt.subplots(2,4,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    ax.plot(df2.voltage_snspd_measure_V, df2.current_measure_A*1e6, '.-') # Plot data
    if portmap is not None: device_str = f' ({portmap[port]})'
    else: device_str = ''
    ax.set_title(f'Port {port}{device_str}')
    ax.set_xlabel('Voltage (mV)')
    ax.set_ylabel('Ibias (uA)')
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename, dpi = 300)

# Reset things
vs.set_voltage(0)


#%% Counts vs Ibias

# Set up experiment parameters
parameter_dict = dict(
    temperature = [3.5,2.5,3,3.5],
    att_db = [0,10,20,30,np.inf],
    port =  [1,2,3,4,5,6,7,8],
    ibias =  np.linspace(0,15e-6,401), 
    vtrig = 25e-3,
    count_time = 0.5,
    rbias = 100e3,
    delay = 0.1,
    portmap = portmap,
    **additional_info,
)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_counter,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S counts vs bias')
df.to_csv(filename +  '.csv')

# Plot
fig, axs = plt.subplots(2,4,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    if portmap is not None: device_str = f' ({portmap[port]})'
    else: device_str = ''
    for att_db, df3 in df2.groupby('attenuation_db'):
        ax.plot(df3.ibias_nominal*1e6, df3.count_rate, '.-', label = f'att_db={att_db}') # Plot data
    ax.set_title(f'Port {port}{device_str}')
    ax.set_xlabel('Current (uA)')
    ax.set_ylabel('Count rate (1/s)')
    ax.set_yscale('log')
    ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename, dpi = 300)

# Reset things
vs.set_voltage(0)


#%% Trigger sweep

parameter_dict = dict(
    temperature = 3.5,
    port = [1,2,3,4,5,6,7,8],
    att_db = np.inf,
    ibias = 0e-6,
    vtrig = np.arange(0,100e-3,5e-3),
    count_time = 0.5,
    rbias = 100e3,
    delay = 0.1,
    # Variables closest to bottom change fastest!
)

# Initialization
vs.set_output(True); vs.set_voltage(0)
time.sleep(0.5)

# Run experiment
df = run_experiment(
    experiment_fun = experiment_counter,
    parameter_dict = parameter_dict
    )


fig, axs = plt.subplots(2,4,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    ax.plot(df2.vtrig*1e3, df2.count_rate, '.-') # Plot data
    # ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title('Port %s' % port)
    ax.set_xlabel('Voltage (mV)')
    ax.set_ylabel('Count rate (1/s)')
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S SNSPD TV4')
plt.savefig(filename + '.png', dpi = 300)
