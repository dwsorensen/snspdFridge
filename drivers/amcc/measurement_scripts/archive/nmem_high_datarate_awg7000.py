#%%
from instruments.rigol_dg5000 import RigolDG5000
from instruments.lecroy_620zi import LeCroy620Zi
from instruments.srs_sim928 import SIM928
from instruments.switchino import Switchino
import time
import datetime
import pickle
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm 



# Creates a pulse shape with points like [(t1, y1), (t2, y2), ...]
def pulse(center_time, width, edge_width, voltage):
    times = [-(width/2+edge_width), -width/2, width/2, width/2+edge_width]
    times = np.array(times) + center_time
    voltages = [0, voltage, voltage, 0]
    return list(zip(times, voltages))

def append_pulse(tv_list, delay, width, edge_width, voltage):
    t_final = max(np.array(tv_list)[:,0])
    new_pulse_tv = pulse(center_time = t_final + width/2 + edge_width + delay,
                         width = width, edge_width = edge_width, voltage = voltage)
    return tv_list + new_pulse_tv

# Function to find threshold crossings, from
# http://stackoverflow.com/questions/23289976/how-to-find-zero-crossings-with-hysteresis
def threshold_with_hysteresis(x, th_lo, th_hi, initial = False):
    hi = x >= th_hi
    lo_or_hi = (x <= th_lo) | hi
    ind = np.nonzero(lo_or_hi)[0]
    if not ind.size: # prevent index error if ind is empty
        return np.zeros_like(x, dtype=bool) | initial
    cnt = np.cumsum(lo_or_hi) # from 0 to len(x)
    return np.where(cnt, hi[ind[cnt-1]], initial)

def read_ic_n_times(num_sweeps = 100, R_AWG = 10e3):
    ic_data = []
    for n in range(num_sweeps):
        awg.trigger_now()
        time.sleep(0.1)
        ic_data.append(lecroy.get_parameter_value('P1')/R_AWG)
    return ic_data
    
def pulse_from_dual_srs(srs_pos, srs_neg, i_pulse, R_SRS = 10e3):
    if i_pulse > 0:
        srs_pos.set_voltage(i_pulse*R_SRS)
        time.sleep(0.5)
        srs_pos.set_voltage(0)
        time.sleep(0.5)
    elif i_pulse < 0:
        srs_neg.set_voltage(-i_pulse*R_SRS)
        time.sleep(0.5)
        srs_neg.set_voltage(0)
        time.sleep(0.5)

def staircase(srs_pos, srs_neg, currents, num_sweeps):
    write_currents = []
    ic_data = []
    for i in tqdm(currents):
        pulse_from_dual_srs(srs_pos, srs_neg, i_pulse = i, R_SRS = 10e3)
        ic_data += read_ic_n_times(num_sweeps = num_sweeps, R_AWG = 10e3)
        write_currents += [i] + [0]*(num_sweeps-1)
        pulse_from_dual_srs(srs_pos, srs_neg, i_pulse = -i, R_SRS = 10e3)
        ic_data += read_ic_n_times(num_sweeps = num_sweeps, R_AWG = 10e3)
        write_currents += [-i] + [0]*(num_sweeps-1)
    return {'write_currents':write_currents, 'ic_data':ic_data}

def staircase_vs_ports(srs_pos, srs_neg, currents, num_sweeps, port_pair):
    switch.select_ports(port_pair)
    time.sleep(1)
    return staircase(srs_pos, srs_neg, currents, num_sweeps)
    

#%%============================================================================
# Setup instruments
#==============================================================================

from instruments.tektronix_awg7000 mport TektronixAWG7000
awgw = TektronixAWG7000('TCPIP0::%s::4000::SOCKET' % '192.168.1.101')
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % '192.168.1.100')
awg = RigolDG5000('USB0::0x1AB1::0x0640::DG5T171200124::INSTR')
switch = Switchino('COM7')


# %%===========================================================================
# Perform alternating staircase measurement
# =============================================================================
# First set up Ic measurement on LeCroy + AWG, then do rest of code
srs_pos = SIM928('GPIB0::4', 1)
srs_neg = SIM928('GPIB0::4', 4)
srs_pos.reset(); srs_pos.set_output(True)
srs_neg.reset(); srs_neg.set_output(True)
lecroy.set_trigger_mode('Normal')

