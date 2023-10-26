# Ic measurement code
# Run add_path.py first
from measurement.ic_sweep import *
from useful_functions.save_data_vs_param import *


### Instrument configuration
lecroy_ip = 'touchlab1.mit.edu'
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % lecroy_ip)


traces_x = []
traces_y = []
time_start = time.time()
for n in range(100):
    x,y = lecroy.get_single_trace(channel = 'C1')
    traces_x.append(x)
    traces_y.append(y)
    # plt.plot(x,y)
# plt.show()
print(time.time() - time_start)
