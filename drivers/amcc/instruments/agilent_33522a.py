

import pyvisa as visa
import numpy as np

class Agilent33522a(object):
    """Python class for Agilent 33522a 30MHz 2-channel
    arbitrary waveform generator, written by Adam McCaughan"""

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

    def reset(self):
        self.write('*RST')
        
    def identify(self):
        return self.query('*IDN?')

    def set_trigger(self, external_trigger = False, delay = 0.0, channel = 1):
        if external_trigger:    self.write('TRIG%s:SOUR EXT' % channel)
        else:                   self.write('TRIG%s:SOUR IMM' % channel)
        self.write('TRIG:DEL %s' % (delay)) # Delay in seconds

    def trigger_now(self, channel = 1):
        self.write('TRIG%s' % channel)


    def set_freq(self, freq=1000, channel = 1):
        self.write('SOUR%s:FREQ %0.6e' % (channel, freq))
        
    def get_freq(self, channel = 1):
        return float(self.query('SOUR%s:FREQ?' % channel))

    def set_vpp(self, vpp=0.1, channel = 1):
        self.write('SOUR%s:VOLT %0.6e' % (channel, vpp))

    def get_vpp(self, channel = 1):
        return float(self.query('SOUR%s:VOLT?' % channel))
        
    def set_voffset(self, voffset = 0.0, channel = 1):
        self.write('SOUR%s:VOLT:OFFS %0.6e' % (channel, voffset))

    def set_output(self,output=False, channel = 1):
        if output is True:  self.write('OUTPUT%s ON' % channel)
        else:               self.write('OUTPUT%s OFF' % channel)

    def set_load(self, high_z=False, channel = 1):
        if high_z is True:  self.write('OUTP%s:LOAD INF' % channel)
        else:               self.write('OUTP%s:LOAD 50' % channel)

    def set_arb_wf(self, t = [0.0, 1e-3], v = [0.0,1.0], dt = 1e-4, channel = 1):
        """ Input voltage values will be scaled to +/-1.0, you can then adjust the overall
        amplitude using the set_vpp function.  The 33250a does not allow the input of time for each
        point, so we instead use interpolation here to create waveform of 2^14 equally-spaced 
        points, after which you can use set_freq to get the desired freq"""


        t = np.array(t);  v = np.array(v)

        vpp = max(v) - min(v)
        voffset = (max(v) + min(v))/2
        v = v-min(v);  v = 2*v/max(v);  v = v-1
        # Change timeout to 60 sec to allow writing of waveform
        temp = self.pyvisa.timeout; self.pyvisa.timeout = 20e3
        total_time = t[-1] - t[0]
        num_samples = total_time/dt

        t_interp = np.linspace(t[0],t[-1], num_samples)
        v_interp = np.interp(t_interp, t, v)

        data_strings = ['%0.3f' % x for x in v_interp]
        data_msg = ', '.join(data_strings)

        self.write('SOURCE%s:FUNC ARB' % channel)
        self.write('SOURce%s:DATA:VOLatile:CLEar' % channel)
        self.write('SOURce%s:DATA:ARB TEMPARB%s, %s' % (channel, channel, data_msg))
        self.write('SOURce%s:FUNCtion:ARBitrary TEMPARB%s' % (channel, channel))

        sample_rate = num_samples/total_time
        if (sample_rate > 250e6):
            raise ValueError('[Agilent33522a] set_arb_wf() sample rate too high (tried %0.6e Sa/s, 250 MSa/s max)' % sample_rate)
        self.write('SOURce%s:FUNCtion:ARBitrary:SRATe %0.6e' % (channel, sample_rate))
        self.set_vpp(vpp, channel = channel)
        self.set_voffset(voffset, channel = channel)

    def sync_arbs(self):
        """ Makes sure the first point of each arb waveform lines up initially """
        self.write('SOURCE:FUNC:ARB:SYNC')


    # def set_sin(self, freq=1000, vpp=0.1, voffset=0):
    #     # In a string, %0.6e converts a number to scientific notation like
    #     # print '%.6e' %(1234.56789) outputs '1.234568e+03'
    #     self.write('APPL:SIN %0.6e HZ, %0.6e VPP, %0.6e V' % (freq,vpp,voffset))

    # def set_pulse(self, freq=1000, vlow=0.0, vhigh=1.0, width = 100e-6, edge_time = 1e-6):
    #     vpp = vhigh-vlow
    #     voffset = vpp/2
    #     self.write('APPL:PULS %0.6e HZ, %0.6e VPP, %0.6e V' % (freq,vpp,voffset))
    #     self.write('PULS:WIDT %0.6e' % (width))
    #     self.write('PULS:TRAN %0.6e' % (edge_time))


    # def set_freq(self, freq=1000):
    #     self.write('FREQ %0.6e' % (freq))
        
    # def get_freq(self):
    #     return float(self.query('FREQ?'))

    # def set_vpp(self, vpp=0.1):
    #     self.write('VOLT %0.6e' % (vpp))

    # def get_vpp(self):
    #     return float(self.query('VOLT?'))
        
    # def set_voffset(self, voffset = 0.0):
    #     self.write('VOLT:OFFS %0.6e' % (voffset))

    # def set_vhighlow(self, vlow=0.0, vhigh=1.0):
    #     if vhigh > vlow:
    #         self.set_vpp(vhigh-vlow)
    #         self.set_voffset((vhigh+vlow)/2.0)
    #         self.set_polarity(inverted = False)
    #     elif vhigh < vlow:
    #         self.set_vpp(vlow-vhigh)
    #         self.set_voffset((vhigh+vlow)/2.0)
    #         self.set_polarity(inverted = True)

    # def set_output(self,output=False):
    #     if output is True:  self.write('OUTPUT ON')
    #     else:               self.write('OUTPUT OFF')

    # def set_load(self, high_z=False):
    #     if high_z is True:  self.write('OUTP:LOAD INF')
    #     else:               self.write('OUTP:LOAD 50')

    # def set_polarity(self, inverted = False):
    #     if inverted is True:  self.write('OUTP:POL INV')
    #     else:               self.write('OUTP:POL NORM')

    # def set_trigger(self, external_trigger = False, delay = 0.0):
    #     if external_trigger:    self.write('TRIG:SOUR EXT' )
    #     else:                   self.write('TRIG:SOUR IMM' )
    #     self.write('TRIG:DEL %s' % (delay)) # Delay in seconds


    # def trigger_now(self):
    #     self.write('*TRG')


    # def set_burst_mode(self, burst_enable = True, num_cycles = 1, phase = 0):
    #     if burst_enable:
    #         self.write('BURS:STAT ON') # Enables burst state
    #         self.write('BURS:NCYC %s' % (num_cycles))
    #         self.write('BURS:PHAS %s' % (phase)) # Phase in degrees

    #     else:
    #         self.write('BURS:STAT OFF')  # Disables burst state
        

    # def set_arb_wf(self, t = [0.0, 1e-3], v = [0.0,1.0], name = 'ARB_PY'):
    #     """ Input voltage values will be scaled to +/-1.0, you can then adjust the overall
    #     amplitude using the set_vpp function.  The 33250a does not allow the input of time for each
    #     point, so we instead use interpolation here to create waveform of 2^14 equally-spaced 
    #     points, after which you can use set_freq to get the desired freq"""

    #     t = np.array(t);  v = np.array(v)

    #     v = v-min(v);  v = 2*v/max(v);  v = v-1
    #     # Change timeout to 60 sec to allow writing of waveform
    #     temp = self.pyvisa.timeout; self.pyvisa.timeout = 60e3
    #     t_interp = np.linspace(t[0],t[-1],2**14) # Can be up to 2**14 long
    #     v_interp = np.interp(t_interp, t, v)

    #     data_strings = ['%0.3f' % x for x in v_interp]
    #     data_msg = ', '.join(data_strings)

    #     self.write('DATA VOLATILE, ' + data_msg) # Form of "DATA VOLATILE, 1, .67, .33, 0, -.33", p200 user's guide
    #     name = name[0:8].upper()
    #     self.write('DATA:COPY %s, VOLATILE' % name)
    #     self.write('APPL:USER')  # Set output to ARB
    #     self.write('FUNC:USER %s' % name) # Select the waveform in the volatile memory
    #     self.write('APPL:USER')
    #     self.timeout = temp
    #     # self.write('FUNC USER') # Output the selected waveform

    # def setup_heartbeat_wf(self):
    #     heartbeat_t = [0.0, 4.0/8, 5.0/8, 6.0/8,  7.0/8, 8.0/8]
    #     heartbeat_v = [0.0,   0.0,   1.0,   0.0,   -1.0,   0.0]
    #     freq_gen.set_arb_wf(t = heartbeat_t, v = heartbeat_v, name = 'HEARTBEA')


    # def select_arb_wf(self, name = 'HEARTBEA'):
    #     name = name[0:8].upper()
    #     self.write('APPL:USER')  # Set output to ARB
    #     self.write('FUNC:USER %s' % name)
    #     self.write('APPL:USER')  # Set output to ARB