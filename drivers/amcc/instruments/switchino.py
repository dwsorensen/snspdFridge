import pyvisa as visa
import time

class Switchino(object):
    """Python class for a single-pull 10-throw switch,
    written by Adam McCaughan"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        self.current_ports = [-1,-1]
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands

    def read(self):
        return self.pyvisa.read()
    
    def write(self, string):
        self.pyvisa.write(string)

    def query(self, string):
        return self.pyvisa.query(string)

    def close(self):
        self.pyvisa.close()

    def identify(self):
        return self.query('*IDN?')

    def select_port(self, port = 2, switch = 1):
        if port is None:
            self.disable(switch = switch)
        else:
            self.query('SWITCH %s PORT %s' % (switch, port))
        self.current_ports[switch-1] = port
        time.sleep(0.1)
        return port

    def select_ports(self, port_pair = (3,5)):
        self.select_port(port = port_pair[0], switch = 1)
        self.select_port(port = port_pair[1], switch = 2)
        return port_pair
    
    def get_current_port(self, switch = 1):
        if switch == 1:
            return self.current_ports[0]
        if switch == 2:
            return self.current_ports[1]

    def disable(self, switch = None):
        if switch is None:
            self.query('SWITCH 1 OFF')
            self.query('SWITCH 2 OFF')
        if switch == 1:
            self.query('SWITCH 1 OFF')
        if switch == 2:
            self.query('SWITCH 2 OFF')
            
        
# g = GenericInstrument('GPIB0::24')
# g.identify()




