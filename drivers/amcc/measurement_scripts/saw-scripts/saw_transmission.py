#Import Necessary Packages
import numpy as np
from matplotlib import pyplot as plt
import pickle
import scipy
from scipy.signal import hilbert
from scipy.signal import gausspulse
from scipy.signal import hilbert
from scipy.signal import gausspulse
from scipy.signal import butter, filtfilt
from scipy.signal import freqs
import sys
import pandas as pd
import time
from tqdm import tqdm
import datetime
 
#NEcessary instruments, ie scope and AWG
import pyvisa as visa
from amcc.instruments.tektronix_awg610 import TektronixAWG610
from amcc.instruments.lecroy_620zi import LeCroy620Zi
 
#Close and then print out all connected instruments
rm = visa.ResourceManager()
print(rm.list_resources())
 

from amcc.standard_measurements.parameterized_measurements import run_experiment, parameter_combinations

#%% ALL FUNCTIONS
def gaussian_pulse( #Make envelop-ed Pulse with carrier frequency f
    samples_per_sec,
    envelope_width = 0.1e-6,
    # envelope_start_time = 10e-6,
    carrier_freq = 1e9,
    ):
    # Generate gaussian pulse
    dt = 1/samples_per_sec
    t_start = -envelope_width*2
    t_end = envelope_width*2
    t = np.arange(t_start, t_end, dt)
    pulse = gausspulse(t, fc=carrier_freq, bw = 1/(envelope_width*carrier_freq))
  
    # # Create blank array and add pulse to the correct location
    # output = np.zeros_like(t)
    # idx = int((envelope_start_time-t[0])/dt)

    # output[idx:idx+len(pulse)] += pulse
    pulse[0] = 0
  
    return t, pulse
 
 
def fft_power_spectrum(t,y): #FFT to get scope traces in frequency domain
    ps = np.abs(np.fft.fft(y))**2
    w = np.fft.fft(t)
    freqs = np.fft.fftfreq(len(t), t[1]-t[0])
    idx = np.argsort(freqs)
    freqs = freqs[idx]
    ps = ps[idx]
    return freqs, ps
 
#Low pass Fuilters on data in frequency domain
def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)
  
def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def _np_ffill(arr, axis = 0):
    """ Keeps NaNs from killing the IQ analysis """
    idx_shape = tuple([slice(None)] + [np.newaxis] * (len(arr.shape) - axis - 1))
    idx = np.where(~np.isnan(arr), np.arange(arr.shape[axis])[idx_shape], 0)
    np.maximum.accumulate(idx, axis=axis, out=idx)
    slc = [np.arange(k)[tuple([slice(None) if dim==i else np.newaxis
        for dim in range(len(arr.shape))])]
        for i, k in enumerate(arr.shape)]
    slc[axis] = idx
    return arr[tuple(slc)]

def iq_analysis(t, signal, carrier_freq, lowpass_freq = None):
    dt = t[1]-t[0]
    t = np.array(t)
    signal = np.array(signal)
    I = _np_ffill(signal)*np.sin(2*np.pi*carrier_freq*t)
    Q = _np_ffill(signal)*np.cos(2*np.pi*carrier_freq*t)
    if lowpass_freq is not None:
        I = butter_lowpass_filter(I, cutoff = lowpass_freq, fs = 1/dt, order=5)
        Q = butter_lowpass_filter(Q, cutoff = lowpass_freq, fs = 1/dt, order=5)
    amplitude = np.sqrt(I**2+Q**2)
    phase = np.arctan2(Q,I)
    return I,Q, amplitude, phase

