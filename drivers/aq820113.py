from __future__ import print_function
import base_laser
import aq8201
import Gpib
import time
import numpy as np
import math

params = [
    {"name": "AQ8201-13 GPIB Address", "type": "int", "limits": (1, 32), "value": 4},
    {
        "name": "AQ8201-13 Slot",
        "type": "int",
        "values": {1, 2, 3, 5, 6, 7, 8, 9, 10},
        "value": 3,
    },
]


class dev(base_laser.dev, aq8201.dev):
    def __init__(self, addr, serialport="", slot=1):
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
                slot = serialport

        else:
            gpibaddress = addr
        self.slot = slot
        self.addr = gpibaddress
        params[0]["value"] = gpibaddress
        params[1]["value"] = slot
        if not hasattr(
            self, "p"
        ):  # create attribute p because class was instantiated w/o list
            self.p = deepcopy(params)
        self.std_init()

    def std_init(self):
        self.meter.write("C%d" % self.slot)
        self.meter.write("LUS0")  # Set to wavelength units of nm
        self.meter.write("LEMO0")  # Set to external modulation off
        self.meter.write("LIMO0")  # Set internal to CW
        self.meter.write("LCOHR1")  # Set coherence ctrl on (wide bandwidth)
        """
        self.meter.write('C%d'%self.slot)
        self.wlmin = self.meter.query('LWMIN?').strip().lstrip('LWMIN')
        self.wlmin = float(self.wlmin)
        self.meter.write('C%d'%self.slot)
        #time.sleep(1)
        self.wlmax = self.meter.query('LWMAX?').strip().lstrip('LWMAX')
        self.wlmax = float(self.wlmax)
        print 'WL range: ',self.wlmin, self.wlmax
        """

    def identify(self):
        chassisid = super(dev, self).identify()
        # self.meter.write('C%d'%self.slot)
        # should we do a MOD?
        # slotid = self.meter.query('MOD?',0.1)
        slotid = ""
        return "# Chassis gpib %d: \t%s\n# Slot %d: \t\t%s\n" % (
            self.addr,
            chassisid,
            self.slot,
            slotid,
        )

    def writeconfig(self, fp):
        super(dev, self).writeconfig(fp)
        self.meter.write("C%d" % self.slot)
        msgin = self.meter.query("MODEL?")
        fp.write("#  MODEL?: %s\n" % msgin.strip())
        self.meter.write("C%d" % self.slot)
        msgin = self.meter.query("LD?")
        fp.write("#  LD?: %s\n" % msgin.strip())
        cohl = self.get_cohl()
        fp.write("#  Coherence Control: %d\n" % cohl)
        lwlcal = self.get_lwlcal()
        fp.write("#  LWLCAL: %.2f\n" % lwlcal)
        latl = self.get_latl()
        fp.write("#  LATL: %.2f\n" % latl)
        fp.flush()

    def get_lambda(self):
        # self.meter.write('C%d'%self.slot)
        self.set_slot()
        msg = self.meter.query("LW?")
        if len(msg.strip()) == 0:
            self.wl = float("NaN")
            # print 'Trying to read again',repr(self.meter.read(100))
        else:
            self.wl = float(msg.strip().lstrip("LW"))
        return self.wl

    def set_lambda(self, value):
        loop = 0
        while loop < 3:
            self.meter.write("C%d" % self.slot)
            value = "%.1f" % np.around(value, 1)
            self.meter.write("LW%s" % (value))
            self.wl = self.get_lambda()
            if value != "%.1f" % self.wl:
                loop += 1
            else:
                return 0
        print(
            "Problem setting wavelength on the laser to %d, gpib: %d, slot: %d got:%f"
            % (value, self.addr, self.slot, self.wl)
        )
        return -1

    def get_cmd(self, cmd):
        loop = 0
        while loop < 3:
            self.meter.write("C%d" % self.slot)
            msg = self.meter.query("%s?" % cmd)
            msg = msg.strip()
            if len(msg) > 0:
                value = float(msg.strip().split(cmd)[1])
                return value
            else:
                loop += 1
        print("Problem getting cohl from the laser")
        value = -1
        return value

    def get_lopt(self):
        self.lopt = self.get_cmd("LOPT")
        self.lopt = int(self.lopt)
        if self.lopt < 0:
            return -1
        else:
            return self.lopt

    """
    def set_lopt(self,value):
        self.meter.write('C%d'%self.slot)
        self.meter.write('LOPT %d'%value)
        self.lopt=self.get_lopt()
        if value != self.lopt:
            print 'Problem setting lopt on the laser to %d, gpib: %d, slot: %d got: %f'%(value, self.addr, self.slot,self.lopt)
            return -1
        return 0
    """

    def get_cohl(self):
        loop = 0
        while loop < 3:
            self.meter.write("C%d" % self.slot)
            msg = self.meter.query("LCOHR?")
            msg = msg.strip()
            if len(msg) > 0:
                self.cohl = float(msg.strip().lstrip("LCOHR"))
                return self.cohl
            else:
                loop += 1
        print("Problem getting cohl from the laser")
        self.cohl = -1
        return self.cohl

    def set_cohl(self, value):
        self.meter.write("C%d" % self.slot)
        value = int(value)
        if value > 1:
            value = 1
        self.meter.write("LCOHR%d" % int(value))
        if value != self.get_cohl():
            print(
                "Problem setting cohl on the laser to %d, gpib: %d, slot: %d"
                % (value, self.addr, self.slot)
            )
        return None

    def set_power(self, value_W):
        self.meter.write("C%d" % self.slot)
        value = 10. * math.log10(value_W) + 30
        self.meter.write("LPL%.2f" % float(value))
        if value_W != self.get_power():
            print(
                "Problem setting the power on the laser to %f, gpib: %d, slot: %d"
                % (value_W, self.addr, self.slot)
            )
        return None

    def get_power(self):
        self.meter.write("C%d" % self.slot)
        msgin = self.meter.query(b"LPL?")
        # print 'power msgin',msgin
        power = 10. ** (float(msgin)) * 1e-3
        return power

    def set_lopt(self, value):
        self.meter.write("C%d" % self.slot)
        self.meter.write("LOPT%d" % value)

    def set_lwlcal(self, value):
        self.meter.write("C%d" % self.slot)
        value = "%.2f" % np.around(value, 2)
        self.meter.write("LWLCAL%s" % (value))
        if value != "%.2f" % self.get_lwlcal():
            print(
                "Problem setting the lwcal on the laser to %s, gpib: %d, slot: %d"
                % (value, self.addr, self.slot)
            )
        return None

    def set_latl(self, value):
        self.meter.write("C%d" % self.slot)
        self.meter.write("LATL%.2f" % float(value))
        if value != self.get_latl():
            print(
                "Problem setting the latl level on the laser to %f, gpib: %d, slot: %d"
                % (value, self.addr, self.slot)
            )
        return None

    def get_lwlcal(self):
        self.meter.write("C%d" % self.slot)
        msgin = self.meter.query("LWLCAL?").strip().lstrip("LWLCAL")
        return float(msgin)

    def get_latl(self):
        self.meter.write("C%d" % self.slot)
        # self.meter.write('LATL?')
        # msgin = self.meter.read(100)
        msgin = self.meter.query("LATL?", 0.5)
        msgin = msgin.strip().lstrip("LATL")
        try:
            ans = float(msgin)
        except:
            print("could not convert %s" % repr(msgin))
            ans = float("nan")
        return ans

    def enable(self):
        self.set_lopt(1)

    def disable(self):
        self.set_lopt(0)

    def get_status(self):
        self.meter.write("C%d" % self.slot)
        start = time.time()
        # while True: # wait while zeroing
        msgin = self.meter.query("LMSTAT?").strip().lstrip("LMSTAT")
        print("get_status", msgin)
        if len(msgin) != 1:
            msgin = "ZZZ"
        return msgin


if __name__ == "__main__":
    # laser = dev('dev3',1)
    laser = dev(6, "/dev/ttyUSB0", 1)
    print(laser.get_lambda())
    """
    laser.set_power(1e-3)
    #print pm.zero()
    print laser.get_lambda()
    import sys
    laser.writeconfig(sys.stdout)
    laser.enable()
    laser.get_status()
    laser.set_cohl(1)
    print laser.get_lambda()
    """
    laser.close()
