#-*- coding: utf-8 -*-
"""
Created on Thu Jul 16 13:51:16 2015

@author: qittlab
"""

import numpy as np
import serial
import time
import sys

class CTC(object):
    # def __init__(self, port=0, baud_rate=9600, time_out=1):
    # def __init__(self, serialport='/dev/ttyACM0', baud_rate=9600, time_out=1):
    def __init__(self, serialport='/dev/ttyACM0', baud_rate=9600, time_out=1):
        self.params = {}
        self.params["serialport"] = serialport
        self.params["baud_rate"] = baud_rate
        self.params["time_out"] = time_out
        # self.dev = serial.Serial('/dev/ttyACM'+str(port),
        self.dev = serial.Serial(self.params['serialport'],
              baudrate=baud_rate, timeout=time_out, rtscts=True)
        self.names = self.get_names().lower().split(str.encode(', '))
        print ('self.names',self.names)
        self.mode = "none"

    def get_names(self):
        '''Returns the names of the channels of the temperature controller'''
        msg = 'getoutputnames?'
        return self.write(msg)
    
    def get_all(self):
        '''Returns the values of all the channels in the same order as .get_names()'''
        msg = 'getoutput?'
        return self.write(msg)
        
    def set_out(self, ch_name, val=-1):
        '''Sets the value of the output of an OUT channel such as HP or Out2'''
        ch_name = ch_name.lower()
        self.check_channel_name(ch_name)
        if val != -1:
            if ch_name == "relays":
                msg = '%s.value = %i'%(ch_name, val)
            else:
                msg = '%s.value = %.3f'%(ch_name, val)
        else:
            msg = '%s.off'%ch_name
        self.write(msg)
        
    def get_val(self, ch_name):
        '''Returns the value of the channel specified'''        
        self.check_channel_name(ch_name)
        msg = '%s.value?'%ch_name
        return float(self.write(msg))
        
    def set_IO_type(self, ch_name, IO_type):
        '''Set an AIO channel (HS, SwRbias, Switchbias,Switch) to meas out,
        set out, or input'''
        IO_types = set(['meas out', 'set out', 'input'])
        if not IO_type.lower() in IO_types:
            print ('The IO type you specified is not valid')
            raise ValueError
        else:
            msg = '%s.IOtype = %s'%(ch_name, IO_type)
            self.write(msg)
        
    def writeRaw(self, msg):
        '''Write a message to the temperature controller and return response'''
        self.dev.write(msg+'\r\n')
        sys.stdout.write('working')
        return 'working!!'
#        return self.dev.readline().strip('\r\n')

    def write(self, msg):        
        '''Write a message to the temperature controller and return response'''
        self.dev.write((msg+'\r\n').encode())
        msgout = self.dev.readline().strip(str.encode('\r\n'))
        return msgout
        
    def read(self):
        '''Returns a message from the temperature controller'''
        return self.dev.readline().strip('\r\n'.encode())
        
    #def write_read(self, msg):
    #    '''Write a message to a temperature controller and return its
    #    response'''
    #    self.write(msg)
    #    return self.read()

    def pid_on(self, ch_name):
        '''Turn the PID on for specified channel'''
        self.check_channel_name(ch_name)
        msg = '%s.pid.mode = on'%ch_name
        self.write(msg)
        
    def pid_off(self, ch_name):
        '''Turn the PID off for specified channel'''
        self.check_channel_name(ch_name)
        msg = '%s.pid.mode = off'%ch_name
        self.write(msg)

    def check_channel_name(self, ch_name):
        '''A method for checking if the specified channel name is valid'''
        if not ch_name.lower().encode() in set(self.names):
            raise ValueError('The channel name you specified is not valid')
            
    def set_pid(self, ch_name, pid):
        '''Set the PID values for a channel, takes either P, [P], [P,I],
        or [P,I,D]'''
        self.check_channel_name(ch_name)
        if type(pid) in set([float, int]):
            pid = [pid]
        if len(pid) > 3:
            raise ValueError('must be a list of length 3 or less')
        if len(pid) > 0:
            self.write('%s.pid.p = %0.3f'%(ch_name, pid[0]))
        if len(pid) > 1:
            self.write('%s.pid.i = %0.3f'%(ch_name, pid[1]))
        if len(pid) > 2:
            self.write('%s.pid.d = %0.3f'%(ch_name, pid[3]))
            
    def set_pid_input(self, ch_name, input_ch_name, setpoint):
        '''Set the input channel for PID control'''
        self.check_channel_name(ch_name)
        self.check_channel_name(input_ch_name)
        self.write('%s.pid.input = %s'%(ch_name, input_ch_name))
        self.write('%s.pid.setpoint = %.3f'%(ch_name, setpoint))

    def set_limits(self, ch_name, low_lmt, hi_lmt):
        '''Set the low and high limits of an output channel'''
        self.check_channel_name(ch_name)
        self.write('%s.Lowlmt = %.3f'%(ch_name, low_lmt))
        self.write('%s.Hilmt = %.3f'%(ch_name, hi_lmt))
    
    def set_units(self, ch_name, units):
        '''Set the units of a channel: V, K, mK, C, F, W, A]'''
        if units.lower() in set(['c', 'f']):
            units = '\xb0'+units
        self.check_channel_name(ch_name)
        unit_types = set(['v', '\xb0c', 'k', 'mk', '\xb0f', 'w', 'a'])
        if not units.lower() in unit_types:
            print ('not a valid unit type')
            raise ValueError
        self.write('%s.units = %s'%(ch_name, units))

    def set_cal_type(self, ch_name, cal_type):
        '''Set whether a channel uses a calibration file off the USB drive
        or a built in calibration'''
        self.check_channel_name(ch_name)
        cal_types = set(['file, standard'])
        if not cal_type.lower() in cal_types:
            print ('not a valid calibration type')
            raise ValueError
        self.write('%s.cal.type = %s'%(ch_name, cal_type))
    
    def set_up_switch_thermometer(self):
        '''This method runs to set up the reading the switch temperature'''
        self.set_IO_type('SwRbias', 'Input')
        self.set_units('SwRbias', 'v')
        self.set_IO_type('Switchbias', 'setout')
        self.set_limits('Switchbias', 0, 3)
        self.set_units('Switchbias', 'v')
        self.set_pid_input('Switchbias', 'SwRbias', 0.98)
        self.set_pid('Switchbias', [0.9, 0.5, 0])
        self.set_IO_type('Switch', 'input')
        self.set_cal_type('Switch', 'file')

    def primingMode(self):
        self.set_out('hs',0)
        time.sleep(0.5)
        self.set_out('relays',3)
        time.sleep(0.5)
        self.pid_on('hp')
        self.mode = "priming"

    def coolingMode(self):
        self.pid_off('hp')
        time.sleep(0.5)
        self.set_out('hp',0)
        time.sleep(0.5)
        self.set_out('relays',0)
        time.sleep(0.5)
        self.set_out('hs',3.5)
        self.mode = "cooling"
    
    def getMode(self):
        return self.mode
