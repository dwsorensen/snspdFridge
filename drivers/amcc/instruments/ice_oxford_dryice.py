import pyvisa as visa
import time
import ctypes  # For showing message box
import logging
import sys


def printline(text):
    """ Prints a single line and erases itself to prevent spamming the console"""
    print("\r", text, end="")
    # print("\033[A\033[A")
    # print(text)
    

def message_box(title, text, style):
    """ Returns True if "OK" is clicked or False if "Cancel" is clicked
    
        Styles are
        0 = "OK" -> OK returns 1
        1 = "OK / Cancel" -> OK returns 1 / Cancel returns 2
        2 = "Abort / Retry / Ignore" -> returns 4/5/6
        """
    # The 0x1000 (or 0x40000) makes the window appear on top
    response = ctypes.windll.user32.MessageBoxW(0, text,  title,  0x1000+style)
    if response == 1:
        return True
    elif response == 2:
        return False
    else:
        return response

class IceOxfordDryIce(object):
    """Python class for the ICE Oxford Dry ICE 1.5K system,
    written by Adam McCaughan"""
    def __init__(self, ip = '127.0.0.1', port = 6340):
        self.ip = ip
        self.port = port
        if 'ice-oxford' not in logging.Logger.manager.loggerDict:
            # Create the logger
            logger = logging.getLogger('ice-oxford')
            logger.setLevel(logging.DEBUG)
            # Create 3 "handlers" two which output to a log file, the other to stdout
            handler1 = logging.StreamHandler(sys.stdout)
            handler2 = logging.FileHandler(r'C:\Users\qittlab\Documents\ice-oxford-python-control.log', mode='a')
            handler3 = logging.FileHandler(r'C:\Users\qittlab\Documents\ice-oxford-python-control-DEBUG.log', mode='a')
            handler1.setLevel(logging.INFO)
            handler2.setLevel(logging.INFO)
            handler3.setLevel(logging.DEBUG)
            # Set the format of the log messages
            log_date_format = '%Y-%m-%d %H:%M:%S'
            handler1.setFormatter(logging.Formatter(fmt = '%(asctime)s (%(user-initials)s) %(message)s', datefmt=log_date_format))
            handler2.setFormatter(logging.Formatter(fmt = '%(asctime)s.%(msecs)03d,\t%(user-initials)s,\t%(levelname)s,\t%(message)s', datefmt=log_date_format))
            handler3.setFormatter(logging.Formatter(fmt = '%(asctime)s.%(msecs)03d,\t%(user-initials)s,\t%(levelname)s,\t%(message)s', datefmt=log_date_format))
            # Create the logger
            logger.addHandler(handler1)
            logger.addHandler(handler2)
            logger.addHandler(handler3)
            # Add extra "user" default information
            
        else:
            logger = logging.getLogger('ice-oxford')
            
        logger = logging.LoggerAdapter(logger, extra = {'user-initials':'n/a'})
        self.logger = logger
        self.logger.debug('Starting new logger')
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands
        self.ice_connect()

    def read(self):
        response = self.pyvisa.read()
        self.logger.debug(f'pyvisa read: {response}')
        if self._stop_execution is True: raise Exception('Stop-execution was requested')
        return response
    
    def write(self, string):
        self.logger.debug(f'pyvisa write: {string}')
        if self._stop_execution is True: raise Exception('Stop-execution was requested')
        self.pyvisa.write(string)

    def query(self, string, expected_response = None):
        self.logger.debug(f'pyvisa query write: {string}')
        if self._stop_execution is True: raise Exception('Stop-execution was requested')
        response = self.pyvisa.query(string)
        self.logger.debug(f'pyvisa query read:  {response} (expected {expected_response})')
        if expected_response is not None:
            self._check_response(response, expected = expected_response)
        return response

    def close(self):
        self.pyvisa.close()
    
    def ice_connect(self):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(f'TCPIP0::{self.ip}::{self.port}::SOCKET')
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        self.pyvisa.read_termination = '\r\n'
        self.pyvisa.write_termination = '\r\n'
        self._allow_gas_manipulation = False
        self._stop_execution = False
        response = self.query('CONNECT LEMON')
        self._check_response(response, expected = 'CONNECTED')
    
    def ice_disconnect(self):
        response = self.query('DISCONNECT LEMON')
        self._check_response(response, expected = 'OK')
        self.close()

    def identify(self):
        return self.query('*IDN?')
    
    def _check_response(self, response, expected = "OK"):
        if response != expected:
            raise ValueError("WARNING: Instrument did not return correct response." +
                             f"  Expected '{expected}' / received '{response}' ")
    
    def _parse_nv(self, nv):
        if nv not in {'static','dynamic',1,2}:
            raise ValueError("needle valve variable must be one of {'static','dynamic',1,2}")
        if nv in {'static', 1}:
            return 1
        elif nv in {'dynamic', 2}:
            return 2
        
    def _parse_nv_mode(self, mode):
        if mode.lower() not in {'manual','auto'}:
            raise ValueError("mode must be one of {'manual','auto'}")
        return mode.upper()
    
    def _parse_channel(self, channel):
        if channel.upper() not in {'A','B','C','D1','D2','D3','D4','D5'}:
            raise ValueError("channel must be one of {'A','B','C','D1','D2','D3','D4','D5'}")
        return channel.upper()
    
    def _parse_heater(self, heater):
        if heater not in {'static','dynamic',1,2}:
            raise ValueError("Heater variable must be one of {'static','dynamic',1,2}")
        if heater in {'static', 1}:
            return 1
        elif heater in {'dynamic', 2}:
            return 2
        
    def _parse_pressure_sensor(self, sensor):
        if sensor.lower() not in {'dump','circulation','sample space'}:
            raise ValueError("sensor must be one of {'dump','circulation','sample space'}")
        return sensor.upper()
    
    def _parse_valve(self, valve):
        if valve.upper() not in {'SV1','SV2','SV3', 'SV4'}:
            raise ValueError("valve must be one of {'SV1','SV2','SV3', 'SV4'}")
        return valve.upper()
    
    def _verify_not_in_dynamic_mode(self):
        if self.get_valve_state('SV4') is True:
            raise ValueError("ERROR: Cannot perform operation while in dynamic mode (SV4 open)")
            
    def set_needle_valve_mode(self, nv, mode):
        nv = self._parse_nv(nv)
        mode = self._parse_nv_mode(mode)
        if (nv == 2) and mode == 'AUTO' and (self.get_valve_state('SV4') == False):
            raise ValueError("ERROR: Not allowed to open dynamic needle valve when SV4 is closed")
        self.query(f'NV{nv} MODE={mode}', 'OK')
        
    def set_needle_valve_pressure(self, nv, mbar):
        nv = self._parse_nv(nv)
        self.query(f'NV{nv} SETPOINT={mbar}', 'OK')
        
    def set_needle_valve_output_percent(self, nv, percent):
        nv = self._parse_nv(nv)
        if (nv == 2) and (percent != 0) and (self.get_valve_state('SV4') == False):
            raise ValueError("ERROR: Not allowed to open dynamic needle valve when SV4 is closed")
        self.query(f'NV{nv} MAN OUT={percent}', 'OK')
        
    def apply_needle_valve_settings(self, nv):
        nv = self._parse_nv(nv)
        time.sleep(1)
        self.query(f'NV{nv} SET VALUES', 'OK')
        # time.sleep(0.1)
    
    def set_needle_valve_pid(self, nv = 'static', p = None, i = None, d = None):
        nv = self._parse_nv(nv)
        response = self.query(f'NV{nv} PID={p},{i},{d}')
        self._check_response(response, expected = 'OK')
    
    def set_heater_mode(self, heater, mode):
        heater = self._parse_heater(heater)
        mode = self._parse_nv_mode(mode)
        self.query(f'HEATER{heater} MODE={mode}', 'OK')
        
    def set_heater_range(self, heater, heater_range = 'off'):
        heater = self._parse_heater(heater)
        if heater_range.lower() not in {'off','low','medium','high'}:
            raise ValueError("heater_range variable must be one of {'off','low','medium','high'}")
        self.query(f'HEATER{heater} RANGE={heater_range.upper()}', 'OK')
        
    def set_heater_channel(self, heater, channel):
        heater = self._parse_heater(heater)
        channel = self._parse_channel(channel)
        self.query(f'HEATER{heater} CHAN={channel.upper()}', 'OK')
        
    def set_heater_setpoint_temp(self, heater, temp):
        heater = self._parse_heater(heater)
        if temp > 300:
            raise ValueError("Heater setpoint temp not allowed beyond 300K")
        self.query(f'HEATER{heater} SETPOINT={temp}', 'OK')
        
    def set_heater_pid(self, heater, p = 75, i = 0, d = 0):
        heater = self._parse_heater(heater)
        self.query(f'HEATER{heater} PID={p},{i},{d}', 'OK')
        
    def set_heater_output_percent(self, heater, percent):
        heater = self._parse_heater(heater)
        self.query(f'HEATER{heater} MAN OUT={percent}', 'OK')
        
    def apply_heater_settings(self, heater):
        heater = self._parse_heater(heater)
        time.sleep(1)
        self.query(f'HEATER{heater} SET VALUES', 'OK')
        # time.sleep(0.1)
    
    def configure_heater_manual(self, heater, heater_range, percent, apply_settings = True):
        self.set_heater_mode(heater = heater, mode = 'manual')
        self.set_heater_range(heater = heater, heater_range = heater_range)
        self.set_heater_output_percent(heater = heater, percent = percent)
        if apply_settings is True:
            self.apply_heater_settings(heater = heater)
    
    def configure_heater_auto(self, heater, heater_range, temp, apply_settings = True):
        self.set_heater_mode(heater = heater, mode = 'auto')
        # self.set_heater_pid(heater, p = p, i = i, d = d)
        self.set_heater_range(heater = heater, heater_range = heater_range)
        self.set_heater_setpoint_temp(heater = heater, temp = temp)
        if apply_settings is True:
            self.apply_heater_settings(heater = heater)
    
    def configure_needle_valve_manual(self, nv, percent, apply_settings = True):
        self.set_needle_valve_mode(nv = nv, mode = 'manual')
        self.set_needle_valve_output_percent(nv = nv, percent = percent)
        if apply_settings is True:
            self.apply_needle_valve_settings(nv)
            
    def configure_needle_valve_auto(self, nv, mbar, apply_settings = True):
        self.set_needle_valve_mode(nv = nv, mode = 'auto')
        self.set_needle_valve_pressure(nv = nv, mbar = mbar)
        if apply_settings is True:
            self.apply_needle_valve_settings(nv)
    
    def disable_heater(self, heater):
        self.set_heater_mode(heater = heater, mode = 'manual')
        self.set_heater_range(heater = heater, heater_range = 'off')
        self.set_heater_output_percent(heater = heater, percent = 0)
        self.apply_heater_settings(heater = heater)
    
    def set_dual_cool_temp_channel(self, channel):
        channel = self._parse_channel(channel)
        self.query(f'DC TEMP CHAN={channel.upper()}', 'OK')
    
    def get_temperature(self, channel, raw = False, retry = 1):
        channel = self._parse_channel(channel)
        if raw is False:
            response = self.query(f'TEMPERATURE {channel}?') # Response like 'TEMPERATURE D1=70.897100'
            temperature = float(response.split('=')[-1])
            if temperature == 0 and retry > 0:
                return self.get_temperature(channel = channel, raw = raw, retry = retry-1)
            else:
                return temperature
        else:
            response = self.query(f'RAW {channel}?') # Response like 'TEMPERATURE D1=70.897100'
            raw = float(response.split('=')[-1])
            return raw
    
    def get_pressure(self, sensor = 'dump'):
        sensor = self._parse_pressure_sensor(sensor)
        response = self.query(f'{sensor} PRESSURE?') # Response like 'TEMPERATURE D1=70.897100'
        pressure_mbar = float(response.split('=')[-1])
        return pressure_mbar
        
    def get_valve_state(self, valve = 'SV1'):
        valve = self._parse_valve(valve)
        response = self.query(f'GB {valve}?')
        state = response.split('=')[-1]
        if state == 'OPEN':
            return True
        elif state == 'CLOSED':
            return False
        else:
            raise ValueError('ERROR: Valve state query returned {response}')


    def set_valve_state(self, valve = 'SV1', opened = False):
        valve = self._parse_valve(valve)
        if self._allow_gas_manipulation is not True:
            raise ValueError('ERROR: Valve state setting is currently disabled')
        if opened is True:
            self.query(f'GB {valve}=OPEN', 'OK')
        elif opened is False:
            self.query(f'GB {valve}=CLOSED', 'OK')
        else:
            raise ValueError('ERROR: set_valve_state() requires `opened` to be True or False')
            
    
    def disable_valves(self):
        for valve in ['SV1','SV2','SV3','SV4']:
            self.set_valve_state(valve, opened = False)
    
    def set_pump_state(self, on = False):
        if self._allow_gas_manipulation is not True:
            raise ValueError('ERROR: Pump state setting is currently disabled')
        if on is True:
            self.query('GB PUMP=ON', 'OK')
        elif on is False:
            self.query('GB PUMP=OFF', 'OK')
        else:
            raise ValueError('ERROR: set_pump_state() requires `on` to be True or False')
    
    
    def apply_heat_switch_settings(self):
        self.query('HEAT SW1 SET VALUES', 'OK')
        
    def set_heat_switch_mode(self, mode = 'manual'):
        mode = self._parse_nv_mode(mode)
        self.query(f'HEAT SW1 MODE={mode}', 'OK')
        
    def set_heat_engaged(self, engaged = False):
        if engaged is True:
            self.query('HEAT SW1 RELAY=ON', 'OK')
        elif engaged is False:
            self.query('HEAT SW1 RELAY=OFF', 'OK')
        else:
            return ValueError('Heat switch engaged argument must be True or False')
    
    def configure_heat_switch_manual(self, engaged = False, apply_settings = True):
        self.set_heat_switch_mode( mode = 'manual')
        self.set_heat_engaged(engaged = engaged)
        if apply_settings is True:
            self.apply_heat_switch_settings()
    
    def boil_off_liquid_helium(self, heater_target_temp = 4):
        if self.get_temperature('C') > 4 and self.get_temperature('D1') > 4 and self.get_pressure('circulation') < 0.5:
            self.logger.info('Temps >5K and circulation pressure < 0.5 mbar, no boiling necessary')
            return
        self.logger.info('Closing needle valves')
        self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
        self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
        self.logger.info('Enabling heaters to boil off residual liquid helium')
        self.configure_heater_auto(heater = 'static', heater_range = 'medium', temp = heater_target_temp, apply_settings = True)
        self.configure_heater_auto(heater = 'dynamic', heater_range = 'medium', temp = heater_target_temp, apply_settings = True)
        time.sleep(5)
        pressure = temp_vti = temp_dynamic = 1e9
        self.logger.info('Waiting until circulation pressure < 0.5 mbar & temps > 5K (ensure liquid boiled off)')
        while pressure > 0.5 or temp_vti < 5 or temp_dynamic < 5:
            pressure = self.get_pressure('circulation')
            temp_vti = self.get_temperature('C')
            temp_dynamic = self.get_temperature('D1')
            self.logger.info(f' - Circulation pressure {pressure:.2f} mbar / VTI {temp_vti:.1f} K / Dynamic {temp_dynamic:.1f} K*')
            time.sleep(0.5)
        self.logger.info('Disabling heaters')
        self.disable_heater(heater = 'static')
        self.disable_heater(heater = 'dynamic')
        time.sleep(10)
        self.logger.info('Performing final temperature check (>4K on dynamic & VTI)')
        if self.get_temperature('C') < 4 or self.get_temperature('D1') < 4:
            raise ValueError('ERROR: The VTI or dynamic is still below 4K, boiling process failed')
    
    def precool_vti(self):
        """ Flows helium through the VTI to precool it to 20K """
        self.initialize_system_parameters()
        self.logger.info('Checking VTI temperature < 20K')
        if self.get_temperature('C') < 20:
            self.logger.info('VTI temperature <20K, no need to cool down')
            return
        self.disable_heater(heater = 'static')
        self.disable_heater(heater = 'dynamic')
        self.logger.info('VTI >20K, opening static needle valve to cool down')
        self.configure_needle_valve_manual(nv = 'static', percent = 80, apply_settings = True)
        temp = self.get_temperature('C')
        while temp > 20:
            time.sleep(.5)
            temp = self.get_temperature('C')
            self.logger.info(f'VTI temperature {temp:.1f} K (target 20K)*')
        self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
    
    
    def purge_gas_box_and_sample_line(self):
        self._verify_not_in_dynamic_mode()
        if message_box(title = 'Purge gas box and sample line',
                       text = 'CLOSE Sample-space manual valve', 
                       style = 1) is False:
            raise ValueError('Purge gas box & sample line process aborted')
        else:
            self._allow_gas_manipulation = True
            self.set_pump_state(on = True)
            self.disable_valves()
            time.sleep(20)
            self.set_valve_state('SV3', opened = True)
            time.sleep(5)
            self.set_valve_state('SV1', opened = True)
            time.sleep(0.5)
            self.set_valve_state('SV1', opened = False)
            time.sleep(2)
            self.set_valve_state('SV2', opened = True)
            time.sleep(5)
            self.set_valve_state('SV2', opened = False)
            self.set_valve_state('SV3', opened = False)
            time.sleep(1)
            self.set_pump_state(on = False)
            self.disable_valves()
            self._allow_gas_manipulation = False
    
    def pump_sample_space(self, skip_warning = False):
        self._verify_not_in_dynamic_mode()
            
        if skip_warning is False and message_box(title = 'Pump sample space',
                       text = 'OPEN Sample-space manual valve', 
                       style = 1) is False:
            raise ValueError('Pump sample space process aborted')
        if self.get_pressure('sample space') < 10:
            self.logger.info('Pressure already below 10 mbar, no need to pump sample space')
            return None
        self._allow_gas_manipulation = True
        self.set_pump_state(on = True)
        self.disable_valves()
        time.sleep(20)
        self.set_valve_state('SV3', opened = True)
        time.sleep(5)
        self.set_valve_state('SV2', opened = True)
        # Wait until pressure < 10 mbar
        pressure = self.get_pressure('sample space')
        while pressure > 10:
            pressure = self.get_pressure('sample space')
            self.logger.info(f'Sample space pressure {pressure:.1f} mbar (target 10)*')
            time.sleep(1)
        self.set_valve_state('SV2', opened = False)
        self.set_valve_state('SV3', opened = False)
        self.set_pump_state(on = False)
        self._allow_gas_manipulation = False
    
    def pump_and_flush(self, skip_warning = False):
        """ Pumps out the sample space, then flushes it with helium.  Repeats
        this process 2x times, and then peforms a final pumpout """
        # Initial checks and warnings
        self._verify_not_in_dynamic_mode()
        if skip_warning is False and message_box(title = 'Pump and flush',
                       text = 'OPEN Sample-space manual valve', 
                       style = 1) is False:
            raise ValueError('Pump and flush process aborted')
        flush_pressure_mbar = 200
        
        # Perform initial pump out
        self.logger.info('Pumping out sample space')
        self._allow_gas_manipulation = True
        self.set_pump_state(on = True)
        time.sleep(20)
        self.set_valve_state('SV3', opened = True)
        time.sleep(2)
        self.set_valve_state('SV2', opened = True)
        pressure = self.get_pressure('sample space')
        while pressure > 10:
            pressure = self.get_pressure('sample space')
            self.logger.info(f'Sample space pressure {pressure:.1f} mbar (target 10)*')
            time.sleep(1)
        self.set_valve_state('SV3', opened = False)
        
        # Iterate flushing with helium then pumping out again
        for n in range(2):
            self.logger.info(f'Flushing/purging with helium ({n+1} of 2 times)')
            self.set_valve_state('SV1', opened = True)
            pressure = self.get_pressure('sample space')
            while pressure < flush_pressure_mbar:
                pressure = self.get_pressure('sample space')
                self.logger.info(f'Sample space pressure {pressure:.1f} mbar (target {flush_pressure_mbar})*')
                time.sleep(1)
            self.set_valve_state('SV1', opened = False)
            time.sleep(1)
            self.set_valve_state('SV3', opened = True)
            while pressure > 10:
                pressure = self.get_pressure('sample space')
                self.logger.info(f'Sample space pressure {pressure:.1f} mbar (target 10)*')
                time.sleep(1)
            self.set_valve_state('SV3', opened = False)
            time.sleep(1)
        self.set_valve_state('SV2', opened = False)
        self.set_pump_state(on = False)
        self._allow_gas_manipulation = False
    
    def change_sample(self):
        # Ready system for sample change
        atmospheric_pressure_mbar = 800
        if message_box(title = 'Change sample',
                       text = 'OPEN Sample-space manual valve', 
                       style = 1) is False:
            raise ValueError('Change sample process aborted')
        self.initialize_system_parameters()
        self._verify_not_in_dynamic_mode()
        self.logger.info("Disengaging heat switch")
        self.configure_heat_switch_manual(engaged = False, apply_settings = True)
        # self.logger.info("Purging gas box and sample line")
        # self.purge_gas_box_and_sample_line()
        self.boil_off_liquid_helium(heater_target_temp = 20)
        self._allow_gas_manipulation = True
        
        # Open valves to add helium and wait until pressure > 850 mbar
        self.set_valve_state('SV1', opened = True)
        self.set_valve_state('SV2', opened = True)
        pressure = self.get_pressure('sample space')
        while pressure < atmospheric_pressure_mbar:
            pressure = self.get_pressure('sample space')
            self.logger.info(f'Sample space pressure {pressure:.1f} mbar (target {atmospheric_pressure_mbar})*')
            time.sleep(1)
        
        # Perform sample change
        message_box(title = 'Pump sample space',
                    text = 'After swapping probe press OK', 
                    style = 0)
        self.set_valve_state('SV1', opened = False)
        self.set_valve_state('SV2', opened = False)
        self.pump_and_flush(skip_warning = True)
        
    def hibernate(self, skip_warning = False):
        self._verify_not_in_dynamic_mode()
        if skip_warning is not False:
            message_box('Hibernation','CLOSE Sample-space manual valve', 0)
        self.configure_heat_switch_manual(engaged = False, apply_settings = False)
        self.initialize_system_parameters()
        self.configure_needle_valve_manual(nv = 'static', percent = 0, apply_settings = True)
        self.configure_needle_valve_manual(nv = 'dynamic', percent = 0, apply_settings = True)
        if self.get_temperature('C') > 20:
            self.logger.info("Warning: VTI above 20K, cooling down before continuing")
            self.precool_vti()
        elif self.get_temperature('C') < 4 or self.get_temperature('D1') < 4:
            self.logger.info("Warning: Both VTI and dynamic temperatures must be above " +
                  "4K to engage heat switch.  There may be liquified helium, " +
                  "need to boil it off ")
            self.boil_off_liquid_helium(heater_target_temp = 20)
        self.configure_heat_switch_manual(engaged = True, apply_settings = True)
    
    def add_exchange_gas(self, num_standard_volumes, skip_pumpout = False, skip_warning = False):
        # Checks and warnings
        self._verify_not_in_dynamic_mode()
        if skip_warning is False and message_box(title = 'Add exchange gas',
                       text = 'OPEN Sample-space manual valve', 
                       style = 1) is False:
            raise ValueError('Add exchange gas process aborted')

        self.logger.info('Adding exchange gas')
        # Perform initial pump out
        self._allow_gas_manipulation = True
        if skip_pumpout is not True:
            self.set_pump_state(on = True)
            time.sleep(20)
            self.set_valve_state('SV3', opened = True)
            time.sleep(5)
            self.set_valve_state('SV3', opened = False)
            time.sleep(2)

        # Add "standard volumes" of gas
        for n in range(num_standard_volumes):
            self.logger.info(f'Adding exchange gas #{n+1} of {num_standard_volumes}')
            self.set_valve_state('SV1', opened = True)
            time.sleep(3)
            self.set_valve_state('SV1', opened = False)
            time.sleep(1)
            self.set_valve_state('SV2', opened = True)
            time.sleep(3)
            self.set_valve_state('SV2', opened = False)
            time.sleep(1)

        # Turn stuff off
        self.set_pump_state(on = False)
        self._allow_gas_manipulation = False
            
    def initialize_system_parameters(self):
        self.logger.info('Disabling and setting heater params...')
        self.disable_heater(heater = 'static')
        self.disable_heater(heater = 'dynamic')
        self.set_heater_pid(heater = 'static', p = 75, i = 0, d = 0)
        self.set_heater_pid(heater = 'dynamic', p = 75, i = 0, d = 0)
        self.set_heater_channel(heater = 'static', channel = 'C')
        self.set_heater_channel(heater = 'dynamic', channel = 'D1')
        self.set_heater_setpoint_temp(heater = 'static', temp = 6)
        self.set_heater_setpoint_temp(heater = 'dynamic', temp = 6)
        self.logger.info('Configuring sensors...')
        self.set_dual_cool_temp_channel(channel = 'D3')
        self.query('HEAT SW1 INPUT=C', 'OK')
        self.query('HEAT SW1 MODE=MANUAL', 'OK')
        self.query('HEAT SW1 SET VALUES', 'OK')

