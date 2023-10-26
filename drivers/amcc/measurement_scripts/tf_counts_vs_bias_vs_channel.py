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

# Close all open resources
rm = visa.ResourceManager()
print(rm.list_resources())
[i.close() for i in rm.list_opened_resources()]


def parameter_combinations(parameters_dict):
    for k,v in parameters_dict.items():
        try: v[0]
        except: parameters_dict[k] = [v]
        if type(v) is str:
            parameters_dict[k] = [v]
    value_combinations = list(itertools.product(*parameters_dict.values()))
    keys = list(parameters_dict.keys())
    return [{keys[n]:values[n] for n in range(len(keys))} for values in value_combinations]


def run_experiment(experiment_fun, parameter_dict, testname = 'Unnamed'):
    # Create combinations and manipulate them as needed
    parameter_dict_list = parameter_combinations(parameter_dict)
    
    # Run each parameter set as a separate experiment
    data_list = []
    for p_d in tqdm(parameter_dict_list):
        data_list.append(experiment_counter(**p_d))
    
    # Convert list of data-dictionaries to DataFrame
    df = pd.DataFrame(data_list)
    # Save data as CSV
    filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S SNSPD PID')
    df.to_csv(filename + '.csv')
    
    return df


#%% Define our experiments
 

def experiment_counter(
vtrig,
count_time,
ibias,
rbias,
att_db,
delay,
port,
):
    
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
    else:
        att.set_beam_block(False)
        att.set_attenuation(att_db)
    time.sleep(delay)

    counts = counter.timed_count(counting_time=count_time)
    
    data = dict(
        vbias = vbias,
        rbias = rbias,
        ibias = ibias,
        counts = counts,
        vtrig = vtrig,
        count_time = count_time,
        count_rate = counts/count_time,
        att_db = att_db,
        delay = delay,
        port = port,
    )

    return data




#%% Setup instruments

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
counter.set_trigger(trigger_voltage = 0.20, slope_positive = True, channel = 1)

# Setup voltage source
vs = SIM928('COM6', sim900port = 2)
dmm = SIM970('COM6', sim900port = 3)
vs.set_output(True)
vs.set_voltage(0)
 
# Setup switch
switch = Switchino('COM4')


#%% Trigger sweep


parameter_dict = dict(
    port = [1,2,3,4,5,6,7,8,9,10],
    att_db = 0,
    ibias = 9.2e-6,
    vtrig = np.arange(0,0.2,5e-3),
    count_time = 0.1,
    rbias = 10e3,
    delay = 0.1,
    # Variables closest to bottom change fastest!
)

df = run_experiment(
    experiment_fun = experiment_counter,
    parameter_dict = parameter_dict,
    testname = 'SNSPD trigger sweep'
    )


fig, axs = plt.subplots(2,5,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port in [1,2,3,4,5,6,7,8,9,10]:
    df2 = df[df.port == port] # Select only data from one port
    ax = sub_plots[port-1]    # Choose which axis to plot in
    ax.plot(df2.vtrig*1e3, df2.counts, '.-') # Plot data
    # ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title('Port %s' % port)
    ax.set_xlabel('Voltage (mV)')
    ax.set_ylabel('Counts')
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots


#%% Counts vs Ibias
parameter_dict = dict(
    # port = [1,2,3,4,5,6,7,8,9,10],
    port = [2,3,4],
    att_db = 0,
    ibias = np.linspace(0,15e-6,31),
    vtrig = 0.03,
    count_time = 0.25,
    rbias = 10e3,
    delay = 0.1,
)


df = run_experiment(
    experiment_fun = experiment_counter,
    parameter_dict = parameter_dict,
    testname = 'SNSPD counts vs bias'
    )


fig, axs = plt.subplots(2,5,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port in [1,2,3,4,5,6,7,8,9,10]:
    df2 = df[df.port == port] # Select only data from one port
    ax = sub_plots[port-1]    # Choose which axis to plot in
    ax.plot(df2.ibias*1e6, df2.counts, '.-') # Plot data
    # ax.set_xscale('log')
    # ax.set_yscale('log')
    ax.set_title('Port %s' % port)
    ax.set_xlabel('Current (uA)')
    ax.set_ylabel('Counts')
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
