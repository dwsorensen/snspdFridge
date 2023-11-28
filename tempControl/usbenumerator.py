import os
from os.path import join

class USBEnumerator(object):
    def __init__(self,devices={}):
        d=dict(devices)
        if len(d)>0:
            for dev, ids in d.iteritems():
                ids['port']=self.find_tty_usb(ids['vendor'],ids['product'])
        self.devices=d

    def find_tty_usb(self,idVendor, idProduct):
        """find_tty_usb('067b', '2302') -> '/dev/ttyUSB0'"""
        # Note: if searching for a lot of pairs, it would be much faster to search
        # for the enitre lot at once instead of going over all the usb devices
        # each time.
        for dnbase in os.listdir('/sys/bus/usb/devices'):
            dn = join('/sys/bus/usb/devices', dnbase)
            if not os.path.exists(join(dn, 'idVendor')):
                continue
            idv = open(join(dn, 'idVendor')).read().strip()
            if idv != idVendor:
                continue
            idp = open(join(dn, 'idProduct')).read().strip()
            if idp != idProduct:
                continue
            for subdir in os.listdir(dn):
                if subdir.startswith(dnbase+':'):
                    for subsubdir in os.listdir(join(dn, subdir)):
                        if subsubdir.startswith('ttyUSB'):
                            return join('/dev', subsubdir)

if __name__ == '__main__':
    u=USBEnumerator()
    devices={}
    # devices['Prologix']={'vendor':'0403','product':'6001'}
    # devices['SerialAdapter']={'vendor':'067b','product':'2303'}
    devices['SerialAdapter']={'vendor':'0403','product':'6001'}
    devices['Prologix']={'vendor':'067b','product':'2303'}
    for dev, ids in devices.iteritems():
        ids['port']=u.find_tty_usb(ids['vendor'],ids['product'])
    print("inside USBEnumerator")
    print(ids)
