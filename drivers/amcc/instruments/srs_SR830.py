import pyvisa as visa

class SR830DSP(object):
    
    """Python class for SRS SR830 DSP Lock In Amplifier, written by Dana Rampini"""
    
    
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands
        # Anything else here that needs to happen on initialization
        # Configure the termination characters
        self.write('CEOI ON')
        self.write('EOIX ON')

    def read(self):
        return self.pyvisa.read()
    def write(self, string):
        self.pyvisa.write(string)
    def query(self, string):
        return self.pyvisa.query(string)
    def reset(self):
        self.write_simport('*RST')
    def close(self):
        return self.pyvisa.close()
    def identify(self):
        return self.query_simport('*IDN?')
    
    
    
    #Set/ read reference source, INTERNAL OR EXTERNAL, 0 for external, 1 for internal
    def set_reference_sorce(self, trig):
        write_str = 'FMOD '+ str(trig)
        self.write(write_str)
    
    def read_reference_source(self):
        source = self.query('FMOD ?')
        return source
    
    #Set/ read reference phase shift 
    def set_phase(self, phase):
        write_str = 'PHAS '+ str(phase)
        self.write(write_str)
        
    def read_phase(self):
        phase = self.query('PHAS ?')
        return phase
    
    #Set/ read reference frequency 
    def set_freq(self, freq):
        write_str = 'FREQ '+ str(freq)
        self.write(write_str)
        
    def read_freq(self):
        freq = self.query('FREQ ?')
        return freq
    
    #Set/ read reference trigger, 0 = zero crossing, 1 = rising edge, 2 = falling edge  
    def set_reference_trig(self, trig):
        write_str = 'RSLP '+ str(trig)
        self.write(write_str)
          
    def read_reference_trig(self):
        trig = self.query('RSLP ?')
        return trig
    
    #Set/ read amplitude of sine output  
    def set_voltage_amplitude(self, vamp):
        write_str = 'SLVL '+ str(vamp)
        self.write(write_str)
        
    def read_voltage_amplitude(self):
        vamp = self.query('SLVL ?')
        return vamp
    
    #Set/ read detection harmonic 
    def set_harmonic(self, harm):
        write_str = 'HARM '+ str(harm)
        self.write(write_str)
        
    def read_harmonic(self):
        harm = self.query('HARM ?')
        return harm
    
    #Set/ read input configuration 0 = A, 1 = A-B, 2 = I (1 MΩ), 3 =  I (100 MΩ) 
    def set_input_config(self, config):
        write_str = 'ISRC '+ str(config)
        self.write(write_str)
          
    def read_input_config(self):
        config = self.query('ISRC ?')
        return config
    
    #Set/ read input shield grounding 0 = FLOAT, 1 = GROUND
    def set_ground(self, ground):
        write_str = 'IGND '+ str(ground)
        self.write(write_str)
          
    def read_ground(self):
        ground = self.query('IGND ?')
        return ground

    #Set/ read input COUPLING 0 = AC, 1 = DC
    def set_coupling(self, cpl):
        write_str = 'ICPL '+ str(cpl)
        self.write(write_str)
          
    def read_coupling(self):
        cpl = self.query('ICPL ?')
        return cpl
    
    #Set/ read input line notch filter 0 = no filter, 1 = line notch, 2 = 2x line notch, 3 = Botch notch
    def set_notch_filter(self, flt):
        write_str = 'ILIN '+ str(flt)
        self.write(write_str)
          
    def read_notch_filter(self):
        flt = self.query('ILIN ?')
        return flt
    
    #Set/ Read the sensitivity
    """
    i sensitivity i sensitivity
    0 2 nV/fA     13 50 µV/pA
    1 5 nV/fA     14 100 µV/pA
    2 10 nV/fA    15 200 µV/pA
    3 20 nV/fA    16 500 µV/pA
    4 50 nV/fA    17 1 mV/nA
    5 100 nV/fA   18 2 mV/nA
    6 200 nV/fA   19 5 mV/nA
    7 500 nV/fA   20 10 mV/nA
    8 1 µV/pA     21 20 mV/nA
    9 2 µV/pA     22 50 mV/nA
   10 5 µV/pA     23 100 mV/nA
   11 10 µV/pA    24 200 mV/nA
   12 20 µV/pA    25 500 mV/nA
                  26 1 V/µA
    """
    def set_sensiitivity(self, sens):
        write_str = 'SENS '+ str(sens)
        self.write(write_str)
          
    def read_sensitivity(self):
        sens = self.query('SENS ?')
        return sens
    
    #Set/ Read reserve mode  0 = High Reserve, 1 = Normal, 2 = Low Noise (minimum) 
    def set_reserve_mode(self, res):
        write_str = 'RMOD '+ str(res)
        self.write(write_str)
          
    def read_reserve_mode(self):
        res = self.query('RMOD ?')
        return res
    
    #Set/ Read the time constant
    """
    i time constant i time constant
    0 10 µs         10 1 s
    1 30 µs         11 3 s
    2 100 µs        12 10 s
    3 300 µs        13 30 s
    4 1 ms          14 100 s
    5 3 ms          15 300 s
    6 10 ms         16 1 ks
    7 30 ms         17 3 ks
    8 100 ms        18 10 ks
    9 300 ms        19 30 ks
    """
    def set_time_const(self, res):
        write_str = 'OFLT '+ str(res)
        self.write(write_str)
          
    def read_time_const(self):
        tc = self.query('OFLT ?')
        return tc
    
    #Set/ Read low pass filter slope 0 = 6 dB/oct, 1 =  12 dB/oct, 2 = 18 dB/oct, 3 = 24 dB/oct (i=3)
    def set_lp_filter(self, db):
        write_str = 'OFSL '+ str(db)
        self.write(write_str)
          
    def read_lp_filter(self):
        db = self.query('OFSL ?')
        return db
    
    #AUTO GAIN - sets sens/ time constant
    def auto_gain(self):
        self.write('AGAN')
    
    #AUTO RESERVE - sets resrve
    def auto_reserve(self):
        self.write('ARSV')
        
    #AUTO PHASE - resets phase
    def auto_phase(self):
        self.write('APHS')
    
    #AUTO OFFSET - zeros offset of X/Y/R, 1 = X, 2 = Y, 3 = R
    def auto_offset(self, parameter):
        write_str  = 'AOFF ' + str(parameter)
        self.write(write_str)
    
    #Set/ Read CH1 and CH2 displays
    """
    The DDEF command selects the CH1 and CH2 displays. The parameter
    i selects CH1 (i=1) or CH2 (i=2) and is required. The DDEF i, j, k command sets display i to parameter j with ratio k as listed below.
    
    CH1 (i=1)     CH2 (i=2)
    
    j display     j display
    0 X           0 Y
    1 R           1 θ
    2 X Noise     2 Y Noise
    3 Aux In 1    3 Aux In 3
    4 Aux In 2    4 Aux In 4
    
    k ratio       k ratio
    
    0 none        0 none
    1 Aux In 1    1 Aux In 3
    2 Aux In 2    2 Aux In 4
    
    The DDEF? i command queries the display and ratio of display i. The
    returned string contains both j and k separated by a comma. For example, if the DDEF? 1 command returns "1,0" then the CH1 display is R
    with no ratio.
    """
    
    def set_channel_display(self, channel, parameter):
        write_str = 'DDEF ' + str(channel) + '{,'+str(parameter) + ',0}'
        self.write(write_str)
    
    def read_channel_display(self, channel):
        read_str = 'DDEF ? ' + str(channel)
        display = self.query(read_str)
        return display
    
    #Read CH1/CH2 value 1 = CH1, 2 = CH2
    def get_channel_value(self, channel):
        query_str = 'OUTR ? ' + str(channel)
        val = self.query(query_str)
        return val
    
    #Run this to unlock Lock-in so that front panel can be used while connected through GPIB
    def unlock_lockin(self):
        self.write('OVRM 1')
