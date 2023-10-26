import pyvisa as visa

class Agilent89410a:
    def __init__(self, visa_name, trace=1):
        if not 1<=int(trace)<=4:
            raise Exception('Trace must be integer between 1 and 4')
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.trace = str(int(trace))
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)

    def identify(self):
        # expected output: HEWLETT-PACKARD,89410A,3416A01211,A.09.01
        return self.pyvisa.query('*IDN?')

    def cal(self):
        # calibrates analyzer and returns pass/fail result
        return self.pyvisa.query('*CAL?')

    def reset(self):
        # executes a device reset and cancels pending commands/queries
        return self.pyvisa.write('*RST')

    def trigger(self):
        # triggers analyzer when GPIB is designated trigger source and analyzer
        # is waiting to trigger
        return self.pyvisa.write('*TRG')

    def cont(self):
        # continues a paused measurement
        return self.pyvisa.write('CONTINUE')

    def pause(self):
        # Pauses measurement in progress
        return self.pyvisa.write('PAUSE')

    def abort(self):
        # aborts measurement in progress and resets trigger system
        return self.pyvisa.write('ABORT')

    def wait(self):
        # device will not process subsequent commands until preceding ones are 
        # complete
        return self.pyvisa.write('*WAI')

    def preset(self):
        # resets most device parameters to default state
        return self.pyvisa.write('SYSTEM:PRESET')

    def set_free_run_mode(self):
        # sets triggering to free-run mode
        return self.pyvisa.write('TRIG:SOUR IMM')

    def set_detector(self, f='SIGNAL'):
        # determines what analyzer displays when number of data points exceeds
        # displayed points
        if f not in ['SIGNAL','SAMPLE','POSITIVE']:
            raise Exception('invalid input')
        return self.pyvisa.write('SENSE:DETECTOR:FUNCTION '+f)

    def get_ccdf_count(self):
        # returns current number of data samples in CCDF measurement
        return self.pyvisa.query('CALCULATE'+self.trace+':CCDF:COUNT?')

    def get_ccdf_power(self):
        # returns average signal power used to compute CCDF measurement
        return self.pyvisa.query('CALCULATE'+self.trace+':CCDF:POWER?')

    def set_fast_average(self, val=True):
        # Turns fast averaging on or off
        return self.pyvisa.write('AVERAGE:IRES '+'1' if val else '0')

    def get_average_progress(self):
        # returns current number of averages
        return self.pyvisa.query('SENSE:AVERAGE:COUNT:INTERMEDIATE?')

    def get_average_total(self):
        # returns number of averages to be done
        return self.pyvisa.query('SENSE:AVERAGE:COUNT?')

    def set_measurement(self, mode='S', measurement='P'):
        # Sets measurement data to be displayed.
        # Modes:
            # Scalar mode: 'S'
            # Vector mode: 'V'
        # Measurements:
            # Spectrum: 'S'
            # PSD: 'P'
            # Frequency response: 'F'
        s = ''
        if mode is 'S':
            if measurement is 'S':
                s = 'XFR:POW 1'
            elif measurement is 'P':
                s = 'XFR:POW:PSD 1'
            else:
                raise Exception('Invalid measurement in scalar mode')
        elif mode is 'V':
            if measurement is 'S':
                s = 'XFR:POW 1'
            elif measurement is 'P':
                s = 'XFR:POW:PSD 1'
            elif measurement is 'F':
                s = 'XFR:POW:RAT 2,1'
            else:
                raise Exception('Invalid measurement in vector mode')
        else:
            raise Exception('Invalid mode')
        return self.pyvisa.write('CALCULATE'+self.trace+':FEED \''+s+'\'')

    def get_mode(self):
        # returns string representing current measurement and mode
        return self.pyvisa.query('CALCULATE'+self.trace+':FEED?')

    def set_trace_coords(self, coords):
        # sets coordinates of selected trace
        # Coordinate settings:
            # 'MLIN': linear magnitude
            # 'MLOG': log-magnitude
            # 'PHAS': wrapped phase coordinates
            # 'UPH': unwrapped phase coordinates
            # 'REAL': real part of waveform
            # 'IMAG': imaginary part of waveform
            # 'GDEL': group delay
            # 'COMP': complex polar vector diagram
            # 'CONS': constellation polar vector diagram
            # 'IEYE': in-phase eye diagram
            # 'QEYE': quadrature-phase eye diagram
            # 'TEYE': trellis eye diagram
        if coords not in ['MLIN','MLOG','PHAS','UPH','REAL','IMAG', 'DGEL',\
                          'COMP','CONS','IEYE','QEYE','TEYE']:
            raise Exception('Invalid coordinates')
        return self.pyvisa.write('CALCULATE'+self.trace+':FORMAT '+coords)

    def get_trace_coords(self):
        # returns string representing current trace coordinates
        return self.pyvisa.query('CALCULATE'+self.trace+':FORMAT?')

    def set_marker_band_position(self, mkr, pos):
        # sets left or rignt band marker position
        # mkr: 'L' for left. 'R' for right marker
        # pos: x-axis units, e.g. Hz or s
        if mkr not in ['L','R']:
            raise Exception('Invalid mkr')
        return self.pyvisa.write('CALCULATE'+self.trace+':MARKER:BAND:'+\
                         ('START ' if pos is 'L' else 'STOP ')+str(pos))

    def set_marker_coupling(self, val):
        # turn on/off marker coupling; val should be boolean
        return self.pyvisa.write('CALCULATE'+self.trace+'MARKER:COUPLED '+\
                         ('ON' if val else 'OFF'))

    def set_freq_center(self, val):
        # turn on/off marker frequency counter; val should be boolean
        return self.pyvisa.write('CALCULATE'+self.trace+':MARKER:FCOUNT '+\
                         ('ON' if val else 'OFF'))
    def get_freq_center(self):
        # returns frequency counter measurement
        return self.pyvisa.query('CALCULATE'+self.trace+':MARKER:FCOUNT:RESULT?')

    def move_marker(self, move):
        # Moves marker based on value of move variable
        # 'MAX': moves marker to maximum value in trace
        # 'MIN': moves marker to minimum value in trace
        # 'LEFT': moves marker to nearest local maximum to left
        # 'RIGHT': moves marker to nearest local maximum to right
        # 'NEXT': moves marker to next-highest value in trace
        if move not in ['MAX','MIN','LEFT','RIGHT','NEXT']:
            raise Exception('Invalid movement')
        return self.pyvisa.write('CALCULATE'+self.trace+':MARKER:'+\
                                ('MAXIMUM' if move is not 'MIN' else 'MINIMUM')+\
                                (move if move not in ['MIN','MAX'] else ''))
    def set_tracking(self, val):
        # Turns marker peak-tracking on or off. val should be boolean.
        return self.pyvisa.write('CALCULATE'+self.trace+':MARKER:MAXIMUM:TRACK '+\
                                ('ON' if val else 'OFF'))

    def set_coupling(self, coupling = 'AC', channel=1):
        # Sets selected channel to AC (coupling='AC') or DC (coupling='DC') coupling
        if channel not in [1,2] or coupling not in ['AC','DC']:
            raise Exception('Invalid input')
        return self.pyvisa.write('INPUT'+str(channel)+':COUPLING '+coupling)

    def set_input_impedance(self, ohms = 50, channel=1):
        # Sets input impedance. imp should be integer 50, 75, or 1e6 and channel
        # should be 1 or 2.
        if channel not in [1,2] or ohms not in [50,75,1e6]:
            raise Exception('Invalid input. ohms should be integer 50, 75, or 1e6 and channel')
        return self.pyvisa.write('INPUT'+str(channel)+':IMPEDANCE '+str(ohms))

    def set_channel(self, val, channel=1):
        # Turns selected channel on or off. val should be boolean and channel
        # should be 1 or 2.
        if channel not in [1,2]:
            raise Exception('Invalid input')
        return self.pyvisa.write('INPUT'+str(channel)+' '+\
                                ('ON' if val else 'OFF'))

    def set_mode(self, mode):
        # Sets instrument mode. mode should be 'SCALAR' or 'VECTOR'.
        if mode not in ['SCALAR','VECTOR']:
            raise Exception('Invalid input')
        return self.pyvisa.write('INSTRUMENT '+mode)

    def set_average(self, val, tp='VRMS', count=100):
        # Turns averaging on or off based on boolean val. If val is True, 
        # type (tp) can be :
            # 'VRMS' for rms(video)
            # 'ERMS' for rms(video) exponential
            # 'TIME' for time
            # 'TEXP' for time exponential
            # 'CPH' for continuous peak hold
        # Count is number of averages to take; should be integer between 1 and 99999. 
        if not val:
            return self.pyvisa.write('AVERAGE OFF')
        if tp not in ['VRMS','ERMS','TIME','TEXP','CPH'] or not 1<=count<=99999:
            raise Exception('invalid input')
        s = ''
        if tp is 'VRMS':
            s = 'RMS;TCON NORM'
        elif tp is 'ERMS':
            s = 'RMS;TCON EXP'
        elif tp is 'TIME':
            s = 'COMP;TCON NORM'
        elif tp is 'TEXP':
            s = 'COMP;TCON EXP'
        elif tp is 'CPH':
            s = 'MAX'
        return (self.pyvisa.write('AVERAGE ON'),\
                self.pyvisa.write('AVERAGE:TYPE '+s),\
                self.pyvisa.write('AVERAGE:COUNT '+str(count)))

    def set_freq(self, span, center):
        # Specifies resolution span and center. Both should be integers [Hz].
        return (self.pyvisa.write('FREQUENCY:SPAN '+str(span)),\
                self.pyvisa.write('FREQUENCY:CENTER '+str(center)))

    def set_channel_gain(self, gain, channel=1):
        # Sets gain for selected channel; gain should be number between 1e-6 and 1e6
        if channel not in [1,2] or not 1e-6<=gain<=1e6:
            raise Exception('Invalid input')
        return self.pyvisa.write('CORRECTION'+str(channel)+':LOSS:MAGNITUDE '+str(gain))

    def set_dc_offset(self, offset, channel=1):
        # Sets DC offset for selected channel; channel should be 1 or 2 and 
        # offset should be between -20 and 20
        if channel not in [1,2] or not -20<=offset<=20:
            raise Exception('Invalid input')
        return self.pyvisa.write('CORRECTION'+str(channel)+':OFFS '+str(offset))

    def get_x_data(self):
        # Returns x-axis units and data
        return (self.pyvisa.query('TRACE:X:UNIT? TRACE'+self.trace),\
                self.pyvisa.query ('TRACE:X? TRACE'+self.trace))

    def get_y_data(self):
        # Returns y-axis units and data
        return self.pyvisa.query('CALCULATE'+str(self.trace)+':DATA?')
        

