# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 10:46:04 2018

@author: anm16
"""

#%% IMPORT PATH NAME for modules
import sys
import os

snspd_measurement_code_dir = r'C:\Users\anm16\Documents\GitHub\amcc-measurement'
dir1 = os.path.join(snspd_measurement_code_dir,'instruments')
dir2 = os.path.join(snspd_measurement_code_dir,'useful_functions')
dir3 = os.path.join(snspd_measurement_code_dir,'measurement')

if snspd_measurement_code_dir not in sys.path:
    sys.path.append(snspd_measurement_code_dir)
    sys.path.append(dir1)
    sys.path.append(dir2)
    sys.path.append(dir3)

#%%import modules
    
from instruments.srs_sim970 import SIM970
from instruments.srs_sim928 import SIM928


#%% setup
volt_channel = 1
set_voltage = 5.0 
voltage_resistance = 10000
output_current = 2*set_voltage/voltage_resistance
voltmeter = SIM970('GPIB0::4',7)
source1 = SIM928('GPIB0::4', 1)
source2 = SIM928('GPIB0::4', 4)
voltmeter.set_impedance(True,volt_channel)
source1.set_voltage(voltage = set_voltage)
source2.set_voltage(voltage = set_voltage)
volt_sum = 0;
volt_count = 0;

#%%begin testing
source1.set_output(True)
source1.set_output(True)

while volt_count < 100:
    volt_count = volt_count+1
    volt_sum = volt_sum + voltmeter.read_voltage(volt_channel)
    
avg_volt = volt_sum/volt_count
avg_resistance = avg_volt/output_current

print ("Resistance = ",avg_resistance," Ohms")

source1.set_voltage(voltage = 0.0)
source2.set_voltage(voltage = 0.0)
source1.set_output(False)
source1.set_output(False)

#%% end testing