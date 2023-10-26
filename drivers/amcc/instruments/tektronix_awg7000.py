#%%
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

    def trigger_now(self):
        self.write('*TRG')
    
    # Set sampling clock rate; range from 50 kHz to 2.6 GHz
    def set_clock(self, freq = 2.6e9):
        self.write(':FREQuency %0.3e' % freq)
        
    def _new_waveform(self, filename = 'temp', num_points = 1000):
        self.write('WLIST:WAVEFORM:NEW "{}", {:d}, INT'.format(filename, num_points))

    def create_waveform(self, filename = 'temp.wfm', voltages = np.linspace(-1,1,1000), 
                        marker1_data = None, marker2_data = None):
        # NOTE: Currently only works when running on 8-bit DAC mode
        num_pts = len(voltages)
        self._new_waveform(filename = filename, num_points = num_pts)

        # Process described on page 2-23 of Tektronix 7000 Programmer Manual
        if marker1_data is None:
            marker1_data = [0]*num_pts
        if marker2_data is None:
            marker2_data = [0]*num_pts
        wfm_data = np.array((np.array(voltages)+1)/2*(2**8-1)).astype('uint16') # Convert to 8-bit number
        wfm_data = wfm_data << 6 # Shift up 6 bits
        marker_data = (np.array(marker1_data) + 2*np.array(marker2_data)).astype('uint16')
        marker_data = marker_data << 14
        data = wfm_data + marker_data
        if len(voltages) > 650000000: raise ValueError('voltages must be shorter than 650,000,000')
        header_string = f'WLIST:WAVEFORM:DATA "{filename}",'
        self.pyvisa.write_binary_values(header_string, data, datatype='H', is_big_endian=False)

    # def create_marker(self,  marker1_data = [0,1,1,0], marker2_data = [1,1,1,0], filename = 'temp.mkr'):
    #     self._new_waveform(filename = filename, num_points = len(marker1_data))
    #     data = 2*np.array(marker1_data) + np.array(marker2_data)
    #     header_string = f'WLIST:WAVEFORM:MARKer:DATA "{filename}",'
    #     self.pyvisa.write_binary_values(header_string,data, datatype='B')    ### limited to 650,000,000 bytes of data


    # def create_waveform(self, filename = 'temp.wfm', voltages = np.linspace(-1,1,1000),
    #                     marker1_data = None, marker2_data = None):
    #     num_pts = len(voltages)
    #     self._new_waveform(filename = filename, num_points = num_pts)

    #     if marker1_data is None:
    #         marker1_data = [0]*num_pts
    #     if marker2_data is None:
    #         marker2_data = [0]*num_pts
    #     marker_data = 2*np.array(marker1_data) + np.array(marker2_data)

    #     byte_list = []
    #     for n, v in enumerate(voltages):
    #         new_datapoint = struct.pack('<f',v)
    #         new_marker_datapoint = struct.pack('<B',marker_data[n])
    #         byte_list.append(new_datapoint)
    #         byte_list.append(new_marker_datapoint)
    #     data_bytes = b''.join(byte_list)
    #     header_string = f'WLIST:WAVEFORM:DATA "{filename}",'
    #     term_str = '\n'
    #     self.pyvisa.write_raw(header_string.encode() + data_bytes + term_str.encode())
    #     # self.pyvisa.write_binary_values(header_string, data, datatype='H', is_big_endian=False)


    def load_waveform(self, filename = 'temp.wfm', channel = 1):
        self.write(f'SOUR{channel}:WAV "{filename}"')

    # def load_marker(self, filename = 'temp.mkr', channel = 1):
    #     self.instObj.write_binary_values('WLIST:WAVEFORM:MARKer:DATA "{}",'.format(wfName),data, datatype='B')    ### limited to 650,000,000 bytes of data
        
    def set_dac_resolution(self, num_bits = 8, channel = 1):
        self.write(':DAC:RESolution {}'.format(num_bits))

    def set_vpp(self, vpp = 1.0, channel = 1):
        self.write(f'SOUR{channel}:VOLT:AMPLITUDE {vpp:0.3e}')
        
    def set_voffset(self, voffset = 1.0, channel = 1):
        self.write(f':SOUR{channel}:VOLT:OFFSET {voffset:0.3e}')
        
    # Also known as "run mode"
    def set_trigger_mode(self, trigger_mode = False, continuous_mode = False,
                         enhanced_mode = False):
        if trigger_mode:
            self.write('AWGControl:RMODE TRIG')
        if continuous_mode:
            self.write('AWGControl:RMODE CONT')
        if enhanced_mode:
            self.write('AWGControl:RMODE ENH')
        
    def set_marker_vhighlow(self, vlow = 0.0, vhigh = 0.100, marker = 1):
        self.write(f':MARK{marker}:VOLT:LOW {vlow:0.3e}')
        self.write(f':MARK{marker}:VOLT:HIGH {vhigh:0.3e}')
        
        
    def set_output(self, output = False, run = True):
        if output: self.write('OUTPUT1:STATE ON')
        else:      self.write('OUTPUT1:STATE OFF')
            
        if run:    self.write('AWGControl:RUN')
        else:      self.write('AWGControl:STOP')

# try:
#     a.close()
# except:
#     pass
    
# a = TektronixAWG7000('TCPIP0::%s::4000::SOCKET' % '192.168.1.103')


##a.new_waveform(filename = 'hello', num_points = 1000)
#a.create_waveform(filename = 'tempwfm', voltages = np.linspace(-1,1,1000))
#a.load_waveform(filename = 'tempwfm')
#a.query('SYSTEM:ERROR?')
#a.create_marker(marker1_data = [0,1,1,0]*250, marker2_data = [1,1,1,0]*250, filename = 'tempmkr')
#a.load_waveform(filename = 'tempmkr')
#a.query('SYSTEM:ERROR?')