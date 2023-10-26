from __future__ import print_function

# from builtins import input
# from builtins import object
import sys

RQS = 1 << 11
SRQ = 1 << 12
TIMO = 1 << 14
"""
old_raw_input = raw_input

def new_raw_input(prompt):
    result = old_raw_input(prompt)
    if sys.stdin is not sys.__stdin__:
        print result
    return result

raw_input = new_raw_input
"""


class Gpib(object):
    def __init__(self, addr, serialport=""):
        # print 'Using Gpibfake'
        # print 'serialport: ',serialport
        if type(addr) == str:
            addr = int(addr.strip("dev"))
        self.addr = addr

    def write(self, str):
        print("write: %s" % str)

    def read(self, len=512):
        old_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        res = input("trying to read from addr %d: " % self.addr)
        sys.stdout = old_stdout
        return res

    def clear(self):
        print("clear")

    def rsp(self):
        old_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        msg = input("rsp results to send: ")
        sys.stdout = old_stdout
        return int(msg)

    def trigger(self):
        print("trigger")

    def loc(self):
        print("loc")

    def close(self):
        self.loc()

    def config(self, *args):
        print("config", args)

    def tmo(self):
        print("tmo")

    def eos(self):
        print("eos")
