import pyvisa as visa

class PerkinElmer7280(object):
    """Python class for Perkin Elmer 7280 DSP Lock-In Amplifier
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

    def reset(self):
        self.write('ADF 1')
        
    def identify(self):
        return self.query('*IDN?')

    def auto_measure(self):
        self.write('ASM')

    def auto_sensitivity(self):
        self.write('AS')

    def identify(self):
        return self.query('*IDN?')

    def get_R(self):
        return float(self.query('MAG.'))

    def get_phase(self):
        return float(self.query('PHA.'))

    def get_amplitude(self):
        return float(self.query('OA.'))

    def get_freq(self):
        return float(self.query('OF.'))

    def set_amplitude(self, v = 0.001):
        self.write('OA. %0.6f' % v)

    def set_freq(self, freq = 100):
        self.write('OF. %0.3e' % freq)

