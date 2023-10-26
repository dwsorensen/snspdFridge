from __future__ import print_function

# from builtins import str
# from builtins import chr
# from builtins import range
# from builtins import object
#!/usr/bin/env python
import Gpib
import time
import string
import sys


class dev(object):
    def __init__(self, addr, serialport=""):
        """Connect to and reset an agilent 8166A"""
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        """
    if type(addr)==list:
        self.p = addr  # should I make a deepcopy here?  Not sure, will not for now
        for item in self.p:
            if item.has_key('value'):
                name = item['name']
                value = item['value']
                if 'ddress' in name:
                    gpibaddress = value 
                    self.addr = gpibaddress
                elif 'GPIB interface name' in name:
                    portname = value
                    serialport = portname
                elif 'GPIB interface type' in name:
                    gpibtype = value
        #print 'config from list addr: %d, intf name: %s, type: %d'%(gpibaddress, portname, gpibtype)
        addr = gpibaddress
        self.addr = addr
        if gpibtype==2:  # this is prologix
            self.meter = Gpib.Gpib(addr, port=portname)
        elif gpibtype==1:  # this is NI
            self.meter = Gpib.Gpib('dev%d'%addr)
            serialport = 'gpib0'
        else: # pretend it is an NI board
            self.meter = Gpib.Gpib('dev%d'%addr)
            serialport = 'gpib0'
        #print 'config from list addr %d'%(gpibaddress)
    elif isinstance(addr,str):
      self.meter = Gpib.Gpib(addr)
      self.addr = int(addr.strip('dev'))
      serialport = 'gpib0'
    else:
      self.meter = Gpib.Gpib(addr,serialport)
      self.addr = addr
    meter = self.meter
    self.port = serialport
    """
        # self.reset()
        # meter.write('ZERO:AUTO OFF')

    def rd(self):
        return self.rd_new()

    def rd_old(self):
        msg = self.meter.read()
        list = string.split(msg)
        print(list)
        return list[0]

    def rd_new(self):
        while True:
            msg = self.meter.read()
            if len(msg) > 0:
                break
        return msg

    def enable(self, slot):
        msg = "OUTP%s:STAT ON" % (slot)
        self.meter.write(msg)
        time.sleep(0.1)

    def disable(self, slot):
        msg = "OUTP%s:STAT OFF" % (slot)
        self.meter.write(msg)
        time.sleep(0.1)

    def pow_zero(self, slot):
        msg = "sens%d:corr:coll:zero" % (slot)
        self.meter.write(msg)
        time.sleep(10)

    def get_stat(self, slot):
        try:
            msg = "OUTP%s:STAT?" % (slot)
            self.meter.write(msg)
            reading = self.rd()
            return int(reading)
        except self.meter.error:
            return -1

    def get_route(self, slot):
        try:
            msg = "ROUT%s:CHAN?" % (slot)
            self.meter.write(msg)
            reading = self.rd()
            # print reading
            list_switches = string.split(reading, ";")
            switch = []
            # print list_switches
            # print len(list_switches)
            for count in range(len(list_switches)):
                temp = list_switches[count]
                # print count,temp
                temp = string.split(temp, ",")
                # print temp
                switch.append(int(temp[1]))
            # print switch
            return switch[0]
        except self.meter.error:
            return -1

    def set_route(self, slot, channel, port):
        msg = "ROUT%s:CHAN %c,%d" % (slot, channel, port)
        self.meter.write(msg)

    def set_att(self, slot, att):
        """Set the attenuation"""
        msg = "INP%s:ATT %s" % (str(slot), str(att))
        self.meter.write(msg)

    def set_lambda(self, slot, wav):
        """Set the wavelength in nm"""
        msg = "INP%s:WAV %sE-9" % (str(slot), str(wav))
        self.meter.write(msg)

    def set_pow_lambda(self, slot, wav):
        """Set the wavelength in nm"""
        msg = "SENS%s:POW:WAV %sE-9" % (str(slot), str(wav))
        self.meter.write(msg)
        time.sleep(0.1)

    def set_pow_unit(self, slot, unit):
        """set power meter units:0=dBm,1=W"""
        msg = ":SENS%s:POW:UNIT %s" % (str(slot), str(unit))
        self.meter.write(msg)
        time.sleep(0.1)

    def get_pow_unit(self, slot):
        """set power meter units:0=dBm,1=W"""
        msg = ":SENS%s:POW:UNIT?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        result = self.meter.read()
        return int(result)

    def set_pow_atim(self, slot, atim):
        """set averaging time of power meter in (s)"""
        msg = ":SENS%s:POW:ATIM %s" % (str(slot), str(atim))
        self.meter.write(msg)
        time.sleep(0.1)

    def get_pow_atim(self, slot):
        """get the averaging time"""
        msg = ":SENS%s:POW:ATIM?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        avtime = self.meter.read()
        return avtime

    def set_pow_autorange(self, slot, auto):
        """turn auto range off or on"""
        msg = ":SENS%s:POW:RANG:AUTO %s" % (str(slot), str(auto))
        self.meter.write(msg)
        time.sleep(0.1)

    def set_source_lambda(self, slot, wav):
        """Set the wavelength in nm"""
        msg = "SOUR%s:WAV %sE-9" % (str(slot), str(wav))
        # print msg
        self.meter.write(msg)

    def get_att(self, slot):
        """Get the attenuation"""
        # print "hello"
        try:
            msg = ":INP%s:ATT?" % (str(slot))
            self.meter.write(msg)
            # time.sleep(0.1)
            reading = self.rd()
            # time.sleep(0.1)
            return float(reading)
        except self.meter.error:
            return None

    def get_lambda(self, slot):
        """Get the wavelength"""
        try:
            msg = ":INP%s:WAV?" % (str(slot))
            self.meter.write(msg)
            reading = self.rd()
            print(reading)
            return float(reading)
        except self.meter.error:
            return None

    def get_pow_lambda(self, slot):
        """Get the wavelength"""
        try:
            msg = ":SENS%s:POW:WAV?" % (str(int(slot)))
            self.meter.write(msg)
            time.sleep(0.1)
            reading = self.rd()
            time.sleep(0.1)
            # print reading
            return float(reading)
        except self.meter.error:
            return None

    def get_source_lambda(self, slot):
        """Get the wavelength"""
        try:
            msg = ":SOUR%s:WAV?" % (str(slot))
            self.meter.write(msg)
            time.sleep(0.1)
            reading = self.rd()
            # print reading
            return float(reading)
        except self.meter.error:
            return None

    def get_pow(self, slot):
        errornumber = 100
        try:
            msg = ":READ%s:POW?" % (str(slot))
            self.meter.write(msg)
            # poll = self.meter.rsp()
            # print 'rsp: %d'%poll
            # loop =0
            reading = self.rd()
            if float(reading) > 1000:
                return errornumber
            else:
                return float(reading)
        except:
            print("problem reading power")
            # print reading

    def get_pow_old(self, slot):
        """Get the power"""
        wait = 1
        while wait:
            try:
                msg = ":READ%s:POW?" % (str(slot))
                self.meter.write(msg)
                # poll = self.meter.rsp()
                loop = 0
                while ord(poll) == 0:
                    # print "nothing ready"
                    poll = self.meter.rsp()
                    loop = loop + 1
                    if loop == 200:
                        poll = chr(16)
                # print ord(poll)
                if loop > 100:
                    print("Loop: %d" % loop)
                reading = self.rd()
                # poll = self.meter.ibrsp()
                # print length(poll)
                return float(reading)
            except:
                if wait == 3:
                    return -1
                    print(
                        "error reading power: slot %d:%d:<%s>" % (slot, poll, reading)
                    )
                wait = wait + 1

    def identify_slot(self, slot):
        """identify the module in a chosen slot"""
        msg = ":SLOT%s:IDN?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        slotid = self.meter.read()
        return slotid

    def identify_head(self, slot):
        """identify the module in a chosen slot"""
        msg = ":SLOT%s:HEAD1:IDN?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        headid = self.meter.read()
        return headid

    def set_pow_range(self, slot, rang):
        """set the power meter range (dBm)"""
        msg = ":SENS%s:POW:RANG %s" % (str(slot), str(rang))
        self.meter.write(msg)
        time.sleep(0.1)

    def get_pow_range(self, slot):
        """get the range of the power meter"""
        msg = ":SENS%s:POW:RANG?" % str(slot)
        self.meter.write(msg)
        time.sleep(0.1)
        rangevalue = self.meter.read()
        return rangevalue

    def init_pwm_log(self, num_points, slot):
        # global s,addr,int_time,num_points,slot
        # slot = self.slot
        self.log_num_points = num_points
        self.atim = self.get_pow_atim(slot)
        print("init power meter logging ATIM: %e" % self.atim)
        self.meter.write("SENS%d:FUNC:STAT LOGG, STOP\n" % slot)
        self.meter.write("SENS%d:FUNC:STAT?\n" % slot)
        reply = self.meter.read(100)
        # print reply.strip()
        int_time = self.atim
        self.meter.write(
            "SENS%d:FUNC:PAR:LOGG %d, %.1f\n" % (slot, num_points, int_time)
        )
        self.meter.write("SENS%d:FUNC:PAR:LOGG?\n" % slot)
        # s.write('SENS%d:FUNC:PAR:STAB %d, %.1f, %.1f\n'%(slot,num_points,int_time,int_time))
        # s.write('SENS%d:FUNC:PAR:STAB?\n'%slot)

        reply = self.meter.read(100)
        print(reply.strip())

    def start_pwm_log(self, slot):
        self.meter.write("SENS%d:FUNC:STAT LOGG, STAR\n" % slot)
        # s.write('SENS%d:FUNC:STAT STAB, STAR\n'%slot)

    def stop_pwm_log(self, slot):
        self.meter.write("SENS%d:FUNC:STAT LOGG, STOP\n" % slot)

    def read_pwm_log(self, slot):
        # global s,addr,int_time, num_points,slot
        # slot = self.slot
        # time.sleep(int_time*num_points)
        # time.sleep(num_points)
        while True:
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
            self.meter.write("SENS%d:FUNC:STAT?\n" % slot)
            reply = self.meter.read(100)
            # print reply.strip()
            if "COMPLETE" in reply:
                # print
                break
        self.meter.write("SENS%d:FUNC:RES?\n" % slot)
        msgin = self.meter.read(1)
        msgin = self.meter.read(1)
        msgin = self.meter.read(int(msgin))
        # print repr(msgin)
        total_len = int(msgin)
        # print total_len
        data_pwm = ""
        lefttoget = total_len
        while True:
            dat_out = self.meter.readbinary(lefttoget)
            lefttoget = lefttoget - len(dat_out)
            data_pwm = data_pwm + dat_out
            # print repr(dat_out)
            # print len(dat_out)
            # print 'lefttoget: ',lefttoget
            if lefttoget == 0:
                break

    def pm_set_cont_trigger(self, slot, setting):
        # set whether the pm continually updates, setting = 1 updates, 0 waits for trigger
        msg = ":INIT%i:CONT %i" % (slot, setting)
        self.meter.write(msg)

    def pm_get_cont_trigger(self, slot):
        msg = ":INIT%i:CONT?" % slot
        self.meter.write(msg)
        time.sleep(0.1)
        result = self.meter.read()
        return int(result)

    def pm_writeconfig(self, slot, f):
        f.write("#slot id " + self.identify_slot(slot) + "\n")
        f.write("#head id " + self.identify_head(slot) + "\n")
        f.write("#Integration time is " + self.get_pow_atim(slot) + "\n")
        f.write("#Continuous Trigger set to %i\n" % self.pm_get_cont_trigger(slot))
        f.write("#Wavelength: " + str(self.get_pow_lambda(slot)) + "\n")
        return None

    def source_writeconfig(self, slot, f):
        f.write("#slot id " + self.identify_slot(slot) + "\n")
        f.write("#Wavelength set to " + str(self.get_source_lambda(slot)) + "\n")
        return None

    def writeconfig(self, f, slot):
        f.write("#agilent switch slot id " + self.identify_slot(slot) + "\n")

    def reset(self):
        """Reset the DMM and it's registers."""
        self.meter.write("*RST")
        self.meter.write("*CLS")

    def close(self):
        """End communication with the DMM"""
        self.meter.close()


if __name__ == "__main__":
    dev1 = dev("dev10")
    a = dev1.get_lambda(2)
    print("%.2e" % a)
    dev1.close()
