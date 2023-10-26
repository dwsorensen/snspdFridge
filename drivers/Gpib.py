from __future__ import print_function
import os

print('Trying to determine gpib interface being used...')
if 'nt' in os.name:
    try:
      import Gpib_NI
      print('Found NI Gpib board')
    except:
        # print 'could not import real GPIB_NI, checking for prologix'
        import Gpibfake as Gpib_NI

        pass

try:
    import Gpib_prologix as Gpib_prologix_nt_ver2
    # import Gpib_prologix as Gpib_prologix_nt_ver2

    print("Found Prologix interface")
except Exception as e:
    print("could not import Gpib_Prologix, importing fake gpib class")
    print("Exception: " + str(e))
    import Gpibfake as Gpib_prologix

    pass



def flt(s):
    try:
        # float(s)
        return float(s)
    except ValueError:
        return float("NaN")


def Gpib(name, port=""):
    return Gpib_prologix_nt_ver2.Gpib(name, port)


def Gpib2(addr, serialport):
    p = None
    if type(addr) == list:
        p = addr  # should I make a deepcopy here?  Not sure, will not for now
        for item in p:
            if "value" in item:
                name = item["name"]
                value = item["value"]
                if "ddress" in name:
                    gpibaddress = value
                elif "GPIB interface name" in name:
                    portname = value
                    serialport = portname
                elif "GPIB interface type" in name:
                    gpibtype = value

        print(
            "config from list addr %d, intf name %s, type %d"
            % (gpibaddress, portname, gpibtype)
        )
        addr = gpibaddress
        print("GPIB type: " + gpibtype)
        if gpibtype == 2:  # this is prologix
            meter = Gpib(addr, port=portname)
            serialport = portname
        elif gpibtype == 1:  # this is NI
            meter = Gpib("dev%d" % addr)
            serialport = "gpib0"
        else:  # pretend it is an NI board
            meter = Gpib("dev%d" % addr)
            serialport = "gpib0"
    meter = Gpib(addr, serialport)
    addr = addr
    return meter, addr, serialport, p
