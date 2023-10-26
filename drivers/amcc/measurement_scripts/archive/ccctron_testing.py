# Ic measurement code
# Run add_path.py first
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *


### Experimental variables: Scope/AWG
R_AWG_IC = 10e3
R_AWG_BIAS = 10e3
vpp = 8
repetition_hz = 200
pulse_width = 1.0/(8*repetition_hz)


### Instrument configuration
lecroy_ip = 'touchlab1.mit.edu'  # QNN LeCroy 2
# lecroy_ip = '18.62.30.63' 
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)
awg_ic = Agilent33250a('GPIB0::10')
awg_bias = Agilent33250a('GPIB0::11') # Connect awg_bias front panel "Sync" port to "Ext trig" on awg_ic back panel



#########################################
### Initialize instruments
#########################################

lecroy.reset()
awg_bias.reset()
awg_ic.reset()
time.sleep(5)
setup_ic_measurement(lecroy, freq_gen, vpp = vpp, repetition_hz = repetition_hz, trigger_level = 1e-3, trigger_slope = 'Positive')
time.sleep(5)


# Setup lecroy
lecroy.set_coupling(channel = 'C1', coupling = 'DC1M')
lecroy.set_coupling(channel = 'C2', coupling = 'DC50')
lecroy.set_coupling(channel = 'C3', coupling = 'DC1M')
lecroy.set_coupling(channel = 'C4', coupling = 'DC50')
lecroy.set_bandwidth(channel = 'C1', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C2', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C3', bandwidth = '20MHz')
lecroy.set_bandwidth(channel = 'C4', bandwidth = '20MHz')


# Setup AWGs
awg_bias.set_load(high_z = True)
awg_ic.set_load(high_z = True)
awg_bias.set_pulse(freq=repetition_hz, vlow=0.0, vhigh=1.0, width = pulse_width, edge_time = pulse_width/10.0)
awg_ic.set_sin(freq=repetition_hz*2, vpp=vpp, voffset=0)
awg_ic.set_burst_mode(burst_enable = True, num_cycles = 1)
awg_ic.set_trigger(external_trigger = True, delay = pulse_width/10.0)






############### EXPERIMENT SCRIPT
sample_name = 'NWL027E B2ab cccTron'
test_name = 'Fine sweep with negative values'
test_type = 'Readout Ic vs Write Current'

### Experimental variables: about 4 tests/min for 1000 sweeps
currents = np.linspace(-100e-6,200e-6,201)
num_sweeps = 100


### Run experiment!
ic_data_list = []
start_time = time.time()
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))

    awg_bias.set_vhighlow(vlow = 0, vhigh = i*R_AWG_BIAS); time.sleep(0.2)

    voltage_data = run_ic_sweeps(lecroy, num_sweeps = num_sweeps)
    ic_data = voltage_data/R_AWG_IC
    ic_data_list.append(ic_data.tolist())
    print('Current value %0.2f uA  -  Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (i*1e6, np.median(ic_data*1e6), np.std(ic_data*1e6)))


file_path, file_name = save_x_vs_param(ic_data_list,  currents, xname = 'ic_data',  pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        comments = '', filedir = '', zip_file=True)

plot_ic_histogram_vs_current(ic_data_list, currents, file_name = file_name, num_bins = 100, range_min = None, \
                             title = sample_name + '\n' + test_name, current_on_xaxis = True)
