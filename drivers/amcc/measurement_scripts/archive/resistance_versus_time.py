# Written by Adam McCaughan Nov 2015
# Run add_path.py first

from keithley_2400 import Keithley2400
import numpy as np
from pyvisa import pyvisa as visa
import time
import scipy.io
import datetime
from matplotlib import pyplot as plt
import time




k = Keithley2400('GPIB0::14')
k.write('*RST')
k.write(':SYST:RSEN 1') # Turn off "Remote Sensing" aka 4-wire measurement mode
k.write(':CONF:RES') # Configure to resistance mode
k.write(':SENS:RES:RANGE:AUTO 1') # Set resistance range to Auto
k.set_output(True)



test_name = 'NWL037C3 HSQ SNSPD R vs time 300C hotplate'
filename_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ' ' + test_name + '.txt'

# f.write('Source Current=' + str(source_current*1000) + ' (mA)  Time (s), Temperature (K), ')
# for i in range(len(sample_positions)):
    # f.write('R of ' + sample_names[i] + ' (pos ' + str(sample_positions[i]) + ') (Ohms), ')
# f.write('\n')
    
time_start = time.time()
t_list = []
i_list = []
v_list = []
r_list = []

with open(filename_str,'a') as f:  f.write('Time, Resistance, Voltage, Current\n')

while True:
    try:
        time_elapsed = time.time()-time_start

        vout, iout = k.read_voltage_and_current()
        resistance = vout/iout
        t_list.append(time_elapsed)
        i_list.append(iout)
        v_list.append(vout)
        r_list.append(resistance)

        data_str = '%0.1f, %0.3e, %0.3e, %0.3e' % (time_elapsed, resistance, vout, iout)
        print('Time: %0.1f s / Resistance: %0.2f kOhm ' % (time_elapsed, resistance/1e3))
        with open(filename_str,'a') as f:  f.write(data_str + '\n')

        time.sleep(2)

    except:
        break


