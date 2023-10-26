# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 16:21:59 2017

@author: anm16
"""

#%%


######################### UNUSED ######################
######################### UNUSED ######################
######################### UNUSED ######################
######################### UNUSED ######################
######################### UNUSED ######################
#%%
from instruments.perkin_elmer_7280 import PerkinElmer7280
p = PerkinElmer7280('GPIB0::15::INSTR')

def resistance_from_lockin(R_osc = 10e3):
    v_lockin = p.get_R()
    v_osc = p.get_amplitude()
    if v_lockin == 0:
        resistance = 0
    elif v_lockin >= v_osc:
        resistance = np.inf
    else:
        resistance = R_osc/(v_osc/v_lockin-1)
    return resistance

def resistance_from_lockin_currentmode(R_osc = 100e3, R_lockin = 100e3):
    i_lockin = p.get_R()
    v_osc = p.get_amplitude()
    v_dut = i_lockin*R_lockin
    i_osc = (v_osc-v_dut)/R_osc
    resistance = v_dut/(i_osc-i_lockin)
    return resistance



#%% Test lockin result vs frequency
r = []
f = np.logspace(2,5,40)
for n in f:
    p.set_freq(n)
    time.sleep(2)
    r.append(resistance_from_lockin_currentmode(R_osc = 100e3, R_lockin = 1000e3))
plt.figure()
plt.semilogx(f,r)

#%% Using lock-in

sample_name = 'SE029 Device A6'
test_name = 'Megaohm heater R03'
test_type = 'Resistance vs heating'
port_pairs = [(3,4), (5,6), (7,8)]

### Experimental variables: about 4 tests/min for 1000 sweeps
#currents = np.logspace(np.log10(10e-6),np.log10(8000e-6),101)
powers = np.logspace(-6, -3, 201)
currents = np.sqrt(powers/30)
currents = np.hstack([-currents[::-1], 0, currents])
#currents = np.linspace(-200e-6,200e-6,11)
R_heater = 1e3

for m, pp in enumerate(port_pairs):
    
    
    switch.select_port(port = pp[0], switch = 1)
    switch.select_port(port = pp[1], switch = 2)
    time.sleep(0.5)
    print('### Measuring on PORT %s, varying PORT %s ###' % (pp[0], pp[1]))
              
    ### Run experiment!
    vs.set_output(True)
    time.sleep(0.3)
    I_heater_list = []
    V_heater_list = []
    P_heater_list = []
    R_meander_list = []
    V_meander_list = []
    start_time = time.time()
    for n, i in enumerate(currents):
        print('   ---   Time elapsed for measurement %s of %s: %0.2f min    ---   ' % (n, len(currents), (time.time()-start_time)/60.0))
        vs.set_voltage(i*R_heater)
        time.sleep(2)
        v_heater = dmm.read_voltage(channel = 1)
        i_heater = (i*R_heater - v_heater)/R_heater
        p_heater = v_heater*i_heater
        
    #    v_lockin = p.get_R()
    #    if v_lockin == 0:
    #        resistance = 0
    #    else:
    #        resistance = R_lockin/(v_osc/v_lockin-1)
        resistance = resistance_from_lockin_currentmode(R_osc = 100e3, R_lockin = 1e6)
        
        I_heater_list.append(i_heater)
        V_heater_list.append(v_heater)
        P_heater_list.append(p_heater)
        R_meander_list.append(resistance)
#        V_meander_list.append(dmm.read_voltage(channel = 2))
        
    vs.set_output(False)
    
    file_path, file_name = save_xy_vs_param(P_heater_list, R_meander_list, [0], xname = 'P', yname = 'R',  pname = 'powers',
                            test_type = test_type, test_name = '%s %s, ports %s+%s' % (sample_name, test_name, pp[0], pp[1]),
                            legend = False, fig_size_inches = [8,5],
                            xlabel = 'Power (uW)', ylabel = 'Resistance (kOhm)', plabel = 'Power (uW)',
                            xscale = 1e6, yscale = 1e-3, pscale = 1e6,
                            plotstyle = '.', plot_function = plt.semilogx,
                            display_plot = True, extra_data_dict = {'I_heater_list': I_heater_list},
                            comments = '', filedir = '', zip_file=False)
    
#    plt.figure()
#    plt.plot(np.array(I_heater_list)*1e6, np.array(V_meander_list)*1e3, '.')
#    plt.xlabel('Heater current (uA)')
#    plt.ylabel('Meander voltage (mV)')
#    plt.savefig('%s 1' % file_name)
#    
    plt.figure()
    plt.plot(np.array(I_heater_list)*1e6, np.array(P_heater_list)*1e6, '.')
    plt.xlabel('Heater current (uA)')
    plt.ylabel('Heater power (uW)')
    plt.savefig('%s power' % file_name)