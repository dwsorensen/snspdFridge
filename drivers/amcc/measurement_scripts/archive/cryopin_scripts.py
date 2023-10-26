# Written by Adam McCaughan July 8, 2014
# Run add_path.py first

import time
import numpy as np
from pyvisa import pyvisa as visa
from agilent_8153a import *
from anritsu_mg9638a import *
from keithley_2400 import *
from agilent_33250a import *
from lecroy_620zi import *
from useful_functions.save_data_vs_param import *


def wavelength_sweep_test(wavelengths_nm = [1550, 1551], step_delay = 0.1):
    powers = []
    laser_power = ls.get_power()
    for wl in wavelengths_nm:
        ls.set_wavelength(wl)
        # pm.set_wavelength(wl)
        time.sleep(step_delay)
        power_reading = pm.read_power()
        if power_reading > laser_power: power_reading = pm.read_power()
        powers.append(power_reading)
        print('    Power reading at %0.2f nm:   %0.3e uW' % (wl, powers[-1]*1e6))
    return powers


def iv_curve(k, voltages = [0,1e-3,2e-3], compliance_i = 1e-3, step_delay = 0.05, plc_value = 1.0):
    k.set_compliance_i(compliance_i)
    # k.set_output(True)
    k.set_measurement_time(plc_value) # plc_value has a default of 1, max of 10, and min of 0.01
    k.set_voltage(voltages[0]); time.sleep(0.1)
    v_list = []
    i_list = []
    print('This IV curve will take (optimistically): %0.1f min' % (len(voltages)*step_delay/60.0))
    for v in voltages:
        try:
            k.set_voltage(v)
            time.sleep(step_delay)
            vout, iout = k.read_voltage_and_current()
            v_list.append(vout)
            i_list.append(iout)
        except KeyboardInterrupt:
            break
    k.set_voltage(0)
    k.set_measurement_time(1.0)
    k.disable_remote()
    # k.set_output(False)
    return np.array(v_list), np.array(i_list)



def set_awg_vhighlow_sanitized(awg, vlow = 0.0, vhigh = 0.1):
    if vhigh <= vlow:
        print('error, vhigh <= vlow')
    if abs(vhigh) > abs(AWG_V_MAX):
        print('vhigh out of range (%s; Max voltage %s)' % (vhigh, AWG_V_MAX))
        return
    elif abs(vlow) > abs(AWG_V_MAX):
        print('vlow out of range (%s; Max voltage %s)' % (vhigh, AWG_V_MAX))
        return
    awg.set_vhighlow(vlow=vlow, vhigh=vhigh)




#####################################
#####  Test #1:  IV Curve     ########
#####################################

### Initialize Keithley
# k = Keithley2400('GPIB0::14'); k.reset()
# k.setup_2W_source_V_read_I() # k = Keithley attached to channel


### Experimental variables
test_name = 'CryoPIN03 4K hysteresis'
voltages = np.linspace(-1.5,1.5,200)
compliance_i = 4e-3

v_up, i_up = iv_curve(k, voltages = voltages, compliance_i = compliance_i, step_delay = 0.1)
v_down,i_down = iv_curve(k, voltages = np.flipud(voltages), compliance_i = compliance_i, step_delay = 0.1)

save_xy_vs_param([v_up, v_down], [i_up, i_down], [0,0], xname = 'v', yname = 'i', pname = 'null',
                        test_type = 'IV Curve', test_name = test_name,
                        xscale = 1, yscale = 1e3, pscale = 1,
                        xlabel = 'Voltage (V)', ylabel = 'Current (mA)', title = '', legend = False,
                        comments = '', filedir = '', display_plot = True, zip_file=False)



###################################################
#####  Test #2a:  Basic spectrum sweep     ########
###################################################

### Setup instruments
pm = Agilent8153A('GPIB0::22'); pm.setup_basic(lambda_nm = 1550, averaging_time = 0.1)
ls = AnritsuMG9638A('GPIB0::20'); ls.setup_basic(); ls.set_power(10, 'uW')

wavelengths_nm = np.arange(1548, 1551, .01).tolist()
print('Total time: %s sec' % (0.1*len(wavelengths_nm)))
P = wavelength_sweep_test(wavelengths_nm, step_delay = 0.1)
P_dBm = 10*np.log10(np.array(P)*1e3)

save_xy_vs_param([wavelengths_nm], [P_dBm], [0], xname = 'WL', yname = 'P', pname = 'null',
                        test_type = 'Basic spectrum', test_name = '300K after cooldown',
                        xscale = 1, yscale = 1, pscale = 1e3,
                        xlabel = 'Wavelength (nm)', ylabel = 'Power (dBm)', plabel = 'mV',
                        title = '', legend = False,
                        comments = '', filedir = '', display_plot = True, zip_file=False)



######################################################
#####  Test #2b:  Spectrum vs Bias voltage     ########
######################################################
### Setup instruments
pm = Agilent8153A('GPIB0::22'); # pm.setup_basic(lambda_nm = 1550, averaging_time = 0.1)
ls = AnritsuMG9638A('GPIB0::20');# ls.setup_basic(); ls.set_power(10, 'uW')
k = Keithley2400('GPIB0::14'); # k.reset()
# pm = ThorlabsPM100D('USB0::0x1313::0x8078::PM002292')
# k.setup_2W_source_V_read_I() # k = Keithley attached to channel


