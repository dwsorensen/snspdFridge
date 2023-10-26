# Ic measurement code
# Run add_path.py first

import numpy as np
import time
from matplotlib import pyplot as plt
from scipy.optimize import fmin

def setup_ic_measurement_lecroy(lecroy, vpp = 1, repetition_hz = 100, trigger_level = 0.1, trigger_slope = 'Positive',
                        coupling_ch1 = 'DC1M', coupling_ch2 = 'DC1M'):

    # Setup LeCroy scope:
    lecroy.set_coupling(channel = 'C1', coupling = coupling_ch1)
    lecroy.set_coupling(channel = 'C2', coupling = coupling_ch2)
    lecroy.set_bandwidth(channel = 'C1', bandwidth = '20MHz')
    lecroy.set_bandwidth(channel = 'C2', bandwidth = '20MHz')
    lecroy.label_channel(channel = 'C1', label = 'AWG input waveform')
    lecroy.label_channel(channel = 'C2', label = 'Device output')
    lecroy.label_channel(channel = 'F1', label = 'Per-sweep Ic values')
    lecroy.label_channel(channel = 'F2', label = 'Ic values histogram')
    lecroy.set_vertical_scale(channel = 'C1', volts_per_div = 500e-3, volt_offset = 0)
    lecroy.set_vertical_scale(channel = 'C2', volts_per_div = 100e-3, volt_offset = 0)
    lecroy.set_horizontal_scale(time_per_div = (1.0/repetition_hz)/10.0, time_offset = 0)
    lecroy.set_trigger(source = 'C2', volt_level = trigger_level, slope = trigger_slope)
    lecroy.set_trigger_mode(trigger_mode = 'Normal')
    lecroy.set_parameter(parameter = 'P1', param_engine = 'Mean', source1 = 'C1', source2 = None)
    lecroy.setup_math_trend(math_channel = 'F1', source = 'P1', num_values = 10e3)
    lecroy.setup_math_histogram(math_channel = 'F2', source = 'P1', num_values = 300)
    lecroy.set_parameter(parameter = 'P2', param_engine = 'LevelAtX', source1 = 'C1', source2 = None)
    lecroy.set_parameter(parameter = 'P3', param_engine = 'HistogramMedian', source1 = 'F2', source2 = None)
    lecroy.set_parameter(parameter = 'P4', param_engine = 'HistogramSdev', source1 = 'F2', source2 = None)
    lecroy.set_parameter(parameter = 'P5', param_engine = 'FullWidthAtHalfMaximum', source1 = 'F2', source2 = None)
    lecroy.set_display_gridmode(gridmode = 'Single')


def run_ic_sweeps(lecroy, num_sweeps, timeout = 60):
    lecroy.clear_sweeps()
    time.sleep(0.1)
    measured_sweeps = 0
    elapsed_time = 0
    num_sweeps = int(num_sweeps)
    while (measured_sweeps < num_sweeps+1):
        measured_sweeps = lecroy.get_num_sweeps(channel = 'F1')
        time.sleep(0.1)
        elapsed_time += 0.1
        if measured_sweeps == 0 and elapsed_time > 1:
            return np.array([0]*num_sweeps)
    x, ic_values = lecroy.get_wf_data(channel='F1')
    while len(ic_values) < num_sweeps:
        x, ic_values = lecroy.get_wf_data(channel='F1')
        time.sleep(0.05)
    return ic_values[:num_sweeps] # will occasionally return 1-2 more than num_sweeps


def gumbel_pdf(theta, x):
    a = theta[0]; b = theta[1]
    return 1.0/b*np.exp((x-a)/b - np.exp((x-a)/b))


def gumbel_dist_error_fun(theta, data, min_prob = 1e-2):
    pdf_fun = gumbel_pdf
    prob = pdf_fun(theta = theta, x = data)
    prob[prob<min_prob] = min_prob  # Otherwise any datapoint with probability zero returns log(P(x)=0) = -Inf
    log_likelihood = np.sum(np.log(prob))
    return -log_likelihood


def analyze_ic_values(ic_values):
    theta0 = [np.median(ic_values), np.std(ic_values)*10]
    thetaopt = fmin(gumbel_dist_error_fun, theta0, [ic_values])
    ic = thetaopt[0]
    delta_ic = thetaopt[1]
    return ic, delta_ic


def calc_ramp_rate(vpp, R, repetition_hz, wf = 'RAMP'):
    if wf.upper() == 'HEARTBEAT':
        T = 1.0/repetition_hz
        T_ramp = T/8.0
        I_max = (vpp/2.0)/R
        return I_max/T_ramp
    elif wf.upper() == 'SINE':
        return (vpp/2.0)/R * (2*np.pi*repetition_hz)
    elif wf.upper() == 'RAMP':
        return (vpp/R) / (1/repetition_hz)
    else:
        print('Incorrect waveform (must be "sine" or "heartbeat" or "ramp")')
        return 0


