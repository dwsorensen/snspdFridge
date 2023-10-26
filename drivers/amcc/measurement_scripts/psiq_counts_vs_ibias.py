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
from amcc.instruments.agilent_53131a import Agilent53131a
from amcc.instruments.switchino import Switchino
from amcc.instruments.jds_ha9 import JDSHA9
from amcc.instruments.srs_sim928 import SIM928
from amcc.instruments.srs_sim970 import SIM970
from matplotlib import pyplot as plt
from amcc.instruments.lecroy_620zi import LeCroy620Zi
from amcc.standard_measurements.parameterized import experiment_counter, run_experiment, experiment_iv_sweep

##% Close all open resources
rm = visa.ResourceManager()
print(rm.list_resources())
[i.close() for i in rm.list_opened_resources()]



#%% Setup instruments

#Lecroy scope
# lecroy_ip = '192.168.1.100'
# lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)

#Laser attenuator
att = JDSHA9('GPIB1::15::INSTR')
att.reset()
att.set_wavelength(1550)
att.set_beam_block(True)
att.set_attenuation(0)

# Setup counter
counter = Agilent53131a('GPIB1::7::INSTR')
counter.reset()
counter.set_impedance(ohms = 50)
counter.set_coupling(dc = True)
counter.setup_timed_count()
counter.set_trigger(trigger_voltage = 0.20, slope_positive = True, channel = 1)

# Setup voltage source
vs = SIM928('GPIB1::4::INSTR', 1)
dmm = SIM970('GPIB1::4::INSTR', 7)
vs.set_output(True)
vs.set_voltage(0)
dmm.set_range(autorange = False, voltage_max = 20, channel = 1)
dmm.set_range(autorange = False, voltage_max = 20, channel = 2)
# Setup switch
switch = Switchino('ASRL4::INSTR')


#%% Information about device

portmap = None
portmap = {
    1: '3.I.4',
    2: '3.I.9',
    3: '3.I.14',
    4: '3.I.19',
    5: '3.J.4',
    6: '3.J.9',
    7: '3.J.14',
    8: '3.J.19',
}


additonal_info = {}

additional_info = dict(
    #sample_name = 'se075',
    study = 'SCE-229' ,
    wafer = 20,
    #die = 'A'
    #die_location = '(1,1)',
    sub_die = 3,
    )



#%% IV Sweep

# Initial calculations
didt = 100e-9/100e-3 # Fix the ramp rate
dt = 200e-3 # Set the time between measurements to get `di`
i = np.arange(0, 16e-6, didt*dt)


# Set up experiment parameters
parameter_dict = dict(
    vs = vs,
    dmm = dmm,
    port =  [1,2,3,4,5,6,7,8],
    rbias = 20e3,
    ibias = np.concatenate((i,i[::-1],-i,-i[::-1])),
    delay = dt,
    portmap = portmap,
    **additional_info,
    )


# Initialization
att.set_beam_block(True)
vs.set_output(True); vs.set_voltage(0)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_iv_sweep,
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
    ax.plot(df2.vdut, df2.ibias*1e6, '.-') # Plot data
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
    vs = vs,
    dmm = dmm,
    counter = counter,
    att = att,
    #att_db = [0],
    att_db = [0,10,30,np.inf],
    #port =  [8],
    port =  [1,2,3,4,5,6,7,8],
    ibias =  np.linspace(0,16e-6,101), 
    vtrig = 30e-3,
    count_time = 0.5,
    rbias = 10e3,
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
        ax.plot(df3.ibias*1e6, df3.count_rate, '.-', label = f'att_db={att_db}') # Plot data
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
    vs = vs,
    dmm = dmm,
    counter = counter,
    att = att,
    #port = [1,2,3,4,5,6,7,8],
    port = [1],
    att_db = [0],
    ibias = 10e-6,
    vtrig = np.arange(0,200e-3,5e-3),
    count_time = 0.5,
    rbias = 10e3,
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
