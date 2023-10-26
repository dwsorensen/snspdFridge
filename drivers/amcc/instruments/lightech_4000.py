import pyvisa as visa

class LT4000(object):
    """Python class for a generic SCPI-style instrument interface,
    written by Adam McCaughan. Edited 10/21 by sonia buckley for LightTech LT4000
    programmable variable optical attenuator with on-off shutter"""
    
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands

    def read(self):
        return self.pyvisa.read()
    
    def write(self, string):
        self.pyvisa.write(string+'\n')

    def query(self, string):
        return self.pyvisa.query(string+'\n')

    def close(self):
        self.pyvisa.close()
        
    def reset(self):
        self.write('*RST\n')

    def identify(self):
        return self.query('*IDN?\n')

    def set_attenuation(self, module_no, att): #Modules 1-3 are attenuators. I think a number between 0 and 800
        self.write('SWITCH:'+str(module_no)+':'+str(att)+'\n')

    def switch_on(self, module_no): # Modules 4-6 are switches
        self.write('SWITCH:'+str(module_no)+':'+'2\n')

    def switch_off(self, module_no):
        self.write('SWITCH:'+str(module_no)+':'+'1\n')

# g = GenericInstrument('GPIB0::24')
# g.identify()