def data_list_to_histogram_list(data_list, num_bins = 100, range_min = None, range_max = None, plotme = False):
    hist_list = []
    for data in data_list:
        if range_min is None:  range_min = np.min(data_list)
        if range_max is None:  range_max = np.max(data_list)
        bin_vals, bin_edges = np.histogram(data, bins = num_bins, range=(range_min, range_max))
        bin_centers = bin_edges[:-1] + (bin_edges[1]-bin_edges[0])/2.0
        hist_list.append(bin_vals)
    return hist_list, bin_centers


def quick_ic_test(lecroy, num_sweeps = 1000):
    ic_data = run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R
    print('Median = %0.2f uA / σ = %0.2f uA' % (np.median(ic_data*1e6), np.std(ic_data*1e6)))


def quick_retrap_test(lecroy, num_sweeps = 1000):
    ic_data = run_ic_sweeps(lecroy, num_sweeps = num_sweeps)/R
    print('Median Iretrap = %0.2f uA / Std. dev Iretrap = %0.2f uA' % (np.median(ic_data*1e6), np.std(ic_data*1e6)))
    lecroy.set_trigger(source = 'C2', volt_level = trigger_level, slope = 'Positive')


def fit_ic_histogram(ic_values, bins = 100, binrange = None, plot = False):
    ic_hist, bin_edges = np.histogram(a = ic_values, bins = bins)
    ic_hist_x = bin_edges[:-1] + (bin_edges[1]-bin_edges[0])/2.0

    ic, delta_ic = analyze_ic_values(ic_values)
    ic_hist_fit_x = np.linspace(min(ic_values), max(ic_values), bins)
    ic_hist_fit = gumbel_pdf([ic, delta_ic], ic_hist_fit_x)
    ic_hist_fit = ic_hist_fit/float(np.max(ic_hist_fit))
    ic_hist = ic_hist/float(np.max(ic_hist))
    if plot:
        plt.bar(ic_hist_x, ic_hist, width=(ic_hist_x[1]-ic_hist_x[0]))
        plt.plot(ic_hist_x, ic_hist_fit, 'r')
        plt.show()
    return ic_hist_x, ic_hist, ic_hist_fit


def plot_ic_histogram_vs_current(ic_data_list, currents, file_name, num_bins = 100, range_min = None, title = '', current_on_xaxis = False):
    # Plot histogram vs other things in 2D
    ic_data_list_toplot = np.array(ic_data_list)
    ic_hist_list, ic_bins = data_list_to_histogram_list(ic_data_list_toplot, num_bins = num_bins, range_min = range_min)


    if current_on_xaxis is True:
        extent = [currents[0]*1e6, currents[-1]*1e6, ic_bins[0]*1e6, ic_bins[-1]*1e6]
        plt.imshow(np.flipud(np.transpose(ic_hist_list)), extent=extent, aspect = 'auto',  interpolation='nearest')
        plt.ylabel('Ic distribution values (uA)'); plt.xlabel('Write port current (uA)')
        plt.title(title)
    else:
        extent = [0, len(currents), ic_bins[0]*1e6, ic_bins[-1]*1e6]
        plt.subplot(211)
        plt.imshow(np.flipud(np.transpose(ic_hist_list)), extent=extent, aspect = 'auto',  interpolation='nearest')
        plt.title(title)
        plt.ylabel('Ic distribution values (uA)'); plt.xlabel('Experiment number')
        plt.subplot(212)
        plt.plot(np.array(currents)*1e6, 'o')
        plt.ylabel('Write current (uA)'); plt.xlabel('Experiment number')
        plt.grid(b=True, which='major', color='gray', linestyle='--')
        plt.xlim([0.5, len(currents)-0.5])
    plt.savefig(file_name)
    plt.show()


def plot_ic_histogram_vs_current_norm(ic_data_list, currents, file_name, num_bins = 100, range_min = None, title = '', current_on_xaxis = False):
    # Plot histogram vs other things in 2D
    ic_data_list_toplot = np.array(ic_data_list)
    ic_hist_list, ic_bins = data_list_to_histogram_list(ic_data_list_toplot, num_bins = num_bins, range_min = range_min)


    if current_on_xaxis is True:
        extent = [currents[0]*1e6, currents[-1]*1e6, ic_bins[0]*1e6, ic_bins[-1]*1e6]
        plt.imshow(np.flipud(np.transpose(ic_hist_list)), extent=extent, aspect = 'auto',  interpolation='nearest')
        plt.ylabel('Ic distribution ratios'); plt.xlabel('Write port current ratio (ig/ig_sw)')
        plt.title(title)
    else:
        extent = [0, len(currents), ic_bins[0]*1e6, ic_bins[-1]*1e6]
        plt.subplot(211)
        plt.imshow(np.flipud(np.transpose(ic_hist_list)), extent=extent, aspect = 'auto',  interpolation='nearest')
        plt.title(title)
        plt.ylabel('Ic distribution values (uA)'); plt.xlabel('Experiment number')
        plt.subplot(212)
        plt.plot(np.array(currents)*1e6, 'o')
        plt.ylabel('Write current (uA)'); plt.xlabel('Experiment number')
        plt.grid(b=True, which='major', color='gray', linestyle='--')
        plt.xlim([0.5, len(currents)-0.5])
    plt.savefig(file_name)
    plt.show()