#standard testing for SNSPD
#add path
import sys
import os

snspd_measurement_code_dir = r'C:\Users\qnn-smallroom\Desktop\Di\snspd-measurement-code'
dir1 = os.path.join(snspd_measurement_code_dir,'instruments')
dir2 = os.path.join(snspd_measurement_code_dir,'useful_functions')
dir3 = os.path.join(snspd_measurement_code_dir,'measurement')

if snspd_measurement_code_dir not in sys.path:
    sys.path.append(snspd_measurement_code_dir)
    sys.path.append(dir1)
    sys.path.append(dir2)
    sys.path.append(dir3)

#import library
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *
from agilent_53131a import Agilent53131a
from jds_ha9 import JDSHA9
from keithley_2700 import *
#from instruments.ThorlabsPM100_meta import *
#from cryocon34 import *
import pyvisa as visa
from time import sleep


#########################################
### Sample information
#########################################
sample_name = 'SPE529'
test_name = 'array'
filedirectry = r'C:\Users\qnn-smallroom\Desktop\Di\SPE529'


#########################################
### Connect to instruments
#########################################

#lecroy_ip = 'touchlab1.mit.edu'; 
lecroy_ip = '18.62.10.142' 
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)
k = Keithley2700("GPIB::16"); k.reset()
#counter = Agilent53131a('GPIB0::3')
#counter.basic_setup()
#cryocon = Cryocon34('GPIB0::4')
#att = JDSHA9('GPIB0::5')
SRS1 = SIM928(2, 'GPIB0::2'); SRS1.reset()
SRS2 = SIM928(4, 'GPIB0::2'); SRS2.reset()
SRS3 = SIM928(6, 'GPIB0::2'); SRS3.reset()
SRS4 = SIM928(7, 'GPIB0::2'); SRS4.reset()
SRS5 = SIM928(8, 'GPIB0::2'); SRS5.reset()
#initiate the power meter
#inst = visa.instrument('USB0::0x1313::0x8078::PM002229::INSTR', term_chars='\n', timeout=1)
#pm = ThorlabsPM100Meta(inst)
R1_srs = 10e3
R2_srs = 10e3
R3_srs = 10e3
R4_srs = 10e3
R5_srs = 100e3

def count_rate_curve(currents, counting_time = 0.1):
    count_rate_list = []
    start_time = time.time()
    SRS.set_output(True)
    for n, i in enumerate(currents):
        # print '   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0)
        SRS.set_voltage(np.sign(i)*1e-3); time.sleep(0.05); SRS.set_voltage(i*R_srs); time.sleep(0.05)

        count_rate = counter.count_rate(counting_time=counting_time)
        count_rate_list.append(count_rate)
        print('Current value %0.2f uA - Count rate = %0.2e   (%s of %s: %0.2f min)' % (i*1e6, count_rate, n, len(currents), (time.time()-start_time)/60.0))
    SRS.set_output(False)
    return np.array(count_rate_list)


##########################################
# Simple Isw test
###########################################
#parameters
V_source_i = 10e-6*R5_srs
V_source_f = 40e-6*R5_srs
step = 1e-6*R5_srs

#here we go
V_source = np.arange(V_source_i,V_source_f, step)
V_device = []
I_device = [] 
SRS5.set_voltage(V_source_i)
SRS5.set_output(True)
k.setup_read_volt()
k.read_voltage()
sleep(1)

for v in V_source:
    SRS5.set_voltage(v)
    sleep(0.1)
    vread = k.read_voltage()
    iread = (v-vread)/R5_srs
    # print('V=%.4f V, I=%.2f uA, R =%.2f' %(vread, iread*1e6, vread/iread))
    V_device.append(vread)
    I_device.append(iread)

plt.plot(np.array(V_device)*1e6, np.array(I_device)*1e6, '-o')
plt.xlabel('Voltage')
plt.ylabel('Current (uA)')
plt.title('V-I Curve')

print(('Ic = %.2f uA' %(np.max(I_device)*1e6)))
plt.show()



#########################################
### Setup counter
#########################################
### Scan counter trigger levels - Make sure trigger voltage is well above noise level
trigger_v, count_rate = counter.scan_trigger_voltage([-0.5,0.5], counting_time=0.2, num_pts=100)
plt.plot(trigger_v, np.log10(count_rate),'o')
plt.show()

