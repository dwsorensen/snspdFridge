import pyvisa as visa

class dev(object):
    """Python class for SaeWoo's low-noise 4-port voltage source
    written by Dileep V. Reddy ported by Daniel W Sorensen"""
    def __init__(self, visa_name):
        self.rm = visa.ResourceManager()
        self.visa_name = visa_name
        self.pyvisa = self.rm.open_resource(visa_name)
        self.pyvisa.timeout = 5000 # Set response timeout (in milliseconds)
        self.maxvolt = 2.5
        self.minvolt = -2.5
        self.val = 0.0
        # self.pyvisa.query_delay = 1 # Set extra delay time between write and read commands

    def writeconfig(self, f):
        pass

    def get_volt(self):
        return self.val

    def read(self):
        return self.pyvisa.read()
        
    def resetConnection(self):
        self.pyvisa = self.rm.open_resource(self.visa_name)
        self.pyvisa.timeout = 5000

    def write(self, string):
        self.pyvisa.write(string)

    def query(self, string):
        try:
          return self.pyvisa.query(string)
        except visa.VisaIOError:
          self.resetConnection()
          return self.pyvisa.query(string)

    def close(self):
        self.pyvisa.close()

    def clamp(self, num):
        return max(min(num, self.maxvolt), self.minvolt)

    def set_volt(self, *args):
        if len(args) == 2:
            channel = args[0]
            volts = args[1]
        else:
            volts = args[0]
            channel = 1

        self.val = volts
        if channel > 3:
            channel = 3
        print("Output: " + str(self.query('%s %s' % (channel, self.clamp(volts)))))

    def disable(self):
        for chan in range(0, 4):
            self.set_volt(channel=chan, volts=0.0)
