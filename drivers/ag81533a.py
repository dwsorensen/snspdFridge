from __future__ import print_function

# from builtins import str
#!/usr/bin/env python
# import sys
# import os
# import string
import time

# import threading
import ag8166
from copy import deepcopy
import numpy as np
import logging

logger = logging.getLogger(__name__)
params = [
    {
        "name": "AG81533A power meter GPIB Address",
        "type": "int",
        "limits": (1, 32),
        "value": 5,
    },
    {"name": "AG81533A slot", "type": "int", "limits": (1, 20), "value": 1},
]


def flt(s):
    try:
        return float(s)
    except ValueError:
        return float("NaN")


class dev(ag8166.dev):
    def __init__(self, addr, serialport="", slot=2):
        """ Written by SaeWoo and Jeff """
        ag8166.dev.__init__(self, addr, serialport)
        if type(addr) == list:
            self.p = addr  # should I make a deepc$py here? for now no...
            for item in self.p:
                if "value" in item:  # item.has_key('value'):
                    name = item["name"]
                    value = item["value"]
                    if "ddress" in name:
                        gpibaddress = value
                    elif "slot" in name:
                        slot = value
            # print 'config from list addr %d, slot %d'%(gpibaddress, slot)
        elif type(addr) == str:
            # The arguments are shifted by 1
            gpibaddress = int(addr.strip("dev"))
            if type(serialport) == int:
                slot = serialport
        else:
            gpibaddress = addr
        self.slot = slot
        self.gpibaddress = gpibaddress
        # print type(gpibaddress)
        params[0]["value"] = gpibaddress
        params[1]["value"] = self.slot
        if not hasattr(self, "p"):
            self.p = deepcopy(params)
        self.get_atim()

    def get_param(self, msgout):
        reply = self.meter.query(msgout)
        try:
            ret = float(reply.strip())
        except:
            ret = float("NaN")
            print("get_param, %s, reply %s" % (msgout, repr(reply)))
        return ret

    def get_param_old(self, msgout):
        self.meter.write(msgout)
        # while not(self.meter.rsp()&16):
        #     time.sleep(0.1)
        count = 0
        while True:
            time.sleep(0.01)
            reply = self.meter.read()
            if len(reply) > 0:
                break
            print("get_param count %d" % count)
            if count == 3:
                reply = "3000"
                break
            else:
                count += 1
            # reply = self.meter.query(msgout,0.1)
            # print 'get_param: %s'%repr(reply.strip())
        try:
            ret = float(reply.strip())
            return ret
        except:
            return float("NaN")

    def set_param(self, msgout, msgcheck, value):
        self.meter.write(msgout)
        ret = self.get_param(msgcheck)
        if ret != value:
            print("problem with %s" % msgout)
            raise Exception("problem with %s" % msgout)
            ret = float("NaN")
        return ret

    def get_cont(self):
        msgout = "INIT%d:CONT?\n" % (self.slot)
        return int(self.meter.query(msgout))

    def set_cont(self, value):
        msg1 = "INIT%d:CONT %d" % (self.slot, value)
        msg2 = "INIT%d:CONT?" % (self.slot)
        self.cont = self.set_param(msg1, msg2, value)
        return self.cont

    def get_power(self):
        reply = self.meter.query("READ%d:POW?\n" % self.slot, 0.5 + self.atim).strip()
        # print 'pow: ',repr(reply)
        """
        self.meter.write('READ%d:POW?\n'%self.slot)
        time.sleep(self.atim/2)
        while True:
            reply = self.meter.read().strip()
            if len(reply)>0:
                break;
            print 'Trying to read power again'
        """
        if len(reply) == 0:
            self.power = -1
            print(self.meter.read().strip())
        else:
            self.power = float(reply.strip())
        return self.power

    def get_lambda(self):
        msgout = "SENS%d:POW:WAV?\n" % (self.slot)
        self.wl = self.get_param(msgout)
        return self.wl

    def set_lambda(self, value):
        self.meter.write("SENS%d:POW:WAV %fE-9\n" % (self.slot, value))
        self.wl = self.get_lambda() * 1e9
        if self.wl != value:
            print("problem setting PM wavelength to %f, got: %f" % (value, self.wl))
            self.meter.write("SENS%d:POW:WAV %fE-9\n" % (self.slot, value))
            self.wl = self.get_lambda() * 1e9
        return self.wl

    def get_atim(self):
        failed_attempts = 0
        while True:
            msg = "SENS%d:POW:ATIM?\n" % self.slot
            msgin = self.meter.query(msg)
            try:
                self.atim = float(msgin.strip())
                break
            except:
                logger.info('get_atim failed msgin:[%r]' %
                             (msgin))
                if failed_attempts == 5:
                    return -1
                failed_attempts += 1
        return self.atim

    def set_atim(self, value):
        self.meter.write("SENS%d:POW:ATIM %f\n" % (self.slot, float(value)))
        self.atim = self.get_atim()
        if self.atim != value:
            print("problem setting atim to %f, %f" % (value, self.atim))
        return self.atim

    def get_range(self):
        msg = "SENS%d:POW:RANG?\n" % (self.slot)
        rng = self.get_param(msg)
        if np.isnan(rng):  # ==float('nan'):
            print("Problem getting the PM range")
            rng = 1000
        self.range = int(rng)
        # print 'get_range:',reply
        return self.range

    def set_pow_autorange(self, auto):
        """turn auto range off or on"""
        msg = ":SENS%d:POW:RANG:AUTO %d" % (self.slot, auto)
        self.meter.write(msg)
        time.sleep(0.1)

    def set_range(self, value):
        self.set_pow_autorange(0)
        self.meter.write("SENS%d:POW:RANG %f\n" % (self.slot, value))
        self.range = self.get_range()
        if self.range != value:
            print("Problem setting range to %f" % value)
        return self.range

    def set_unit(self, value):
        self.meter.write("SENS%d:POW:UNIT %f\n" % (self.slot, value))
        self.unit = self.get_unit()
        if self.unit != value:
            print("problem setting unit to %f" % value)
        return self.unit

    def get_unit(self):
        self.unit = self.get_param("SENS%d:POW:UNIT?" % self.slot)
        return self.unit

    def get_unit_old(self):
        self.meter.write("SENS%d:POW:UNIT?\n" % self.slot)

        reply = self.meter.read(100).strip()
        try:
            self.unit = int(float(reply.strip()))
        except:
            print(("could not convert", repr(reply)))
        return self.unit

    def identify(self):
        msg = "*IDN?"
        self.meter.write(msg)
        time.sleep(0.1)
        chassisid = self.meter.read().strip()
        """identify the module in a chosen slot"""
        slot = self.slot
        msg = ":SLOT%s:IDN?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        slotid = self.meter.read().strip()
        """identify the module in a chosen slot"""
        msg = ":SLOT%s:HEAD1:IDN?" % (str(slot))
        self.meter.write(msg)
        time.sleep(0.1)
        headid = self.meter.read().strip()

        return_msg = "# Chassis gpib %d: \t%s\n" % (self.gpibaddress, chassisid)
        return_msg += "# Slot %d: \t\t%s\n# Head: \t\t%s\n" % (
            self.slot,
            slotid,
            headid,
        )
        return return_msg

    def writeconfig(self, f):
        msg = self.identify()
        # f.write('# Agilent 86142a in slot %d\n'%(self.slot))
        # f.write('#    ID: %s\n'%msg)
        f.write(msg)
        wl = self.get_lambda()
        atim = self.get_atim()
        rang = self.get_range()
        f.write("# wavelength: %e\n# ATIM: %f\n# Range: %d\n" % (wl, atim, rang))
        f.flush()

    def close(self):
        self.meter.close()

    def init_pwm_log(self, num_points):
        # global s,addr,int_time,num_points,slot
        slot = self.slot
        self.log_num_points = num_points
        with self.meter.lock:
            self.atim = self.get_atim()
        logger.debug("init power meter logging ATIM (ag81533): %e" % self.atim)
        with self.meter.lock:
            self.meter.write("SENS%d:FUNC:STAT LOGG, STOP\n" % slot)
            self.meter.write("SENS%d:FUNC:STAT?\n" % slot)
            reply = self.meter.read(100)
            # print reply.strip()
            int_time = self.atim
            self.meter.write(
                "SENS%d:FUNC:PAR:LOGG %d, %.2f\n" % (slot, num_points, int_time)
            )
            self.meter.write("SENS%d:FUNC:PAR:LOGG?\n" % slot)
            # s.write('SENS%d:FUNC:PAR:STAB %d, %.1f, %.1f\n'%(slot,
            #         num_points, int_time, int_time))
            # s.write('SENS%d:FUNC:PAR:STAB?\n'%slot)

            reply = self.meter.read(100)
        logger.debug("after init, check status: " + reply.strip())

    def start_pwm_log(self):
        while True:
            self.meter.write("SENS%d:FUNC:STAT LOGG, STAR\n" % self.slot)
            self.log_start_time = time.time()
            reply = self.meter.query("SENS%d:FUNC:STAT?\n" % self.slot)
            logger.debug("Check status after start:" + reply.strip())
            if "NONE" in reply:
                reply = self.meter.query("SENS%d:FUNC:STAT?\n" % self.slot)
                logger.debug("Checked status again start:" + reply.strip())
            if "LOGGING_STABILITY" in reply:
                break

    def stop_pwm_log(self):
        self.meter.write("SENS%d:FUNC:STAT LOGG, STOP\n" % self.slot)
        self.log_start_time = 0

    def read_pwm_log(self):
        # global s,addr,int_time, num_points,slot
        slot = self.slot
        # time.sleep(int_time*num_points)
        # time.sleep(num_points)
        timetowait = self.atim * self.log_num_points
        dt = time.time() - self.log_start_time
        # should do something if log_start_time == 0
        if self.log_start_time == 0:
            print("Error, pwm_log was not started")
            return None
        if dt < timetowait:
            logging.debug(
                "need to wait for logging to finish: %.1f" % (timetowait - dt)
            )
            time.sleep(timetowait - dt)
        count = 0
        while True:
            with self.meter.lock:
                reply = self.meter.query("SENS%d:FUNC:STAT?\n" % slot)
            if "COMPLETE" in reply:
                break
            logging.debug("status: " + reply.strip())
            if "NONE" in reply:
                logging.debug("Problem with logging.  Power meter stopped logging")
                return None
            time.sleep(.1)
            if count == 30:
                logging.debug(
                    "Problem reading log, queried and should be done, but not"
                )
                return None
            else:
                count += 1
        count = 0
        with self.meter.lock:
            while True:
                logger.debug("get results")
                self.meter.write("SENS%d:FUNC:RES?" % slot)
                time.sleep(.1)
                # print 'try to read'
                msgin = self.meter.readbinary(2)
                logger.debug("binary read:" + repr(msgin))
                if msgin[0] == "#":
                    break
            if count == 30:
                logger.error("Can not read log")
                time.sleep(0.1)
                return None
            else:
                count += 1

            msgin = self.meter.readbinary(int(msgin[-1]))
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
        # print len(data_pwm)
        msgin = self.meter.read()
        # print 'end of pwmlog %s'%(repr(msgin))
        if msgin[0] != "\n":
            print("Problem with binary x-fer... Did not get \\n at the end")
        block = np.fromstring(data_pwm, dtype="float32")
        # print repr(data_pwm)
        # f = open('raw.out','wb')
        # f.write(data_pwm)
        # f.close()
        # print  block.shape
        # return data_pwm
        return block

    # def get_status(self):
    #     m = 'STAT%d:OPER?'%self.slot
    #     ans = self.get_param(m)
    #     if np.isnan(ans):
    #         ans = -1
    #     else:
    #         ans = int(ans)
    #     return ans
    #
    def get_status_tqdm(self):
        return self.get_status_tqdm_rsp()

    def get_status_tqdm_get_status(self):
        m = "STAT%d:OPER?" % self.slot
        ans = self.meter.query(m)
        import tqdm

        for count in tqdm.trange(40):
            ans = ans.strip()
            try:
                ret = int(ans)
                break
            except:
                # print('bad get_status: ',repr(ans))
                ret = -1
            ans = self.meter.readline()
        return ret

    def get_status_tqdm_rsp(self):
        import tqdm

        m = "STAT%d:OPER?" % self.slot
        self.meter.write(m)
        ret = -1
        import tqdm

        for count in tqdm.trange(40):
            if self.meter.rsp() & 16:
                ret = self.meter.readline().strip()
                ret = int(ret)
                break
            time.sleep(1)
        return ret

    def get_status(self):
        m = "STAT%d:OPER?" % self.slot
        ans = self.meter.query(m)
        count = 0
        while True:
            ans = ans.strip()
            try:
                ret = int(ans)
                break
            except:
                # print('bad get_status: ',repr(ans))
                ret = -1
                count += 1
            if count > 40:
                break
            ans = self.meter.readline()
        return ret

    def get_status_new2(self):
        self.meter.write("STAT%d:OPER?" % self.slot)
        # function was bombing out when this line was inside the loop.
        # Too many writes of this command causing buffer to pile up with
        # results before the first result could be read.  Send the commmand
        # once, and read until you get the answer.
        msg = ""
        while True:
            m = self.meter.read(100)
            if len(m) > 0:
                msg += m
            else:
                time.sleep(1)
            if "\n" in msg:
                break
        # print repr(msgin)
        self.status = int(msg.strip())
        return self.status

    def get_status_old(self):
        self.meter.write("STAT%d:OPER?" % self.slot)
        # function was bombing out when this line was inside the loop.
        # Too many writes of this command causing buffer to pile up with
        # results before the first result could be read.  Send the commmand
        # once, and read until you get the answer.
        while True:
            msgin = self.meter.read(100)
            print("msgin: " + repr(msgin))
            if len(msgin.strip()) > 0:
                if msgin[-1] == "\n":
                    break
            time.sleep(1)
        # print repr(msgin)
        self.status = int(msgin.strip())
        return self.status

    def zero(self):
        print("starting zero")
        start = time.time()
        status = self.get_status()
        print("status before zero %d" % status)
        self.meter.write("SENS%d:CORR:COLL:ZERO" % (self.slot))
        time.sleep(1)
        # check status until zero is complete
        while True:
            status = self.get_status_tqdm()
            print("zero status: %d" % status)
            if status == 0:
                break
        t = time.time() - start
        print("zero time: %.2f" % t)
        return t

    def loc(self):
        self.meter.loc()


