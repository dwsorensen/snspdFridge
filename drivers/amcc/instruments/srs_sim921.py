import pyvisa as visa
import numpy as np

class SIM921(object):
    """Python class for SRS SIM921 AC resistance bridge inside a SIM900
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


    # def write_simport(self, message):
    #     write_str = 'SNDT ' + str(self.sim900port) + ',\"' + message + '\"'
    #     # print write_str
    #     self.write(write_str) # Format of 'SNDT 4,\"GAIN 10\"'


    # def read_simport(self):
    #     self.query('GETN? %s' % self.sim900port)

    def write_simport(self, message):
        self.write('CONN %d,"xyz"' % self.sim900port)
        self.write(message)
        self.write('xyz')


    def read_simport(self):
        self.write('CONN %d,"xyz"' % self.sim900port)
        data = self.read()
        self.write('xyz')
        return data

    # def ask_simport(self, message):
    #     write_str = 'SNDT ' + str(self.sim900port) + ',\"' + message + '\"'
    #     self.write_simport(write_str)
    #     return self.query(write_str) # Format of 'SNDT 4,\"GAIN 10\"'

    def query_simport(self, message):
        self.write('CONN %d,"xyz"' % self.sim900port)
        reply = self.query(message)
        self.write('xyz')
        return reply

    def identify(self):
        return self.query_simport('*IDN?')

    def read_resistance(self):
        R = float(self.query_simport('RVAL?'))
        return R

    def set_range(self, max_resistance = 200):
        range_code = np.ceil(np.log10(max_resistance/(20e-3)))
        range_code = int(range_code)
        self.write_simport('RANG %s' % range_code)

    def set_excitation(self, voltage = 10e-6):
        valid_voltages = [3e-6, 10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3]
        if voltage not in valid_voltages:
            raise ValueError('Excitation voltage must be in [3e-6, 10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3]')
        excitation_code = np.where(voltage == np.array(valid_voltages))[0][0]
        self.write_simport('EXCI %s' % excitation_code)


    def set_time_constant(self, time_constant = 1):
        valid_tc = [0.3, 1, 3, 10, 30, 100, 300]
        if time_constant not in valid_tc:
            raise ValueError('Time constant must be in [0.3, 1, 3, 10, 30, 100, 300]')
        time_constant_code = np.where(time_constant == np.array(valid_tc))[0][0]
        self.write_simport('TCON %s' % time_constant_code)



    # def set_impedance(self, gigaohm = False, channel = 1):

    #     # In a string, %0.4e converts a number to scientific notation
    #     self.write('CONN %d,"xyz"' % self.sim900port)
    #     if gigaohm is True:
    #         # First set autoranging bits to not control the attenuator / divider
    #         self.write('AUTO %s,13' % (channel))
    #         # Then set the divider manually
    #         self.write('DVDR %s,2' % (channel))
    #     else:
    #         self.write('AUTO %s,15' % (channel))
    #         self.write('DVDR %s,1' % (channel))
    #     self.write('xyz')


# dmm = SIM970(visa_name = 'GPIB0::24', sim900port = 2)
# dmm.read_voltage(channel = 2)