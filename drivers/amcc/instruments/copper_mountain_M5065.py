# -*- coding: utf-8 -*-
"""
Created on Wed Nov 24 14:52:57 2021

@author: dsr1
"""


import win32com.client # Needs pywin32 extension
instrument = 'S2VNA'
app = win32com.client.Dispatch(instrument + ".application")


def check_ready():
    return app.Ready

def set_freq_range(self, f_start = 10e6, f_stop = 3e9, f_center = None, f_span = None):
    # Sets frequency range by start and stop if centre and span are not defined
    if (f_center is None) and (f_span is None):
    	app.scpi.GetSENSe(1).frequency.start = f_start
    	app.scpi.GetSENSe(1).frequency.stop = f_stop
        
    # Sets frequency range by centre and span if defined
    elif (f_center is not None) and (f_span is not None):
        app.scpi.GetSENSe(1).frequency.center = f_center
        app.scpi.GetSENSe(1).frequency.span = f_span


def get_power():
    power_level_dbm = app.scpi.GetSOURce(1).power.level.immediate.amplitude
    return power_level_dbm


def set_power(power_dbm):
    app.scpi.GetSOURce(1).power.level.immediate.amplitude = power_dbm

# Sets measurement mode (Input 'S11' or 'S21')
def set_mode(mode = 'S11'):
    app.scpi.GetCALCulate(1).GetPARameter(1).define = mode
    app.scpi.GetCALCulate(1).GetPARameter(1).select()

def set_format(measure_format = 'mlog'):
    if measure_format not in ['mlog','phase','polar']: # fixme add others
        raise ValueError("Wrong measurement format string, need 'mlog','phase','polar'")
    app.scpi.GetCALCulate(1).selected.format = measure_format

def set_num_points(num_points):    
    app.scpi.GetSENSe(1).sweep.points = num_points


def run_single_measurement():    
    app.scpi.trigger.sequence.single()
    
# def measure():
#Execute the measurement

def get_data():
    app.scpi.GetCALCulate(1).GetPARameter(1).select()
    output = app.scpi.GetCALCulate(1).selected.data.Fdata
    output = output[0::2] # Discard extaneous (complex) frequency points
    freqs = app.scpi.GetSENSe(1).frequency.data
    return freqs, output


set_num_points(10001)
set_power(0)
set_mode(mode = 'S11')
set_format(measure_format = 'phase')
run_single_measurement()
freqs, output = get_data()
plt.plot(freqs, output)

