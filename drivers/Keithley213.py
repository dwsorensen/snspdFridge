from __future__ import print_function

# from builtins import range
# from builtins import object
# import serial
# import Gpib_prologix_nt_ver2 as Gpib
import Gpib

params = [
    {"name": "GPIB Address", "type": "int", "limits": (1, 32), "value": 9},
    {"name": "Channel", "type": "int", "values": {1, 2, 3, 4}, "value": 1},
]


class dev(object):
    def __init__(self, addr, serialport="", ch=4):
        self.ch = ch  # set default channel
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        self.currentV = None
        if type(addr) == list:
            self.p = addr  # should I make a deepcopy here?  Not sure, will not for now
            for item in self.p:
                if "value" in item:
                    name = item["name"]
                    value = item["value"]
                    if "ddress" in name:
                        gpibaddress = value
                    if "Channel" in name:
                        self.ch = value
                        print("setting channel from parameters: %d" % self.ch)
        elif type(addr) == str:  # Arguments are shifted by 1
            gpibaddress = int(addr.strip("dev"))
            if type(serialport) == int:
                self.ch = serialport
        else:  # prologix being used, arguments are correct
            gpibaddress = addr

        self.addr = gpibaddress

    #    def set_volt(self, channel, V):
    #    def set_volt(self, V):

    def set_volt(self, *args):
        if len(args) == 2:
            channel = args[0]
            V = args[1]
        else:
            V = args[0]
            channel = self.ch

        msg = "P%d V%f X\r\n" % (channel, V)
        # print("MSG to send")
        self.meter.write(msg)
        self.currentV = V

    # 	print msg
    # def get_src_volt(self, channel):

    def get_src_volt(self, *args):
        if len(args) == 0:
            channel = self.ch
        else:
            channel = args[0]
        msg = "P%d V? X\r\n" % (channel)
        # self.meter.write(msg)
        # actualV = self.meter.read().strip()
        actualV = self.meter.query(msg)
        # print 'read %s'%repr(actualV)
        if len(actualV) == 0:
            return float("NaN")
        else:
            idx = len(actualV) - 1 - actualV[::-1].find("V")
            if idx < len(actualV):
                actualV = actualV[(idx + 1) :]

        # print 'actualV: %s'%actualV
        return float(actualV)

    # def get_volt(self,channel):
    def get_volt(self, *args):
        return self.get_src_volt(*args)

    def set_power_on(self):
        for k in range(1, 5):
            self.set_volt(k, 0)

    def set_power_off(self):
        for k in range(1, 5):
            self.set_volt(k, 0)

    def identify(self):
        identity = "Keithley213 4 channels; addr: %d; output port: %d" % (
            self.addr,
            self.ch,
        )
        return identity

    def writeconfig(self, f):
        msg = self.identify().strip()

        f.write("# " + msg + "\n")
        status_list = ["U0", "U1", "U2", "U3", "U4", "U7", "U8"]
        for cmd in status_list:
            msgin = self.meter.query("%s X\r\n" % cmd).strip()
            f.write("# %s: %s\n" % (cmd, msgin))
        f.write("#\n")
        f.flush()

    def close(self):
        self.set_power_off()


if __name__ == "__main__":
    import serial

    # serialport = serial.Serial('/dev/tty.usbserial-PXHBW0TN', 9600, timeout = 0.5)
    serialport = serial.Serial("COM8", 9600, timeout=0.5)
    source = dev(9, serialport)
    # source.meter.write('++addr')
    # print source.port.read()
    source.set_volt(1, 0)
