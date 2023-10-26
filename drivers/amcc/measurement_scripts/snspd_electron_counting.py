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

from amcc.standard_measurements.parameterized_measurements import run_experiment, experiment_counter, experiment_iv_sweep



#%%

# Create instruments
vs_snspd = SIM928('ASRL10::INSTR', 1)
vs_tunnel = SIM928('ASRL10::INSTR', 4)
dmm = SIM970('ASRL10::INSTR', 7)
counter = Agilent53131a('GPIB0::7::INSTR')
switch = Switchino('ASRL11::INSTR')

# Initalize instruments
vs_snspd.set_voltage(0)
vs_snspd.set_output(True)
vs_tunnel.set_voltage(0)
vs_tunnel.set_output(True)
dmm.set_impedance(gigaohm=True, channel = 3)
dmm.set_impedance(gigaohm=True, channel = 4)

# Setup counter for reading
counter.reset()
counter.set_impedance(ohms = 50)
counter.set_coupling(dc = True)
counter.setup_timed_count()
counter.set_trigger(trigger_voltage = 0.20, slope_positive = True, channel = 1)

#%%
self.write('CONN %d,"xyz"' % 7)
self.query('DVDR? %s' % 4)
self.write('xyz')
#%% IV Sweep
rbias = 10e6
portmap = None
vs = vs_tunnel

# Vibiasing
vbias = np.linspace(0,0.2,31)
i = vbias/rbias
# ibias = np.concatenate((i,i[::-1],-i,-i[::-1]))
ibias = i

# # I-biasing
# i = np.arange(0, 20e-6, 1e-6)
# ibias = np.concatenate((i,i[::-1],-i,-i[::-1]))

# Set up experiment parameters
parameter_dict = dict(
    vs = vs,
    dmm = dmm,
    rbias = rbias,
    ibias = ibias,
    delay = 0.5,
    v1_channel = 1,
    v2_channel = 2,
    # vdiff_channel = 3,
    )


