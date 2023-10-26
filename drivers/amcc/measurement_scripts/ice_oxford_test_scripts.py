# Current try:
    # Precool dynamic to 20K (needle valve open)
    # Until probe is cold:
        # Set dynamic heater to Medium/40%
        # Set dynamic needle to 15mbar
    # Close dynamic needle valve, pump out till <0.5mbar
    # Start static routine
        # start @ 15mbar (25 mbar?)
# Next try
    # After dynamic needle valve reaches 20K, don't close SV4 just open VTI needle valve @ 15mbar
    # Once VTI gets cold, do dynamic+heater again to get probe < 20K
    # Pump out to 0.5mbar and close SV4
    # Open VTI completely for 1 minute, close, then set to 10 mbar
    # Add 10 heliums
    # When VTI gets <4K
        # open wide for 30s
        # then close
        # then set to 5mbar?
# Notes
    # With VTI @ 15 mbar / 100K, VTI cools at 10deg/6mins = 1.66 deg/min
    # With dynamic @ 25 mbar / 125K, probe(?) cools at 50deg/4mins = 12.5 deg/min
                                        # and uses 170mbar helium in that 4 mins = 42mbar/min
    # With dynamic @ 25 mbar / 125K, probe(?) cools at 50deg/5.3mins = 12.5 deg/min
                                        # and uses 170mbar helium in that 4 mins = 42mbar/min
import pyvisa as visa
import time
import ctypes  # For showing message box
import logging
import sys
from amcc.instruments.ice_oxford_dryice import IceOxfordDryIce
import numpy as np

ice = IceOxfordDryIce()
ice.identify()

#%%
time.sleep(3600*1.5)
self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)


#%%
# ice.close()



self = ice

probe_sensor = 'D3'
temp_vti = temp_dynamic = temp_probe = 1e9
# dynamic_open = True
target_dynamic_precool = 40
# target_vti_precool = 50
# target_dynamic2 = 3
target_probe = 20


# Check that probe sensor is working
if not 0 < self.get_temperature(probe_sensor) <= 350:
    raise ValueError('ERROR: Probe sensor disconnected/out of range, dual-cool cancelled')


ice.initialize_system_parameters()

# def wait_for_criteria(less_than = True, temp_vti = None, temp_dynamic = None, temp_probe = None):
#     """ If temp_vti = 50 and less_than=True, will wait until VTI is less than 50K """
#     if less_than is True:
#         compare_function = np.less
#     else:
#         compare_function = np.greater
#     while compare_function(temp_dynamic > target_dynamic_precool):
#         temp_vti = self.get_temperature('C')
#         temp_dynamic = self.get_temperature('D1')
#         temp_probe = self.get_temperature(probe_sensor)
#         self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K*')


temp_vti = self.get_temperature('C')
temp_dynamic = self.get_temperature('D1')
temp_probe = self.get_temperature(probe_sensor)

# Perform initial pump out
self._allow_gas_manipulation = True
self.logger.info('Opening needle valves and SV4')
self.set_valve_state('SV4', opened = True)
self.logger.info('Configuring heaters to prevent liquid helium from accumulating')

# Precool dynamic with NV wide open
if temp_dynamic > target_dynamic_precool:
    self.logger.info('Precooling dynamic')
    self.configure_needle_valve_manual(nv = 'dynamic', percent = 100, apply_settings = True)
    while temp_dynamic > target_dynamic_precool:
        temp_vti = self.get_temperature('C')
        temp_dynamic = self.get_temperature('D1')
        temp_probe = self.get_temperature(probe_sensor)
        self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K*')
    self.logger.info('Done precooling')
    self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
    time.sleep(5) # Allow time for needle valve to close

# Cool probe with dynamic @ 10mbar
self.logger.info('Cool probe with dynamic')
self.configure_needle_valve_auto(nv = 'dynamic', mbar = 10, apply_settings = True)
self.configure_heater_manual(heater = 'dynamic', heater_range = 'medium', percent = 30, apply_settings = True)
while temp_probe > target_probe:
    temp_vti = self.get_temperature('C')
    temp_dynamic = self.get_temperature('D1')
    temp_probe = self.get_temperature(probe_sensor)
    self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K')