# import time
# import re
# from matplotlib import pyplot as plt
# import numpy as np
# from math import floor, ceil, log10, sqrt

# def _stof(s):
#     a = [int(b) for b in s]
#     return (a[0]/abs(a[0]))*(abs(a[0])+a[1]*10**(-1*len(str(a[1]))))*10**a[2]

# def getData(fc,fw):
#     instr = AG89410A()
#     instr.preset()
#     instr.setTraceCoords('MLIN')
#     instr.setCoupling('DC')
#     instr.setIntImp(1e6)
#     instr.setMode('SCALAR')
#     instr.setMeasurement('S','P')
#     instr.setupF(fw,fc)
#     instr.setAvg(True, count=100)
#     instr.setChannel(1)
#     instr.setFastAvg(True)
#     instr.setChGain(1)
#     instr.setDetector('POSITIVE')
#     instr.setFreeTrig()
    
#     while instr.getAvgProgress()==instr.getAvgTotal():
#         pass
#     while instr.getAvgProgress()!=instr.getAvgTotal():
#         pass
    
#     Y = instr.getYData()
#     Y = re.findall('[+-]\d+[.]\d+[E][+-]\d+(?=,)',Y)
#     Y = [re.findall('[+-]?\d+',str(y)) for y in Y]
#     Y = [_stof(y) for y in Y]
#     del instr
#     return [[fw,fc],Y]

# def plotData(f,Y):
#     X = np.linspace(f[1]-f[0],f[1]+f[0],len(Y))
#     plt.plot(X,Y)
#     plt.xlabel('Frequency[Hz]')
#     plt.ylabel('Amplitude[vrms]')
#     #plt.xscale('log')
#    # plt.yscale('log')
#     plt.ylim([.9*min(Y),1.1*max(Y)])
#     print str(X[np.argmax(Y)])+'\t'+str(max(Y))
#     print str(X[np.argmin(Y)])+'\t'+str(min(Y))
#     plt.show()
#     return


# def exp():
#     [f,Y] = getData(5e6,1e6)
#     plotData(f,Y)
#     print 'expected noise: '+str(calcExpNoise(1e6))
#     print 'mean noise: '+str(np.mean(Y))


# def calcExpNoise(R):
#     k = 1.3806e-23
#     T = 273
#     return 2*sqrt(k*R*T)
            
            
            
            
            
            
            
            
            
            
            
            
            
            