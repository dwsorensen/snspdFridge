import pyvisa as visa

class HP34420A(object):
    """Python class for a generic SCPI-style instrument interface,
    written by Adam McCaughan. Edited for Keysight 34420 nanovolt/microohm meter
    by Sonia Buckley 10/2021"""

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

    def identify(self):
        return self.query('*IDN?')

    def reset(self):
        return self.write('*RST')

    def setup_voltage_measurement(self):
        pass

    def setup_2wire_measurement(self):
        pass

    def setup_4wire_measurement(self):
        pass    

    def read_voltage(self):
        return float(self.query('READ?'))

    def measure_resistance(self):
        return float(self.query('READ?'))

# g = GenericInstrument('GPIB0::24')
# g.identify()