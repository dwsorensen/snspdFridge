from __future__ import print_function

# from builtins import chr
# from builtins import object
import Gpib
import threading
import time
import string
import numpy as np

DEBUG = False
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


import re

non_decimal = re.compile(r"^\d.]+")


def flt(string_):
    string2 = non_decimal.sub("", string_)
    return float(string2)


class dev(object):
    def set_slot(self):
        while True:
            self.meter.write("C%d" % self.slot)
            msgin = self.meter.query("C?", wait=0.01, attempts=1).strip()
            # print 'set_slot msgin:',repr(msgin)
            msgin = msgin.decode()
            if "%02d" % self.slot == msgin.split("C")[-1]:
                break
            else:
                print("Could not set to slot %d, got:%s" % (self.slot, msgin))
        # print 'set to slot: %d'%self.slot


if __name__ == "__main__":
    pass
