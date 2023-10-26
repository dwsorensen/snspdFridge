# Ic measurement code
# Run add_path.py first

from lecroy_620zi import LeCroy620Zi
from agilent_33250a import Agilent33250a
from keithley_2400 import Keithley2400
from agilent_53131a import Agilent53131a
from srs_sim928 import SIM928
from pyvisa import pyvisa as visa
import numpy as np
import time
import datetime
from matplotlib import pyplot as plt
from scipy.optimize import fmin
import scipy.io
import pickle as pickle


def count_rate_vs_parameter(counter, set_param_function, param_values, counting_time = 0.1, delay_time = 0.05):
    dcr = []
    for val in param_values:
        set_param_function(val)
        time.sleep(delay_time)
        dcr.append(counter.count_rate(counting_time))
    return param_values, dcr


### Experimental variables: Counter/Voltage source
R = 100e3
trigger_level = -250e-3
counting_time = 0.1

### Instrument configuration
c = Agilent53131a('GPIB0::3')
vsource1 = SIM928(6,'GPIB0::2')
lecroy_ip = '18.62.12.216'
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)

### Initialize instruments
c.basic_setup()
time.sleep(1)
c.set_trigger(trigger_voltage = trigger_level, trigger_slope = 'NEG')
vsource1.reset()
vsource1.set_output(True)


# # Test trigger voltages
# v, dcr = c.scan_trigger_voltage(voltage_range=[-1.5,1.5], counting_time=0.1, num_pts=100)
# plt.plot(v,np.log(dcr)); plt.show()





############### EXPERIMENT SCRIPT
test_name = 'SNSPD nTron nTron NWL007A Port 2 0uA to 40uA'

### Experimental variables: about 4 tests/min for 1000 sweeps
currents = np.arange(13e-6, 15e-6, 10e-9)
# currents = np.linspace(-25e-6, 25e-6, 100)


### Run counts vs bias
vsource1.set_voltage(0)
voltages, dcr = count_rate_vs_parameter(counter = c, set_param_function = vsource1.set_voltage,
                    param_values = currents*R, counting_time = 0.1)
plt.plot(currents*1e6,dcr); plt.xlabel('Bias current (uA)'); plt.ylabel('Count rate (Hz)'); plt.show()


ic_data_list = []
I_list = []
V_list = []
start_time = time.time()
for n in range(len(currents)):
    print('Time elapsed for measurement %s of %s: %0.2f min' % (n, len(currents), (time.time()-start_time)/60.0))
    k.set_current(currents[n])
    voltage_data = measure_ic_values(lecroy, num_sweeps = num_sweeps)
    ic_data = voltage_data/R
    ic_data_list.append(ic_data.tolist())
    v,i = k.read_voltage_and_current()
    I_list.append(i); V_list.append(v)
    print('Current value %0.2f uA  -  Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (I_list[-1]*1e6, np.median(ic_data*1e6), np.std(ic_data*1e6)))



# Save data
filesave_dict = {'ic_data': ic_data_list, 'I': I_list, 'V': V_list}

time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
filename =  time_str + ' ' + test_name
scipy.io.savemat(filename + '.mat', mdict=filesave_dict)
f = open(filename + '.pickle', 'wb')
pickle.dump(filesave_dict, f)
f.close()
print('Saved as %s' % filename)




# Plot histogram vs other things in 2D
y_axis = I_list
ic_hist_list, ic_bins = data_list_to_histogram_list(ic_data_list, num_bins = 100)
ic_hist_list = np.flipud(ic_hist_list)
extent = [ic_bins[0]*1e6,ic_bins[-1]*1e6,y_axis[0]*1e6,y_axis[-1]*1e6]
plt.imshow(ic_hist_list, extent=extent, aspect = 'auto')
plt.show()
