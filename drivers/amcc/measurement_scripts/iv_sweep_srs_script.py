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
from amcc.instruments.srs_sim928 import SIM928
from amcc.instruments.srs_sim970 import SIM970
from matplotlib import pyplot as plt

from amcc.standard_measurements.parameterized_measurements import run_experiment, experiment_counter, experiment_iv_sweep


# Close all open resources
rm = visa.ResourceManager()
[i.close() for i in rm.list_opened_resources()]

# Create instruments
vs = SIM928('ASRL10::INSTR', 1)
dmm = SIM970('ASRL10::INSTR', 7)

# Initialize instruments
vs.set_voltage(0)
vs.set_output(True)

# switch = Switchino('COM7')
# switch = Switchino('ASRL11::INSTR')
#%% IV Sweep
rbias = 100e3
portmap = None
ibias = np.linspace(0,1.5e-6,31)
# ibias = np.concatenate((ibias,ibias[::-1],-ibias,-ibias[::-1]))

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
