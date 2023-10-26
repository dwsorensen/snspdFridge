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
from TimeTagger import setLogger, createTimeTagger, Combiner, Coincidence, Counter, Countrate
from TimeTagger import Correlation, TimeDifferences, TimeTagStream, Scope, Event, CHANNEL_UNUSED, UNKNOWN, LOW, HIGH, LOGGER_WARNING
from amcc.standard_measurements.parameterized import run_experiment, parameter_combinations

##% Close all open resources
rm = visa.ResourceManager()
print(rm.list_resources())
[i.close() for i in rm.list_opened_resources()]


try:
    tagger.reset()
except:
    pass
time.sleep(1)
tagger = createTimeTagger()

#%% Define our experiments
 

def experiment_counter(
vtrig,
count_time,
ibias,
rbias,
att_db,
delay,
port,
portmap = None,
**kwargs
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
    v1 = dmm.read_voltage(1)
    v2 = dmm.read_voltage(2)
    ibias_meas = (v1-v2)/rbias
    
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    data = dict(
        port = port,
        device = device,
        vbias = vbias,
        vbias_meas = v1,
        vdut = v2,
        rbias = rbias,
        ibias = ibias,
        ibias_meas = ibias_meas,
        counts = counts,
        vtrig = vtrig,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        **kwargs
    )

    return data


def experiment_timetagger_2ch(
vtrig,
count_time,
ibias,
rbias,
att_db,
dead_time,
delay,
**kwargs
):
    
    
    vbias = ibias*rbias
    vs.set_voltage(vbias)
    
    # Set trigger level -- Negative channel numbers indicated "falling" edge
    tagger.setTriggerLevel(1, vtrig)
    tagger.setTriggerLevel(-2, -vtrig)

    # Negative channel numbers indicated "falling" edge
    dead_time_ps = int(np.round(dead_time*1e12))
    tagger.setDeadtime(1, dead_time_ps)
    tagger.setDeadtime(-2, dead_time_ps)
    
    
    if att_db == np.inf:
        att.set_beam_block(True)
    else:
        att.set_beam_block(False)
        att.set_attenuation(att_db)
    time.sleep(delay)
    
    ## Get raw tags
    # stream = TimeTagStream(tagger, n_max_events=int(100e6), channels = [1, -2])
    # stream.startFor(count_time*1e12)
    # stream.waitUntilFinished(timeout=-1)
    # buffer = stream.getData()
    # timestamps = buffer.getTimestamps()
    # channels = buffer.getChannels()
    
    corr = Correlation(tagger, channel_1 = 1, channel_2 = -2, binwidth = 1, n_bins = 10000)
    corr.startFor(count_time*1e12)
    corr.waitUntilFinished(timeout=-1)
    bin_counts = corr.getData()
    bin_centers = corr.getIndex()
    
    v1 = dmm.read_voltage(1)
    v2 = dmm.read_voltage(2)
    ibias_meas = (v1-v2)/rbias
    
    counts = sum(bin_counts)
    
    data = dict(
        vbias = vbias,
        vbias_meas = v1,
        vdut = v2,
        rbias = rbias,
        ibias = ibias,
        ibias_meas = ibias_meas,
        counts = counts,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        vtrig1 = vtrig,
        vtrig2 = -vtrig,
        dead_time = dead_time,
        bin_counts = bin_counts,
        bin_centers = bin_centers,
        **kwargs
    )
    
    df = pd.DataFrame(data)

    return df




def experiment_timetagger_2ch_stream_temp(
vtrig,
count_time,
ibias,
rbias,
att_db,
dead_time,
delay,
**kwargs
):
    
    
    vbias = ibias*rbias
    vs.set_voltage(vbias)
    
    # Set trigger level -- Negative channel numbers indicated "falling" edge
    tagger.setTriggerLevel(1, vtrig)
    tagger.setTriggerLevel(-2, -vtrig)

    # Negative channel numbers indicated "falling" edge
    dead_time_ps = int(np.round(dead_time*1e12))
    tagger.setDeadtime(1, dead_time_ps)
    tagger.setDeadtime(-2, dead_time_ps)
    
    
    if att_db == np.inf:
        att.set_beam_block(True)
    else:
        att.set_beam_block(False)
        att.set_attenuation(att_db)
    time.sleep(delay)
    
    ## Get raw tags
    # stream = TimeTagStream(tagger, n_max_events=int(100e6), channels = [1, -2])
    # stream.startFor(count_time*1e12)
    # stream.waitUntilFinished(timeout=-1)
    # buffer = stream.getData()
    # timestamps = buffer.getTimestamps()
    # channels = buffer.getChannels()
    timestamps,channels = read_and_filter_timetags_from_stream(stream, trigger_channel = 1, duration = count_time)
    
    v1 = dmm.read_voltage(1)
    v2 = dmm.read_voltage(2)
    ibias_meas = (v1-v2)/rbias
    
    counts = sum(channels == 1)
    if counts == 0:
        timestamps = [0]
        channels = [0]
    
    data = dict(
        vbias = vbias,
        vbias_meas = v1,
        vdut = v2,
        rbias = rbias,
        ibias = ibias,
        ibias_meas = ibias_meas,
        counts = counts,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        vtrig1 = vtrig,
        vtrig2 = -vtrig,
        dead_time = dead_time,
        timestamps = np.array(timestamps, dtype = np.int64),
        channels = np.array(channels, dtype = np.int64),
        **kwargs
    )
    
    df = pd.DataFrame(data)

    return df



#================================================================
# IV Curves, Single and Steady State
#================================================================

def iv_sweep(
        port,
        t_delay,
        rbias,
        ibias,
        portmap = None,
        **kwargs,
        ):
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
        ibias_meas = (v1-v2)/rbias,
        vbias = vbias,
        vbias_meas = v1,
        vdut = v2,
        time = time.time(),
        **kwargs,
        )
    return data



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
 
