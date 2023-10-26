import pyvisa as visa

class SIM922(object):
    """Python class for SRS SIM928 Isolated Voltage Source inside a SIM900
    mainframe, written by Adam McCaughan"""
    def __init__(self, visa_name, sim900port):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands
        self.sim900port = sim900port
        # Anything else here that needs to happen on initialization
        # Configure the termination characters
        self.write('CEOI ON')
        self.write('EOIX ON')

    def read(self):
        return self.pyvisa.read()
    def write(self, string):
        self.pyvisa.write(string)
    def query(self, string):
        return self.pyvisa.query(string)
    def reset(self):
        self.write_simport('*RST')
    def close(self):
        return self.pyvisa.close()
    def identify(self):
        return self.query_simport('*IDN?')


    def write_simport(self, message):
        write_str = 'SNDT ' + str(self.sim900port) + ',\"' + message + '\"'
        # print write_str
        self.write(write_str) # Format of 'SNDT 4,\"GAIN 10\"'

    def read_simport(self):
        self.query('GETN? %s' % self.sim900port)

    def query_simport(self, message):
        write_str = 'SNDT ' + str(self.sim900port) + ',\"' + message + '\"'
        self.write_simport(write_str)
        return self.query(write_str) # Format of 'SNDT 4,\"GAIN 10\"'


    def read_temp(self, channel = 1):
        # In a string, %0.4e converts a number to scientific notation
        self.write('CONN %d,"xyz"' % self.sim900port)
        v = float(self.query('TVAL? %s' % channel))
        self.write('xyz')
        return v

#temp_reader = SIM922('GPIB0::6', sim900port = 1)
#temp_reader.read_temp(2)