from usbenumerator import USBEnumerator
from Sensor import Sensor
import string
import serial
import sys
from CTC100 import CTC


class CTC100sensor(Sensor, CTC):
    """
    Interface with the CTC100 sensor. This extends the general Sensor class.
    """

    # Initialize the CTC100 device
    def initialize(self):
        self.devicename = "CTC100"

        # serialport = serial.Serial('/dev/ttyACM0',9600,timeout=1)
        # serialport = serial.Serial('/dev/ttyUSB1',9600,timeout=1)
        #serialport.write('++auto 0\n')
        # self.dev = serialport

        print ("identifier string : " + str(self.write('*IDN?')))
        
        self.channel_names = self.get_names().lower().split(str.encode(', '))
        
        self.SensorIDListReadable = self.get_names().lower().split(str.encode(', '))
        
        print (self.SensorIDListReadable)

    def get_sensorIDs(self):
        return self.channel_names
        
    def get_sensorIDsReadable(self):
        return self.SensorIDListReadable

    # Returns the current value of a given channel from the CTC100
    def get_sensor_value(self, channel_name):
        # Return a dictionary {channel_name: value} item containing the value of the requested sensor
        return self.write_read(channel_name)


    # Returns the values of all the sensors
    def get_all_sensor_values(self):
        # Return a dictionary {sensorID1: value1, sensorID2, value2 ...} of all sensor values
        return self.get_all()

#    # Write directly to the sensor
#    def write(self, msgin):
#        msgin += '\r\n'
#        ctc = self.ctc
#        ctc.write(msgin)
#        msg = ctc.readline()
#        # print "result of query: ", msg
#        #msg = string.replace(msg,',','\t')
#        #msg = string.replace(msg,'\r','')
#        #msg = string.replace(msg,'\n','')
#        #msg = msg.split('\t')
#        msg.strip('\n').strip('\r')
#        msgout = [x.strip(' ') for x in msg.split(',')]
#        if len(msgout) < 2:
#            return msgout[0]
#        else:
#            return msgout

    # Raw message to write directly to the controller
#    def writeRaw(self, msgToWrite):
#        msgToWrite += '\r\n'
#        ctc = self.ctc
#        ctc.write(msgToWrite)
#        msg = ctc.readline()
#        # print "result of query: ", msg
#        #msg = string.replace(msg,',','\t')
#        #msg = string.replace(msg,'\r','')
#        #msg = string.replace(msg,'\n','')
#        #msg = msg.split('\t')
#        msg.strip('\n').strip('\r')
#        return msg

    def writeRaw(self, msg):
        '''Write a message to the temperature controller and return response'''
        self.dev.write(mystr.encode(sstr(msg)+'\r\n'))
        # sys.stdout.write('working')
#        return 'working!!'
        return self.dev.readline().strip(str.encode('\r\n'))

    def write(self, msg):        
        '''Write a message to the temperature controller and return response'''
        self.dev.write(str.encode(str(msg)+'\r\n'))
        msgout = self.dev.readline().strip(str.encode('\r\n'))
        #print "msgout from write : ", msgout 
        if len(msgout) < 2:
            return msgout[0]
        else:
            return msgout

    # Close the connection with the device
    def shutdown(self):
        self.ctc.close()

if __name__=='__main__':
    ctc = CTC()
    ctc.write('IDN*?')
    print (ctc.read())
    print (ctc.get_sensorIDsReadable())
