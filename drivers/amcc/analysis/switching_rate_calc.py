from matplotlib import pyplot as plt
import scipy.io
import numpy as np
from numpy import log, log10, exp

def values_to_hist(values, num_bins):
    bin_counts, bin_edges = np.histogram(values, bins = num_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:])/2
    return bin_centers, bin_counts


def FD_transform(counts, didt, Delta_I):
    """ Performs the Fulton-Dunkelberger transformation.  Note that for Ic sweeps, the
    scaling coefficient is (dI/dt)/(Delta_I) [Delta_I is the spacing between
    the I bins]"""
    P = np.flipud(counts)
    Gamma_SW = [0,0]
    for K in range(2,len(P)):
        Gamma_SW.append( didt/Delta_I * np.log( (P[K] + np.sum(P[:K-1])) / float(np.sum(P[:K-1])) )  )
    Gamma_SW = np.flipud(np.array(Gamma_SW))
    return Gamma_SW


def Gamma_SW_FD_transform(ic_values, didt, num_bins = 1000):
    """ Converts a list of ic values into a switching rate versus bias current plot.
        This conversion is done via the Fulton-Dunkelberger transformation """
    I, counts = values_to_hist(values = ic_values, num_bins = num_bins)
    Delta_I = I[1]-I[0]
    Gamma_SW = FD_transform(counts, didt, Delta_I)
    return I, counts, Gamma_SW

    
def Gumbel_distribution(x = np.linspace(200e-6,300e-6), mu = 250e-6, beta = 2e-6):
    """ Returns points of the reverse Gumbel distribution """
    z = (x-mu)/beta
    return 1/beta*np.exp(z-np.exp(z))
    
    
def Gumbel_parameters_from_Ic_statistics(ic_values):
    """ Uses the median and std of the ic values to calculate parameters for a
    reverse Gumbel distribution of the form by 1/beta*exp(z-exp(z)) where
    z = (x-mu)/beta """
    beta = np.std(ic_values)*np.sqrt(6)/np.pi
    mu = np.median(ic_values) - beta*np.log(np.log(2))
    return mu, beta
    
    
def Gamma_SW_Ic_statistics(ic_values, didt, I = np.linspace(0,500e-6)):
    mu, beta = Gumbel_parameters_from_Ic_statistics(ic_values)
    Gamma_SW = didt/beta*np.exp((I-mu)/beta)
    return Gamma_SW


#==============================================================================
# Example code
#==============================================================================
    
d = scipy.io.loadmat('2016-11-29-10-41-41-SE005-Device-C4-Ic-Sweep.mat')
ic_values = d['ic_data']
didt = 0.4

# FD transform
I_FD, counts, Gamma_SW_FD = Gamma_SW_FD_transform(ic_values, didt, num_bins = 100)
plt.semilogy(I_FD, Gamma_SW_FD, 'g.')

# Switching rates estimated from the median and variance of the Ic distribution
I_stat = np.linspace(240e-6,280e-6)
Gamma_SW_stat = Gamma_SW_Ic_statistics(ic_values, didt, I = I_stat)
plt.semilogy(I_stat, Gamma_SW_stat, 'b')



#==============================================================================
# Unused code from the analysis folder
#==============================================================================

#def gumbel_pdf(theta, x):
#    a = theta[0]; b = theta[1]
#    return 1.0/b*np.exp((x-a)/b - np.exp((x-a)/b))
#
#
#def gumbel_dist_error_fun(theta, data, min_prob = 1e-2):
#    pdf_fun = gumbel_pdf
#    prob = pdf_fun(theta = theta, x = data)
#    prob[prob<min_prob] = min_prob  # Otherwise any datapoint with probability zero returns log(P(x)=0) = -Inf
#    log_likelihood = np.sum(np.log(prob))
#    return -log_likelihood
#
#
#def analyze_ic_values(ic_values):
#    theta0 = [np.median(ic_values), np.std(ic_values)*10]
#    thetaopt = fmin(gumbel_dist_error_fun, theta0, [ic_values])
#    ic = thetaopt[0]
#    delta_ic = thetaopt[1]
#    return ic, delta_ic

    
    
    
##==============================================================================
## Code I tried to use to map SNSPD jitters to switching rates; didn't work
##==============================================================================
#def Gamma_SW_jitter(td_values, dde = 0.0001, num_bins = 1000):
#    """ Performs the Fulton-Dunkelberger transformation on a list of time delay
#        values.  First, generates a histogram with num_bins bins, then performs
#        the FD transformation on that histogram """
#    t, counts = values_to_hist(values = td_values, num_bins = num_bins)
#    Delta_t = t[1]-t[0]
#    Gamma_SW = nonunity_FD_transform(counts, scaling_coeff = 1/Delta_t, dde = dde)
#    return t, counts, Gamma_SW
#
#
## Performs the Fulton-Dunkelberger transformation, which converts
## counts versus time histogram to a count rate versus time chart
#def Gamma_SW_jitter_histogram(t, counts, dde = 0.0001):
#    Delta_t = t[1]-t[0]
#
#    # The FD transform assumes a 100% chance of the event happening, but sometimes
#    # we want to include DDE (thus <100% chance of an event). This line adds fake 
#    # counts to the end of the PDF, where the "non-detected" events can be placed
#    # It essentially does the accounting for DDE (tested w/the reverse transform, it works)
#    counts = np.append(counts, np.sum(counts)*(1-dde)/dde)
#    t = np.append(t, t[-1] + Delta_t)
#    
#    P = counts/float(np.sum(counts)) # Convert number of counts to probability
#    P = np.flipud(P)
#    Gamma_SW = [0,0]
#    for K in range(2,len(P)):
#        Gamma_SW.append(  1/Delta_t * np.log( (P[K] + np.sum(P[:K-1])) / np.sum(P[:K-1]) )  )
#    Gamma_SW = np.flipud(np.array(Gamma_SW))
#    P = np.flipud(P)
#    
#    return P[:-1], Gamma_SW[:-1]
#
#def nonunity_FD_transform(counts, scaling_coeff = 1, dde = 1):
#    """ The FD transform assumes a 100% chance of the event happening, but sometimes
#    we want to include DDE (thus <100% chance of an event). This line adds fake 
#    counts to the end of the PDF/histogram , where the "non-detected" events can be placed
#    It essentially does the accounting for DDE (tested w/the reverse transform, it works) """
#    counts = np.append(counts, np.sum(counts)*(1-dde)/dde)
#    nonunity_Gamma_SW = FD_transform(counts, scaling_coeff = scaling_coeff)
#    return nonunity_Gamma_SW[:-1]