def write_awg_gaussian_pulse(
    samples_per_sec,
    carrier_freq,
    pulse_duration,
    plot = False,
    ):
    t, pulse_data = gaussian_pulse(samples_per_sec, envelope_width = pulse_duration, carrier_freq = carrier_freq) #Create Pulse
     
    marker_data = np.zeros_like(pulse_data)
    marker_data[int(len(pulse_data)/2):] = 1
    if plot is True:
        plt.figure()
        plt.plot(t*1e9, pulse_data, t*1e9, marker_data)
        plt.xlabel('Time (ns)')
    
    # Load gaussian pulse waveform on AWG
    awg.set_marker_vhighlow( vlow = 0.0, vhigh = 1, marker = 1, channel = 1)
    awg.create_waveform(voltages = pulse_data.tolist(), filename = 'temp.wfm', marker1_data = marker_data.tolist(), auto_fix_sample_length = True)
    awg.load_file('temp.wfm')
    awg.set_clock(samples_per_sec)
    
def saw_transmission_experiment(
    carrier_freq,
    pulse_duration,
    vpp,
    samples_per_sec = 2.6e9,
    num_averages = 2000,
    channels = ['F1','F2','F3'],
    ):

    write_awg_gaussian_pulse(samples_per_sec, carrier_freq, pulse_duration)
    awg.set_vpp(vpp = vpp, channel = 1)
    # lowpass_freq = carrier_freq/4
    
    lecroy.clear_sweeps()
    time.sleep(2.5)
    while lecroy.get_num_sweeps(channel) < num_averages:
        time.sleep(0.1)
    
    df_list = []
    for ch in channels:
        t,v = lecroy.get_wf_data(channel = ch)
        # I,Q, amplitude, phase = iq_analysis(t, v, carrier_freq = carrier_freq, lowpass_freq = lowpass_freq)
        data = dict(
            t = t,
            v = v,
            carrier_freq = carrier_freq,
            channel = ch,
            pulse_duration = pulse_duration,
            vpp = vpp,
            samples_per_sec = samples_per_sec,
            num_averages = num_averages,
            )
        df_list.append(pd.DataFrame(data))
    df = pd.concat(df_list)
    
    return df

def find_local_peak(t,y, tcenter = 250e-9, tspan = 1e-6):
    """ Given time array t and signal array y, finds the maximum value of
    y within window `tpsan` of the time `tcenter` """
    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx, array[idx]
    t = np.array(t)
    y = np.array(y)
    idx1, _ = find_nearest(t,tcenter-tspan/2)
    idx2, _ = find_nearest(t,tcenter+tspan/2)
    sel = slice(idx1,idx2)
    ymax = np.max(y[sel])
    tmax = t[sel][np.argmax(y[sel])]
    return tmax, ymax


#%% Initialize instruments
awg = TektronixAWG610('GPIB0::1::INSTR')
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % '192.168.1.100')

# Setup scope - CH1 = carrier pulse, CH2 = marker trigger
lecroy.reset()
lecroy.set_coupling(channel = 'C1', coupling = 'DC50') 
lecroy.set_coupling(channel = 'C2', coupling = 'DC50')
lecroy.set_coupling(channel = 'C3', coupling = 'DC50') 
lecroy.set_coupling(channel = 'C4', coupling = 'DC50')
lecroy.set_trigger_mode(trigger_mode = 'Normal')
lecroy.set_display_gridmode(gridmode = 'Dual')
lecroy.set_trigger(source = 'C4', volt_level = 0.5)
lecroy.set_vertical_scale(channel = 'C1', volts_per_div = 0.01)
lecroy.set_vertical_scale(channel = 'C2', volts_per_div = 0.01)
lecroy.set_vertical_scale(channel = 'C3', volts_per_div = 0.01)
lecroy.set_vertical_scale(channel = 'C4', volts_per_div = 0.5)
lecroy.set_horizontal_scale(100e-9, time_offset = -400e-9)

lecroy.setup_math_wf_average(math_channel = 'F1', source = 'C1', num_sweeps = 100000)
lecroy.setup_math_wf_average(math_channel = 'F2', source = 'C2', num_sweeps = 100000)
lecroy.setup_math_wf_average(math_channel = 'F3', source = 'C3', num_sweeps = 100000)

# lecroy.set_sample_mode(num_segments=200)
lecroy.set_sample_mode(sequence = False)

