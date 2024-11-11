from uldaq import get_daq_device_inventory, DaqDevice, InterfaceType, AOutFlag
import time

class dev:
    def __init__ (self,boardIndex = 0):
        self.interface_type = InterfaceType.ANY
        self.devices = get_daq_device_inventory(self.interface_type)
        self.daq_device = DaqDevice(self.devices[boardIndex])
        self.ao_device = self.daq_device.get_ao_device()
        self.daq_device.connect(connection_code=0)
        self.ao_info = self.ao_device.get_info()
        self.output_range = self.ao_info.get_ranges()[0]

    def set_volt(self,channel,value):
        print("MC setting channel %i to %.3f"%(channel, value))
        self.ao_device.a_out(channel,self.output_range,AOutFlag.DEFAULT,float(value))


if __name__ == "__main__":
    dev = dev()
    dev.set_volt(6,1)
    input("Press <enter> to go back to 0")
    dev.set_volt(6,0)