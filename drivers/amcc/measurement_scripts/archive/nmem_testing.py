# Run add_path.py first
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *


def interleave_array(array_tuple):
    return np.vstack(array_tuple).reshape((-1,),order='F')


#########################################
### Instrument configuration
#########################################

lecroy_ip = 'touchlab1.mit.edu'  # QNN LeCroy 2
# lecroy_ip = '18.62.30.63' 
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)
awg = Agilent33250a('GPIB0::10')
SRS = SIM928(2, 'GPIB0::2')



#########################################
### Initialize instruments
#########################################

lecroy.reset()
awg.reset()
time.sleep(5)
setup_ic_measurement(lecroy, awg, vpp = vpp, repetition_hz = repetition_hz, trigger_level = 1e-3, trigger_slope = 'Positive')
time.sleep(5)





##########################################################
############### EXPERIMENT SCRIPT
############### SRS goes very negative, zero, then high
############### Ic data taken at each step
###########################################################

sample_name = 'NWL027F Device B4ab nMEM with cccTron readout (SHUNTED write)'
test_name = 'Bit error rate test'
test_type = 'Ic Sweep vs Write current'

bits = np.random.randint(0,2,100)
currents = np.empty(bits.shape)
currents[bits==1] = 400e-6
currents[bits==0] = -200e-6

# currents = np.linspace(-1000e-6,1000e-6,21)
# currents = np.concatenate((currents, -currents))
# currents = interleave_array(array_tuple = (currents, -currents))
# currents = np.repeat(currents, 20)
# currents = np.concatenate((currents, -currents))
R_SRS = 1e3
R_AWG = 10e3
num_sweeps = 50



### Run experiment!
ic_step1_list = []
ic_step2_list = []
ic_step3_list = []
ic_step4_list = []
sleep_delay = 0.2
current_vs_time = []

start_time = time.time()
SRS.set_output(True)
awg.set_output(False)
# SRS.set_voltage(-200e-6*R_SRS); time.sleep(sleep_delay); SRS.set_voltage(0); time.sleep(sleep_delay); current_vs_time += [0,0,0,0,0] + [-20]*10
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))
   
    # SRS.set_voltage(-i*R_SRS); time.sleep(sleep_delay); current_vs_time += [-i]*10
    # awg.set_output(True); ic_step1_list.append( run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R_AWG ); awg.set_output(False)

    # SRS.set_voltage(0); time.sleep(sleep_delay); current_vs_time += [0]*10
    # awg.set_output(True); ic_step4_list.append( run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R_AWG ); awg.set_output(False)

    SRS.set_voltage(i*R_SRS); time.sleep(sleep_delay); current_vs_time += [i]*10
    # awg.set_output(True); ic_step3_list.append( run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R_AWG ); awg.set_output(False)

    SRS.set_voltage(0); time.sleep(sleep_delay); current_vs_time += [0]*10
    awg.set_output(True); ic_step4_list.append( run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R_AWG ); awg.set_output(False); time.sleep(sleep_delay)

SRS.set_output(False); awg.set_output(True)

data_dict =  {'ic_step1': ic_step1_list, 'ic_step2':ic_step2_list, 'ic_step3':ic_step3_list, 'ic_step4':ic_step4_list, 'currents': currents}
file_path, file_name = save_data_dict(data_dict = data_dict, test_type = test_type, test_name = sample_name + ' ' + test_name,
                        filedir = '', zip_file=True)


plot_ic_histogram_vs_current(ic_step4_list, currents, file_name = file_name, num_bins = 100, range_min = None, title = sample_name + '\n' + test_name)
# plt.plot(np.array(current_vs_time[0:200])*1e6); plt.show()


# Compile all Ic sweeps into one fat histogram
d = np.concatenate(ic_step4_list)
d = d[d>200e-6]
plt.hist(d*1e6, bins = 200); plt.xlabel('Current (uA)'); plt.ylabel('Counts')
plt.show()


##########################################################
############### EXPERIMENT SCRIPT
############### SRS goes very negative, to zero, to a specific current, to zero, and then ic is measured once
###########################################################
sample_name = 'NWL016G'
test_name = 'First sweep'
test_type = 'Readout Ic vs Write Current'

### Experimental variables
currents = np.linspace(0,100e-6,401)
num_sweeps = 200
R_SRS = 10e3

### Run experiment!
ic_data_list = []
I_list = []
start_time = time.time()
SRS.set_output(True)
for n in range(len(currents)):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))

    i = currents[n]
    SRS.set_voltage(-10); time.sleep(0.1)
    SRS.set_voltage(-1e-3); time.sleep(0.1);
    SRS.set_voltage(i*R_gate); time.sleep(0.1)
    SRS.set_voltage(np.sign(i)*1e-3); time.sleep(0.1);

    awg.trigger_now()
    voltage_data = lecroy.get_parameter_value(parameter = 'P1')
    ic_data = voltage_data/R_SRS
    ic_data_list.append(ic_data)
    I_list.append(i)
    print('Current value %0.2f uA  -  Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (i*1e6, np.median(ic_data*1e6), np.std(ic_data*1e6)))
SRS.set_output(False)

plt.plot(currents, ic_data_list, '.')
plt.show()


file_path, file_name = save_x_vs_param(ic_data_list,  I_list, xname = 'ic_data',  pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        comments = '', filedir = '', zip_file=False)


i = currents[n]; SRS.set_voltage(np.sign(i)*1e-3); time.sleep(0.05); SRS.set_voltage(i*R_gate); time.sleep(0.05)