# Next, use the above information to set the counter trigger level
counter.set_trigger(0.15)



#####################################################################
### Measure and plot dark count rate curve + laser count rate curve
#####################################################################
###################################################
#set the bias current range that you want to test
###################################################
currents = np.linspace(0e-6, 25e-6, 50)
counting_time = .5


# With laser off, measure dark count rate curve (DCR)
att.set_beam_block(True)
DCR = count_rate_curve(currents, counting_time = counting_time)
# Turn on laser, measure laser count curve (LCR)
att.set_beam_block(False)
LCR = count_rate_curve(currents, counting_time = counting_time)


data_dict = {'LCR':LCR, 'DCR':DCR, 'currents':currents}
file_path, file_name  = save_data_dict(data_dict, test_type = 'DCR and LCR', test_name = sample_name,
                        filedir = filedirectry, zip_file=True)

plt.semilogy(1e6*currents, LCR, 'o', label='Laser count rate (LCR)')
plt.semilogy(1e6*currents, DCR, 'o', label='Dark count rate (DCR)')
plt.semilogy(1e6*currents, LCR-DCR, 'o', label='LCR - DCR')
plt.legend(loc='upper left')
plt.xlabel('Bias current (uA)'); plt.ylabel('Counts (Hz)'); plt.title('Counts vs Bias\n' + sample_name)
plt.savefig(file_path + '.png')
plt.show()


#########################################
### Laser attenuation vs count rate curves
#########################################

currents1 = np.arange(0e-6, 18e-6, 4e-6)
currents2 = np.arange(18e-6, 25e-6, 0.5e-6)
currents = np.concatenate([currents1, currents2])
db_attenuation = np.arange(0, 25, 5)
counting_time = 1

att.set_beam_block(False)

lcr_list = []
powers = []
for db in db_attenuation:
    att.set_attenuation_db(db)
    LCR = count_rate_curve(currents, counting_time = counting_time)
    powers.append(pm.read_value())
    lcr_list.append(LCR)
att.set_beam_block(True)
DCR = count_rate_curve(currents, counting_time = counting_time)


data_dict = {'LCR':lcr_list, 'DCR':DCR, 'currents':currents, 'db_attenuation':db_attenuation, 'powers': powers}
file_path, file_name  = save_data_dict(data_dict, test_type = 'Laser attenuation vs count rate', test_name = sample_name,
                        filedir = filedirectry, zip_file=True)

for n, db in enumerate(db_attenuation): plt.semilogy(1e6*currents, lcr_list[n]+1, 'o-', label=('%0.1f dB' % db))
plt.semilogy(1e6*currents, DCR+1, 'kx-', label='DCR')
plt.legend(loc='upper left')
plt.xlabel('Bias current (uA)'); plt.ylabel('Counts (Hz)'); plt.title('Counts vs Bias\n' + sample_name)
plt.savefig(file_path + '.png')
plt.show()

 

#########################################
### Setup jitter measurement
#########################################
#!set your trigger level and bias current here
SRS.set_voltage(29e-6*R_srs)
trigger_level = 150e-3

lecroy.reset()
SRS.set_output(True)
time.sleep(5)

lecroy.set_display_gridmode(gridmode = 'Single')
lecroy.set_coupling(channel = 'C2', coupling = 'DC50')
lecroy.label_channel(channel = 'C2', label = 'SNSPD trace')
lecroy.label_channel(channel = 'C3', label = 'Photodiode reference')
lecroy.view_channel(channel = 'C1', view = False)
lecroy.view_channel(channel = 'C2', view = True)
lecroy.view_channel(channel = 'C3', view = True)
lecroy.view_channel(channel = 'C4', view = False)

lecroy.set_vertical_scale(channel = 'C2', volts_per_div = 100e-3, volt_offset = 0)
lecroy.set_vertical_scale(channel = 'C3', volts_per_div = 50e-6, volt_offset = 0)
lecroy.set_horizontal_scale(time_per_div = 10e-9, time_offset = 0)

