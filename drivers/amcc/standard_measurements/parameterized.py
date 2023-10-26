import numpy as np
import time
from tqdm import tqdm
import itertools
import pandas as pd
try:
    from TimeTagger import TimeTagStream, Countrate
except:
    pass


def parameter_combinations(parameters_dict):
    for k,v in parameters_dict.items():
        try: v[0]
        except: parameters_dict[k] = [v]
        if type(v) is str:
            parameters_dict[k] = [v]
        if np.size(v) == 0:
            raise ValueError(f'parameter_combinations() error: passed empty array for key "{k}"')
    value_combinations = list(itertools.product(*parameters_dict.values()))
    keys = list(parameters_dict.keys())
    return [{keys[n]:values[n] for n in range(len(keys))} for values in value_combinations]


def run_experiment(experiment_fun, parameter_dict):
    # Create combinations and manipulate them as needed
    parameter_dict_list = parameter_combinations(parameter_dict)
    
    # Run each parameter set as a separate experiment
    data_list = []
    for p_d in tqdm(parameter_dict_list):
        data = experiment_fun(**p_d)
        data_list.append(data)
    
    # Convert list of data-dictionaries to DataFrame
    if isinstance(data, pd.DataFrame):
        df = pd.concat(data_list, ignore_index=True)
    elif isinstance(data, dict):
        df = pd.DataFrame(data_list)    
    return df


def experiment_counter(
    vs,
    dmm,
    counter,
    vtrig,
    count_time,
    ibias,
    rbias,
    delay,
    att_db = np.inf,
    att = None,
    port = None,
    switch = None,
    portmap = None,
    v1_channel = 1,
    v2_channel = 2,
    **kwargs
    ):
        
    # Select port
    if (switch is None) and (port is not None):
        raise ValueError('Error: Port was selected, but switch is None/not specified')
    elif (switch is not None) and (port != switch.get_current_port()):
        vs.set_voltage(0)
        vs.set_output(True)
        switch.select_port(port)
        time.sleep(0.25)
    
    # Set bias current and counter trigger level
    vbias = ibias*rbias
    vs.set_voltage(vbias)
    counter.set_trigger(trigger_voltage = vtrig, slope_positive = (vtrig>=0), channel = 1)
    
    # Set optical attenuator value
    if att is not None:
        if att_db == np.inf:
            att.set_beam_block(True)
        else:
            att.set_beam_block(False)
            att.set_attenuation(att_db)
    time.sleep(delay)

    # Measure number of counts in `count_time`
    counts = counter.timed_count(counting_time=count_time)
    v1 = dmm.read_voltage(v1_channel)
    v2 = dmm.read_voltage(v2_channel)
    ibias_measured = (v1-v2)/rbias
    
    # Use the `portmap` dictionary to define the device name according to port number 
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    data = dict(
        port = port,
        device = device,
        vbias = vbias,
        vbias_measured = v1,
        vdut = v2,
        rbias = rbias,
        ibias = ibias,
        ibias_measured = ibias_measured,
        vtrig = vtrig,
        counts = counts,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        **kwargs
    )

    return data

#================================================================
# IV Curves, Single and Steady State
#================================================================

def experiment_iv_sweep(
        vs,
        dmm,
        delay,
        rbias,
        ibias,
        switch = None,
        port = 1,
        portmap = None,
        v1_channel = 1,
        v2_channel = 2,
        vdiff_channel = None, # Read using differential voltage instead
        **kwargs,
        ):
    # Select port
    if (switch is not None) and (port != switch.get_current_port()):
        switch.select_port(port = port, switch = 1)
        vs.set_voltage(0)
        time.sleep(1)
    
    # Use the `portmap` dictionary to define the device name according to port number 
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    # Set voltage, wait `delay`, then take measurement
    vbias = rbias*ibias
    vs.set_voltage(vbias)
    time.sleep(delay)
    if vdiff_channel is None:
        v1 = dmm.read_voltage(channel = v1_channel)
        v2 = dmm.read_voltage(channel = v2_channel)
    else:
        v1 = vbias
        v2 = vbias + dmm.read_voltage(channel = vdiff_channel)
    
    ibias = (v1-v2)/rbias
    
    data = dict(
        port = port,
        device = device,
        rbias = rbias,
        vbias = vbias,
        vbias_measured = v1,
        vdut = v2,
        ibias = ibias,
        ibias_measured = (v1-v2)/rbias,
        **kwargs,
        )
    return data



def experiment_swabian_basic_1ch_counts(
    vs,
    dmm,
    tagger,
    vtrig,
    count_time,
    ibias,
    rbias,
    delay,
    dead_time,
    att_db = np.inf,
    att = None,
    port = None,
    switch = None,
    portmap = None,
    v1_channel = 1,
    v2_channel = 2,
    **kwargs
    ):
    
    
    # Select port
    if (switch is not None) and (port != switch.get_current_port()):
        vs.set_voltage(0)
        vs.set_output(True)
        switch.select_port(port)
        time.sleep(0.25)
    
    # Set bias current and counter trigger level
    vbias = ibias*rbias
    vs.set_voltage(vbias)
    tagger.setTriggerLevel(1, vtrig)
    dead_time_ps = int(np.round(dead_time*1e12))
    tagger.setDeadtime(1, dead_time_ps)
    
    # Set optical attenuator value
    if att is not None:
        if att_db == np.inf:
            att.set_beam_block(True)
        else:
            att.set_beam_block(False)
            att.set_attenuation(att_db)
    time.sleep(delay)

    # Measure number of counts in `count_time`
    counter = Countrate(tagger, channels = [1])
    counter.startFor(count_time*1e12)
    counter.waitUntilFinished(timeout=-1)
    counts = counter.getCountsTotal()[0]
    
    v1 = dmm.read_voltage(v1_channel)
    v2 = dmm.read_voltage(v2_channel)
    ibias_measured = (v1-v2)/rbias
    
    # Use the `portmap` dictionary to define the device name according to port number 
    if (portmap is not None): device = portmap[port]
    else: device = None
    
    data = dict(
        port = port,
        device = device,
        vbias = vbias,
        vbias_measured = v1,
        vdut = v2,
        rbias = rbias,
        ibias = ibias,
        ibias_measured = ibias_measured,
        vtrig = vtrig,
        counts = counts,
        count_time = count_time,
        count_rate = counts/count_time,
        attenuation_db = att_db,
        delay = delay,
        **kwargs
    )

    return data