awg.set_output(True, channel = 1)
awg.set_burst_mode(burst_enable = True, num_cycles = 1, phase = 0, trigger_source = 'MAN', channel = 1)
time.sleep(1) 

currents = np.linspace(0, 300e-6, 30)
num_sweeps = 10

port_pairs = [
#        (2,1),
        (4,3),
        (6,5),
        (8,7),
#        (10,9),
#        (1,2),
#        (3,4),
#        (5,6),
#        (7,8),
#        (9,10),
        ]

data = {port_pair : staircase_vs_ports(srs_pos, srs_neg, currents, num_sweeps, port_pair) for port_pair in tqdm(port_pairs)}
switch.disable()

filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
pickle.dump({'data':data}, open(filename + '.pickle', 'wb'))

for pp in port_pairs:
    # Plot everything
    write_currents = data[pp]['write_currents']
    ic_data = data[pp]['ic_data']
    fig = plt.figure()
    plt.subplot(211)
    plt.title('Ports %s' % str(pp))
    [plt.axvline(x*num_sweeps, color='lightgray') for x in range(len(ic_data)//num_sweeps)]
    plt.axhline(0, color='lightgray')
    plt.plot(np.array(write_currents)*1e6, '.')
    plt.ylabel('I_write (uA)')
    plt.subplot(212)
    [plt.axvline(x*num_sweeps, color='lightgray') for x in range(len(ic_data)//num_sweeps)]
    plt.plot(np.array(ic_data)*1e6, '.')
    plt.ylabel('Ic_read (uA)')
    plt.xlabel('Trial #')
    fig_filename = filename + ('Ports %s' % str(pp))
    pickle.dump(fig, open(fig_filename + '.fig.pickle', 'wb'))
    plt.savefig(fig_filename)


# %%==========================================================================
# Much faster 2D map of pulse width vs pulse amplitude
# =============================================================================

num_samples_reset = 1
num_samples_delay = 500
num_samples_write = 1

marker_data =  [0] + [1]*num_samples_reset + [0]*num_samples_delay + [0]*num_samples_write + [0]*num_samples_delay
voltage_data = [0] + [0]*num_samples_reset + [0]*num_samples_delay + [1]*num_samples_write + [0]*num_samples_delay

awgw.create_waveform(voltages = voltage_data, filename = 'temp.wfm', clock = None, marker_data = marker_data, auto_fix_sample_length = True)
awgw.load_file('temp.wfm')
#awgw.set_trigger_mode(triggered_mode = True)
awgw.set_vpp(1)
awgw.set_marker_vhighlow(vlow = -0.6, vhigh = 0.000)
awgw.set_trigger_mode(trigger_mode = True)
awgw.set_output(True)
awgw.trigger_now()



# Setup Ic measurement channel
lecroy.set_trigger_mode('Normal')
lecroy.set_trigger('C3', volt_level = 0.1)
awg.setup_arb_wf(t = [0,2,9.5,10], v = [0,0,1,0], channel = 1)
awg.set_burst_mode(burst_enable = True, num_cycles = 1, phase = 0, trigger_source = 'MAN', channel = 1)
awg.set_freq(freq = 200, channel = 1)
awg.set_vhighlow(vhigh = 4, vlow = 0, channel = 1)
awg.set_output(True, channel = 1)
awg.trigger_now(channel = 1)

# Setup parameters
R_AWG = 10e3
#write_pulse_voltage_split = 0.5
#write_pulse_volage_attenuation = 
#write_voltage_scale = 46e-3/1 # # 3 dB power splitter + 1 kOhm resistor -> 1V pulse becomes 46 mV
write_voltage_scale = 0.5


def pulse_ic_vs_width_voltage(v = 0.2, w = 100e-9, verbose = False):
    
        # Apply reset pulse + write pulse
        awgw.set_vpp(2*v/write_voltage_scale)
        awgw.set_clock(min(num_samples_write / w, 2.6e9))
        awgw.trigger_now()
        
        # Read out Ic of device
        time.sleep(0.1)
        awg.trigger_now(channel = 1)
        time.sleep(0.01)
        ic = lecroy.get_parameter_value('P1')/R_AWG
        if ic<10e-6: ic = pulse_ic_vs_width_voltage(v = v, w = w)
        else:
            if verbose: print('%0.1f ns, %0.1f mV => %i uA' % (w*1e9,v*1e3,ic*1e6))
        return ic

def ic_vs_pulse(pulse_voltages, reset_voltage = -0.6, R_AWG = 10e3, port_pair = None, verbose = False):
    if port_pair is not None:
        switch.select_ports(port_pair)
        time.sleep(1)
    awgw.set_marker_vhighlow(vlow = reset_voltage, vhigh = 0.000)
    # Create write pulse series
    ic_data = []
    trial_v_w_ic = []
    for v in pulse_voltages:
#        # Setup memory write pulse first to avoid errors from AWG relay clicking when adjusted
#        awg.set_vhighlow(vlow = 0, vhigh = v, channel = 2)
#        time.sleep(2)
        for w in pulse_widths:
            ic = pulse_ic_vs_width_voltage(v = v, w = w, verbose = verbose)
            ic_data.append(ic)
            trial_v_w_ic.append([v,w,ic_data[-1]])
            
    V,W = np.meshgrid(pulse_voltages, pulse_widths, indexing = 'ij')
    IC = np.reshape(ic_data, W.shape)
    data = {'ic_data': ic_data,
            'pulse_voltages': pulse_voltages,
            'pulse_widths' : pulse_widths,
            'trial_v_w_ic' : trial_v_w_ic,
            'IC' : IC,
            'V' : V,
            'W' : W,
            'reset_voltage' : reset_voltage,
            'port_pair' : port_pair,
            'write_voltage_scale' : write_voltage_scale,
            'R_AWG' : R_AWG,
            'ramp_rate' : awg.get_vpp()/R_AWG/0.75*awg.get_freq(),
            }
    return data
        
#%%


switch.select_ports((5,6))

print(pulse_ic_vs_width_voltage(v = 0.25, w = 100e-9)*1e6)
print(pulse_ic_vs_width_voltage(v = 0.001, w = 100e-9)*1e6)


#%%
#def temp():
#    awgw.set_output(False)
#    awgw.load_file('temp.seq') # Need to not have the file of interest loaded so that the output doesn't get disabled
#    awgw.create_pulse('write_pulse.wfm', width = w, edge_width = 1e-12, voltage = v)
#    awgw.load_file('pulse_test.seq')
#    awgw.set_output(True)
#    awgw.query('*OPC?')

pulse_widths = np.logspace(np.log10(1e-7), np.log10(1/2.6e9), 100)
pulse_voltages = np.logspace(np.log10(.1), np.log10(0.001), 100)
reset_voltage = -1

port_pairs = [
        (1,1),
#        (2,1),
#        (4,3),
#        (6,5),
#        (8,7),
#        (10,9),
#        (1,2),
#        (3,4),
#        (5,6),
#        (7,8),
#        (9,10),
        ]

data = {port_pair : ic_vs_pulse(pulse_voltages, reset_voltage = reset_voltage, R_AWG = 10e3, verbose = True, port_pair = port_pair) for port_pair in tqdm(port_pairs)}
switch.disable()

#data = {'ic':IC, 'pulse_widths': pulse_widths, 'pulse_voltages': pulse_voltages}
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
pickle.dump({'data':data}, open(filename + '.pickle', 'wb'))

# Plot 
for pp, d in data.items():
    IC = d['IC']
    V = d['V']
    W = d['W']
    IC[IC<=10e-6] = np.nan
#    extraIC = np.zeros((IC.shape[0]+1, IC.shape[1]+1)); extraIC[:-1, :-1] = IC
#    extraV = np.zeros((V.shape[0]+1, V.shape[1]+1)); extraV[:-1, :-1] = V
#    extraW = np.zeros((W.shape[0]+1, W.shape[1]+1)); extraW[:-1, :-1] = W
    fig, ax = plt.subplots()
    ax.set_yscale('log')
    ax.set_xscale('log')
    plt.xlabel('Pulse width (s)')
    plt.ylabel('Pulse ampitude (V)')
    plt.title('Ports %s' % str(pp))
    im = ax.pcolor(W, V, IC*1e6)
    fig.colorbar(im)
    
    fig_filename = filename + ('Ports %s' % str(pp))
    pickle.dump(fig, open(fig_filename + '.fig.pickle', 'wb'))
    plt.savefig(fig_filename)


#%% Get data for a particular pulse width
pulse_voltages = np.linspace(5e-3, 30e-3, 50)
num_repeats = 200
w = 100e-9

data = {}
for port_pair in tqdm(port_pairs):
    switch.select_ports(port_pair)
    pulse_ic_vs_width_voltage(v = min(pulse_voltages), w = w, verbose = True)
    time.sleep(2)
    data[port_pair] = [[pulse_ic_vs_width_voltage(v = v, w = w, verbose = True) for n in range(num_repeats)] for v in pulse_voltages]

fig = plt.figure()
for pp, d in data.items():
    plot(pulse_voltages*1e3, np.mean(d,1)*1e6, '.', label = str(pp))

plt.xlabel('Pulse voltage (mV)')
plt.ylabel('Ic (uA)')
plt.legend()
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
pickle.dump({'data':data}, open(filename + '.pickle', 'wb'))
plt.tight_layout()
fig_filename = filename + ('Ports %s' % str(pp))
pickle.dump(fig, open(fig_filename + '.fig.pickle', 'wb'))
plt.savefig(fig_filename)


#%%


awgw = TektronixAWG7000('TCPIP0::%s::4000::SOCKET' % '192.168.1.103')

#%%============================================================================
# Setup pulse train waveforms
#==============================================================================
num_bits = 100
len_delay = 1
len_signal_write = 1
len_signal_read = 1
len_read_delay = 0
np.random.seed(2)
#write_voltages = np.random.choice([-1, 1], num_bits)
write_voltages = [-1,1]*100
prbs_voltage = [0]
prbs_marker = [0]*(len_read_delay+1)
for n,wb in enumerate(write_voltages):
    prbs_voltage += [wb]*len_signal_write + [0]*len_delay + [0]*len_signal_read + [0]*len_delay
    prbs_marker +=  [0]*len_signal_write +  [0]*len_delay + [1]*len_signal_read + [0]*len_delay
    
plot(np.array(prbs_voltage) + 2.5)
plot(np.array(prbs_marker))

sync_marker = [1]*(len(prbs_marker)//4)
sync_marker += [0]*(len(prbs_marker)-len(sync_marker))

awgw.write('WLIST:WAVEFORM:DELETE ALL')
awgw.create_waveform(voltages = prbs_voltage, filename = 'temp',
                     marker1_data = prbs_marker, marker2_data = sync_marker)
awgw.load_waveform('temp')
awgw.set_trigger_mode(continuous_mode=True)
awgw.set_output(True)
awgw.query('SYSTEM:ERROR?')

#%%
write_time = 10e-9
write_vpp = 0.1
write_voffset = 0.000
read_vpp = .53
delay_ns = 0

awgw.set_clock(len_signal_write/write_time)
awgw.set_marker_vhighlow(vlow = 0.000, vhigh = read_vpp)
awgw.set_vpp(write_vpp)
#awgw.set_voffset(write_voffset)
#awgw.set_marker_delay(delay_ns*1e-9)



#%% Run high-speed digital write waveform



#%%

##write_voltages = [1,-1, 1.5, -1.5, 2, -2, 2.5, -2.5, 3, -3]
##write_voltages = [, -3]
#write_voltage = 3
#write_voltages = np.random.choice([write_voltage, -write_voltage], 100)
#read_voltage = 2.5
#wait_time = 200e-9
#write_time = .05e-6
#read_time = .05e-6
#edge_time = .0e-6
#dt = 5e-9
#write_tv_list = [(0,0)]
#read_tv_list = [(0,0)]
#for n, wv in enumerate(write_voltages):
#    write_tv_list += pulse(center_time = (2*n+1)*wait_time, width = write_time, edge_width = edge_time,
#                     voltage = wv)
#    read_tv_list += pulse(center_time = (2*n+2)*wait_time, width = write_time, edge_width = edge_time,
#                     voltage = read_voltage)
#t_end = np.array(read_tv_list)[-1,0]
#write_tv_list += [(t_end,0)]
#read_tv_list  += [(t_end,0)]
#plt.plot(np.array(write_tv_list)[:,0], np.array(write_tv_list)[:,1])
#plt.plot(np.array(read_tv_list)[:,0], np.array(read_tv_list)[:,1] +3.5)
#
#
#awg.set_output(False, channel = 1)
#awg.set_output(False, channel = 2)
#
#awg.set_load(high_z = True, channel = 1)
#awg.set_load(high_z = True, channel = 2)
#
#awg.set_arb_wf(t = np.array(write_tv_list)[:,0], v = np.array(write_tv_list)[:,1],
#           dt = dt, channel = 1)
#awg.set_arb_wf(t = np.array(read_tv_list)[:,0], v = np.array(read_tv_list)[:,1],
#           dt = dt, channel = 2)
#awg.sync_arbs()
#
#awg.set_output(True, channel = 1)
#awg.set_output(True, channel = 2)

#%%


#==============================================================================
# Get data
#==============================================================================
lecroy.set_trigger_mode('Single')
time.sleep(1)

#x1,y1 = lecroy.get_wf_data(channel = 'C1')
x2,y2 = lecroy.get_wf_data(channel = 'C2')
x3,y3 = lecroy.get_wf_data(channel = 'C3')



#==============================================================================
# Analyze the output
#==============================================================================
hi = 0.010
lo = 0.005
thresholded_read_output = threshold_with_hysteresis(x = y2, th_lo = lo, th_hi = hi, initial = False)

read_time_indices = np.where(np.diff(thresholded_read_output + 0.0) == 1)
read_times = x2[read_time_indices]


hi = 2
lo = 1
thresholded_write_input = threshold_with_hysteresis(x = -y3, th_lo = lo, th_hi = hi, initial = False)

write_time_indices = np.where(np.diff(thresholded_write_input + 0.0) == 1)
write_times = x3[write_time_indices]


if read_times[0] < write_times[0]:
    read_times = read_times[1:]
if read_times[-1] < write_times[-1]:
    write_times = write_times[:-1]

print((len(read_times)))
print((len(write_times)))

# %%

# Export to MATLAB:
data_dict = {'x1':x1, 'x2':x2, 'y1':y1, 'y2':y2, 'x3':x3, 'y3':y3}
file_path, file_name  = save_data_dict(data_dict, test_type = 'Trace data for MATLAB', test_name = '',
                        filedir = '', zip_file=False)

#plt.plot(x1*1e6, y1/(max(y1)-min(y1)),
#         x2*1e6, y2/(max(y2)-min(y2)),
#         x3*1e6, y3/(max(y3)-min(y3)),
#                    )


#
#t = np.array(write_tv_list)[:,0]
#v = np.array(write_tv_list)[:,1]
#channel = 2
#num_samples = 2**16
#dt = 10e-6
#
#t = np.array(t);  v = np.array(v)
#
#vpp = max(v) - min(v)
#voffset = (max(v) + min(v))/2
#v = v-min(v);  v = 2*v/max(v);  v = v-1
## Change timeout to 60 sec to allow writing of waveform
#temp = awg.pyvisa.timeout; awg.pyvisa.timeout = 2e3
#total_time = t[-1] - t[0]
#num_samples = total_time/dt
#
#t_interp = np.linspace(t[0],t[-1], num_samples)
#v_interp = np.interp(t_interp, t, v)
#
#data_strings = ['%0.3f' % x for x in v_interp]
#data_msg = ', '.join(data_strings)
#
#awg.write('SOURCE%s:APPLY:ARB' % channel)
#awg.write('SOURce%s:DATA:VOLatile:CLEar' % channel)
#awg.write('SOURce%s:DATA:ARB TEMPARB%s, %s' % (channel, channel, data_msg))
#awg.write('SOURce%s:FUNCtion:ARBitrary TEMPARB%s' % (channel, channel))
#
#sample_rate = num_samples/total_time
#if (sample_rate > 250e6):
#    raise ValueError('[Agilent33522a] set_arb_wf() sample rate too high (tried %0.6e Sa/s, 250 MSa/s max)' % sample_rate)
#awg.write('SOURce%s:FUNCtion:ARBitrary:SRATe %0.6e' % (channel, sample_rate))
#awg.set_vpp(vpp, channel = channel)
#awg.set_voffset(voffset, channel = channel)