### Experimental variables
test_name = 'CryoPIN03 Single Resonance vs Bias 4K closeup'
voltages = np.linspace(0, 1.6, 5)
# voltages = [0]
compliance_i = 4e-3
wavelengths_nm = np.arange(1550.45, 1550.65, .002).tolist()
step_delay = 0.5
pm.set_averaging_time(averaging_time = 0.1)


### Run experiment with multiple sweeps
P_list = []; WL_list = []
start_time = time.time()
k.set_compliance_i(compliance_i)
k.set_output(True)
for n in range(len(voltages)):
    print('Time elapsed for measurement %s: %0.2f min' % (n, (time.time()-start_time)/60.0))
    k.set_voltage(voltages[n]); time.sleep(0.1)
    P = wavelength_sweep_test(wavelengths_nm, step_delay = step_delay)
    P_list.append(P)
    WL_list.append(wavelengths_nm)
k.set_voltage(0); k.disable_remote()

dB_P_list = 10*np.log10(np.array(P_list)*1e3)

save_xy_vs_param(WL_list, dB_P_list, voltages, xname = 'WL', yname = 'P', pname = 'voltages',
                        test_type = 'Spectrum vs Bias', test_name = test_name,
                        xscale = 1, yscale = 1, pscale = 1e3,
                        xlabel = 'Wavelength (nm)', ylabel = 'Power (dBm)', plabel = 'mV',
                        title = '', legend = True,
                        comments = '', filedir = '', display_plot = True, zip_file=False)





# ########################################################
# #####  Test #3:  Microwave modulation of PIN    ########
# ########################################################

AWG_V_MAX = 1.51

### Setup instruments
awg = Agilent33250a('GPIB0::10')

lecroy_ip = 'touchlab2.mit.edu'  # QNN LeCroy 2
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip); #lecroy.reset()


# set_awg_vhighlow_sanitized(awg, vlow = -0.1, vhigh = 1.5)
# awg_pulse_width = 30e-9
# awg_pulse_edge_time = 5e-9
# awg_pulse_height = 1.5
test_name = 'Long pulse'
test_type = 'CryoPIN03 300K Pulse Modulation 100 ps Rise pulse'
wavelengths = np.arange(1550.25, 1550.75, 0.05)

t_opt_list = []
y_opt_list = []
for wl in wavelengths:
    ls.set_wavelength(wl)
    lecroy.clear_sweeps()
    time.sleep(5) # Time to let the averaging happen
    t_opt,y_opt = lecroy.get_wf_data(channel = 'F1')
    t_opt_list.append(t_opt.tolist())
    y_opt_list.append(y_opt.tolist())


# Plug in AWG at this point
t_awg, y_awg = lecroy.get_wf_data(channel = 'F2')


file_path, file_name  = save_xy_vs_param(t_opt_list, y_opt_list, wavelengths, xname = 't_opt', yname = 'y_opt', pname = 'wavelengths',
                        test_type = test_type, test_name = test_name,
                        xscale = 1e9, yscale = 1e6, pscale = 1,
                        xlabel = 'Time (ns)', ylabel = 'Optical Power (uW)', plabel = 'nm',
                        title = '', legend = True,
                        extra_data_dict = { 't_awg':t_awg, 'y_awg':y_awg},
                        comments = '', filedir = '', display_plot = True, zip_file=False)


plt.plot(t_opt*1e9, y_opt*1e6)
plt.xlabel('Time (ns)'); plt.ylabel('Photodiode readout (uW)')



# data_dict = {'t_opt':t_opt, 'y_opt':y_opt, 't_awg':t_awg, 'y_awg':y_awg, 'awg_pulse_width':awg_pulse_width, \
#             'awg_pulse_height':awg_pulse_height, 'awg_pulse_edge_time':awg_pulse_edge_time}
# file_path, file_name  = save_data_dict(data_dict, test_type = , test_name = test_name,
#                         filedir = '', zip_file=False)


plt.subplot(2,1,1)
plt.plot(t_awg*1e9, y_awg)
plt.xlabel('Time (ns)'); plt.ylabel('Input voltage (V)')
plt.subplot(2,1,2)
plt.plot(np.transpose(t_opt_list)*1e9, np.transpose(y_opt_list)*1e6)
plt.xlabel('Time (ns)'); plt.ylabel('Photodiode readout (uW)')
plt.savefig(file_name + ' subplot.png')
plt.show()




plt.subplot(2,1,1)
plt.plot(t_awg*1e9, y_awg)
plt.xlabel('Time (ns)'); plt.ylabel('Input voltage (V)')
plt.subplot(2,1,2)
for n in range(len(t_opt_list)):
    x = np.array(t_opt_list)*1e9
    y = np.array(y_opt_list)*1e6
    y = y - np.mean(y[0:10])
    plt.plot(x, y)
plt.xlabel('Time (ns)'); plt.ylabel('Photodiode readout (relative uW)')
plt.savefig(file_name + ' subplot reference.png')
plt.show()