awg.reset()
awg.set_vpp(vpp = 2, channel = 1)
awg.set_voffset(voffset = 0, channel = 1)
# awg.set_trigger_mode(continuous_mode=True)
awg.set_trigger_mode(trigger_mode=True)
awg.set_trigger_source(internal=True, internal_interval=1e-3)
awg.set_output(True)
 
#%% Create initial Gaussian Pulse waveform

write_awg_gaussian_pulse(
    samples_per_sec = 2.6e9,
    carrier_freq = 500e6,
    pulse_duration = 100e-9,
    plot = True,
    )


#%% Measure single carrier frequency

df = saw_transmission_experiment(
    carrier_freq = 700e6,
    pulse_duration = 30e-9,
    vpp = 1.2,
    samples_per_sec = 2.6e9,
    num_averages = 1200,
    # channels = ['F1','F2','F3'],
    channels = ['F1'],
    )
#%%
carrier_freq = df.carrier_freq.unique()[0]
I,Q, amplitude, phase = iq_analysis(df.t, df.v, carrier_freq, lowpass_freq = carrier_freq/4)
plt.figure()
plt.plot(df.t*1e9, df.v, df.t*1e9, Q, df.t*1e9, I, df.t*1e9, amplitude)
plt.legend(['Signal (V)', 'Q', 'I', 'amplitude'])
plt.xlabel('Time (ns)')
# plt.savefig(filename + 'final.png', dpi = 300)


#%% Run experiment

parameter_dict = dict(
    carrier_freq = np.linspace(40e6,1000e6,321),
    pulse_duration = [10e-9,20e-9,50e-9],
    vpp = [0.8],
    samples_per_sec = 2.6e9,
    num_averages = 5000,
    # channels = [['F1']],
    channels = [['F1','F2','F3']],
    ) # Lowest variable is fastest-changing index


# Run the experiment
df = run_experiment(
    experiment_fun = saw_transmission_experiment,
    parameter_dict = parameter_dict,
    )


# Save data
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw-transducer')
df.to_parquet(filename +  '.parquet', compression='gzip')



#%% Plot a select few frequencies

# Downselect which data to examine
dfp = df[
    df.carrier_freq.isin([ 1.36e+08, 4.24e+08, 6.16e+08, 8.08e+08, 1.00e+09]) &
    # df.vpp.isin([ 1.36e+08, 4.24e+08, 6.16e+08, 8.08e+08, 1.00e+09]) &
    df.pulse_duration.isin([10e-9]) &
    df.channel.isin(['F1'])
    ]

plt.figure()
for (carrier_freq,vpp,channel,pulse_duration), df2 in dfp.groupby(['carrier_freq','vpp','channel','pulse_duration']):
    I,Q, amplitude, phase = iq_analysis(df2.t, df2.v, carrier_freq, lowpass_freq = carrier_freq/4)
    # tmax4, ymax4 = find_local_peak(df4.t,amplitude4, 228e-9, 30e-9)
    plt.plot(df2.t*1e9, df2.v, label = f'f={carrier_freq/1e6} MHz')
    plt.plot(df2.t*1e9, amplitude, '--', label = f'f={carrier_freq/1e6} MHz')
plt.legend()
plt.xlabel('Time (ns)')
plt.ylabel('Voltage (V)')

# F1 - 115ns
# F2 - 363ns
# F3 - 284
#%% Analyzing pulse heights and times

def get_amplitude_peak(t,y, carrier_freq, tcenter, tspan = 50e-9):
    I,Q, amplitude, phase = iq_analysis(np.array(t), np.array(y), carrier_freq, lowpass_freq = carrier_freq/4)
    tmax, ymax = find_local_peak(t,amplitude, tcenter, tspan)
    return tmax,ymax
    