# Setup switch
switch = Switchino('ASRL4::INSTR')

# # Set input delay
# tagger.setInputDelay(channel = 1, delay = 2.35e-9*1e12)
# tagger.setInputDelay(channel = 1, delay = 2.35e-9*1e12)
# tagger.setInputDelay(channel = 1, delay = 0)
# tagger.setInputDelay(channel = 1, delay = 0)

#%% Information about device

portmap = None
# portmap = {
#     1 : 'row3dev2',
#     2 : 'row3dev3',
#     3 : 'row3dev4',
#     4 : 'row3dev5',
#     5 : 'row3dev6',
#     6 : 'row3dev7',
#     7 : 'row3dev8',
#     8 : 'row3dev9',
#     }


additonal_info = {}
# additional_info = dict(
#     sample_name = 'TV4',
#     study = 14,
#     wafer = 20,
#     die_location = '(1,1)',
#     sub_die = 3,
#     )
additional_info = dict(
    sample_name = 'se075',
    # study = 14,
    wafer = 'CNSN08',
    die = 'A'
    # die_location = '(1,1)',
    # sub_die = 3,
    )



#%% IV Sweep

# Initial calculations
didt = 100e-9/100e-3 # Fix the ramp rate
dt = 500e-3 # Set the time between measurements to get `di`
i = np.arange(0, 8e-6, 0.1e-6)


