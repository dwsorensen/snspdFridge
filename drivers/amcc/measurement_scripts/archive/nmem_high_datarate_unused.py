
#%% Setup 


write_times = np.logspace(np.log10(1e-7), np.log10(10e-9), 10)
read_max_v = []
reference_max_v = []
num_bits_required = 100000
data = []

for wt in write_times:
    time_per_sample = wt
    
    read_pulse_amplitude = 1.3
    write_pulse_amplitude = .21
    delay_ns = 0
    
    # Thermoelectric offsets
    read_vlow = -0.00
    write_voffset = 0.020
    
    awgw.set_clock(1/time_per_sample)
    awgw.set_marker_vhighlow(vlow = read_vlow, vhigh = read_vlow + read_pulse_amplitude)
    awgw.set_vpp(write_pulse_amplitude*2)
    awgw.set_voffset(write_voffset)
    awgw.set_marker_delay(delay_ns*1e-9)
    lecroy.set_horizontal_scale(time_per_div = max(time_per_sample,5e-9)/10, time_offset = -time_per_sample/2)
    
    lecroy.set_trigger_mode('Stop')
    time.sleep(3)
    lecroy.clear_sweeps()
    time.sleep(1)
    lecroy.set_trigger_mode('Normal')
    while lecroy.get_num_sweeps('F1') < num_bits_required:
        time.sleep(5)
    lecroy.set_trigger_mode('Stop')
    time.sleep(5)
    temp, reference_max_v = lecroy.get_wf_data('F1')
    temp, read_max_v = lecroy.get_wf_data('F5')
    new_data = {
            'write_time_ns' : wt,
            'read_pulse_amplitude' : read_pulse_amplitude,
            'write_pulse_amplitude' : write_pulse_amplitude,
            'read_vlow' : read_vlow,
            'write_voffset' : write_voffset,
            'read_max_v' : read_max_v,
            'reference_max_v' : reference_max_v,
                }
    data.append(new_data)

#data = {'ic':IC, 'pulse_widths': pulse_widths, 'pulse_voltages': pulse_voltages}
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
pickle.dump({'data':data}, open(filename + '.pickle', 'wb'))
#%%
    

for d in data:
    figure(1)
#    plot(d['read_max_v'], d['reference_max_v'], '.', label = (round(d['write_time_ns']*1e9)))
    bits_written = np.array(d['read_max_v']) > 0.4
    bits_read = np.array(d['reference_max_v']) < 0.080
    num_errors = np.sum(bits_written != bits_read)
    figure(2)
    loglog(d['write_time_ns'],num_errors/len(d['read_max_v']),'.')
figure(1)
legend()


#%% Get lecroy waveform
t,v = lecroy.get_wf_data('C2')
data = {
        't':t,
        'v':v,
        'prbs_voltage':prbs_voltage,
        'read_marker':read_marker,
        }



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