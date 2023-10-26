


def count_rate_vs_parameter(counter, set_param_function, param_values, counting_time = 0.1, delay_time = 0.05):
    count_rates = []
    start_time = time.time()
    for n, val in enumerate(param_values):
        print('Time elapsed for measurement %s of %s: %0.2f min' % (n, len(param_values), (time.time()-start_time)/60.0))
        set_param_function(val)
        time.sleep(delay_time)
        count_rates.append(counter.count_rate(counting_time))
        print('Parameter value %0.2f  ->  Count rate %0.3f kcps' % (val, count_rates[-1]/1000.0))

    return param_values, count_rates



#########################################
### Set laser attenuation
#########################################




#########################################
### Counts vs trigger level
#########################################


from instruments.agilent_53131a import *
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *

counter = Agilent53131a('GPIB0::3')
counter.basic_setup()

trigger_voltages = np.linspace(-1, 1, 100)
voltages, cr = count_rate_vs_parameter(counter = counter, set_param_function = counter.set_trigger,
                    param_values = trigger_voltages, counting_time = 0.1)
counter.set_trigger(trigger_voltage = -0.200)

plt.plot(voltages,np.log10(cr),'.')
plt.xlim([min(trigger_voltages), max(trigger_voltages)])
plt.ylabel('Log10(Count rate)')
plt.xlabel('Trigger voltage (V)')
plt.title('Port 7 Counts vs trigger level')
plt.show()




#########################################
### Counts vs bias for individual ports
#########################################


from instruments.agilent_53131a import *
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *

counter = Agilent53131a('GPIB0::3')
counter.basic_setup()

vs1 = SIM928(2, 'GPIB0::2')
vs1.reset()
vs1.set_output(True)
R_SRS = 10e3

counter.set_trigger(trigger_voltage = -0.200, trigger_slope = 'NEG')
currents = np.linspace(0.190, 0.250, 50)


### Run counts vs bias
vs1.set_voltage(0)
voltages, dcr = count_rate_vs_parameter(counter = c, set_param_function = vs1.set_voltage,
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