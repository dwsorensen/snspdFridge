import random

class Sensor(object):
    def __init__(self, devicename=None, params = None):
        self.devicename = devicename
        self.params = params
        super(Sensor, self).__init__()

        self.sensorIDList = ['sensor1', 'sensor2'] # Array of sensor names (key)
        self.sensorDetails = [0 , 1,2] # Array of the port/channel/etc the sensors are found on
        self.sensorDictionary = dict(zip(self.sensorIDList, self.sensorDetails))
        self.SensorIDListReadable = []
        self.SensorDictionaryReadable = []
        self.initialize()

    # Function to initalize and connect to the sensor device
    def initialize(self):
        pass

    # Returns the current value of a given sensor
    def get_sensor_value(self, sensorID):
        # Return a dictionary {sensorID: value} item containing the value of the requested sensor
        pass

    # Returns the values of all the sensors
    def get_all_sensor_values(self):
        # Return a dictionary {sensorID1: value1, sensorID2, value2 ...} of all sensor values
        # pass
        values = {self.sensorIDList[0]: random.random(), self.sensorIDList[1]: random.random()}
        # print str(values)
        return values


    # Returns the list of sensor IDs
    def get_sensorIDs(self):
        return self.sensorIDList

    # Returns the list of sensor IDs that can be read
    def get_sensorIDsReadable(self):
        return self.SensorIDListReadable

    # Sets the value of a given sensor
    def set_sensorIDValue(self, sensorID, value):
        pass

    # Raw message to write directly to the controller
    def writeRaw(self, msgToWrite):
        pass

    # shutdown the connection with the device. Release it.
    def shutdown(self):
        pass
