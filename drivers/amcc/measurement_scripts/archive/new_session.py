import sys
import os

snspd_measurement_code_dir = r'C:\Users\ProbeStation\Desktop\Di Zhu - Probe Station\snspd-measurement-code'
dir1 = os.path.join(snspd_measurement_code_dir,'instruments')
dir2 = os.path.join(snspd_measurement_code_dir,'useful_functions')
dir3 = os.path.join(snspd_measurement_code_dir,'measurement')

if snspd_measurement_code_dir not in sys.path:
    sys.path.append(snspd_measurement_code_dir)
    sys.path.append(dir1)
    sys.path.append(dir2)
    sys.path.append(dir3)
    
# Ic measurement code
# Run add_path.py first
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *
from agilent_53131a import Agilent53131a
from jds_ha9 import JDSHA9
from instruments.ThorlabsPM100_meta import *
from cryocon34 import *
import pyvisa as visa


#########################################
### Sample information
#########################################
sample_name = 'SPE725'
test_name = 'CR_DE'
filedirectry = 'C:\\Users\ProbeStation\Desktop\Di Zhu - Probe Station\SPE 725 110615'

#########################################
### Connect to instruments
#########################################

#lecroy_ip = 'touchlab1.mit.edu'; 
lecroy_ip = '18.62.10.142' 
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)
counter = Agilent53131a('GPIB0::3')
counter.basic_setup()
# cryocon = Cryocon34('GPIB0::4')
att = JDSHA9('GPIB0::5')
SRS = SIM928(4, 'GPIB0::4'); SRS.reset()
#initiate the power meter
inst = visa.instrument('USB0::0x1313::0x8078::PM002229::INSTR', term_chars='\n', timeout=1)
pm = ThorlabsPM100Meta(inst)
R_srs = 100e3

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