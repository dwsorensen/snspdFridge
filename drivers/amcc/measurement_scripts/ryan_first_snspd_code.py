import numpy as np
import time
from amcc.instruments.agilent_53131a import Agilent53131a
from amcc.instruments.jds_ha9 import JDSHA9
from amcc.instruments.srs_sim928 import SIM928
from amcc.instruments.srs_sim970 import SIM970
from matplotlib import pyplot as plt

# Setup voltage source
vs = SIM928('GPIB0::4::INSTR', sim900port = 1)
dmm = SIM970('GPIB0::4::INSTR', sim900port = 7)
vs.set_output(True)
vs.set_voltage(0)
 
#Laser attenuator
att = JDSHA9('GPIB0::15::INSTR')
att.reset()
att.set_wavelength(1550)
att.set_beam_block(True)
att.set_attenuation(0)

# Setup counter
counter = Agilent53131a('GPIB0::7::INSTR')
counter.reset()
counter.set_impedance(ohms = 50)
counter.set_coupling(dc = True)
counter.setup_timed_count()
counter.set_trigger(trigger_voltage = 0.050, slope_positive = True, channel = 1)




#%% Task 1 - IV curve of SNSPD
# Measure V on DMM, starting at I=0 -> 20uA -> 0uA -> -20uA -> 0uA


#Notes, using 10K resistor, get 10uA 0-100mA
start = 0
end = 0.2
num_pts = 100

R = 10e3
data = []
actual_set_voltage = []
vs.set_output(True)

x = np.array(np.linspace(start, end, num_pts)) #0-10
y = np.array(np.linspace(end, start, num_pts)) #10-0
z = np.array(np.linspace(start, -end, num_pts)) #0-10
a = np.array(np.linspace(-end, start, num_pts)) #-10 -0 

full_range = np.concatenate((x,y,z,a))

for i in full_range:
    vs.set_voltage(i)
    
    # Get raw data
    v_in = dmm.read_voltage(channel = 1)
    v_dut = dmm.read_voltage(channel = 2)
    
    # Compute derived values
    ibias = (v_in-v_dut)/R
    
    # Store data in list
    # actual_set_voltage.append(dmm.read_voltage(channel = 1))
    # data.append(dmm.read_voltage(channel = 2))
    ibias = 
    time.sleep(0.25)


plt.scatter(1e3*np.array(data), np.array(actual_set_voltage)*1e6/R )
plt.xlabel('voltage (mV)')
plt.ylabel('current (uA)')


#%% Task 2 - PCR and DCR curve of SNSPD
# Measure counts for various current values (0-20uA)
    # Set bias current
    # Measure counts for 0.5 sec
    # Repeat
    
R = 10e3
counts_dcr = []
actual_set_voltage_dcr = []
counts_pcr = []
actual_set_voltage_pcr = []
    
#Peaks are around 150mV, setting trigger to 100mV
counts = counter.timed_count(counting_time = 0.5)

#DCR
att.set_wavelength(1550)
att.set_attenuation(0)
att.set_beam_block(True)

start_bias = 0
end_bias = 0.1
num_pts = 100

for i in np.linspace(start_bias, end_bias, num_pts):
    vs.set_voltage(i)
    actual_set_voltage_dcr.append(dmm.read_voltage(channel = 1))
    counts_dcr.append(counter.timed_count(counting_time = 0.5))
    time.sleep(0.4)
#%%  
#PCR
vs.set_voltage(0)
att.set_wavelength(1550)
att.set_attenuation(8)
att.set_beam_block(False)
time.sleep(1)
counts_pcr = []

start_bias = 0
end_bias = 0.1
num_pts = 20

for i in np.linspace(start_bias, end_bias, num_pts):
    vs.set_voltage(i)
    actual_set_voltage_pcr.append(dmm.read_voltage(channel = 1))
    counts_pcr.append(counter.timed_count(counting_time = 0.5))
    time.sleep(0.4)

time.sleep(1)
vs.set_voltage(0)
att.set_attenuation(0)
att.set_beam_block(True)
#%%


#%%

vs.set_voltage(0)
time.sleep(3)
vs.set_voltage(1)
# Measure as fast as possible for ~5 seconds
time_start = time.time()

dmm_1_count = []
dmm_2_count = []
start_bias = 0
end_bias = 0.2
num_pts = 100

vs.set_voltage(1)
time.sleep(1)

while time.time()-time_start < 3:
    dmm_1_count.append(dmm.read_voltage(channel = 1))
    
time_elapsed = time.time() - time_start

#print("1 reading per", 1/len(dmm_1_count)/time_elapsed, 'seconds')

#%%
plt.plot(np.linspace(0, time_elapsed, len(dmm_1_count)) , dmm_1_count)