# # Initialization
# att.set_beam_block(True)
vs.set_voltage(0); vs.set_output(True);
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
fig, axs = plt.subplots(1,1,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    ax.plot(df2.vdut*1e3, df2.ibias_measured*1e6, '.-') # Plot data
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


R, voffset = np.polyfit(df.ibias_measured,df.vdut, deg = 1)
print(f'R = {R:0.1f}')
#%%

def experiment_electron_counting(
    vs_snspd,
    vs_tunnel,
    dmm,
    counter,
    vtrig,
    count_time,
    ibias,
    vbias_tunnel,
    rbias,
    rbias_tunnel,
    delay,
    att_db = np.inf,
    port = None,
    att = None,
    switch = None,
    **kwargs
    ):
        
    if (switch is not None) and (port != switch.get_current_port()):
        vs_snspd.set_voltage(0)
        vs_snspd.set_output(True)
        switch.select_port(port)
        time.sleep(0.25)
    
    vbias = ibias*rbias
    vs_snspd.set_voltage(vbias)
    vs_tunnel.set_voltage(vbias_tunnel)
    if (ibias>0): vtrig = np.abs(vtrig)
    else:         vtrig = -np.abs(vtrig)
    counter.set_trigger(trigger_voltage = vtrig, slope_positive = (vtrig>0), channel = 1)
    
    if att is not None:
        if att_db == np.inf:
            att.set_beam_block(True)
        else:
            att.set_beam_block(False)
            att.set_attenuation(att_db)
    time.sleep(delay)

    counts = counter.timed_count(counting_time=count_time)
    v1 = dmm.read_voltage(1)
    v2 = dmm.read_voltage(2)
    v3 = dmm.read_voltage(3)
    v4 = dmm.read_voltage(4)
    ibias_measured = (v1-v2)/rbias
    itunnel_measured = (v3-v4)/rbias_tunnel
    
    data = dict(
        port = port,
        vbias = vbias,
        vbias_tunnel = vbias_tunnel,
        vbias_measured = v1,
        vsnspd = v2,
        vbias_tunnel_measured = v3,
        vtunnel_measured = v4,
        rbias = rbias,
        ibias = ibias,
        ibias_measured = ibias_measured,
        itunnel_measured = itunnel_measured,
        vtrig = vtrig,
        counts = counts,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        **kwargs
    )

    return data


portmap = None

# Set up experiment parameters
parameter_dict = dict(
    vs_snspd = vs_snspd,
    vs_tunnel = vs_tunnel,
    dmm = dmm,
    counter = counter,
    port = 1,
    vtrig = 100e-3,
    count_time = 1,
    ibias = np.linspace(0,30e-6,101),
    vbias_tunnel = 0, #np.linspace(-3,-4,101),
    rbias = 100e3,
    rbias_tunnel = 378e3,
    delay = 0.1,
    )


# # Initialization
# att.set_beam_block(True)
vs_snspd.set_voltage(0); vs_snspd.set_output(True);
vs_tunnel.set_voltage(0); vs_tunnel.set_output(True);
time.sleep(0.5)

# Run the experiment
df = run_experiment(
    experiment_fun = experiment_electron_counting,
    parameter_dict = parameter_dict,
    )


# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S electron counting')
df.to_csv(filename +  '.csv')

# Finalize
vs_snspd.set_voltage(0)
vs_tunnel.set_voltage(0)

#%% Plot counts vs bias
fig, axs = plt.subplots(1,1,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    if portmap is not None: device_str = f' ({portmap[port]})'
    else: device_str = ''
    for name, df3 in df2.groupby('vbias_tunnel'):
        ax.plot(df3.ibias*1e6, df3.count_rate, '.-', label = f'Vtunnel={name} V') # Plot data
    ax.set_title(f'Port {port}{device_str}')
    ax.set_xlabel('Current (uA)')
    ax.set_ylabel('Count rate (1/s)')
    ax.set_yscale('log')
    ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename + ' counts vs bias', dpi = 300)


#%% Plot counts vs vtunnel
fig, axs = plt.subplots(1,1,figsize = [16,8], sharex=True)
sub_plots = np.ravel(axs) # Convert 2D array of sub_plots to 1D
for port, df2 in df.groupby('port'):
    ax = sub_plots[port-1]    # Choose which axis to plot in
    if portmap is not None: device_str = f' ({portmap[port]})'
    else: device_str = ''
    for name, df3 in df2.groupby('ibias'):
        ax.plot((df3.vbias_tunnel*1e6), df3.count_rate, '.-', label = f'ibias={name*1e6:0.1f}uA') # Plot data
    ax.set_title(f'Port {port}{device_str}')
    ax.set_xlabel('Tunneling voltage (V)')
    ax.set_ylabel('Count rate (1/s)')
    ax.set_yscale('log')
    ax.legend()
fig.tight_layout()
# fig.suptitle(title); fig.subplots_adjust(top=0.88) # Add supertitle over all subplots
plt.savefig(filename + ' counts vs vtunnel', dpi = 300)


#%% Plot 2D histogram
import matplotlib

fig, ax = plt.subplots()
# ax.set_xscale('log')
dfp = df.pivot('ibias', 'vbias_tunnel', 'count_rate')
im = ax.pcolor(dfp.columns, dfp.index*1e6, dfp, vmin = None, vmax = None, norm=matplotlib.colors.LogNorm())
cbar = fig.colorbar(im)
cbar.set_label('Count rate (1/s)')
# plt.title('Ibias (uA)')
plt.xlabel('Vtunnel (V)')
plt.ylabel('Ibias (uA)')

fig.tight_layout()
plt.savefig(filename + ' 2d plot', dpi = 300)


#%%============================================================================
# Run trigger level sweep
# =============================================================================
parameter_dict = dict(
    vprobe = 4,
    ibias = 14e-6,
    count_time = 0.1,
    rbias = 10e3,
    v_trigger = np.arange(0,200e-3,10e-3),
    )

# Create combinations and manipulate them as needed
parameter_dict_list = parameter_combinations(parameter_dict)

data_list = []
for p_d in tqdm(parameter_dict_list):
    data_list.append(experiment_electron_counting(**p_d))

#Save the data 
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S snspd electron counting')
df = pd.DataFrame(data_list)
df.to_csv(filename + '.csv')

# FIXME PLOT HERE
df.plot('v_trigger','counts', logy=True)



