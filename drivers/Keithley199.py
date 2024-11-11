from __future__ import print_function

# from builtins import str
# from builtins import object
# import serial
import Gpib
import string

# import Gpib_prologix_nt_ver2 as Gpib


class dev(object):
    def __init__(self, addr, serialport=""):
        """Connect to and reset a Keithley199"""
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        self.meter.write("F0X\r\n")
        self.meter.write("R1X\r\n")

    def get_dvm_volt(self):
        msg = "G1X\r\n"
        self.meter.write(msg)
        msgout = self.meter.read(100)

        # print repr(msgout)
        if len(msgout) == 0:
            print("Got empty string")
            msgout = "NaN"
        # return float(msgout)
        x = float(msgout.decode().strip("\r\n"))

        return x
        # return map(float,msgout.split('\n')[1:2])[0]

    def get_volt(self):
        return self.get_dvm_volt()

    def identify(self):
        identity = "Keithley199 dmm; addr: " + str(self.addr)
        return identity

    def writeconfig(self, f):
        msg = self.identify().strip()
        f.write("# " + msg + "\n")
        f.flush()

    def close(self):
        self.meter.write("F0X\r\n")


if __name__ == "__main__":
    import serial

    # 	serialport = serial.Serial('/dev/ttyUSB0', 9600, timeout = 0.5)
    #        source = device(9,serialport)
    # 	source.meter.write('++addr')
    # 	print source.port.read()
    # dmm = device('dev8')
    serialport = serial.Serial("/dev/tty.usbserial-PXHBW0TN", 9600, timeout=0.5)
    dmm = dev(8, serialport)
    x = dmm.get_volt()
    print(x)
    # fileName = '/Users/lab/Downloads/xxx'
    # f = open(fileName, 'w')
    # dmm.writeconfig(f)