data_list = []
for (carrier_freq,vpp,pulse_duration), dfx in df.groupby(['carrier_freq','vpp','pulse_duration']):
    df1 = dfx[dfx.channel == 'F1']
    df2 = dfx[dfx.channel == 'F2']
    df3 = dfx[dfx.channel == 'F3']
    t1,y1 = get_amplitude_peak(df1.t,df1.v, carrier_freq = carrier_freq, tcenter = 115e-9, tspan = 50e-9)
    t2,y2 = get_amplitude_peak(df2.t,df2.v, carrier_freq = carrier_freq, tcenter = 363e-9, tspan = 50e-9)
    t3,y3 = get_amplitude_peak(df3.t,df3.v, carrier_freq = carrier_freq, tcenter = 284e-9, tspan = 50e-9)
    data = dict(
        carrier_freq = carrier_freq,
        vpp = vpp,
        pulse_duration = pulse_duration,
        t1 = t1,
        y1 = y1,
        t2 = t2,
        y2 = y2,
        t3 = t3,
        y3 = y3,
        )
    data_list.append(data)

dfa = pd.DataFrame(data_list)
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw-transducer analysis')
dfa.to_parquet(filename +  '.parquet')


#%% Plotting all ymax/tmax values

# Downselect which data to examine
dfp = df[
    df.carrier_freq.isin([ 1.36e+08, 4.24e+08, 6.16e+08, 8.08e+08, 1.00e+09])
    # & df.vpp.isin([ 1.36e+08, 4.24e+08, 6.16e+08, 8.08e+08, 1.00e+09])
    & df.pulse_duration.isin([10e-9])
    # & df.channel.isin(['F1'])
    ]

fig,axs = plt.subplots(3, sharex = True)
for (carrier_freq,vpp,pulse_duration), dfx in dfp.groupby(['carrier_freq','vpp','pulse_duration']):
    df1 = dfx[dfx.channel == 'F1']
    df2 = dfx[dfx.channel == 'F2']
    df3 = dfx[dfx.channel == 'F3']
    I,Q, amplitude1, phase = iq_analysis(df1.t,df1.v, carrier_freq, lowpass_freq = carrier_freq/4)
    I,Q, amplitude2, phase = iq_analysis(df2.t,df2.v, carrier_freq, lowpass_freq = carrier_freq/4)
    I,Q, amplitude3, phase = iq_analysis(df3.t,df3.v, carrier_freq, lowpass_freq = carrier_freq/4)
    t1,y1 = get_amplitude_peak(df1.t,df1.v, carrier_freq = carrier_freq, tcenter = 115e-9, tspan = 50e-9)
    t2,y2 = get_amplitude_peak(df2.t,df2.v, carrier_freq = carrier_freq, tcenter = 363e-9, tspan = 50e-9)
    t3,y3 = get_amplitude_peak(df3.t,df3.v, carrier_freq = carrier_freq, tcenter = 284e-9, tspan = 50e-9)
    axs[0].plot(df1.t*1e9, amplitude1, label = f'f={carrier_freq/1e6} MHz / vpp={vpp} / pd={pulse_duration*1e9:0.1f}ns')
    axs[1].plot(df2.t*1e9, amplitude2, label = f'f={carrier_freq/1e6} MHz / vpp={vpp} / pd={pulse_duration*1e9:0.1f}ns')
    axs[2].plot(df3.t*1e9, amplitude3, label = f'f={carrier_freq/1e6} MHz / vpp={vpp} / pd={pulse_duration*1e9:0.1f}ns')
    axs[0].plot(t1*1e9, y1, 'k*', markersize = 10)
    axs[1].plot(t2*1e9, y2, 'k*', markersize = 10)
    axs[2].plot(t3*1e9, y3, 'k*', markersize = 10)
plt.legend()
# plt.title('Output from terminal 4')
plt.xlabel('Time (ns)')
axs[0].set_ylabel('IQ Amplitude')
axs[1].set_ylabel('IQ Amplitude')
axs[2].set_ylabel('IQ Amplitude')
axs[0].set_title('Terminal 2 output')
axs[1].set_title('Terminal 3 output')
axs[2].set_title('Terminal 4 output')



