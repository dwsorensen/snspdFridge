from __future__ import print_function

# from builtins import chr
import aq820121
import Gpib
import time
import numpy as np

####
#  This stuff below is not correct... Needs to be fixed
params = [
    {"name": "AQ8233 GPIB Address", "type": "int", "limits": (1, 32), "value": 4},
    {"name": "AQ8233 Slot", "type": "int", "values": {1, 2, 3}, "value": 3},
]
#####

rng_list = np.arange(30, -70, -10)
rng_dict = {}
for i, val in enumerate(rng_list):
    rng_dict[int(val)] = chr(ord("C") + i)
rng_dict[111] = chr(65)  #  Shane changed this so I can set the OPM range to auto.
atime_dict = {}
atime_list = [1, 2, 5, 10, 20, 50, 100, 200]
unit_dict = {
    "L": 9,
    "M": 6,
    "N": 3,
    "O": 0,
    "P": -3,
    "Q": -6,
    "R": -9,
    "S": -12,
    "T": -15,
    "Z": -18,
}

for i, val in enumerate(atime_list):
    atime_dict[int(val)] = chr(ord("A") + i)


def find_key(d, v):
    for key, value in list(d.items()):
        if v == value:
            return key
    return None


class dev(aq820121.dev):
    def __init__(self, addr, serialport="", slot=1, powmeter=1):
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        meter = self.meter
        #  fill in correct values for params, and make a copy of this instance
        if type(addr) == list:
            self.p = addr  # should I make a deepcopy here?  Not sure, will not for now
            for item in self.p:
                if "value" in item:
                    name = item["name"]
                    value = item["value"]
                    if "ddress" in name:
                        gpibaddress = value
                    elif "Slot" in name:
                        slot = value
            print("config from list addr %d, slot %d, ch %d" % (gpibaddress, slot, ch))
        elif type(addr) == str:  # Arguments are shifted by 1
            gpibaddress = int(addr.strip("dev"))
            if type(serialport) == int:
                powmeter = slot
                slot = serialport
        else:
            gpibaddress = addr
        self.powmeter = powmeter
        self.slot = slot
        self.addr = gpibaddress
        params[0]["value"] = gpibaddress
        params[1]["value"] = slot
        if not hasattr(
            self, "p"
        ):  # create attribute p because class was instantiated w/o list
            self.p = deepcopy(params)
        # print(self.addr, self.slot, self.powmeter)
        # self.set_powmeter(self.powmeter)
        # self.std_init()
        # print('done with init')

    def get_powmeter(self):
        self.meter.write("C%d" % self.slot)
        msg = self.meter.query("D?")
        value = msg.strip().lstrip("D")
        print(("get_powmeter", value))
        return int(value)  #  Need to change to try exception here...

    def set_powmeter(self, value):
        self.meter.write("C%d" % self.slot)
        while True:
            self.meter.write("D%d" % value)
            time.sleep(0.5)
            # print 'readline after setting',repr(self.meter.readline())
            check = self.get_powmeter()
            if value != check:
                print(
                    "Problem setting which powermeter to %d, gpib: %d, slot: %d"
                    % (value, self.addr, self.slot)
                )
        return value

    def identify(self):
        # print('called identify')
        msg = super(dev, self).identify()
        msg += "#  power meter: %d\n" % self.powmeter
        return msg


if __name__ == "__main__":
    pm = dev(11, "/dev/ttyUSB0", 10, 1)
    print(pm.identify())
    # print pm.zero()
    print(pm.get_powmeter())
    # print pm.get_status()
    # pm.meter.write('C%d'%pm.slot)
    # print pm.identify()
    # pm.meter.write('PZ')
    # pm.zero()
    import sys

    pm.writeconfig(sys.stdout)
