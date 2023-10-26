import pyvisa as visa
import numpy as np
import time


class Agilent53131a(object):
    """Python class for Agilent 53131a counter, written by Adam McCaughan
    Use like c = Agilent53131a('GPIB0::3')"""
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

    def set_impedance(self, ohms = 50, channel = 1):
        self.write(':INP%s:IMP %s' % (channel, ohms)) # Set input impedance to 50 ohms
        
    def set_hysteresis(self, hysteresis_percent = 50, channel = 1):
        self.write(':EVEN%s:HYST:REL %i' % (channel, hysteresis_percent)) # Set hysteresis (?)

    def set_coupling(self, dc = True, channel = 1):
        if dc == True: 
            self.write(':INP%s:COUP DC' % (channel))
        else: 
            self.write(':INP%s:COUP AC' % (channel))
            
    def setup_totalize(self, continuous = True, channel = 1):
#        self.write(':FUNC "TOT 1"') # Totalize on channel 1
        self.write(':CONF:TOT:CONT')

    def set_100khz_filter(self, filter = False, channel = 1):
        if filter == True:
            self.write(':INP%s:FILT ON' % (channel))
        if filter == False:
            self.write(':INP%s:FILT OFF' % (channel))
        
    def start_totalize(self):
        self.write(':INIT:IMM')
        
    def stop_totalize(self):
        self.write(':ABORT')
        return int(float(self.query(':FETCH?')))
    
        
    def set_trigger(self, trigger_voltage = 0.500, slope_positive = True, channel = 1, trigger_level_auto = False):
        if slope_positive == True:
            trigger_slope = 'POS'
        else:
            trigger_slope = 'NEG'
        self.write(':EVEN%s:SLOP %s' %  (channel, trigger_slope)) # Or POS. Trigger on negative slope
        
        if trigger_level_auto is False:
            self.write(':EVEN:LEV:AUTO OFF') # Turn off auto trigger level
            self.write(':EVEN%s:LEV %0.3fV' % (channel, trigger_voltage)) # Set trigger level

    def setup_timed_count(self, channel = 1):
        self.write(':INP:FILT OFF') # Turn off 100kHz lowpass filter
        self.write(':FUNC "TOT %s"' % channel) # Totalize on channel 1
        self.write(':TOT:ARM:STAR:SOUR IMM') # Set start source to immediate (run on command)
        self.write(':TOT:ARM:STOP:SOUR TIM') # Set stop source to time (wait certain time)


    def setup_ratio(self):
        self.write(':FUNC "FREQ:RAT 1,2"') # Get ratio between 1 and 2
        self.write(':FREQ:ARM:STAR:SOUR IMM') # Set start source to immediate (run on command)
        self.write(':FREQ:ARM:STOP:SOUR TIM') # Set stop source to time (wait certain time)

    def timed_count(self, counting_time = 0.1):
        self.write(':TOT:ARM:STOP:TIM %0.3f' % counting_time) # Set stop time to # of seconds
        dcr = self.query(':READ?')
        dcr = float(dcr)
        # time.sleep(counting_time + 0.1)
        return dcr

    def timed_frequency_ratio(self, counting_time = 0.1):
        self.write(':FREQ:ARM:STOP:TIM %0.3f' % counting_time) # Set stop time to # of seconds
        ratio = float(self.query(':READ?'))
        return ratio

    def counts_vs_time(self, trigger_voltage= -0.075, counting_time=0.1, total_time=2):
        self.set_trigger(trigger_voltage)
        num_tests = int(total_time/counting_time)
        dcr = []
        t = []
        start_time = time.time()
        for n in range(num_tests):
            dcr.append(self.get_dcr(counting_time))
            t.append(time.time() - start_time)

        return  t, dcr
    

    def scan_trigger_voltage(self, voltages=np.linspace(0,0.1,40), counting_time=0.1):
        counts_list = []
        for v in voltages:
            self.set_trigger(v)
            time.sleep(0.1)
            counts = self.timed_count(counting_time)
            counts_list.append(counts)
            print(('Trigger voltage = %0.3f  /  Count rate %0.1f' % (v, counts)))
        return voltages, np.array(counts_list)/float(counting_time)