#%% Plot pulse arrival times
plt.figure()
for (vpp,pulse_duration), df2 in dfa.groupby(['vpp','pulse_duration']):
    plt.plot(df2.carrier_freq/1e6, (df2.t3)*1e9, '.-', label = f'vpp={vpp}V / pd={pulse_duration*1e9:0.1f}ns')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Time (ns)')
plt.title('Pulse arrival time\n(Terminal 2)')
plt.legend()
plt.tight_layout()
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw')
plt.savefig(filename + '.png')

#%% Plot pulse amplitudes
plt.figure()
for (vpp,pulse_duration), df2 in dfa.groupby(['vpp','pulse_duration']):
    plt.plot(df2.carrier_freq/1e6, (df2.y3), '.-', label = f'vpp={vpp}V / pd={pulse_duration*1e9:0.1f}ns')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Amplitude (uV)')
plt.title('Pulse amplitude\n(Terminal 2)')
plt.legend()
plt.tight_layout()
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw')
plt.savefig(filename + '.png')

#%% Plot ringing periods with autocorrelation

data_list = []
for (carrier_freq), df2 in df[df.channel == 'F1'].groupby(['carrier_freq']):
    t = np.array(df2.t)
    v = np.array(df2.v)
    I,Q, amplitude, phase = iq_analysis(t, v, carrier_freq, lowpass_freq = carrier_freq/4)
    total_time = t[-1]-t[0]
    amplitude_corr = np.correlate(amplitude, amplitude, mode='full')
    t_corr = np.linspace(-total_time,total_time,len(amplitude_corr))
    tmax, ymax = find_local_peak(t_corr,amplitude_corr, 45e-9, 20e-9)
    data = dict(
        carrier_freq = carrier_freq,
        t = tmax,
        y = ymax,
        )
    data_list.append(data)
    # if carrier_freq == 3.70e+08:
    #     plt.figure()
    #     plt.plot(df2.t*1e9, df2.v*1e6, '.-', label = f'vpp={vpp}V')
    #     plt.figure()
    #     plt.plot(t_corr*1e9, amplitude_corr, '.-')

dfa = pd.DataFrame(data_list)
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw-transducer analysis')
dfa.to_parquet(filename +  '.parquet')

plt.figure()
plt.plot(dfa.carrier_freq/1e6, dfa.t*1e9, '.-')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Time (ns)')
plt.title('Pulse ringing/interarrival time\n(Terminal 3)')
plt.legend()
plt.tight_layout()
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S saw')
plt.savefig(filename + '.png')

f = np.array(dfa.carrier_freq)
t = np.array(dfa.t)
sel = (f > 200e6) & (f < 600e6)
slope, t0 = np.polyfit(f[sel],t[sel],1)
print(f'fslope = {slope:0.3e}, t_0 = {t0:0.3e}')

 
#%% Quick frequency power spectrum check
  
plt.figure()
freqs, ps = fft_power_spectrum(t,v)
plt.semilogy(freqs/1e6, ps)
freqs, ps = fft_power_spectrum(t,Q)
plt.semilogy(freqs/1e6, ps)
plt.xlabel('Frequency (MHz)')
plt.legend(['Signal', 'Q'])
 
#%% Lowpass filter I/Q to eliminate frequency-doubled sideband
dt = 1/2.6e9
cutoff_f = 10e6
Q_lowpass = butter_lowpass_filter(Q, cutoff = cutoff_f, fs = 1/dt, order=5)
I_lowpass = butter_lowpass_filter(I, cutoff = cutoff_f, fs = 1/dt, order=5)
  
plt.figure()
plt.plot(t,signal, t,I_lowpass,t,Q_lowpass)
plt.legend(['signal', 'I','Q'])
#%%
signal_tot = np.sqrt(I_lowpass**2+Q_lowpass**2)
plt.figure()
 
