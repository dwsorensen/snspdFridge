#%%
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
    
    
### Either of these works:
# import instruments.keithley_2400
# import keithley_2400