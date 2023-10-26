from unittest import result
import pyvisa as visa
from time import sleep
import numpy as np
import sys
import struct

#AGILENT 8163A is a mainframe that can contain attenuators, power meters, lasers etc.

class Agilent8163A(object):
    """Python class for Agilent 8163a mainframe. This is a small mainframe that can hold power meters, 
    detectors or attenuators. Commands tested only for power meters 81532A and 81533B in slot SLOT.
    Adapted from Adam McCaughan instrument by Sonia Buckley, 03/26/2022. """
    
    ##############################
    # ALL MODULES
    ##############################
    
    def __init__(self, visa_name, slot):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        self.slot = slot
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
        self.write('*RST')

    def identify(self):     
        mainframe = self.query('*IDN?')
        sleep(0.1)
        slot_module = self.query(':SLOT%s:IDN?'%str(self.slot))
        sleep(0.1)
        return mainframe, slot_module
    
    def enable(self):
        self.write('OUTP%s:STAT ON'%(self.slot))
        
    def disable(self):
        self.write('OUTP%s:STAT OFF'%(self.slot))
        
    ##############################
    # POWER METERS
    ##############################

    def read_power(self):
        msg = ':READ%s:POW?'%(str(self.slot))
        power = self.query(msg)
        return power

    def set_pm_wavelength(self, wavelength_nm):
        """Set the wavelength in nm"""
        self.write('SENS%s:POW:WAV %sE-9'%(str(self.slot),str(wavelength_nm)))

    def set_pm_power_unit(self,unit):
        """set power meter units:0=dBm,1=W"""
        self.write(':SENS%s:POW:UNIT %s'%(str(self.slot),str(unit)))
        
    def get_pm_power_unit(self):
        """set power meter units:0=dBm,1=W"""
        result_number = self.query(':SENS%s:POW:UNIT?'%(str(self.slot)))
        if result_number == 0:
            result = 'dBm'
        elif result_number == 1:
            result = 'W'
        else:
            print("get_pm_power_unit request returned something weird.")
        return result
    
    def set_pm_averaging_time(self,averaging_time):
      """set averaging time of power meter in (s)"""
      self.write(':SENS%s:POW:ATIM %s'%(str(self.slot),str(averaging_time)))
      
    def get_pm_averaging_time(self,slot):
        """get the averaging time"""
        averaging_time = self.query(':SENS%s:POW:ATIM?'%(str(slot)))
        return averaging_time
      
    def set_pm_autorange(self,auto):
        """turn auto range off or on"""
        self.write(':SENS%s:POW:RANG:AUTO %s'%(str(self.slot),str(auto)))

    def set_pm_range(self,range):
      """set the power meter range (dBm)"""
      self.write(':SENS%s:POW:RANG %s'%(str(self.slot),str(range)))
      
    def get_pm_range(self):
        """get the range of the power meter"""
        rangevalue = self.query(':SENS%s:POW:RANG?'%str(self.slot))
        return rangevalue
        
    def init_pm_log(self,num_points,averaging_time):
        self.log_num_points = num_points
        self.write('SENS%d:FUNC:PAR:LOGG %d, %.1f\n'%(self.slot, num_points, averaging_time))
      
    def start_pm_log(self):
        self.write('SENS%d:FUNC:STAT LOGG, STAR\n'%(self.slot))
                
    def stop_pm_log(self):
        self.write('SENS%d:FUNC:STAT LOGG, STOP\n'%(self.slot))
  
    def trigger_data_logging(self):
        self.write('trig1:input ign\n')
        self.write("SENS1:FUNC:PAR:LOGG 10, 0.1\n")
        self.write("sens1:chan1:func:stat logg,star\n")
        
        while True:
            sleep(1)
            sys.stdout.write('.')
            sys.stdout.flush()
            self.write('sens1:chan1:func:stat?\n')
            
            if 'COMPLETE' in reply:
                break
      
        msgin = self.query('SENS%d:FUNC:RES?\n'%(self.slot))  

        datout = msgin[4:]
        length = len(datout)
        runs = int(length/4)
        for n in range(0, runs):
            bindat = datout[n*4:(n+1)*4]
            fltdat = struct.unpack('f', bindat)
 
    def read_pm_log(self,slot,nump):
        
        while True:
            sleep(1)
            sys.stdout.write('.')
            sys.stdout.flush()
            reply = self.query('SENS%d:FUNC:STAT?\n'%self.slot)
        
            if 'COMPLETE' in reply:
                break
        msgin = self.query('SENS%d:FUNC:RES?\n'%self.slot)  
        datout = msgin[4:]
        if nump > 20:
            datout = msgin[5:]
        length = len(datout)
        runs = int(length/4)
        print("\nreceived %d datapoints"%runs)
        
        data = []

        for n in range(0, runs):
            bindat = datout[n*4:(n+1)*4]
            fltdat = struct.unpack('f', bindat)
            data.append(fltdat[0])
        return data
    
    def pm_set_cont_trigger(self, setting):
        #set whether the pm continually updates, setting = 1 updates, 0 waits for trigger
        self.write(':INIT%i:CONT %i'%(self.slot,setting))
        
    def pm_get_cont_trigger(self):
        result = self.query(':INIT%i:CONT?'%self.slot)
        return int(result)
        
    def zero_pm(self):
        stat = 1
        while stat != 0:
            msg = 'SENS%d:CORR:COLL:ZERO'%(self.slot)
            self.write(msg)
            sleep(0.5)
            ret = self.query(msg +"?")
            while ret == "":
                ret = self.query(msg +"?")
            try: 
                temp = str(ret[1:-1])
            except: 
                temp = '1'
            if temp.isdigit():
                stat = int(str(temp))
            else:
                stat = 1
        return ret
    
    def setup_pm_basic(self, wavelength_nm = 1550, averaging_time = 0.1):
        self.reset()
        self.set_pm_averaging_time(averaging_time = averaging_time) # Sets averaging time, 20ms < value < 3600s
        self.set_pm_wavelength(wavelength_nm = wavelength_nm)

    ##############################
    # LASERS
    ##############################
    
    def set_source_lambda(self, wavelength):
        """Set the wavelength in nm"""
        self.write('SOUR%s:WAV %sE-9'%(str(self.slot),str(wavelength)))
        
    def get_source_lambda(self):
        """Get the wavelength"""
        reading = self.query(':SOUR%s:WAV?'%(str(self.slot)))
        return float(reading)    
    
    ##############################
    # ATTENUATORS
    ##############################
    
    def set_attenuation(self, attenuation):
        """Set the attenuation"""
        self.write('INP%s:ATT %s'%(str(self.slot),str(attenuation)))
