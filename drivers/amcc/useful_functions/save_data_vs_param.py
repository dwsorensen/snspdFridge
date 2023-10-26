# Written by Adam McCaughan Jan 17, 2014
# Run add_path.py first

import numpy as np
import time
import os
import scipy.io
import datetime
from matplotlib import pyplot as plt
import pickle as pickle
import matplotlib.cm as cm
import zipfile


def save_xy_vs_param(X, Y, P, xname = 'x', yname = 'y', pname = 'p',
                        test_type = 'Y Measurement', test_name = 'Test01',
                        xlabel = 'amps', ylabel = 'volts', plabel = 'farads', title = '', legend = False,
                        xscale = 1, yscale = 1, pscale = 1,
                        plotstyle = '-', plot_function = plt.plot,
                        plabels_explicit = None,
                        plot_every_n = 1,
                        extra_data_dict = {}, fig_size_inches = None,
                        comments = '', filedir = '', display_plot = False, zip_file=True):
    """ Save list-of-lists X and Y data, along with list P (parameter) as MATLAB .mat file and Python .pickle file 
    and additionally zips those .mat and .pickle files together with a .png of the graph """
    X = np.array(X); Y = np.array(Y); P = np.array(P)
    data_dict = {xname:X, yname:Y, pname:P, 'comments':comments}
    data_dict.update(extra_data_dict)
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    file_name =  '%s %s %s' % (test_type, time_str, test_name)
    file_path = os.path.join(filedir, file_name)

    # Save data in MATLAB and pickle formats
    scipy.io.savemat(file_path + '.mat', mdict=data_dict)
    # f = open(file_path + '.pickle', 'wb'); pickle.dump(data_dict, f); f.close()
    fig = plt.figure()
    if fig_size_inches is not None: fig.set_size_inches(fig_size_inches)

    # Plot data
    if X.ndim == 1:
        plot_function(X*xscale, Y*yscale, plotstyle)
    elif X.ndim == 2:
        mycm = cm.winter
        cm_indices = np.linspace(0, mycm.N*0.8, len(X))
        for n in range(len(X))[::plot_every_n]:
            if plabels_explicit is None: 
                plabel_text = '%0.3f %s' % (P[n]*pscale, plabel)
            else:
                plabel_text = plabels_explicit[n]
            plot_function(X[n]*xscale, Y[n]*yscale, plotstyle, label = plabel_text,  c = mycm(int(cm_indices[n])))
    plt.xlabel(xlabel); plt.ylabel(ylabel); plt.title(title)
    if legend is True: plt.legend(loc='best')
    # plt.gca().get_xaxis().get_major_formatter().set_useOffset(False) # Remvoes relative shift on graph
    plt.savefig(file_path + '.png')

    print('Saving data and figure with filename: %s' % file_name)
    if zip_file:
        zf = zipfile.ZipFile(file_path + '.zip', 'w')
        for name in ['.mat', '.png']:
            zf.write(file_path + name, arcname = file_name + name, compress_type = zipfile.ZIP_DEFLATED)

    if display_plot is True: plt.show()
    else: plt.close()
    return (file_path, file_name)


def save_x_vs_param(X, P, xname = 'x',  pname = 'p',
                        test_type = 'X Measurement', test_name = 'Test01',
                        extra_data_dict = {},
                        comments = '', filedir = '', zip_file=True):
    """ Save list-of-lists X data, along with list P (parameter) as MATLAB .mat file and Python .pickle file 
    and additionally zips those .mat and .pickle files together with a .png of the graph """
    data_dict = {xname:X, pname:P, 'comments':comments}
    data_dict.update(extra_data_dict)
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    file_name =  '%s %s %s' % (test_type, time_str, test_name)
    file_path = os.path.join(filedir, file_name)

    # Save data in MATLAB and pickle formats
    scipy.io.savemat(file_path + '.mat', mdict=data_dict)
    # f = open(file_path + '.pickle', 'wb'); pickle.dump(data_dict, f); f.close()

    print('Saving data and figure with filename: %s' % file_name)
    if zip_file:
        zf = zipfile.ZipFile(file_path + '.zip', 'w')
        for name in ['.mat']:
            zf.write(file_path + name, arcname = file_name + name, compress_type = zipfile.ZIP_DEFLATED)

    return (file_path, file_name)





def save_data_dict(data_dict, test_type = 'X Measurement', test_name = 'Test01',
                        filedir = '', zip_file=True):
    """ Directly input the data dictionary that scipy.io.savemat wants, and automatically zip the pickle
        and matlab file up """
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    file_name =  '%s %s %s' % (test_type, time_str, test_name)
    file_path = os.path.join(filedir, file_name)

    # Save data in MATLAB and pickle formats
    scipy.io.savemat(file_path + '.mat', mdict=data_dict)
    # f = open(file_path + '.pickle', 'wb'); pickle.dump(data_dict, f); f.close()

    print('Saving data and figure with filename: %s' % file_name)
    if zip_file:
        zf = zipfile.ZipFile(file_path + '.zip', 'w')
        for name in ['.mat']:
            zf.write(file_path + name, arcname = file_name + name, compress_type = zipfile.ZIP_DEFLATED)

    return (file_path, file_name)





# X = []
# Y = []
# P = []
# for n in range(10):
#     X.append(np.linspace(0,10,100))
#     Y.append(np.random.rand(100) + n)
#     P.append(n)
    
    
# fn = save_xy_vs_param(X, Y, P, xname = 'f', yname = 'output', pname = 'shift',
#                         test_type = 'ZZZ Measurement', test_name = 'Test01',
#                         xlabel = 'Frequency (GHz)', ylabel = 'Whatup', title = 'Hey there',
#                         filedir = '/Users/amcc/Documents/MATLAB',
#                         legend = True, display_plot = True)

