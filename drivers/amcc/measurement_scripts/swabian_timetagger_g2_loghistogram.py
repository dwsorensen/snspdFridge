
# from amcc.instruments.srs_sim928 import SIM928
import time 
import numpy as np
import datetime
import pandas as pd

from TimeTagger import createTimeTagger
from TimeTagger import HistogramLogBins, TimeTagStream


# create a timetagger instance
try:
    tagger.reset()
except:
    pass
time.sleep(1)
tagger = createTimeTagger()

#%%

trigger_level1 = 0.04
dead_time_ps = int(round(200e-9*1e12))
measurement_time = 1


# Negative channel numbers indicated "falling" edge
tagger.setTriggerLevel(1, trigger_level1)
tagger.setDeadtime(1, dead_time_ps)

    
# Create histogram measurement
hist = HistogramLogBins(tagger,
                               click_channel = 1, 
                               start_channel = 1, 
                               exp_start = np.log10(100e-9), 
                               exp_stop = np.log10(1e-3), 
                               n_bins = 100)

# Get raw timetags
stream = TimeTagStream(tagger, n_max_events = 100e6, channels = [1])

# Start measurements
hist.startFor(measurement_time*1e12)
stream.startFor(measurement_time*1e12)
hist.waitUntilFinished(timeout=-1)
stream.waitUntilFinished(timeout=-1)


# Get raw timetags
buffer = stream.getData()
timestamps = buffer.getTimestamps()
channels = buffer.getChannels()
print(f'Collect {len(timestamps)} counts')

# Get histogram
g2_counts = hist.getDataNormalizedG2()
g2_bin_edges = hist.getBinEdges()/1e12


timestr = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

# Plot
plt.figure()
plt.semilogx( g2_bin_edges[:-1], g2_counts)
plt.xlabel('Time (s)')
plt.ylabel('g2')
plt.savefig(f'{timestr} g2 histogram.png')

# Save data
df_timetags = pd.DataFrame({'timestamps':timestamps})
df_timetags.to_parquet(f'{timestr} g2 timetags.parquet', compression = 'gzip')
df_hist = pd.DataFrame({'g2_counts':g2_counts, 'g2_bin_edges':g2_bin_edges[1:]})
df_hist.to_parquet(f'{timestr} g2 histogram.parquet', compression = 'gzip')