import pyvisa as visa
import numpy as np
import time

class JDSHA9(object):
    """Python class for JDS HJA9 Optical Attenuator, written by Adam McCaughan."""

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

    def set_wavelength(self, wavelength_nm = 1550):
        self.write((':INP:WAV %d nm' % wavelength_nm))

    def set_attenuation(self, attenuation_db = 10):
        self.write((':INP:ATT %0.1f dB' % attenuation_db))


    def set_beam_block(self, beam_block = True):
        self.write((':OUTP:STAT %d' % (not beam_block)))


# att = JDSHA9('GPIB0::10')