self.disable_heater('dynamic')
self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)

# Cool VTI @ 25mbar
self.logger.info('Cool VTI')
self.configure_needle_valve_auto(nv = 'static', mbar = 25, apply_settings = True)
# # self.configure_heater_manual(heater = 'dynamic', heater_range = 'medium', percent = 40, apply_settings = True)
while temp_vti > 30:
    temp_vti = self.get_temperature('C')
    temp_dynamic = self.get_temperature('D1')
    temp_probe = self.get_temperature(probe_sensor)
    self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K')
self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)

# Re-cool probe with dynamic @ 10 mbar
self.logger.info('Re-cool probe with dynamic')
self.configure_needle_valve_auto(nv = 'dynamic', mbar = 10, apply_settings = True)
time.sleep(10)
self.configure_heater_manual(heater = 'dynamic', heater_range = 'medium', percent = 30, apply_settings = True)
while temp_probe > 20:
    temp_vti = self.get_temperature('C')
    temp_dynamic = self.get_temperature('D1')
    temp_probe = self.get_temperature(probe_sensor)
    self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K')
self.disable_heater('dynamic')
self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)

self.logger.info('Done cooling probe, waiting for circulation pressure to drop below 0.5 mbar')
pressure = 1e9
while pressure > 0.5:
    pressure = self.get_pressure('circulation')
    self.logger.info(f'Circulation pressure {pressure:.1f} mbar (target 0.5)')
    time.sleep(1)
        
self.logger.info('Disabling heaters and closing SV4 valve')
self.disable_heater('static')
self.disable_heater('dynamic')
self.set_valve_state('SV4', opened = False)

self._allow_gas_manipulation = False


# self.configure_needle_valve_manual(nv = 'static', percent = 100, apply_settings = True)
# self.add_exchange_gas(10, skip_warning = True)
# time.sleep(60)
# self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
# time.sleep(5)
self.configure_needle_valve_auto(nv = 'static', mbar = 10, apply_settings = True)


while (temp_vti > 1.66) or (temp_dynamic > 1.66) or (temp_probe > 1.66):
    temp_vti = self.get_temperature('C')
    temp_dynamic = self.get_temperature('D1')
    temp_probe = self.get_temperature(probe_sensor)
    self.logger.info(f'VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K')
self.configure_needle_valve_auto(nv = 'static', mbar = 5, apply_settings = True)
#%%


# # Flow cold helium through dynamic longer than necessary to cool probe
# self.configure_needle_valve_auto(nv = 'static', mbar = 10, apply_settings = True)
# # self.configure_heater_auto(heater = 'dynamic', heater_range = 'medium', temp = 4, apply_settings = True)
# for n in range(600):
#     printline(f'Waiting to cool probe (minute {n/60:.2f} of 10)')
#     time.sleep(.5)
# self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)

# self.configure_needle_valve_auto(nv = 'static ', mbar = 10, apply_settings = True)
# # self.configure_heater_auto(heater = 'dynamic', heater_range = 'medium', temp = 4, apply_settings = True)
# for n in range(600):
#     printline(f'Waiting to cool probe 2 (minute {n/60:.2f} of 10)')
#     time.sleep(.5)
# self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)

# FIXME - This may be the part that's messing up the transition from dynamic to static
# Boil any residual liquid helium ^ pump it back into the dump before closing SV4
self.boil_off_liquid_helium()
self.set_valve_state('SV4', opened = False)
self.configure_needle_valve_auto(nv = 'static', mbar = 10, apply_settings = True)

# Add exchange gas
self.add_exchange_gas(10, skip_warning = True)
# self.add_exchange_gas(9, skip_pumpout=True,skip_warning = True)
self._allow_gas_manipulation = False


#%%

target_dynamic2 = 3


