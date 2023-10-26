# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 14:30:29 2022

@author: dsr1
"""

import pyvisa as visa

class Agilent34970a(object):
    """Python class for Agilent 33250a 80MHz Frequency Generator, written by Adam McCaughan"""

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
        self.write('*RST')
        
    """
    NOTE: Channel convention: (@number1number2number3)
    For 4x8 switching matrix, unit 34904A
        number1: slot number
        number2: row
        number3: column
            eg: (@123) is slot 1, row 2, column 3
            can also do range: (@105:110,215)
                The scan list now contains channels 5 through 10
                (slot 100) and channel 15 (slot 200).
    """
    
    def switch_open_channel(self, ch_list): #opens channel, can be a list
        
        self.write('ROUTe:OPEN (@%s)' %ch_list) #closes channel, can be a list
    
    def switch_close_channel_exclusive(self, ch_list):
        
        self.write('ROUTe:CLOSe:EXCLusive (@s)' %ch_list)
     
    def switch_close_channel(self, ch_list):
        
        self.write('ROUTe:CLOSe (@%s)' %ch_list)







