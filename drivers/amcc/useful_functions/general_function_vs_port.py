

#%%============================================================================
# Perform measurement vs parameter sweep for pairs of ports
#==============================================================================
import time
from tqdm import tqdm # Requires "colorama" package also on Windows to display properly

def measure_vs_parameter(measurement_function, parameter_list, *args, **kwargs):
    data_dict = {}
    start_time = time.time()
    for n, p in enumerate(parameter_list):
        data_dict[p] = measurement_function(p, *args, **kwargs)
        elapsed_time = (time.time()-start_time)/60.0
        print('   ---   Time elapsed for measurement %s of %s: %0.2f min (~%0.2f min remaining)   ---   '\
              % (n+1, len(parameter_list), elapsed_time, (len(parameter_list)-(n+1))*elapsed_time/(n+1)))
    return data_dict

data_dict = {}
for n, port_pair in enumerate(port_pairs):
    data_dict[port_pair] = {p:v for }
d = {n: n**2 for n in range(5)}


data_dict = {port_pair : {p:run_ic_sweeps(p) for p in tqdm(parameter_list)} for port_pair in port_pairs}

# Run Ic sweep vs current for several port pairs
port_pairs = 
data_dict = {}
for port_pair in port_pairs:
    data_dict[port_pair] = {p:run_ic_sweeps(p) for p in tqdm(parameter_list)}

def measure_vs_ports(switch, measurement_function, switch1_ports = None, switch2_ports = None, port_pairs = None, *args, **kwargs):
    if port_pairs is None:
        if switch2_ports is None:
            switch2_ports = [None]*len(switch1_ports)
        port_pairs = list(zip(switch1_ports, switch2_ports))
    
    data_dict = {}
    start_time = time.time()
    for n, port_pair in enumerate(port_pairs):
        switch.select_port(port = port_pair[0], switch = 1)
        switch.select_port(port = port_pair[1], switch = 2)
        time.sleep(0.5)
        elapsed_time = (time.time()-start_time)/60.0
        print('######################################################################')
        print('### Selecting (Switch 1 PORT %s) and (Switch 2 PORT %s) ' % (port_pair[0], port_pair[1]))
        print('######################################################################')
        data_dict[port_pair] =  measurement_function(*args, **kwargs)
        print('######################################################################')
        print('### Total time elapsed  %s of %s: %0.2f min (~%0.2f min remaining) '\
              % (n+1, len(port_pairs), elapsed_time/60.0, (len(port_pairs)-(n+1))*elapsed_time/(n+1)))
        print('######################################################################')
        print('\n')
    return data_dict


def measure_vs_parameter_vs_ports(switch, measurement_function, parameter_list, switch1_ports = None, switch2_ports = None, port_pairs = None, *args, **kwargs):
    if port_pairs is None:
        if switch2_ports is None:
            switch2_ports = [None]*len(switch1_ports)
        port_pairs = list(zip(switch1_ports, switch2_ports))
    
    data_dict = {}
    start_time = time.time()
    for n, port_pair in enumerate(port_pairs):
        switch.select_port(port = port_pair[0], switch = 1)
        switch.select_port(port = port_pair[1], switch = 2)
        time.sleep(0.5)
        elapsed_time = (time.time()-start_time)/60.0
        print('######################################################################')
        print('### Selecting (Switch 1 PORT %s) and (Switch 2 PORT %s) ' % (port_pair[0], port_pair[1]))
        print('######################################################################')
        data_dict[port_pair] = measure_vs_parameter(measurement_function, parameter_list, *args, **kwargs)
        print('######################################################################')
        print('### Total time elapsed  %s of %s: %0.2f min (~%0.2f min remaining) '\
              % (n+1, len(port_pairs), elapsed_time/60.0, (len(port_pairs)-(n+1))*elapsed_time/(n+1)))
        print('######################################################################')
        print('\n')
    return data_dict


#def test_measurement_function(parameter):
#    print('Test function %s' % parameter)
#    time.sleep(0.1)
#    return parameter*2
#
#parameter_list = np.linspace(-200e-6,200e-6,5)
#measure_vs_parameter(test_measurement_function, parameter_list)
#
#measure_vs_parameter_vs_ports(switch, test_measurement_function, parameter_list, port_pairs = [(3,5), (6,7)])


#%%
#x = 1
#currents = np.linspace(0,40, 4)
#data_dict = {}
#for pp in [(1,2), (3,4), (5,6)]:
#    data = {}
#    for i in currents:
#        ic_values = np.random.randn(3) + x*10
#        data[i] = ic_values
#        x = x+1
#    data_dict[pp] = data
#    
##%%
#new_data = []
#for port_pair, data in data_dict.items():
#    for parameter, values in data.items():
#        new_data.append([port_pair, parameter, values])
#new_data = np.array(new_data)
#
##%%
#data_by_parameter = []
#for port_pair, data in data_dict.items():
#    for parameter, values in data.items():
#        new_data.append([port_pair, parameter, values])
#new_data = np.array(new_data)