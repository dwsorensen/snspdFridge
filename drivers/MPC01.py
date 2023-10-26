# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 11:14:35 2014

@author: qittlab
"""
from __future__ import print_function

# from builtins import zip
import Gpib
import time
import baseinst


class dev(baseinst.dev):
    def __init__(self, addr, serialport=""):
        self.meter, self.addr, self.port, self.p = Gpib.Gpib2(addr, serialport)
        meter = self.meter

    def getOPC(self):
        while True:
            opc = self.meter.query("*OPC?").strip()
            try:
                value = int(opc[0])
                break
            except:
                print("failed opc ", repr(opc))
        return value

    def getOPC_v2(self):
        attempts_left = 5
        while attempts_left:
            msgin = self.meter.rsp()
            # self.meter.port.write('++spoll\r')
            # msgin =  self.meter.port.readline()
            # print('spoll: '+repr(msgin))
            # msgin = msgin.strip()
            # print('spoll after strip: '+repr(msgin))
            try:
                value = int(msgin)
                # print('spoll value: %d' % value)
                return value % 2 == 0
                # break
            except:
                attempts_left -= 1
                print("failed spoll:" + repr(msgin))
        print("could not retrieve serial poll")
        raise ValueError("can not retrieve spoll in MPC01")

    def setAxis(self, axis, value):
        val = (value // 0.15) * 0.15
        msg = "%s=%.2f\n" % (axis, val)
        self.meter.write(msg)
        # print('sleep')
        time.sleep(.1)
        while True:
            opc = self.getOPC_v2()
            """
            check = self.getAxis(axis)
            if abs(value-check)<0.15:
               break
            print ('OPC: %d, trying to set %c to %.2f, at %.2f'%(opc,axis,value,check))
            """
            if opc == 1:
                break
        # print ('done, opc: %d'%self.getOPC())
        return

    def getAxis(self, axis):
        msg = "%c?\n" % axis
        self.meter.write(msg)
        local_count = 0
        while True:
            poll = self.meter.rsp()
            local_count += 1
            #print('poll', poll)
            if poll & (1 << 6):
                break
            if local_count > 100:
                print(self.meter.readline().strip())
                self.meter.write(msg)
                local_count = 0
        msgin = self.meter.readline().strip()
        #  Split at '\n'
        msgin = msgin.split("\n")
        if len(msgin[0]) > 0:
            msgin = msgin[0]

        while True:
            if "=" in msgin:
                # print(repr(msgin))
                value = msgin.split("=")
                print(value)
                axisvalue = value[1]
                value = value[0].replace(" ", "")
                return float(value)
            else:
                try:
                    return float(eval(msgin))
                except:
                    print("failed to read", repr(msgin), float(msgin))
                    msgin = self.meter.readline()

    def setAll(self, vector):
        for axis, value in zip(["X", "Y", "Z"], vector):
            self.setAxis(axis, value)

    def writeconfig(self, f):
        f.write("#Polarization controller is " + self.identify().strip() + "\n")
        x = self.getAxis("X")
        y = self.getAxis("Y")
        z = self.getAxis("Z")
        f.write("# X: %.2f\n# Y: %.2f\n# Z: %.2f\n" % (x, y, z))
        return None


if __name__ == "__main__":
    pc = dev(5, "/dev/ttyUSB0")
    import sys

    while True:
        print("set to 90")
        pc.setAxis("X", 90)
        print("set to 0")
        pc.setAxis("X", 0)
    pc.writeconfig(sys.stdout)
