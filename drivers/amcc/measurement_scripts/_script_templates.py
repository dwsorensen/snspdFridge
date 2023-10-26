# Run add_path.py first
from amcc.instruments.rigol_dg5000 import RigolDG5000
from amcc.instruments.lecroy_620zi import LeCroy620Zi
from amcc.instruments.switchino import Switchino
from amcc.instruments.tektronix_awg610 import TektronixAWG610
from amcc.instruments.srs_sim970 import SIM970
from amcc.instruments.srs_sim928 import SIM928

from tqdm import tqdm # Requires "colorama" package also on Windows to display properly
import numpy as np
import pandas as pd
import numpy as np
import time

# =============================================================================
# Connect instruments
# =============================================================================
lecroy = LeCroy620Zi("TCPIP::%s::INSTR" % '192.168.1.100')
# awg = RigolDG5000('USB0::0x1AB1::0x0640::DG5T171200124::INSTR')
# dmm = SIM970('GPIB0::4', sim900port = 7)
switch = Switchino('COM7')

# =============================================================================
# Setup Lecroy for high-speed amplified data
# =============================================================================
lecroy.reset()
time.sleep(5)
lecroy.set_trigger(source = 'C1', volt_level = 0.1, slope = 'Positive')
lecroy.set_trigger_mode(trigger_mode = 'Normal')
lecroy.set_coupling(channel = 'C1', coupling = 'DC50')
lecroy.set_coupling(channel = 'C2', coupling = 'DC50')
lecroy.set_horizontal_scale(1e-6)
lecroy.set_vertical_scale(10e-3)
lecroy.set_parameter(parameter = 'P1', param_engine = 'Delay', source1 = 'C1', source2 = None)
lecroy.setup_math_histogram(math_channel = 'F2', source = 'P1', num_values = 300)
lecroy.set_parameter(parameter = 'P5', param_engine = 'HistogramSdev', source1 = 'F2', source2 = None)
lecroy.set_parameter(parameter = 'P6', param_engine = 'HistogramMedian', source1 = 'F2', source2 = None)