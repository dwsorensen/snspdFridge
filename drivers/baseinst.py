# from builtins import object
import time


class dev(object):
    def identify(self):
        msg = "*IDN?"
        retmsg = self.meter.query(msg).strip()
        if len(retmsg) == 0:
            retmsg = "Device does not support *IDN? command"
        return retmsg

    def writeconfig(self, f):
        msg = self.identify()
        f.write("# %s\n" % msg)
        f.flush()

    def close(self):
        """End communication with the DMM"""
        self.meter.loc()
