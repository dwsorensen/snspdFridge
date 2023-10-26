import pyvisa as visa

class SIM970(object):
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


    def read_voltage(self, channel = 1):
        # In a string, %0.4e converts a number to scientific notation
        self.write('CONN %d,"xyz"' % self.sim900port)
        v = float(self.query('VOLT? %s' % channel))
        self.write('xyz')
        return v

    def set_impedance(self, gigaohm = False, channel = 1):

        # In a string, %0.4e converts a number to scientific notation
        self.write('CONN %d,"xyz"' % self.sim900port)
        if gigaohm is True:
            # First set autoranging bits to not control the attenuator / divider
            self.write('AUTO %s,13' % (channel))
            # Then set the divider manually
            self.write('DVDR %s,2' % (channel))
        else:
            self.write('AUTO %s,15' % (channel))
            self.write('DVDR %s,1' % (channel))
        self.write('xyz')
        
    def set_range(self, autorange = False, voltage_max = 200e-3, channel = 1):
        if voltage_max not in {200e-3, 1, 2, 20}:
            raise ValueError('voltage_max argument must be one of {200e-3, 1, 2, 20}')
        self.write('CONN %d,"xyz"' % self.sim900port)
        vmax_str = {200e-3 : '200', 1 : '1000', 2 : '2', 20 : '20'}[voltage_max]
        if autorange is True:
            self.write('AUTO %s,ALL' % (channel))
        else:
            self.write('AUTO %s,OFF' % (channel))
            self.write('SCAL %s,%s' % (channel,vmax_str))
        self.write('xyz')
            


# dmm = SIM970(visa_name = 'GPIB0::24', sim900port = 2)
# dmm.read_voltage(channel = 2)