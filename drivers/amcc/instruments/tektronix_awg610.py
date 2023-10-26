#%%
import pyvisa as visa
import struct
import numpy as np

class TektronixAWG610(object):
    """Python class for the Tektronix AWG610 Arbitrary Waveform Generator
    written by Adam McCaughan"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.write_termination = '\n'
        self.pyvisa.read_termination = '\n'
        self.pyvisa.timeout = 5000
        self.fg_mode = False # Otherwise in 'AWG' mode

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
        if self.fg_mode == False:
            self.write('SOURce1:FREQuency %0.3e' % freq)
        else:
            self.write('AWGControl:FG:FREQ %0.3e' % (freq))
        
    def set_vpp(self, vpp = 1.0, channel = 1):
        if self.fg_mode == False:
            self.write('SOUR%s:VOLT %0.3e' % (channel, vpp))
        else:
            self.write('AWGControl:FG%s:VOLT %0.3e' % (channel, vpp))

    def set_voffset(self, voffset = 1.0, channel = 1):
        if self.fg_mode == False:
            self.write('SOUR%s:VOLT:OFFS %0.3e' % (channel, voffset))
        else:
            self.write('AWGControl:FG%s:VOLT:OFFS %0.3e' % (channel, voffset))

    def set_phase(self, phase = 0, channel = 1):
        if self.fg_mode == True:
            self.write('AWGControl:FG%s:PHAS %0.3fDEG' % (channel, phase))
        else:
            raise ValueError('Phase only relevant in FG mode, see set_mode()')

    def set_polarity(self, positive = True, channel = 1):
        if self.fg_mode == True:
            if positive is True: polarity = 'POS'
            else:                polarity = 'NEG'
            self.write('AWGControl:FG%s:POL %s' % (channel, polarity))
        else:
            raise ValueError('Polarity only relevant in FG mode, see set_mode()')

    def set_function_waveform(self, waveform = 'sinusoid', channel = 1):
        valid_waveforms = ['sinusoid', 'triangle', 'square', 'ramp', 'pulse', 'dc']
        if (waveform not in valid_waveforms):
            raise ValueError('Waveform/shape must be one of %s' % valid_waveforms)
        if self.fg_mode == True:
            self.write('AWGControl:FG%s:FUNC %s' % (channel, waveform))
        else:
            raise ValueError('Waveform/shape setting only relevant in FG mode, see set_mode()')

    def set_vhighlow(self, vlow = 0.0, vhigh = 0.100, channel = 1):
        self.set_voffset((vlow+vhigh)/2, channel = channel)
        self.set_vpp(vhigh-vlow, channel = channel)
        

    def set_marker_vhighlow(self, vlow = 0.0, vhigh = 0.100, marker = 1, channel = 1):
        self.write('SOUR%s:MARK%s:VOLT:LOW %0.3e' % (channel, marker, vlow))
        self.write('SOUR%s:MARK%s:VOLT:HIGH %0.3e' % (channel, marker, vhigh))
        
        
    def set_marker_delay(self, delay = 0, marker = 1, channel = 1):
        if (delay < 0) or (delay > 1.5e-9):
            raise ValueError('Delay must be between 0 and 1.5e-9 sec')
        self.write('SOUR%s:MARK%s:DEL %0.3e' % (channel, marker, delay))
        
    # Also known as "run mode"
    def set_trigger_mode(self, trigger_mode = False, continuous_mode = False,
                         enhanced_mode = False):
        if trigger_mode:
            self.write('AWGControl:RMODE TRIG')
        if continuous_mode:
            self.write('AWGControl:RMODE CONT')
        if enhanced_mode:
            self.write('AWGControl:RMODE ENH')
    
    def set_trigger_source(self, internal = True, internal_interval = 1e-3):
        if internal is True:
            self.write('TRIG:SEQ:SOUR INT')
            self.write(f'TRIG:SEQ:TIM {internal_interval}')
        else:
            self.write('TRIG:SEQ:SOUR EXT')
            
    
    def create_waveform(self, voltages = np.linspace(-1,1,1000), filename = 'temp.wfm', clock = None,
                        marker1_data = None, marker2_data = None, auto_fix_sample_length = False,
                        normalize_voltages = False):
        if marker1_data is None:
            marker1_data = [0]*len(voltages)
        if marker2_data is None:
            marker2_data = [0]*len(voltages)
        if auto_fix_sample_length:
            if len(voltages) < 512: voltages += [voltages[0]]*(512-len(voltages))
            if (len(voltages) % 8) != 0: voltages += [voltages[0]]*(8-(len(voltages) % 8))
            if len(marker1_data) < 512: marker1_data += [marker1_data[0]]*(512-len(marker1_data))
            if (len(marker1_data) % 8) != 0: marker1_data += [marker1_data[0]]*(8-(len(marker1_data) % 8))
            if len(marker2_data) < 512: marker2_data += [marker2_data[0]]*(512-len(marker2_data))
            if (len(marker2_data) % 8) != 0: marker2_data += [marker2_data[0]]*(8-(len(marker2_data) % 8))
                
        
        if (len(voltages) < 512) or (len(voltages) % 8 != 0):
            raise ValueError('Length of `voltages` array must be >=512 elements and divisible by 8')
        if (max(voltages) > 1) or (min(voltages) < -1):
            raise ValueError('Values of `voltages` array must be on [-1.0,+1.0] interval')
            
        if normalize_voltages:
            voltages = np.array(voltages)
            voltages = voltages - min(voltages)
            voltages = voltages/max(voltages)*2 -1


        byte_list = []
        marker_data = (np.array(marker1_data) + 2*np.array(marker2_data)).astype('uint16')
        for n, v in enumerate(voltages):
            new_datapoint = struct.pack('<f',v)
            new_marker_data = struct.pack('<B',marker_data[n])
            # if marker_data is None:
            #     new_marker_data = b'\x00'
            # else:
            #     if marker_data[n] == False:
            #         new_marker_data = b'\x00'
            #     else:
            #         new_marker_data = b'\x01'
            # if n < 256: # Use marker 2 as a sync signal
            #     new_marker_data = bytes([new_marker_data[0] + 2])
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
        
        
    def load_file(self, filename = 'temp.wfm', channel = 1):
        self.write('SOUR%s:FUNC:USER "%s"' % (channel, filename))
        
        
    def set_output(self, output = False, run = True, channel = 1):
        if output: self.write('OUTPUT%s:STATE ON' % channel)
        else:      self.write('OUTPUT%s:STATE OFF' % channel)
            
        if run:    self.write('AWGControl:RUN')
        else:      self.write('AWGControl:STOP')
    
    def set_mode(self, fg_mode = False):
        if fg_mode == False:
            self.write('AWGC:FG 0')
            self.fg_mode = False
        else:
            self.write('AWGC:FG 1')
            self.fg_mode = True
            
    def set_lowpass_filter(self, freq = None, channel = 1):
        valid_freqs = [None, 20e6, 50e6, 100e6, 200e6]
        if freq in valid_freqs:
            if freq == None: freq = 9.9e37
            self.write('OUTPUT%s:FILTER:LPASS:FREQ %0.1E' % (channel, freq))
        else:
            raise ValueError('Lowpass filter freq must be in %s' % valid_freqs)
        
        
    def create_sequence(self, filename = 'temp.seq', wfm_filenames = ['temp.wfm', 'temp2.wfm'], wfm_filenames_ch2 = None,
                        wfm_repeats = None, wfm_trigger_wait = None):
        
        num_waveforms = len(wfm_filenames)
        if wfm_repeats is None: wfm_repeats = [1]*num_waveforms
        if wfm_trigger_wait is None: wfm_trigger_wait = [0]*num_waveforms
        # Forming header string for the SCPI command
        header_string = 'MAGIC 3002\r\n'
        seq_string = 'LINES %i\r\n' % num_waveforms
        waveform_string_list = []
        if wfm_filenames_ch2 is None: wfm_filenames_ch2 = ['']*len(wfm_filenames)
        for n, fn in enumerate(wfm_filenames):
            waveform_string_list.append('"%s", "%s", %i, %i, 0, 0\r\n' % (fn, wfm_filenames_ch2[n], wfm_repeats[n], wfm_trigger_wait[n]))
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
#awg.create_waveform(voltages = np.linspace(0,1,1000), filename = 'temp.wfm')
#awg.create_waveform(voltages = np.linspace(0,0,1000), filename = 'delay1000.wfm')
#awg.create_waveform(voltages = np.sin(np.linspace(0,4*pi,1000)), filename = 'temp2.wfm')
#awg.set_trigger_mode(trigger_mode = True)
#awg.set_output(True)
#awg.write_sequence(filename = 'temp.seq', wfm_filenames = ['temp.wfm', 'temp2.wfm'])
#awg.trigger()


#%%



#mystr = (':FUNC:USER %s' % ("'anm15.wfm'"))
#awg.write(mystr)
#term_str = '\r\n'
#data_to_write = mystr.encode() + term_str.encode()
#
#awg.pyvisa.write_raw(data_to_write)
#awg.query('SYSTEM:ERROR?')

#%% Deprecated usage of socket instead of pyvisa
##x = awg.pyvisa.read_raw()
#
#import socket
#HOST = "192.168.1.101"    # The remote host
#PORT = 4000             # The same port as used by the server
#
#s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
#s.connect((HOST, PORT))
#input_buffer = 2 * 1024
#
##cmd = "*idn?" + "\r\n"
#cmd = 'MMEMORY:DATA? "D_610.WFM"' + "\r\n"
#s.send(cmd.encode())
#idresp = s.recv(input_buffer)
#print(idresp)
#
#s.close()
#

    