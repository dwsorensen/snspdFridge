#Got this to import
from __future__ import print_function
import base_optical_switch
import Gpib

params = [
    {"name": "AQ820x-43 GPIB Address", "type": "int", "limits": (1, 32), "value": 4},
    {"name": "AQ820x-43 Slot", "type": "int", "limits": {1, 12}, "value": 3},
    {"name": "AQ820x-43 Bank", "type": "int", "values": {1, 2}, "value": 1},
]


class dev(base_optical_switch.dev):
    def __init__(self, addr, serialport="", slot=1, bank=1):
        print("Serial port: " + str(serialport))
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
            print(
                "config from list addr %d, slot %d, ch %d" % (gpibaddress, slot, bank)
            )
        elif type(addr) == str:  # Arguments are shifted by 1
            gpibaddress = int(addr.strip("dev"))
            if type(serialport) == int:
                bank = slot
                slot = serialport

        else:
            gpibaddress = addr
        self.bank = bank
        self.slot = slot
        self.addr = gpibaddress
        params[0]["value"] = gpibaddress
        params[1]["value"] = slot
        if not hasattr(
            self, "p"
        ):  # create attribute p because class was instantiated w/o list
            self.p = deepcopy(params)

    def identify(self):
        chassisid = super(dev, self).identify()
        self.meter.write("C%d" % self.slot)
        slotid = self.meter.query("MOD?", 0.1).strip()
        return "# Chassis gpib %d: \t%s\n# Slot %d: \t\t%s\n" % (
            self.addr,
            chassisid,
            self.slot,
            slotid,
        )

    def writeconfig(self, fp):
        super(dev, self).writeconfig(fp)
        msgin = self.meter.query("MODEL?")
        fp.write("#  MODEL?: %s\n" % msgin.strip())
        # msgin = self.meter.query('AD?')
        # fp.write('#  AD?: %s\n'%msgin.strip())
        fp.flush()

    def get_route(self):
        loop = 0
        while loop < 3:
            self.meter.write("C%d" % self.slot)
            self.meter.write("D%d" % self.bank)
            msg = self.meter.query("SASB?", 0.5)
            msg = msg.strip()
            # print 'msg from get_route',msg
            if len(msg) > 0:
                if ("SSTRAIGHT" in msg) or ("SA1SB1" in msg):
                    self.output = 1
                elif ("SCROSS" in msg) or ("SA1SB2" in msg):
                    self.output = 2
                else:
                    self.output = 0
                return self.output
            else:
                loop += 1
        print("Problem getting route")
        self.output = -1
        return self.output
        """
        self.meter.write('C%d\n'%self.slot)
        msg = self.meter.query('AAV?\n')
        self.att = float(msg.strip().lstrip('AAV'))
        return self.att
	"""

    def set_route(self, value):
        self.meter.write("C%d\n" % self.slot)
        self.meter.write("D%d\n" % self.bank)
        self.meter.write("SA1SB%d\n" % (value))
        # print 'get_route from set_route',self.get_route()
        if value != self.get_route():
            print(
                "Problem setting route to %d, gpib: %d, slot: %d"
                % (value, self.addr, self.slot)
            )
        return self.output

    def route(self, value):
        self.set_route(value)


if __name__ == "__main__":
    # sw = dev('dev3',8,2)
    sw = dev(5, "/dev/ttyUSB0", 4, 1)
    print("get_route", sw.get_route())
    sw.set_route(1)
    print("get_route", sw.get_route())
    sw.set_route(2)
    import sys

    # att.enable()
    # att.set_att(11)
    # print att.meter.query('ASHTR?')
    print(repr(sw.identify()))
    sw.writeconfig(sys.stdout)
    # att.disable()
