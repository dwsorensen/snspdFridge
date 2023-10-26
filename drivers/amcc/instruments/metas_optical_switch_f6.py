
#%%
import serial
import time
#%%
class MSF6(object):
    """Specialty optical switch assembled by METAS with 4 sercalo MEMs switches inside."""

    def __init__(self, serial_port):
            self.Serial = serial.Serial(serial_port, timeout = 1)

    def read(self):
        b = self.Serial.readline()
        return b.decode()

    def write(self, string):
        self.Serial.write(str.encode(string+'\r'))

    def query(self, string):
        self.write(string)
        time.sleep(0.1)
        return self.read()

    def close(self):
        self.Serial.close()
        
    def reset(self):
        self.write('R!')

    def identify(self):
        return self.query('I?')

    def list_commands(self):
        return self.query('H') #output weird, need to figure out how to escape carriage returns in print

    def set_remote(self):
        self.write('C!R')

    def set_local(self):
        self.write('C!L')

    def switch(self, module_number, switch_position):
        self.write('S!'+str(module_number)+str(switch_position))

    def query_switch_position(self, module_number):
        return_string = self.query('S?'+str(module_number))
        return int(return_string[3])


# %%
