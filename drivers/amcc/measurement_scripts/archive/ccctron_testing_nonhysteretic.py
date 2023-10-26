# Ic measurement code
# Run add_path.py first
from measurement.ic_sweep import *
from measurement.iv_sweep import *
from useful_functions.save_data_vs_param import *


### Experimental variables: Scope/AWG
R_AWG = 100e3
vpp = 8
repetition_hz = 200


### Instrument configuration
lecroy_ip = 'touchlab1.mit.edu'  # QNN LeCroy 2
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)
awg = Agilent33250a('GPIB0::10')

SRS = SIM928(4, 'GPIB0::2')
SRS.reset()
R_SRS = 10e3


#########################################
### Initialize instruments
#########################################

lecroy.reset()
awg.reset()
time.sleep(5)
setup_ic_measurement(lecroy, awg, vpp = vpp, repetition_hz = repetition_hz, trigger_level = 1e-3, trigger_slope = 'Positive')
time.sleep(2)



#########################################
### Sample and equipment setup
#########################################

sample_name = 'SPE511 F3ab cccTron'
currents = np.linspace(-60e-6,60e-6,121)
num_sweeps = 200
awg_voltage = 8
trigger_level = 5e-3



#########################################
######    Quick Ic Test  ####
#########################################

### Quick Ic Test
num_sweeps = 500
voltage_data = run_ic_sweeps(lecroy, num_sweeps = num_sweeps)
ic_data = voltage_data/R_AWG
print('Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (np.median(ic_data*1e6), np.std(ic_data*1e6)) + \
        ' [Ramp rate of %0.3f A/s (Vpp = %s V, rate = %s Hz, R = %s kOhms)]' \
            % (calc_ramp_rate(vpp, R_AWG, repetition_hz, 'SINE'), vpp, repetition_hz, R_AWG/1e3))

# Plot histogram
plt.hist(ic_data*1e6, bins = 200, color = 'g')
plt.xlabel('Ic (uA)')
plt.title('')
plt.show()


#########################################
### Script for experiments 1 and 2
#########################################

###### Sub-configuration for Experiment 1: Channel (+)Ic vs gate current

test_type = 'Ic sweep'
test_name = 'Positive Ic vs gate current'
lecroy.set_trigger(source = 'C2', volt_level = trigger_level, slope = 'positive')
awg.set_vhighlow(vlow = 0, vhigh = awg_voltage)


###### Sub-configuration for Experiment 2: Channel (-)Ic vs gate current
test_type = 'Ic sweep'
test_name = 'Negative Ic vs gate current'
lecroy.set_trigger(source = 'C2', volt_level = -trigger_level, slope = 'negative')
awg.set_vhighlow(vlow = -awg_voltage, vhigh = 0)



# Setup instruments
lecroy.set_coupling(channel = 'C1', coupling = 'DC1M') # CH1 is input voltage readout
lecroy.set_coupling(channel = 'C2', coupling = 'DC1M') # CH2 is channel voltage readout
lecroy.set_coupling(channel = 'C3', coupling = 'DC50') # CH3 on scope connected to gate input
lecroy.set_bandwidth(channel = 'C1', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C2', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C3', bandwidth = '20MHz')

### Run experiment!
ic_data_list = []
start_time = time.time()
SRS.set_output(True)
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))

    SRS.set_voltage(i*R_SRS); time.sleep(0.05)

    voltage_data = run_ic_sweeps(lecroy, num_sweeps = num_sweeps)
    ic_data = voltage_data/R_AWG
    ic_data_list.append(ic_data.tolist())
    print('Current value %0.2f uA  -  Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (i*1e6, np.median(ic_data*1e6), np.std(ic_data*1e6)))
SRS.set_output(False)

file_path, file_name = save_x_vs_param(ic_data_list,  currents, xname = 'ic_data',  pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        comments = '', filedir = '', zip_file=True)

plot_ic_histogram_vs_current(ic_data_list, currents, file_name = file_name, num_bins = 100, range_min = None, \
                             title = sample_name + '\n' + test_name, current_on_xaxis = True)





#########################################
### Script for experiment 3:  Averaged IV curves
#########################################
test_type = 'IV curves'
test_name = 'IV vs gate current'
currents  = np.linspace(-60e-6,60e-6,61)

ex = {}
ex['num_iv_datapoints'] = 10e3
ex['num_sweeps'] = 200

ex['awg_freq'] = 100
ex['awg_vpp'] = 14
ex['R_AWG'] = 100e3
ex['R_AWG_shunt'] = 1e6
ex['R_SRS'] = 10e3
ex['R_SRS_shunt'] = 50

ex['lowpass_AWG'] = 'Mini Circuits BLP-5+'
ex['lowpass_SRS'] = 'Mini Circuits BLP-1.9+'
ex['lowpass_Port1'] = 'Mini Circuits VLFX-80'
ex['lowpass_Port2'] = 'Mini Circuits VLFX-80'


# lecroy.reset()
setup_iv_sweep(lecroy, awg, vpp = ex['awg_vpp'], repetition_hz = ex['awg_freq'], trigger_level = 0,
                num_sweeps = ex['num_sweeps'], num_datapoints = ex['num_iv_datapoints'], trigger_slope = 'Positive')


### Run experiment!
V_list = []
I_list = []
start_time = time.time()
SRS.set_output(True)
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))

    SRS.set_voltage(i*R_SRS); time.sleep(0.05)

    V,I = run_iv_sweeps(lecroy, num_sweeps = num_sweeps, R = 10e3)
    V_list.append(V.tolist())
    I_list.append(I.tolist())