self._allow_gas_manipulation = True
self.set_valve_state('SV4', opened = True)
time.sleep(0.5)
self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
self.configure_needle_valve_auto(nv = 'dynamic', mbar = 5, apply_settings = True)

temp_dynamic = 1e9
while temp_dynamic > target_dynamic2:
    temp_dynamic = self.get_temperature('D1')
    temp_probe = self.get_temperature(probe_sensor)
    printline(f'Dynamic {temp_dynamic:.1f} K / Probe {temp_probe:.1f} K')
    # If dynamic gets cold first, turn it off
    if temp_dynamic < target_dynamic2:
        print(f'\nDynamic precool temperature reached ({target_dynamic}K), closing dynamic needle')
        self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)

self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
self._allow_gas_manipulation = False

#%% Temp

self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
print(datetime.datetime.now())
while self.get_pressure('circulation') > 0.5:
    printline(f'Pressure {self.get_pressure("circulation")}')
print('')
print(datetime.datetime.now())
time.sleep(60*30)
self.configure_needle_valve_auto(nv = 'static', mbar = 5, apply_settings = True)

#%% Configure system properly after restarting software
ice.initialize_system_parameters()


#%% Warm up to test cooldown process

# ice.initialize_system_parameters()
ice.configure_heat_switch_manual(engaged = False, apply_settings = True)
ice.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
ice.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
ice.configure_heater_auto(heater = 'static', heater_range = 'medium', temp = 70, apply_settings = True)
ice.configure_heater_auto(heater = 'dynamic', heater_range = 'medium', temp = 70, apply_settings = True)



#%% Get system ready for warmup / power outage

message_box('ICE Oxford warmup procedure', 'Close the dump-output valve [press OK when ready]', 0)
ice.configure_heat_switch_manual(engaged = False, apply_settings = True)
ice.configure_needle_valve_manual(nv = 'static', percent = 100, apply_settings = True)
ice.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
ice.set_heater_pid(heater = 'static', p = 10, i = 0, d = 0)
ice.set_heater_pid(heater = 'dynamic', p = 10, i = 0, d = 0)
ice.configure_heater_auto(heater = 'static', heater_range = 'high', temp = 10, apply_settings = True)
ice.configure_heater_auto(heater = 'dynamic', heater_range = 'high', temp = 10, apply_settings = True)

print(f'Initial dump pressure = {ice.get_pressure("dump")}.  Waiting 5 minutes')
time.sleep(5*60)
print(f'Dump pressure after 5 mins = {ice.get_pressure("dump")}.  Waiting another 5 minutes')
time.sleep(5*60)
print(f'Dump pressure after 10 mins = {ice.get_pressure("dump")}.')
message_box('ICE Oxford warmup procedure', 'Please check to make sure the dump pressure has plateaued [press OK when ready]', 0)
message_box('ICE Oxford warmup procedure', 'Close the return-to-dump valve [press OK when ready]', 0)
ice.disable_heater(heater = 'static')
ice.disable_heater(heater = 'dynamic')
message_box('ICE Oxford warmup procedure', 'Quit the ICE Oxford software [press OK when complete]', 0)

message_box('ICE Oxford warmup procedure', 'Turn off compressor [press OK when complete]', 0)
message_box('ICE Oxford warmup procedure', 'Turn off large pump (Kashiyama 36E) [press OK when complete]', 0)
message_box('ICE Oxford warmup procedure', 'Switch off the Mini-Cube power [press OK when complete]', 0)
message_box('ICE Oxford warmup procedure', 'Turn off the power strip on back of the electronics box [press OK when complete]', 0)
message_box('ICE Oxford warmup procedure', 'Shut off the helium cylinder [press OK when complete]', 0)
message_box('ICE Oxford warmup procedure', 'Turn off computer [press OK when ready]', 0)

#%% Stabilize with liquid helium in VTI


self.configure_needle_valve_manual(nv = 'static', percent = 100, apply_settings = True)
time.sleep(60)
self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
time.sleep(5)
self.configure_needle_valve_auto(nv = 'static', mbar = 5, apply_settings = True)
