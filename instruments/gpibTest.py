import serial
import time

port = serial.Serial("/dev/ttyUSB0",115200,timeout = 1)

port.write("++mode 1\n".encode())
port.write("++auto 0\n".encode())
port.write("++addr 6\n".encode())
port.write("++eoi 1\n".encode())
port.write("C6\n".encode())
# addr = port.readline()
# print("Address: " + addr.decode())
# port.write("++mode\n".encode()) 
# mode = port.readline()
# print("MODE: "+ mode.decode())

port.write("C?\n".encode())
port.write("++read eoi\n".encode())
response = port.readline()
print(response)

#print("Resetting")
#port.write("++rst\n".encode())
#time.sleep(10)
#print("Reset complete")
#port.close()






"""
port.write("++eos 3\n".encode())
port.write("*IDN?\n".encode())
port.write("++read eoi\n".encode())
time.sleep(0.05)
response = port.readline()
print(response)
port.close()
"""