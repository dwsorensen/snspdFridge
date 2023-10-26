import pyvisa as visa
import numpy as np

class AgilentFieldFox(object):
    """Python class for a generic SCPI-style instrument interface,
    written by Adam McCaughan"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 30000 # Set response timeout (in milliseconds)
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
        self.write('*RST')


    # Sets measurement mode (Input 'S11' or 'S21')
    def set_mode(self, mode):
        if (mode is 'S11'):
            # Set to Network Analayser Mode
            self.write('INST:SEL "NA"')
            # Disables hold if one exists
            self.write('INIT:CONT 1')
            # Set mode to S11
            self.write('CALC:PAR:DEF S11')
            
        elif (mode is 'S21'):
            # Set to Network Analayser Mode
            self.write('INST:SEL "NA"')
            # Disables hold if one exists
            self.write('INIT:CONT 1')
            # Set mode to S11
            self.write('CALC:PAR:DEF S21')
        
    def set_num_points(self, num_points = 201):
            self.write('SWE:POIN %i' % num_points)

    # Sets frequency range
    def set_freq_range(self, f_start = 10e6, f_stop = 3e9, f_center = None, f_span = None):
        # Sets frequency range by start and stop if centre and span are not defined
        if (f_center is None) and (f_span is None):
            self.write('FREQ:STAR %0.6e' % f_start)
            self.write('FREQ:STOP %0.6e' % f_stop)
            
        # Sets frequency range by centre and span if defined
        elif (f_center is not None) and (f_span is not None):
            self.write('FREQ:CENT %0.6e' % f_center)
            self.write('FREQ:SPAN %0.6e' % f_span)

        
    # Changes the power (0 to -31 dBm in 1 dBm steps)
    def set_power(self, power_dbm = -31):
        self.write('SOUR:POW %0.1f' % power_dbm)

    # Changes format. Input 'MLOG' for dB, 'MLIN' for relative
    def set_format(self, measure_format):
        # Select measurement format
        self.write('CALC:FORM %s' % measure_format)

    # Pull whatever S21 or S11 data is on the screen - in terms of dB or absolute magnitude
    def measure(self, trace = 1):
        num_points = int(self.query('SENS:SWEEP:POINTS?'))
        freq_start = float(self.query('SENS:FREQ:STAR?'))
        freq_stop = float(self.query('SENS:FREQ:STOP?'))

        # Setup Network Analyser
        self.write('INIT:CONT 0')    # Turn off continuous sweeping
        self.query('INIT:IMM;*OPC?') # Initiate 1 sweep and wait until operation complete
        # Select trace to measure
        self.write('CALC:PAR%i:SEL' % trace)
            
        # Read data and parse into a list of floats
        magnitude_data = self.query('CALC:DATA:FDATa?')
        magnitude_data = magnitude_data.split(",")
        mags = [None] * num_points
        for i in range(0, num_points):
            mags[i] = float(magnitude_data[i])
                
        # Creating a vector of frequencies to correspond to magnitude data
        freq_range = freq_stop - freq_start
        freq_increment = freq_range / (num_points - 1)
        
        # Initialising variable "freqs" with num_points number of elements
        freqs = [None] * num_points
        for i in range(0, num_points):
            freqs[i] = freq_start + freq_increment * i

        self.write('INIT:CONT 1') # Turn back on continuous sweeping

        # Return values
        return np.array(freqs), np.array(mags)