plt.plot(t, signal, t, Q_lowpass, t, I_lowpass, t,signal_tot)
plt.legend(['Signal', 'Q', 'I', 'sqrt(I^2+Q^2'])
plt.savefig(filename + 'final.png', dpi = 300)


#%% Make AWG waveform of a single pulse 

channel_data = np.zeros(1024)
channel_data[512] = 1
marker_data = np.zeros(1024)
marker_data[512:] = 1

plt.plot(channel_data)
plt.plot(marker_data)

awg.create_waveform(voltages = channel_data.tolist(), filename = 'temp.wfm', clock = 2.6e9, marker1_data = marker_data.tolist(), auto_fix_sample_length = True, normalize_voltages=True)

awg.load_file('temp.wfm')
#%%  Send single pulse and read out scope for different voltages
num_averages = 1200

fig, axs = plt.subplots(1,1,figsize = [16,8], sharex=True)
for voltage in [1,0.1,0.02]:
    
    awg.set_voffset(0)
    awg.set_vpp(voltage)
    
    lecroy.clear_sweeps()
    time.sleep(3)
    while lecroy.get_num_sweeps('F1') < num_averages:
        time.sleep(0.1)
    t,v = lecroy.get_wf_data(channel = 'F2')
    
    plt.plot(t*1e9, v, label = f'AWG pulse height {voltage} V')
    # plt.legend(['Signal (V)', 'Q', 'I', 'amplitude'])
plt.xlabel('Time (ns)')
# plt.title('Straight w/hotspot')
plt.legend()
# plt.xlim([-10,100])

filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S delay graph')
plt.savefig(filename, dpi = 300)

#%%
plt.figure()
t,v = lecroy.get_wf_data(channel = 'F1')
I,Q, amplitude, phase = iq_analysis(t, v, carrier_freq = carrier_freq, lowpass_freq = carrier_freq/4)
plt.plot(t*1e9, v, t*1e9, Q, t*1e9, I, t*1e9, amplitude)
plt.legend(['Signal (V)', 'Q', 'I', 'amplitude'])
plt.xlabel('Time (ns)')

#%%
# lecroy.clear_sweeps()
# time.sleep(1)
# while lecroy.get_num_sweeps('F1') < 400:
#     time.sleep(0.1)


# plt.figure()
channels =  ['F1','F2','F3']
data = {}
fig, ax = plt.subplots(len(channels), sharex = True)
for n, channel in enumerate(channels):
    t,v = lecroy.get_wf_data(channel = channel)
    data[channel] = {'t':t,'v':v}
    # I,Q, amplitude, phase = iq_analysis(t, v, carrier_freq = carrier_freq, lowpass_freq = carrier_freq/4)
    ax[n].plot(t*1e9, v*1e3, label = channel)
    ax[n].legend()
    ax[n].set_ylabel('Voltage (mV)')
plt.xlabel('Time (ns)')
plt.tight_layout()

# t_none = t
# v_none = v
# t_input_hs = t
# v_input_hs = v
# t_output_hs = t
# v_output_hs = v

#%% Autocorrelate
plt.figure()
v_corr = np.correlate(v, v, mode='full')
total_time = t[-1]-t[0]
t_corr = np.linspace(-total_time,total_time,len(v_corr))
plt.plot(t_corr*1e9, v_corr*1e3, label = 'xxx')
plt.xlabel('Time (ns)')


#%% Quick temp
df_nodut = pd.read_parquet(r'C:\Users\qittlab\2023-02-21 14-07-43 saw-transducer analysis.parquet');
df_dut = pd.read_parquet(r'C:\Users\qittlab\2023-02-17 14-36-54 saw-transducer analysis.parquet');

y4_ref = np.interp(df_dut.carrier_freq, df_nodut.carrier_freq, df_nodut.y1)
plt.plot(df_dut.carrier_freq, df_dut.y4)


plt.plot(df_dut.carrier_freq/1e6, df_dut.y4/y4_ref)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Amplitude (normalized)')
