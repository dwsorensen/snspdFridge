# Ic measurement code
# Run add_path.py first
# from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *
from instruments.hp_8722c import HP8722C

na = HP8722C('GPIB0::8')




def multi_sweep_mag(f_start, f_stop, freq_resolution = 1e6, num_pts = 1601):
    ### Multi-sweep combination
    freq_step = freq_resolution*(num_pts-1)
    freq_bounds = np.linspace(f_start, f_stop, 2 + (f_stop-f_start)//freq_step, endpoint = True)
    freq_bounds = np.round(freq_bounds/40e6)*40e6 # Rounds points to nearest 40 MHz so compatible with HP 8722C


    F = np.array([])
    M = np.array([])
    for n, f_start in enumerate(freq_bounds[:-1]):
        na.freq_range(f_start = freq_bounds[n], f_stop = freq_bounds[n+1], num_pts = num_pts)
        (F_segment, M_segment) = na.run_sweep_mag()
        F = np.concatenate((F, F_segment))
        M = np.concatenate((M, M_segment))
    return F, M





# na.freq_range(f_start = 500e6, f_stop = 1000e6, num_pts = 1601)

# save_xy_vs_param(f, M, [], xname = 'Frequency', yname = 'Magnitude', pname = 'p',
#                         test_type = test_type, test_name = test_name,
#                         xlabel = 'Frequency (MHz)', ylabel = 'Magnitude (dB)', plabel = '', title = '', legend = False,
#                         xscale = 1e-6, yscale = 1, pscale = 1,
#                         comments = '', filedir = '', display_plot = False, zip_file=True)


# na.freq_range(f_center = 12.8e9, f_span = 0.4e9, num_pts = 1601)
# (f, M) = na.run_sweep_mag()
# plt.plot(f/1e9,M)
# plt.show()


############# Sweep spectrum at multiple powers

sample_name = 'NWL032B Device NE harp dual strings'
test_name = 'Single resonance with bias 4.2K'
test_type = 'VNA'

f_start = 4e9
f_stop = 18e9
freq_resolution = 0.1e6


F_list = []
M_list = []
P_list = [0, -10, -20, -30, -40, -50, -60]
start_time = time.time()
for n, p in enumerate(P_list):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(P_list), (time.time()-start_time)/60.0))
    print('Setting power to %s dB' % p)
    na.power(p)
    (F, M) = multi_sweep_mag(f_start = f_start, f_stop = f_stop, freq_resolution = freq_resolution)
    F_list.append(F)
    M_list.append(M)

save_xy_vs_param(F_list, M_list, P_list, xname = 'F', yname = 'M', pname = 'P',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        xlabel = 'Frequency (MHz)', ylabel = 'Magnitude (dB)', plabel = 'Power (dBm)', title = '', legend = True,
                        xscale = 1e-6, yscale = 1, pscale = 1,
                        comments = '', filedir = '', display_plot = False, zip_file=True)

plt.plot(F_list,M_list)
plt.show()










############# Sweep spectrum while biasing with SRS

sample_name = 'NWL032B Device NE harp dual strings'
test_name = 'Closeup of resonance with DC bias 4.2K'
test_type = 'VNA'

R_bias = 100e3
# f_start = 4e9
# f_stop = 18e9
# freq_resolution = 0.1e6


F_list = []
M_list = []
currents = np.linspace(0,30e-6,61)
start_time = time.time()
for n, i in enumerate(currents):
    print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))

    SRS.set_voltage(((i>0)-0.5)/5e2); time.sleep(0.05); SRS.set_voltage(i*R_bias); time.sleep(0.05)

    (F, M) = na.run_sweep_mag()
    F_list.append(F)
    M_list.append(M)

save_xy_vs_param(F_list, M_list, currents, xname = 'F', yname = 'M', pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        xlabel = 'Frequency (MHz)', ylabel = 'Magnitude (dB)', plabel = 'Bias current (uA)', title = '', legend = False,
                        xscale = 1e-6, yscale = 1, pscale = 1e6,
                        comments = '', filedir = '', display_plot = True, zip_file=True)

# plt.plot(F_list,M_list)
# plt.show()





################### Subtract off baseline:
m = np.array(M_list)[-10:,:]
mm = np.mean(m,0)
tiled_mm = np.tile(mm,[np.array(M_list).shape[0],1])
new_m = np.array(M_list) - tiled_mm


sample_name = 'NWL032B Device NE harp dual strings'
test_name = 'Closeup of resonance with DC bias 4.2K subtracted mag'
test_type = 'VNA'

save_xy_vs_param(F_list[0:30], new_m[0:30], currents, xname = 'F', yname = 'M', pname = 'currents',
                        test_type = test_type, test_name = sample_name + ' ' + test_name,
                        xlabel = 'Frequency (MHz)', ylabel = 'Magnitude (dB)', plabel = 'Bias current (uA)', title = '', legend = False,
                        xscale = 1e-6, yscale = 1, pscale = 1e6,
                        comments = '', filedir = '', display_plot = True, zip_file=True)
