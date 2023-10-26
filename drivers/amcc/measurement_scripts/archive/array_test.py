##########################################
# Simple Isw test
###########################################

SRS1.set_voltage(1)
SRS2.set_voltage(1)
SRS3.set_voltage(1)
SRS4.set_voltage(1)

SRS1.set_output(True)
SRS2.set_output(True)
SRS3.set_output(False)
SRS4.set_output(False)




#parameters
V_source_i = 0e-6*R5_srs
V_source_f = 40e-6*R5_srs
step = 1e-6*R5_srs

#here we go
V_source = np.arange(V_source_i,V_source_f, step)
V_device = []
I_device = [] 
SRS5.set_voltage(V_source_i)
SRS5.set_output(True)
k.setup_read_volt()
k.read_voltage()
sleep(1)

for v in V_source:
    SRS5.set_voltage(v)
    sleep(0.1)
    vread = k.read_voltage()
    iread = v/R5_srs
    # print('V=%.4f V, I=%.2f uA, R =%.2f' %(vread, iread*1e6, vread/iread))
    V_device.append(vread)
    I_device.append(iread)

plt.plot(np.array(V_device), np.array(I_device)*1e6, '-o')
plt.xlabel('Voltage (V)')
plt.ylabel('Current (uA)')
plt.title('V-I Curve')

print(('Ic = %.2f uA' %(np.max(I_device)*1e6)))
plt.show()