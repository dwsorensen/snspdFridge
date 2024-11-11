from __future__ import print_function
from builtins import object
import serial
import os, time
import logging

NT = os.name == "nt"
RQS = 1 << 11
SRQ = 1 << 12
TIMO = 1 << 14
import threading

gpiblock = threading.Lock()

# logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


class Gpib(object):
    def __init__(self, addr, serialport):
        if type(serialport) == str:
            self.port = serial.Serial(serialport, 115200, timeout=1)
            self.remote = False
        elif type(serialport) == tuple:
            host, port = serialport
            self.port = remote.Serial(host, port=port, timeout=1.0)
            self.remote = True
        else:
            self.port = serialport
        if self.port.isOpen() == False:
            self.port.open()
        self.addr = addr
        self.port.write(str.encode("++read_tmo_ms %d\n" % 1000))
        self.port.write(str.encode("++auto 0\n"))
        time.sleep(0.1)
        self.skip_close = False
        self.closent()
        self.lock = gpiblock
        # print(self.lock)

    def open(self):
        if NT or self.remote:  # open COM on windows, open socket on remote
            if not self.port.isOpen():
                self.port.open()

    def closent(self):
        if NT or self.remote:
            if not self.skip_close:
                self.port.close()

    def query(self, str, wait=0.05, attempts=5):
        self.open()
        self.skip_close = True
        self.write(str)
        time.sleep(wait)
        self.res = self.readline()
        counter = 0
        while len(self.res) == 0:
            if counter > attempts:
                break
            # self.write(str)
            self.res = self.port.readline()
            print(
                "trying to read again in query:%s %s" % (repr(str), repr(self.res))
            )
            counter += 1
        #print 'prologix query:',repr(self.res)
        self.skip_close = False
        self.closent()
        return self.res

    def write(self, str):
        self.open()
        # print self.addr, str
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("%s\n" % str).encode())
        # print "trying to write: %s"%str
        self.closent()

    def read(self, length=512):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++read eoi\n").encode())
        self.res = self.port.read(length)
        self.closent()
        print("Recieved " + self.res.decode())
        return self.res

    def readline(self):
        self.open()
        self.port.write(('++addr %d\n' % self.addr).encode())
        self.port.write(('++read eoi\n').encode())
        time.sleep(0.1)
        self.res = self.port.readline()
        self.closent()
        return self.res

    def readbinary(self, length=512):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++read eoi\n").encode())
        self.res = self.port.read(length)
        # self.closent()
        return self.res

    def read2(self):
        # print 'read2'
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++read eoi\n").encode())
        fail = 0
        while True:
            self.res = self.port.read(length)
            if len(self.res) > 0:
                break
            fail += 1
            if fail > 2:
                break
        self.closent()
        return self.res

    def clear(self):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++clr\n").encode())
        self.closent()

    def rsp(self):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++spoll\n").encode())
        try:
            self.spb = int(self.port.read(100).strip())
        except:
            print("Error reading serial poll byte")
            self.spb = -1
        self.closent()
        return self.spb

    def trigger(self):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++trg\n").encode())
        self.closent()

    def loc(self):
        self.open()
        self.port.write(("++addr %d\n" % self.addr).encode())
        self.port.write(("++loc\n").encode())
        self.closent()

    def close(self):
        # if not self.port.isOpen():
        self.open()
        self.loc()
        self.closent()

    def config(self):
        self.open()
        self.port.write(("++auto\n").encode())
        print("auto: %d" % int(self.port.read(10)))
        self.closent()