SRS.set_output(False)


file_path, file_name = save_xy_vs_param(V_list, I_list, currents, xname = 'V', yname = 'I', pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        xlabel = 'Voltage (mV)', ylabel = 'Current (uA)', plabel = 'Current (uA)', title = '', legend = False,
                        xscale = 1e3, yscale = 1e6, pscale = 1e6,
                        comments = str(ex), filedir = '', display_plot = True, zip_file=True)



def run_ic_sweeps_vs_power(lecroy, num_sweeps):
    lecroy.clear_sweeps()
    time.sleep(0.1)
    while (lecroy.get_num_sweeps(channel = 'F1') < num_sweeps+1):
        time.sleep(0.1)
    x, ic_values = lecroy.get_wf_data(channel='F1')
    x, power_values = lecroy.get_wf_data(channel='F6')
    while (len(ic_values) < num_sweeps) or (len(power_values) < num_sweeps):
        x, ic_values = lecroy.get_wf_data(channel='F1')
        x, power_values = lecroy.get_wf_data(channel='F6')
        time.sleep(0.05)
    return ic_values[:num_sweeps], power_values[:num_sweeps] # will occasionally return 1-2 more than num_sweeps




##################################################################################
### Script for experiment 4: Gate Ic vs Power applied to channel
##################################################################################


test_type = 'Gate Ic vs Pchannel'
test_name = 'Positive gate Ic'
voltages  = np.linspace(-1.5,1.5,151)

# Experimental setup
ex = {}
ex['awg_freq'] = 200
ex['awg_vpp'] = 14
ex['R_AWG'] = 100e3
ex['R_AWG_shunt'] = 1e6
ex['R_SRS'] = 10e3
ex['R_SRS_shunt'] = 1e3

ex['lowpass_AWG'] = 'Mini Circuits BLP-5+'
ex['lowpass_SRS'] = 'Mini Circuits BLP-1.9+'
ex['lowpass_Port1'] = 'Mini Circuits VLFX-80'
ex['lowpass_Port2'] = 'Mini Circuits VLFX-80'

# Configure lecroy
# lecroy.reset()
setup_ic_measurement(lecroy, awg, vpp = ex['awg_vpp'], repetition_hz = repetition_hz, trigger_level = 5e-3, trigger_slope = 'Positive')
lecroy.view_channel(channel = 'C3', view = True)
lecroy.set_coupling(channel = 'C3', coupling = 'DC50') # CH3 on scope connected to gate input
lecroy.set_bandwidth(channel = 'C3', bandwidth = '20MHz')
lecroy.set_parameter(parameter = 'P6', param_engine = 'Mean', source1 = 'C3')
lecroy.setup_math_trend(math_channel = 'F6', source = 'P6', num_values = 10e3)


### Set Lecroy to proper scales, then run experiment below
### 50 ns/div horizontal width, and check voltages to make sure nothing's over
all_ic_data = []
all_channel_voltage_data = []
all_v_srs = []
start_time = time.time()
SRS.set_output(True)
for n, V_SRS in enumerate(voltages):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(voltages), (time.time()-start_time)/60.0))

    SRS.set_voltage(V_SRS); time.sleep(0.05)

    # Get Ic data
    ic_voltage_data, channel_voltage_data = run_ic_sweeps_vs_power(lecroy, num_sweeps = num_sweeps)
    all_ic_data +=  (ic_voltage_data/ex['R_AWG']).tolist()
    all_v_srs += [V_SRS]*num_sweeps
    all_channel_voltage_data +=  channel_voltage_data.tolist()
SRS.set_output(False)

# Convert raw data to gate Ic values and applied channel power
Ic_gate = np.array(all_ic_data)
V_channel = np.array(all_channel_voltage_data)
V_SRS = np.array(all_v_srs)
I_channel = (V_SRS - V_channel)/ex['R_SRS'] - V_channel/ex['R_SRS_shunt']
P_channel = V_channel*I_channel

# Save data
data_dict =  {'Ic_gate': Ic_gate, 'V_SRS': V_SRS, 'I_channel':I_channel, 'V_channel': V_channel, 'P_channel': P_channel, 'comments': str(ex)}
file_path, file_name = save_data_dict(data_dict = data_dict, test_type = test_type, test_name = sample_name + ' ' + test_name,
                        filedir = '', zip_file=True)

# Plot data and save figure
plt.plot(P_channel*1e9, Ic_gate*1e6, 'o')
plt.xlabel('Applied power to channel (nW)'); plt.ylabel('Gate Ic (uA)')
plt.savefig(file_path + '.png')
plt.show()