if __name__ == "__main__":
    meter = dev("dev1", 1)
    # meter = dev(8,'COM4',2)
    # meter.set_cont(0)
    # print meter.get_cont()
    print(meter.set_atim(1))
    print(meter.get_power())
    meter.set_lambda(1552)
    meter.init_pwm_log(4)
    meter.start_pwm_log()
    msg = meter.read_pwm_log()
    print(msg)
    """
    meter.meter.tmo(12)
    meter.meter.config(12,0)
    meter.set_range(0)
    print 'range:',meter.get_range()
    print meter.identify()
    meter.set_cont(0)
    print meter.get_lambda()
    meter.zero()
    print meter.get_power()
    #meter.meter.eos()
    #print meter.get_lambda()
    print 'status:',meter.get_status()
    #meter.zero()
    #print meter.set_range(-10)
    print 'unit:',meter.set_unit(1)
    print 'pow:',meter.get_power()
    meter.set_pow_autorange(0)
    print 'range:',meter.get_range()
    meter.init_pwm_log(5)
    meter.start_pwm_log()
    msg = meter.read_pwm_log()
    print msg
    meter.start_pwm_log()
    msg = meter.read_pwm_log()
    print msg
    meter.stop_pwm_log()
    meter.loc()
    meter.set_lambda(1540)
    print meter.get_lambda()

    print meter.get_power()
    print meter.identify()
    meter.init_pwm_log(5)
    meter.start_pwm_log()
    msg = meter.read_pwm_log()
    print meter.get_power()
    print msg.mean()
    print meter.get_range()
    meter.stop_pwm_log()
    meter.set_range(-10)
    meter.set_lambda(1470)
    import sys
    f = sys.stdout
    meter.writeconfig(f)
    meter.meter.loc()
    """