# Set up experiment parameters
parameter_dict = dict(
    port =  None,
    rbias = 100e3,
    ibias = np.concatenate((i,i[::-1],-i,-i[::-1])),
    t_delay = dt,
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

parameter_dict = dict(
    att_db = 0,
    vtrig = 0.020,
    rbias = 200e3,
    dead_time = 500e-9,
    delay = 0.1,
    
    # count_time = 1,
    # ibias = -38e-6,
    
    # count_time = 100,
    # ibias = np.arange(3e-6,8e-6,0.02e-6),
    
    count_time = 100,
    ibias = np.linspace(-35e-6,-38.5e-6,9),
    
    # count_time = 100,
    # ibias = [5e-6,5.5e-6,6e-6,6.5e-6,7e-6],
    
    wavelength = 980,
    )

# Initialize
vs.set_voltage(0)
vs.set_output(True)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_timetagger_2ch,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S counts vs bias')
df.to_parquet(filename + '.parquet', compression='gzip')

# Reset things
vs.set_voltage(0)
att.set_beam_block(True)


# Create an only-counts dataframe by throwing away timestamps/channels
dfc = df.drop(columns = ['bin_counts','bin_centers']).drop_duplicates()

# Plot
fig, axs = plt.subplots(1,1,figsize = [8,5], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
ax = sub_plots[0]    # Choose which axis to plot in
if portmap is not None: device_str = f' ({portmap[port]})'
else: device_str = ''
for att_db, df3 in dfc.groupby('attenuation_db'):
    ax.plot(df3.ibias*1e6, df3.count_rate, '.-', label = f'att_db={att_db}') # Plot data
# ax.set_title(f'Port {port}{device_str}')
ax.set_xlabel('Current (uA)')
ax.set_ylabel('Count rate (1/s)')
ax.set_yscale('log')
ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename, dpi = 300)


ds_factor = 10

plt.figure()
for name,group in df.groupby('ibias'):
    x = np.array(group.bin_centers)
    y = np.array(group.bin_counts)
    x = np.mean(x.reshape(-1, ds_factor), 1)
    y = np.sum(y.reshape(-1, ds_factor), 1)
    plt.plot(x/1e3, y, label = f'Ibias = {name*1e6:0.1f} uA')
plt.legend()
plt.xlabel('Time differential (ns)')
plt.ylabel('Counts')
plt.savefig(filename + '2', dpi = 300)


parameter_dict = dict(
    att_db = 0,
    vtrig = 0.020,
    rbias = 200e3,
    dead_time = 500e-9,
    delay = 0.1,
    
    # count_time = 1,
    # ibias = -38e-6,
    
    count_time = 1,
    ibias = np.linspace(-32e-6,-39e-6,200),
    
    # count_time = 100,
    # ibias = np.linspace(-35e-6,-38.5e-6,9),
    
    # count_time = 100,
    # ibias = [5e-6,5.5e-6,6e-6,6.5e-6,7e-6],
    
    wavelength = 980,
    )

# Initialize
vs.set_voltage(0)
vs.set_output(True)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_timetagger_2ch,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S counts vs bias')
df.to_parquet(filename + '.parquet', compression='gzip')

# Reset things
vs.set_voltage(0)
att.set_beam_block(True)


# Create an only-counts dataframe by throwing away timestamps/channels
dfc = df.drop(columns = ['bin_counts','bin_centers']).drop_duplicates()

# Plot
fig, axs = plt.subplots(1,1,figsize = [8,5], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
ax = sub_plots[0]    # Choose which axis to plot in
if portmap is not None: device_str = f' ({portmap[port]})'
else: device_str = ''
for att_db, df3 in dfc.groupby('attenuation_db'):
    ax.plot(df3.ibias*1e6, df3.count_rate, '.-', label = f'att_db={att_db}') # Plot data
# ax.set_title(f'Port {port}{device_str}')
ax.set_xlabel('Current (uA)')
ax.set_ylabel('Count rate (1/s)')
ax.set_yscale('log')
ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename, dpi = 300)


ds_factor = 10

plt.figure()
for name,group in df.groupby('ibias'):
    x = np.array(group.bin_centers)
    y = np.array(group.bin_counts)
    x = np.mean(x.reshape(-1, ds_factor), 1)
    y = np.sum(y.reshape(-1, ds_factor), 1)
    plt.plot(x/1e3, y, label = f'Ibias = {name*1e6:0.1f} uA')
plt.legend()
plt.xlabel('Time differential (ns)')
plt.ylabel('Counts')
plt.savefig(filename + '2', dpi = 300)


#%% Pulsed laser setup

parameter_dict = dict(
    att_db = 0,
    vtrig = 0.020,
    rbias = 200e3,
    dead_time = 500e-9,
    delay = 0.1,
    
    # count_time = 600,
    # ibias = -38e-6,
    
    # count_time = 1,
    # ibias = np.arange(0e-6,8e-6,0.1e-6),
    
    count_time = 1,
    ibias = np.linspace(-34e-6,-38.5e-6,11),
    
    # count_time = 100,
    # ibias = [5e-6,5.5e-6,6e-6,6.5e-6,7e-6],
    
    wavelength = 635,
    )

# Initialize
vs.set_voltage(0)
vs.set_output(True)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_timetagger_2ch_stream_temp,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S counts vs bias')
df.to_parquet(filename + '.parquet', compression='gzip')

vs.set_voltage(-7.6)
#%% Trigger sweep

parameter_dict = dict(
    vtrig = np.linspace(0,200e-3,51),
    count_time = 0.2,
    ibias = [-32e-6,-34e-6,-36e-6,-38e-6,-40e-6,-42e-6],
    rbias = 20e3,
    att_db = np.inf,
    dead_time = 500e-9,
    delay = 0.1,
    wavelength = 370,
    )

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_timetagger_2ch,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S trigger sweep vs counts')
df.to_parquet(filename + '.parquet', compression='gzip')

plt.figure()
for name,df2 in df.groupby(['ibias']):
    plt.xlabel('Voltage (mV)')
    plt.ylabel('Count rate (1/s)')
    plt.semilogy(df2.vtrig1*1e3, df2.counts, label = name)
plt.legend()
plt.xlabel('Trigger level (mV)')
plt.ylabel('Counts')
plt.savefig(filename, dpi = 300)


#%% Optical attenuation vs counts

parameter_dict = dict(
    vtrig = 0.02,
    count_time = 1,
    ibias = [-34e-6,-36e-6,-38e-6],
    rbias = 200e3,
    att_db = np.linspace(0,20,21),
    dead_time = 500e-9,
    delay = 0.1,
    wavelength = 1550,
    )

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_timetagger_2ch,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S attenuation vs counts')
df.to_parquet(filename + '.parquet', compression='gzip')

plt.figure()
for name,df2 in df.groupby(['ibias']):
    plt.xlabel('Voltage (mV)')
    plt.ylabel('Count rate (1/s)')
    plt.semilogy(-df2.attenuation_db, df2.counts, label = name)
plt.legend()
plt.xlabel('Optical attenuation (dB)')
plt.ylabel('Counts')
plt.savefig(filename, dpi = 300)

#%%


import numpy as np
import time
from tqdm import tqdm
import datetime
import pyvisa as visa
import itertools
import pandas as pd
from matplotlib import pyplot as plt

def downsample_histogram(x,y, ds_factor):
    x = np.asarray(x)
    y = np.asarray(y)
    x = np.mean(x.reshape(-1, ds_factor), 1)
    y = np.sum(y.reshape(-1, ds_factor), 1)
    return x,y

df = pd.read_parquet(r'C:\Users\qittlab\2023-05-23 16-53-11 counts vs bias.parquet')
df = df[df.ibias==7e-6]

x,y = downsample_histogram(df.bin_centers,df.bin_counts, ds_factor = 10)
plt.plot(x/1e3,y/max(y))
plt.vlines(np.array(range(-10,10))*0.185, 0, 1, linestyles = ':')

#%% Cut bin histogram into segments
df = pd.read_parquet(r'C:\Users\qittlab\2023-05-24 13-38-13 counts vs bias.parquet')
plt.figure()
df['segments'] = pd.cut(df.bin_centers, bins = 25)
for name,df2 in df.groupby('segments'):
    # plt.plot(df2.bin_centers, df2.bin_counts)
    df3 = df2.groupby('ibias').sum()
    plt.plot(df3.index,df3.bin_counts, label = name)
plt.legend()

#%% Select a small area of the histogram to plot

# df = pd.read_parquet(r'C:\Users\qittlab\2023-05-24 04-45-39 counts vs bias.parquet')
plt.figure()
for bin_center_ps in [-2260,-2000,-1570]:
    # bin_center_ps = -700
    bin_span_ps = 100
    df2 = df[(df.bin_centers >= bin_center_ps-bin_span_ps/2) & (df.bin_centers <= bin_center_ps+bin_span_ps/2)]
    df3 = df2.groupby('ibias').sum()
    plt.plot(df3.index*1e6, df3.bin_counts, label = f'bin_center = {bin_center_ps/1e3:0.2f} ns')
plt.legend()


#%% Use basic counter

from amcc.standard_measurements.parameterized import experiment_counter


parameter_dict = dict(
    vs = vs,
    dmm = dmm,
    counter = counter,
    vtrig = 0.05,
    count_time = 0.5,
    ibias = np.linspace(0,15e-6,16),
    rbias = 100e3,
    delay = 0.1,
    # att_db = np.inf,
    # port = None,
    # att = None,
    # switch = None,
    # portmap = None,
    # v1_channel = 1,
    # v2_channel = 2,
    wavelength = 1550,
    )

# Initialize
vs.set_voltage(0)
vs.set_output(True)
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_counter,
    parameter_dict = parameter_dict,
    )

# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S counts vs bias')
df.to_parquet(filename + '.parquet', compression='gzip')

# Reset things
vs.set_voltage(0)
att.set_beam_block(True)


# Plot
fig, axs = plt.subplots(1,1,figsize = [8,5], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
ax = sub_plots[0]    # Choose which axis to plot in
if portmap is not None: device_str = f' ({portmap[port]})'
else: device_str = ''
for att_db, df3 in dfc.groupby('attenuation_db'):
    ax.plot(df3.ibias*1e6, df3.count_rate, '.-', label = f'att_db={att_db}') # Plot data
# ax.set_title(f'Port {port}{device_str}')
ax.set_xlabel('Current (uA)')
ax.set_ylabel('Count rate (1/s)')
ax.set_yscale('log')
ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename, dpi = 300)

#%%


df = pd.read_parquet(r'C:\Users\qittlab\2023-05-24 13-38-13 counts vs bias.parquet')
fig, ax = plt.subplots()
# ax.set_xscale('log')
dfp = df.pivot('bin_centers', 'ibias', 'bin_counts')
dfp = dfp.groupby(pd.cut(dfp.index, bins = 25)).sum()



df = pd.read_parquet(r'C:\Users\qittlab\2023-05-24 13-38-13 counts vs bias.parquet')
fig, ax = plt.subplots()
# ax.set_xscale('log')
dfp = df.pivot('bin_centers', 'ibias', 'bin_counts')
bin_ranges, bins = pd.cut(dfp.index, bins = 100, retbins = True)
dfp = dfp.groupby(bin_ranges).sum()


#X,Y = np.meshgrid()
im = ax.pcolor(dfp.columns*1e6, bins[:-1], np.log10(dfp))
fig.colorbar(im)
ax.set_xlabel('Current (uA)')
ax.set_ylabel('Count rate (1/s)')

df['segments'] = pd.cut(df.bin_centers, bins = 25)