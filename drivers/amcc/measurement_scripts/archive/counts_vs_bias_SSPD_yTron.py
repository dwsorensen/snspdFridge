from instruments.agilent_53131a import *
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *

# c = Agilent53131a('GPIB0::10')
# c.basic_setup()
# c.set_trigger(-0.075)


counter = Agilent53131a('GPIB0::3')


v = SIM928(2, 'GPIB0::2')
yTron = SIM928(4, 'GPIB0::2')
v.reset()
v.set_output(True)
R_gate = 10e3
R_ytron = 1e3



#then set the trigger level appropriately
counter.set_trigger(-0.2)

#This defines the current values we use to bias the SNSPD:
currents = np.linspace(14e-6, 14e-6, 1)
currentsYtron = np.linspace(35e-6, 60e-6, 50)


#sweep SNSPD bias, measure counts
counts_list = []
I_list = []
I_ytron = []
#start_time = time.time()

for m in range(len(currentsYtron)):
    I_ytron.append(currentsYtron[m])
    for n in range(len(currents)):

        #print '   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0)
        # k.set_current(currents[n]); time.sleep(0.01)
        # v,i = k.read_voltage_and_current()
        yTron.set_voltage(currentsYtron[m]*R_ytron)
        v.set_voltage(0.1);
        i = currents[n]; v.set_voltage(0); time.sleep(0.05); 
        v.set_voltage(i*R_gate); 
        time.sleep(0.05);
        counts = counter.count_rate(counting_time=10)
        counts_list.append(counts)
        I_list.append(i)
    #print 'Current value %0.2f uA  -  Median Ic = %0.2f uA / Std. dev Ic = %0.2f uA' % (I_list[-1]*1e6, np.median(ic_data*1e6), np.std(ic_data*1e6))


plt.plot(1e6*np.array(I_list), np.log(counts_list), 'o')
plt.xlabel('Bias current (uA)')
plt.ylabel('Counts (#/Sec)')
plt.title('Counts vs Bias')
plt.show()


data_dictionary = {"Counts":counts_list, 'CurrentSSPD':I_list, 'CurrentYtron':I_ytron}  
scipy.io.savemat('DCRvsBias_SSPD_Ytroni35uA.mat', mdict=data_dictionary)