#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from past.utils import old_div
import Gpib
import time
import sys, os
import baseinst


class dev(baseinst.dev):
    def __init__(self, addr, serialport="", channel=0):
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        meter = self.meter
        #  A: channel = 0,   B: channel=1,  T:channel=2
        self.channel = channel
        self.count_time = self.get_time()
        self.init()

    """
    def __init__(self, name):
      self.meter = Gpib(name)
      meter = self.meter
      #self.reset()
      #meter.write('ZERO:AUTO OFF')
    """

    def identify(self):
        retmsg = "SR400, gpib: %d" % self.addr
        return retmsg

    def writeconfig(self, f):
        msg = self.identify().strip()
        f.write("# Counter is %s\n" % (msg))
        f.write("# Counter threshold is %s\n" % (self.get_threshold()))
        f.write("# Counter slope (0:+, 1:-) is %.1f\n" % (self.get_slope()))
        f.write("# channel: %d\n" % self.channel)
        f.write("#  time: %e\n" % (self.get_time()))
        # f.write('# Counter slope is %s\n'%(self.get_slope()))

    def get_threshold(self):
        msg = self.meter.query("DL %d" % self.channel).strip()
        try:
            return float(msg)
        except:
            return float("NaN")

    def get_slope(self):
        msg = self.meter.query("DS %d" % self.channel).strip()
        try:
            return float(msg)
        except:
            return float("NaN")

    def set_time(self, dt):
        preset = int(round(dt * 1e7))
        msg = "CP 2, %d" % (preset)
        self.meter.write(msg)
        self.count_time = dt

    def get_time(self):
        msgin = self.meter.query("CP 2")
        self.count_time = old_div(float(msgin.strip()), 1e7)
        return self.count_time

    def set_threshold(self, v):
        self.meter.write("DL %d, %f" % (self.channel, v))

    def get_tot_countAB(self):
        #time.sleep(0.2)
        self.meter.write("CR;CS")
        # self.meter.write('CS');
        #time.sleep(0.2)
        time.sleep(self.count_time)
        while True:
            # rsp = self.meter.query('SS')
            # print(repr(rsp))
            rsp = self.meter.rsp()
            if int(rsp) & 6 == 6:
                break
        #time.sleep(0.1)  #  Seems to be needed on windows machines
        A = self.meter.query("QA", 0.2)
        #time.sleep(0.1)
        B = self.meter.query("QB", 0.2)
        try:
            return float(A), float(B)
        except:
            print("problem with sr400 get_tot_count: %r, %r" % (repr(A), repr(B)))
            return float("NaN"), float("NaN")

    def get_tot_count(self):
        self.meter.write("CR;CS")
        # self.meter.write('CS');
        if self.channel == 0:
            ch_str = "QA"
        elif self.channel == 1:
            ch_str = "QB"
        else:
            print("No channel selected... using ch A")
            ch_str = "QA"
        time.sleep(self.count_time+0.1)
        while True:
            # rsp = self.meter.query('SS')
            # print(repr(rsp))
            rsp = self.meter.rsp()
            if int(rsp) & 6 == 6:
                break
        # print('added sleep on windows machine')
        # time.sleep(0.1)
        counts = self.meter.query(ch_str, 0.2)
        try:
            return float(counts)
        except:
            print("problem with sr400 get_tot_count: %s" % repr(counts))
            return float("NaN")

    def init(self):
        self.meter.write("NE 0")
        self.meter.write("NP 1")

    def set_continuous(self):
        self.meter.write("NE 1")

    def write(self, str):
        self.meter.write(str)

    def read(self):
        a = self.meter.read(100)
        print("read", repr(a))
        return int(a)

    def reset(self):
        """Reset the DMM and it's registers."""
        self.meter.write("*RST")
        self.meter.write("*CLS")

    def close(self):
        """End communication with the DMM"""
        self.meter.close()


if __name__ == "__main__":
    sr = dev(23, "COM4")
    import sys

    sr.writeconfig(sys.stdout)
    while True:
        print(sr.get_tot_count())
    sr.close()
    """
    filename = sys.argv[1]
    file = open(filename,'w');
    dev1 = dev(23,'COM9')
    dev1.write('SD 1')
    counter=1
    while(1):
        #dev1.write('CR');
        #dev1.write('CS');
        time.sleep(.001);
        dev1.write('QA')
        #time.sleep(1)
        a = dev1.read();
        dev1.write('QB')
        b = dev1.read();
        str ='%d:\t%d\t%d' %(counter, a,b)
        print str
        file.write(str+'\n');
        file.flush()
        counter = counter+1;
    dev1.close()
    """
