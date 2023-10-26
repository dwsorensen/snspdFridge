import pyvisa as visa

class ThorlabsPM100D(object):
    """Python class for Thorlabs PM100, written by Adam McCaughan."""
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

    def reset(self):
        self.write('*RST')

    def identify(self):
        return self.query('*IDN?')
        
    def close(self):
        self.pyvisa.close()


    def read_power(self):
        #
        power = float(self.query('READ?'))   # Returns power in watts
        return power


    def set_wavelength(self, lambda_nm):
        pass # Dummy function

    def set_averaging_time(self, averaging_time = 0.1):
        pass # Dummy function

    def get_average_count(self):
        return int(self.query(':SENSE:AVERAGE:COUNT?'))

    def set_average_count(self, average_count = 1):
        self.write(':SENSE:AVERAGE:COUNT %d' % average_count)