lecroy.set_trigger(source = 'C2', volt_level = trigger_level, slope = 'Positive')
lecroy.set_trigger_mode(trigger_mode = 'Normal')
lecroy.set_parameter(parameter = 'P1', param_engine = 'Skew', source1 = 'C3', source2 = 'C2')
lecroy.setup_math_trend(math_channel = 'F1', source = 'P1', num_values = 100e3)
lecroy.setup_math_histogram(math_channel = 'F2', source = 'P1', num_values = 500)
lecroy.set_parameter(parameter = 'P2', param_engine = 'FullWidthAtHalfMaximum', source1 = 'F2', source2 = None)

# One more thing to do:  Set trigger voltage levels for the P1 skew function



#########################################
### Setup jitter measurement
#########################################

# Review the laser count rate graph, and determine 
# the range of currents with LCR > ~100, and DCR << LCR

currents = np.linspace(20e-6, 30e-6, 10)
num_sweeps = 100e3 # For some reason if this is == 10e3, reading the data crashes occasionally
num_bins = 500

jitter_data_list = []
start_time = time.time()
SRS.set_output(True)
for n, i in enumerate(currents):
    SRS.set_voltage(i*R_srs)
    jitter_data = lecroy.collect_sweeps(channel = 'F1', num_sweeps = num_sweeps)
    jitter_data_list.append(jitter_data)


file_path, file_name = save_x_vs_param(jitter_data_list,  currents, xname = 'jitter_data',  pname = 'currents',
                        test_type = 'Jitter IRF data', test_name = sample_name,
                        comments = '', filedir = '', zip_file=True)


for n, data in enumerate(jitter_data_list):
    n, bins, patches = plt.hist(data*1e12, bins = num_bins, normed=True, histtype='stepfilled', label = '%0.1f uA' % (currents[n]*1e6))
    plt.setp(patches, 'alpha', 0.5)
plt.xlabel('Time delay (ps)'); plt.ylabel('Counts'); plt.title('Jitter distributions\n' + sample_name)
plt.savefig(file_path + '.png')
plt.legend()
plt.show()





#########################################
### Trace acquistion of pulses
#########################################

### First adjust scope to include whole pulse shape


#simple single trace of the pulse shape
channel = 'C2'
x,y = lecroy.get_single_trace(channel = channel)
plt.plot(x,y)

data_dict = {'x':x, 'y':y}
file_path, file_name  = save_data_dict(data_dict, test_type = '', test_name = 'read_8_D1_150uA_D2_150uA_D3_150__bias=-6uA_3dB_att',
                        filedir = filedirectry, zip_file=False) 
plt.savefig(file_path + 'pulse_shape' +sample_name + '.png')
plt.show()


### First adjust scope to include whole pulse shape

num_traces = 1
currents = np.linspace(14e-6, 21e-6, 8)

snspd_traces_x_list = []
snspd_traces_y_list = []
pd_traces_x_list = []
pd_traces_y_list = []
start_time = time.time()
SRS.set_output(True)
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))
    SRS.set_voltage(i*R_srs)
    pd_traces_x = [] # Photodiode pulses
    pd_traces_y = []
    snspd_traces_x = [] # Device pulses
    snspd_traces_y = []
    lecroy.clear_sweeps()
    for n in range(num_traces):
        x,y = lecroy.get_single_trace(channel = 'C2')
        snspd_traces_x.append(x);  snspd_traces_y.append(y)
        x,y = lecroy.get_single_trace(channel = 'C3')
        pd_traces_x.append(x);  pd_traces_y.append(y)

    snspd_traces_x_list.append(snspd_traces_x)
    snspd_traces_y_list.append(snspd_traces_y)
    pd_traces_x_list.append(pd_traces_x)
    pd_traces_y_list.append(pd_traces_y)


data_dict = {'snspd_traces_x_list':snspd_traces_x_list, 'snspd_traces_y_list':snspd_traces_y_list, \
             'pd_traces_x_list':pd_traces_x_list, 'pd_traces_y_list':pd_traces_y_list, \
             'currents':currents}
file_path, file_name  = save_data_dict(data_dict, test_type = 'SNSPD trace acquisition', test_name = sample_name,
                        filedir = filedirectry, zip_file=True)


#save screenshots
lecroy.save_screenshot(filename = 'test', filepath = 'C:\\Users\\LeCroyUser\\Dropbox\\dizhu\\screenshots\\', grid_area_only = False)
