#%%
import pyvisa as visa
import array
import struct
import numpy as np


import pyvisa as visa
import array
import struct
import numpy as np


class TektronixAWG7000(object):
    """Python class for the Tektronix AWG610 Arbitrary Waveform Generator
    written by Adam McCaughan"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.write_termination = '\n'
        self.pyvisa.read_termination = '\n'
        self.pyvisa.timeout = 5000

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

#    def setup_pulse(self):
#        self.write('AWGControl:FG:STATE ON') # Sets AWG to "Function Generator" mode
#        self.write('AWGControl:FG1:FUNC PULSE')

    # def set_pulse_width(self, width):
    #     self.write('AWGControl:FG1:PULS:DCYCL %s')

    def trigger_now(self):
        self.write('*TRG')
    
    # Set sampling clock rate; range from 50 kHz to 2.6 GHz
    def set_clock(self, freq = 2.6e9):
        self.write(':FREQuency %0.3e' % freq)
        
    def create_waveform(self, voltages = np.linspace(-1,1,1000), filename = 'temp.wfm',
                        auto_fix_sample_length = False):
        if len(voltages) > 650000000: raise ValueError('voltages must be shorter than 650,000,000')
        header_string = f'WLIST:WAVEFORM:DATA "{filename}",'
        self.pyvisa.write_binary_values(header_string, voltages, datatype='H', is_big_endian=False)

    def create_marker(self,  marker1_data = [0,1,1,0], marker2_data = [1,1,1,0], filename = 'temp.mkr'):
        data = 2*np.array(marker1_data) + np.array(marker2_data)
        header_string = f'WLIST:WAVEFORM:MARKer:DATA "{filename}",'
        self.pyvisa.write_binary_values(header_string,data, datatype='B')    ### limited to 650,000,000 bytes of data

    def load_waveform(self, filename = 'temp.wfm', channel = 1):
        self.write(f'SOUR{channel}:WAV "{filename}"')

    def new_waveform(self, filename = 'temp.wfm', num_points = 1000):
        self.write('WLIST:WAVEFORM:NEW "{}", {:d}, INT'.format(filename, num_points))













    def set_vpp(self, vpp = 1.0):
        self.write(':VOLT %0.3e' % vpp)
        
    def set_voffset(self, voffset = 1.0):
        self.write(':VOLT:OFFS %0.3e' % voffset)
        
    def set_marker_vhighlow(self, vlow = 0.0, vhigh = 0.100):
        self.write(':MARK1:VOLT:LOW %0.3e' % vlow)
        self.write(':MARK1:VOLT:HIGH %0.3e' % vhigh)
        
        
    def set_marker_delay(self, delay = 0):
        if (delay < 0) or (delay > 1.5e-9):
            raise ValueError('Delay must be between 0 and 1.5e-9 sec')
        self.write(':MARK1:DEL %0.3e' % delay)
        
    # Also known as "run mode"
    def set_trigger_mode(self, trigger_mode = False, continuous_mode = False,
                         enhanced_mode = False):
        if trigger_mode:
            self.write('AWGControl:RMODE TRIG')
        if continuous_mode:
            self.write('AWGControl:RMODE CONT')
        if enhanced_mode:
            self.write('AWGControl:RMODE ENH')
    
    
    def create_waveform(self, voltages = np.linspace(-1,1,1000), filename = 'temp.wfm', clock = 2.6e9,
                        marker_data = None, auto_fix_sample_length = False):
        if auto_fix_sample_length:
            if len(voltages) < 512: voltages += [voltages[-1]]*(512-len(voltages))
            if (len(voltages) % 8) != 0: voltages += [voltages[-1]]*(8-(len(voltages) % 8))
            if marker_data is not None:
                if len(marker_data) < 512: marker_data += [marker_data[-1]]*(512-len(marker_data))
                if (len(marker_data) % 8) != 0: marker_data += [marker_data[-1]]*(8-(len(marker_data) % 8))
                
        if (len(voltages) < 512) or (len(voltages) % 8 != 0):
            raise ValueError('Length of `voltages` array must be >=512 elements and divisible by 8')
        if (max(voltages) > 1) or (min(voltages) < -1):
            raise ValueError('Values of `voltages` array must be on [-1.0,+1.0] interval')
            
        byte_list = []
        for n, v in enumerate(voltages):
            new_datapoint = struct.pack('<f',v)
            if marker_data is None:
                new_marker_data = b'\x00'
            else:
                if marker_data[n] == False:
                    new_marker_data = b'\x00'
                else:
                    new_marker_data = b'\x01'
            if n < 256: # Use marker 2 as a sync signal
                new_marker_data = bytes([new_marker_data[0] + 2])
            byte_list.append(new_datapoint)
            byte_list.append(new_marker_data)
        data_bytes = b''.join(byte_list)

        # Forming header string for the SCPI command
        header_string = 'MAGIC 1000\r\n'
        # Forming trailer string for the SCPI command
        if clock is not None:
            trailer_string = 'CLOCK %0.3e\r\n' % clock
        else:
            trailer_string = '\r\n'
        # Determining number of bytes in the data as well as digits in that
        # number to set-up hash statement
        len_body_bytes = len(data_bytes)
        num_digits_body_bytes = len(str(len_body_bytes))
        hash_string = '#' + str(num_digits_body_bytes) + str(len_body_bytes)
        # # Concatenating the data into a single string
        # byte_string = b''.join(data_bytes)
        # Combining the header, trailer, hash statement, and data
        data_bytes = header_string.encode() + hash_string.encode() + data_bytes + trailer_string.encode()
        # Returning the result
        self.write_data_to_file(data = data_bytes, filename = filename)
        
        
    def create_pulse(self, filename, width, edge_width, voltage):
        # Assumes Vpp is set to 1 V
        samples_per_s = 2.6e9
        t = [0, edge_width, edge_width+width, edge_width*2+width]
        v = [0, voltage, voltage, 0]
        t = np.array(t);  v = np.array(v)
        total_time = edge_width*2+width
        num_pts = int(total_time*samples_per_s) + 1
        t_interp = np.linspace(t[0],t[-1], num_pts) # Can be up to 512 kpts long
        v_interp = np.interp(t_interp, t, v).tolist()
        
        if len(v_interp) < 512:
            v_interp += [0]*(512-len(v_interp))
        if (len(v_interp) % 8) != 0:
            v_interp += [0]*(8-(len(v_interp) % 8))
        self.create_waveform(voltages = v_interp, filename = filename)



    def write_data_to_file(self, data, filename = 'temp.wfm'):
        len_data = len(data)
        num_digits_len_data = len(str(len_data))
        header_str = 'MMEMORY:DATA "%s",#%i%i' % (filename, num_digits_len_data, len_data)
        term_str = '\r\n'
        if type(data) is str:
            data = data.encode()
        elif type(data) is bytes:
            pass
        else:
            raise ValueError('write_string_to_file() Argument `data` must be type str or bytes')
        data_to_write = header_str.encode() + data + term_str.encode()
        self.pyvisa.write_raw(data_to_write)
    
    
    def read_file(self, filename = 'temp.wfm'):        
        self.write('MMEMORY:DATA? "%s"' % filename)
        hash_symbol = self.pyvisa.read_bytes(count = 1)
        num_digits = int(self.pyvisa.read_bytes(count = 1))
        num_digits_len_data = int(self.pyvisa.read_bytes(count = num_digits))
        file_data = self.pyvisa.read_bytes(count = num_digits_len_data)
        term_char = self.pyvisa.read_bytes(1)

        return(file_data)
        
        
    def load_file(self, filename = 'temp.wfm'):
        self.write(':FUNC:USER "%s"' % (filename))
        
        
    def set_output(self, output = False, run = True):
        if output: self.write('OUTPUT1:STATE ON')
        else:      self.write('OUTPUT1:STATE OFF')
            
        if run:    self.write('AWGControl:RUN')
        else:      self.write('AWGControl:STOP')
            
            
    def set_lowpass_filter(self, freq = None):
        if freq == None: freq = 9.9e37
        valid_freqs = [20e6, 50e6, 100e6, 200e6, 9.9e37]
        if freq in valid_freqs:
            self.write('OUTPUT1:FILTER:LPASS:FREQ %0.1E' % freq)
        else:
            raise ValueError('Lowpass filter freq must be in %s' % valid_freqs)
        
        
    def create_sequence(self, filename = 'temp.seq', wfm_filenames = ['temp.wfm', 'temp2.wfm'],
                        wfm_repeats = None, wfm_trigger_wait = None):
        
        num_waveforms = len(wfm_filenames)
        if wfm_repeats is None: wfm_repeats = [1]*num_waveforms
        if wfm_trigger_wait is None: wfm_trigger_wait = [0]*num_waveforms
        # Forming header string for the SCPI command
        header_string = 'MAGIC 3002\r\n'
        seq_string = 'LINES %i\r\n' % num_waveforms
        waveform_string_list = []
        for n, fn in enumerate(wfm_filenames):
            waveform_string_list.append('"%s", "", %i, %i, 0, 0\r\n' % (fn, wfm_repeats[n], wfm_trigger_wait[n]))
        waveform_string = ''.join(waveform_string_list)
#        wfm_dec_1 = '"%s", "", 1, 0, 0, 0\r\n' % wfm1
#        wfm_dec_2 = '"%s", "", 1, 0, 0, 0\r\n' % wfm2
        table_jump = 'TABLE_JUMP 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,\r\n'
        logic_jump = 'LOGIC_JUMP -1, -1, -1, -1,\r\n'
        jump_mode = 'JUMP_MODE TABLE\r\n'
        jump_timing = 'JUMP_TIMING ASYNC\r\n'
        strobe = 'STROBE 0'
        
        seq_data = header_string + seq_string + waveform_string + table_jump + logic_jump + jump_mode + jump_timing + strobe
        
        self.write_data_to_file(data = seq_data, filename = filename)
        return seq_data
#
#try:
#    awgw.close()
#except:
#    pass
#awgw = TektronixAWG610('TCPIP0::%s::4000::SOCKET' % '192.168.1.101')
#awgw.query('*IDN?')

#%%
        
    #created 5/2016 by MLS
#Tektronix AWG 7101A
#instrument Driver

# from . import VisaInstruments
# from . import MeasureUtils
# from MeasureUtils import fullSleep
# from pyvisa.compat.struct import unpack, unpack_from
# import numpy as np
# import math
# import struct
# import binascii

# class AWG(object):       
#     """Python class for the Tektronix AWG610 Arbitrary Waveform Generator
#     written by Adam McCaughan, adapted from code from Mike Schneider"""
#     def __init__(self, visa_name):
#         self.rm = visa.ResourceManager()
#         self.pyvisa = self.rm.open_resource(visa_name)
# #        self.pyvisa.write_termination = '\n'
# #        self.pyvisa.read_termination = '\n'
#         self.pyvisa.timeout = 5000

