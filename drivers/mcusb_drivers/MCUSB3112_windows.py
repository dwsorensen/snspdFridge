from mcculw import ul
from mcculw.device_info import DaqDeviceInfo
from mcculw.enums import InterfaceType
import time

def config_first_detected_device(board_num, dev_id_list=None):
    """Adds the first available device to the UL.  If a types_list is specified,
    the first available device in the types list will be add to the UL.

    Parameters
    ----------
    board_num : int
        The board number to assign to the board when configuring the device.

    dev_id_list : list[int], optional
        A list of product IDs used to filter the results. Default is None.
        See UL documentation for device IDs.
    """
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise Exception('Error: No DAQ devices found')

    device = devices[0]
    if dev_id_list:
        device = next((device for device in devices
                       if device.product_id in dev_id_list), None)
        if not device:
            err_str = 'Error: No DAQ device found in device ID list: '
            err_str += ','.join(str(dev_id) for dev_id in dev_id_list)
            raise Exception(err_str)
    # Add the first DAQ device to the UL with the specified board number
    ul.create_daq_device(board_num, device)

class dev:
    def __init__ (self,boardNum = 0):
        self.boardNum = boardNum
        config_first_detected_device(boardNum,[])
        self.daq_dev_info = DaqDeviceInfo(boardNum)
        self.ai_info = self.daq_dev_info.get_ai_info()
        self.ao_info = self.daq_dev_info.get_ao_info()

    def setVolt(self,channel,value):
        print("MC setting channel %i to %.3f"%(channel, value))
        ao_range = self.ao_info.supported_ranges[0]
        ul.v_out(self.boardNum,channel,ao_range, value)

    def getVolt(self,channel):
        print(self.ai_info)
        ai_range = self.ai_info.supported_ranges[0]
        value = ul.v_in(self.boardNum,channel,ai_range)
        return value

if __name__ == "__main__":
    dev = dev()
    dev.setVolt(6,0)
    print(str(dev.getVolt(6)))
    dev.setVolt(6,1)
    print(str(dev.getVolt(6)))