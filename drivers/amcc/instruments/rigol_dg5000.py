

import pyvisa as visa
import numpy as np
import time

class RigolDG5000(object):
    """Python class for the Rigol DG5000 series arbitrary waveform
    generators, written by Adam McCaughan"""

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

    def align_phase(self, channel = 1):
        time.sleep(0.5)
        self.write(':SOUR%s:PHAS:INIT' % channel)


    def set_output(self, output=False, channel = 1):
        if output is True:  self.write('OUTPUT%s ON' % channel)
        else:               self.write('OUTPUT%s OFF' % channel)


    def set_impedance(self, ohms='INF', channel = 1):
        self.write('OUTPUT%s:IMP %s' % (channel,ohms))


    def set_load(self, ohms = 'INF', channel = 1):
        # `ohms` should be the number of ohms or the word 'INF' for high-impedance
        self.write('OUTP%s:LOAD %s' % (channel, ohms))

    def set_polarity(self, inverted = False, channel = 1):
        if inverted is True:  self.write('OUTP%s:POL INV' % channel)
        else:               self.write('OUTP%s:POL NORM' % channel)

    def set_voffset(self, voffset = 0.0, channel = 1):
        self.write(':SOUR%s:VOLT:OFFS %0.6e' % (channel, voffset))

    def set_vpp(self, vpp=0.1, channel = 1):
        self.write(':SOUR%s:VOLT %0.6e' % (channel, vpp))

    def get_vpp(self, channel = 1):
        return float(self.query(':SOUR%s:VOLT?' % (channel)))

    def set_vhigh(self, vhigh = 1, channel = 1):
        self.write('SOUR%s:VOLT:HIGH %0.6e' % (channel, vhigh))

    def set_vlow(self, vlow = 1, channel = 1):
        self.write('SOUR%s:VOLT:LOW %0.6e' % (channel, vlow))

    def set_vhighlow(self, vlow=0.0, vhigh=1.0, channel = 1):
        if vhigh > vlow:
            self.set_vpp(vhigh-vlow, channel = channel)
            self.set_voffset((vhigh+vlow)/2.0, channel = channel)
            self.set_polarity(inverted = False, channel = channel)
        elif vhigh < vlow:
            self.set_vpp(vlow-vhigh, channel = channel)
            self.set_voffset((vhigh+vlow)/2.0, channel = channel)
            self.set_polarity(inverted = True, channel = channel)

    def set_freq(self, freq=1000, channel = 1):
        self.write('SOUR%s:FREQ %0.6e' % (channel, freq))
        
    def get_freq(self, channel = 1):
        return float(self.query('SOUR%s:FREQ?' % channel))

    def set_period(self, period=1e-6, channel = 1):
        self.write('SOUR%s:PER %0.6e' % (channel, period))

    def setup_sin(self, freq=1000, vpp=0.1, voffset=0, phase = 0, channel = 1):
        self.write('SOUR%s:APPL:SIN %0.6e, %0.6e, %0.6e, %0.6e' % (channel, freq, vpp, voffset, phase))

    def setup_square(self, freq=1000, vpp=0.1, voffset=0, phase = 0, channel = 1):
        self.write('SOUR%s:APPL:SQU %0.6e, %0.6e, %0.6e, %0.6e' % (channel, freq, vpp, voffset, phase))

    def setup_dc(self, voffset = 0.1, channel = 1):
        self.write('SOUR%s:FUNC:SHAP DC' % (channel))
        self.set_voffset(voffset, channel)

    def setup_ramp(self, freq=1000, vpp=0.1, voffset=0, symmetry_percent = 100, channel = 1):
        self.write('SOUR%s:APPL:RAMP %0.6e, %0.6e, %0.6e' % (channel, freq, vpp, voffset))
        self.write('SOUR%s:FUNC:RAMP:SYMM %s' % (channel, symmetry_percent))

    def setup_pulse(self, freq=1000, vlow=0, vhigh=0.1, width = 100e-9, rise = 5e-9, fall = None, delay = 0, channel = 1):
        if fall is None: fall = rise
        vpp = vhigh-vlow
        voffset = (vhigh+vlow)/2
        self.write('SOUR%s:APPL:PULS %0.6e, %0.6e, %0.6e, %0.6e' % (channel, freq, vpp, voffset, delay))
        self.write('SOUR%s:PULS:WIDT %0.6e' % (channel, width))
        self.write('SOUR%s:PULS:TRAN:LEAD %0.6e' % (channel, rise))
        self.write('SOUR%s:PULS:TRAN:TRA %0.6e' % (channel, fall))

    def set_pulse_width(self, width = 100e-9, channel = 1):
        self.write('SOUR%s:PULS:WIDT %0.6e' % (channel, width))

    def set_pulse_edge(self, rise = None, fall = None, channel = 1):
        if fall is None: fall = rise
        self.write('SOUR%s:PULS:TRAN:LEAD %0.6e' % (channel, rise))
        self.write('SOUR%s:PULS:TRAN:TRA %0.6e' % (channel, fall))


    # def set_trigger(self, trigger_source = 'MAN', channel = 1):
    #     if trigger_source.upper() == 'INT':   self.write(':SOUR%s:TRIG:SOUR INT' % channel)
    #     elif trigger_source.upper() == 'EXT': self.write(':SOUR%s:TRIG:SOUR EXT' % channel)
    #     elif trigger_source.upper() == 'MAN': self.write(':SOUR%s:TRIG:SOUR MAN' % channel)
    #     else:
    #         raise ValueError("trigger_source must be 'INT' or 'EXT' or 'MAN'")
    #     # self.write('TRIG:DEL %s' % (delay)) # Delay in seconds


    def trigger_now(self, channel = 1):
        self.write('SOUR%s:BURS:TRIG:IMM' % (channel))



    def set_burst_mode(self, burst_enable = True, num_cycles = 1, phase = 0, trigger_source = 'MAN', channel = 1):
        if burst_enable == False:
            self.write(':SOUR%s:BURS:STAT OFF' % channel) # Disables burst state
            return

        self.write(':SOUR%s:BURS:STAT ON' % channel) # Enables burst state
        self.write(':SOUR%s:BURS:MODE TRIG' % channel) # Enables triggered mode
        self.write(':SOUR%s:BURS:NCYC %i' % (channel, num_cycles)) 
        self.write(':SOUR%s:BURS:PHAS %i' % (channel, phase))  # Phase in degrees

        if   trigger_source.upper() == 'INT': self.write(':SOUR%s:BURS:TRIG:SOUR INT' % channel)
        elif trigger_source.upper() == 'EXT': self.write(':SOUR%s:BURS:TRIG:SOUR EXT' % channel)
        elif trigger_source.upper() == 'MAN': self.write(':SOUR%s:BURS:TRIG:SOUR MAN' % channel)
        else:
            raise ValueError("trigger_source must be 'INT' or 'EXT' or 'MAN'")

        

    def setup_arb_wf(self, t = [0.0, 1e-3, 3e-3, 8e-3], v = [0.0,1.0, 0.2, 2.0], num_pts = 1000, channel = 1):
        """ Input voltage values will be scaled to +/-1.0, you can then adjust the overall
        amplitude using the set_vpp function.  The DG5000 does not allow the input of time for each
        point, so we instead use interpolation here to create waveform of num_pts equally-spaced 
        points, after which you can use set_freq to get the desired freq"""

        t = np.array(t);  v = np.array(v)

        v = v-min(v);  v = 2*v/max(v);  v = v-1
        # Change timeout to 60 sec to allow writing of waveform
        temp = self.pyvisa.timeout; self.pyvisa.timeout = 60e3
        t_interp = np.linspace(t[0],t[-1], num_pts) # Can be up to 512 kpts long
        v_interp = np.interp(t_interp, t, v)

        data_strings = ['%0.3f' % x for x in v_interp]
        data_msg = ', '.join(data_strings)

        self.set_vpp(self.get_vpp(channel = channel), channel = channel) # Hack to select a channel
        self.write('DATA VOLATILE, ' + data_msg) # Form of "DATA VOLATILE, 1, .67, .33, 0, -.33", p200 user's guide
        self.write('DATA:POIN:INT LIN') # Set it to linearly interpolate between points
        self.timeout = temp

    def setup_arb_wf_raw(self, voltages = [-1.0, 0.0, 0.5, 0.5, 0.75, 1, 0], channel = 1, normalize = False):

        if normalize:
            voltages = np.array(voltages)
            voltages = voltages - min(voltages)
            voltages = voltages/max(voltages)*2 -1

        temp = self.pyvisa.timeout; self.pyvisa.timeout = 60e3

        # data_strings = ['%0.3f' % x for x in v_interp]
        # data_msg = ', '.join(data_strings)


        #byte_list = []
        #dac_voltage_list = []
        dac_string = ''
        for n, v in enumerate(voltages):
            dac_voltage = int((v+1)/2*(2**14-1))
            dac_string += str(dac_voltage) + ','
        #    dac_voltage_list.append(dac_voltage)
        #    new_datapoint = struct.pack('<H', dac_voltage)
        #    byte_list.append(new_datapoint)
        dac_string = dac_string[:-1]

        self.set_vpp(self.get_vpp(channel = channel), channel = channel) # Hack to select a channel

        self.write(':DATA:DAC VOLATILE,' + dac_string)


        # self.write('DATA VOLATILE, ' + data_msg) # Form of "DATA VOLATILE, 1, .67, .33, 0, -.33", p200 user's guide
        self.query('*OPC?')
        self.write('DATA:POIN:INT OFF') # Set it to linearly interpolate between points
        self.timeout = temp



    def setup_arb_wf_raw_16k_increments(self, voltages = np.linspace(-1,1, 16384), channel = 1, normalize = False):

        self.set_vpp(self.get_vpp(channel = channel), channel = channel) # Hack to select a channel

        if normalize:
            voltages = np.array(voltages)
            voltages = voltages - min(voltages)
            voltages = voltages/max(voltages)*2 -1

        if len(voltages) % 16384 != 0:
            raise ValueError('Length of `voltages` array must be a multiple of 16384')

        while len(voltages) > 0:
            header_string = ':DATA:DAC16 VOLATILE,'
            if len(voltages) > 16384:
                header_string += 'CON,'
                voltages_to_write = voltages[:16384]
                voltages = voltages[16384:]
            else:
                header_string += 'END,'
                voltages_to_write = voltages
                voltages = []
            
            data_bytes = bytearray()
            for v in voltages_to_write:
                dac_voltage = int((v+1)/2*(2**14-1))
                data_bytes += struct.pack('<H', dac_voltage)
                
            len_body_bytes = len(data_bytes)
            num_digits_body_bytes = len(str(len_body_bytes))
            hash_string = '#' + str(num_digits_body_bytes) + str(len_body_bytes)
            
            dac_bytes = header_string.encode() + hash_string.encode() + data_bytes + '\n'.encode()
            self.pyvisa.write_raw(bytes(dac_bytes))

        # self.write('FUNC USER') # Output the selected waveform

    # def setup_heartbeat_wf(self):
    #     heartbeat_t = [0.0, 4.0/8, 5.0/8, 6.0/8,  7.0/8, 8.0/8]
    #     heartbeat_v = [0.0,   0.0,   1.0,   0.0,   -1.0,   0.0]
    #     freq_gen.set_arb_wf(t = heartbeat_t, v = heartbeat_v, name = 'HEARTBEA')


    # def select_arb_wf(self, name = 'HEARTBEA'):
    #     name = name[0:8].upper()
    #     self.write('APPL:USER')  # Set output to ARB
    #     self.write('FUNC:USER %s' % name)
    #     self.write('APPL:USER')  # Set output to ARB