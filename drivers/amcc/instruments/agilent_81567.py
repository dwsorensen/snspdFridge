import pyvisa as visa

class Agilent81567(object):
    """Python class for a generic SCPI-style instrument interface,
    written by Adam McCaughan"""
    def __init__(self, visa_name, slot):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        self.slot = slot
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands

    def read(self):
        return self.pyvisa.read()
    
    def write(self, string):
        self.pyvisa.write(string)

    def query(self, string):
        return self.pyvisa.query(string)

    def close(self):
        self.pyvisa.close()
        
    def reset(self):
        self.write('*RST')

    def identify(self):
        return self.query('*IDN?')

    def set_attenuation(self, attuation_db):
        """Set the attenuation"""
        self.write('INP%s:ATT %s'% (str(self.slot),str(attuation_db)))

    def get_attenuation(self):
        """Set the attenuation"""
        return float(self.query('INP%s:ATT?'% (str(self.slot))))

    def set_enable(self, enable = True):
        """Set the attenuation"""
        if enable == True:
            self.write('OUTP%s:STAT ON' % (self.slot))
        else:
            self.write('OUTP%s:STAT OFF' % (self.slot))

    def get_power(self):
        return float(self.query('OUTP%s:POW?' % (self.slot)))


    def set_power_control(self, watts, enable = True):
        if enable == True:
            self.write('OUTP%s:POWER:CONTROL ON' % (self.slot))
            self.write('OUTP%s:POW  %0.6e' % (self.slot, watts))
        else:
            self.write('OUTP%s:POWER:CONTROL OFF' % (self.slot))


# g = GenericInstrument('GPIB0::24')
# g.identify()




