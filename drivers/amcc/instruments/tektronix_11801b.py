#%%
import pyvisa as visa
import numpy as np

class Tektronix11801B(object):
    """Python class for a Tektronix11801B digital sampling oscilloscope,
    written by Adam McCaughan"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands

    def read(self):
        return self.pyvisa.read()
    
    def write(self, string):
        self.pyvisa.write(string)

    def query(self, string):
        return self.pyvisa.query(string)

    def close(self):
        self.pyvisa.close()
        
    # def reset(self):
    #     self.write('*RST')

    def identify(self):
        return self.query('ID?')

    # Read commands on page 2-30 of programming manual
    def get_wf_data(self):
        yraw = self.query("CURVE?")
        # pre = self.query("WFMPRE?")

        # Get scaling parameters
        xincr = float(self.query("WFMPRE? XINCR")[13:-2])
        xmult = float(self.query("WFMPRE? XMULT")[13:-2])
        xzero = float(self.query("WFMPRE? XZERO")[13:-2])
        ymult = float(self.query("WFMPRE? YMULT")[13:-2])
        yzero = float(self.query("WFMPRE? YZERO")[13:-2])

        # Scale/offset Y
        yraw = yraw[:-2] # Remove \r\n from end
        y = yraw.split(',')[1:]
        y = np.array([float(z) for z in y])
        y = yzero + ymult*y

        # Scale/offset X (probably an error here, no idea)
        x = xincr*np.array(range(len(y)))

        return x,y

#%%
# t = Tektronix11801B('GPIB0::17')
# x,y = t.get_wf_data()