#     def read(self):
#         return self.pyvisa.read()
    
#     def write(self, string):
#         self.pyvisa.write(string)

#     def query(self, string):
#         return self.pyvisa.query(string)

#     def close(self):
#         self.pyvisa.close()

#     def identify(self):
#         return self.query('*IDN?')

#     def reset(self):
#         return self.write('*RST')
#     def awgInit(self):
#         self.instObj.write('*CLS')
#         self.instObj.write('*RST')
#         print(self.instObj.query('*IDN?').strip(), self.instObj.query('*OPT?').strip())
        

#     def setSampleRate(selfsampleRate):        
#         self.instObj.write(':FREQ {}MHz'.format(sampleRate))
#         print(self.instObj.query(':FREQ?'))
        
#     def setRes(self,res):
#         self.instObj.write(':DAC:RESolution {}'.format(res))
#         print(self.instObj.query(':DAC:RESolution?').strip())
        
#     def makeNewWF(self, numPoints, wfName='temp'):
#         self.instObj.write('WLIST:WAVEFORM:NEW "{}", {:d}, INT'.format(wfName, numPoints))
        
#     def loadWF(self,  data, wfName='temp'):
#         print(wfName)    
#         self.instObj.write_binary_values('WLIST:WAVEFORM:DATA "{}",'.format(wfName),data, datatype='H', is_big_endian=False)    ### limited to 650,000,000 bytes of data
#         print(self.instObj.query('WLIST:WAVEFORM:TYPE? "{}"'.format(wfName)))

        
#     def loadMarker(self,  data, wfName='temp'):        
#         self.instObj.write_binary_values('WLIST:WAVEFORM:MARKer:DATA "{}",'.format(wfName),data, datatype='B')    ### limited to 650,000,000 bytes of data

        
#     def enableWF(self, wfName='temp'):         
#         self.instObj.write('SOUR1:WAV "{}"'.format(wfName))
#         self.instObj.write('SOURCE1:VOLTAGE:AMPLITUDE 1')
#         print(self.instObj.query('SYST:ERR?'))
#         self.instObj.write('OUTP1 1')
#         self.instObj.write(':AWGC:RUN')
        
#     def disableWF(self):
#         self.instObj.write('AWGCONTROL:STOP:IMMEDIATE')
#         self.instObj.write(':AWGCONTROL:STOP:IMMEDIATE')
#         print('disable')
#         fullSleep(1)

#     def simEnable(self, wfName='wf1'):
#         self.instObj.write(':AWGC:RUN')
        
    