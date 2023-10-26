import numpy as np
import time
import pandas as pd
from numba import njit

@njit
def filter_timestamps(timestamps, channels, tags_per_side = 5, trigger_channel = 1):
    """ Takes an array of timestamps and channesl from a Swabian timetagger,
    and looks for tags coming from trigger_channel.  When it finds a tag from
    trigger_channel, grabs `tags_per_side` timetags before and after it and saves them """
    new_timestamps = []
    new_channels = []
    tags_per_side = 5
    # FIXME can accidentally create duplicates, make sure to filter them
    # by using a mask that sets any timetags to keep as "1"
    for n in range(tags_per_side+1,len(timestamps)-tags_per_side-1):
        if channels[n] == trigger_channel:
            new_timestamps.extend(timestamps[n-tags_per_side:n+tags_per_side])
            new_channels.extend(channels[n-tags_per_side:n+tags_per_side])
    return new_timestamps, new_channels

#x,y = filter_timestamps(timestamps, channels, trigger_channel = 1)

def read_and_filter_timetags_from_stream(stream, trigger_channel, duration):
    # stream.getData() # Throw away any already-present tags
    stream.clear()
    filtered_timestamps = []
    filtered_channels = []
    while stream.getCaptureDuration()/1e12 < duration:
        time.sleep(0.1)
        buffer = stream.getData()
        timestamps = buffer.getTimestamps()
        channels = buffer.getChannels()
        new_timestamps, new_channels = filter_timestamps(timestamps, channels, trigger_channel = trigger_channel)
        filtered_timestamps.append(new_timestamps)
        filtered_channels.append(new_channels)
        # print(f'Buffer size before: {len(timestamps)} / After: {len(new_timestamps)}')
    # stream.stop()
    return np.concatenate(filtered_timestamps), np.concatenate(filtered_channels)

# x,y = read_and_filter_timetags_from_stream(stream, trigger_channel = 1, duration = 2)
# stream = TimeTagStream(tagger, n_max_events=int(100e6), channels = channels_to_record)

@njit
def find_coincidences(
        timestamps : np.ndarray,
        channels : np.ndarray,
        coincidence_channels : tuple,
        coincidence_window,
        coincidence_buffer,
    ):
    """ Scans through an array of timestamps & channels, and creates a list
    of times/channels of coincidences.  A coincidence is defined as all of the
    `coincidence_channels` appearing exactly once within a time period of of
    `coincidence_window` with no timetags within `coincidence_buffer` time
    on either side of those N tags.

    If  `coincidence_buffer == 0`, a single timetag can be used in
    multiple coincidences.  See here, for 3-fold coincidences
    where a set of 4 timetags has 2 coincidences (1-3-2 and 3-2-1)
    ------1-1-3-2--3--2---3----1---3-1-2-------1-3-2-1-----------> time
            \___/                  \___/       \_\_/_/ 
             YES           NO       YES        YES YES

    If we add a `coincidence_buffer`, the all N timetags must have no other
    timetags within a certain distance from them. Below, this is shown # by 
    only counting coincidences that don't have tags in the  "###" buffers
    ------1-1-3-2--3--2---3----1---3-1-2-------1-3-2-1-----------> time
                                ###\___/###         
             NO            NO       YES          NO
    """

    # Downselect data to only have channels we're interested in and
    # map channel numbers (e.g. [5,9,8,6]) to indices (e.g. [0,1,2,3])
    timestamps_ds = []
    channels_ds = []
    channel_map = {c:n for n,c in enumerate(coincidence_channels)}
    for n, c in enumerate(channels):
        if c in coincidence_channels:
            channels_ds.append(channel_map[c])  
            timestamps_ds.append(timestamps[n])
    channels = np.asarray(channels_ds, dtype = np.int64)
    timestamps = np.asarray(timestamps_ds)
    
    # Iterate through all the timestamps, trying to find coincidences that
    # (1) span less than coincidence_window, and (2) contain all N channels
    num_channels = len(coincidence_channels)
    coincidences = []
    for n, t in enumerate(timestamps[1:-num_channels-1]):
        channels_test = channels[n:n+num_channels]
        tN = timestamps[n+num_channels-1] # Timestamp of Nth timetag
        all_channels = set(channel_map.values())
        tprev = timestamps[n-1]
        tnext = timestamps[n+num_channels]
        is_buffered = (coincidence_buffer==0) or ((t-tprev > coincidence_buffer) and (tnext-tN > coincidence_buffer))
        in_window = (tN-t <= coincidence_window)
        has_all_channels = (set(channels_test) == all_channels)
        # print(f'channels_test = {channels_test} / t = {np.round(t,2)} / tN = {np.round(tN,2)} / tN-t = {np.round(tN-t,2)} / {(tN-t <= coincidence_window) and (set(channels_test) == all_channels)}')
        # print(f'in_window = {in_window} / is_buffered = {is_buffered}  / has_all_channels = {has_all_channels} ')
        if in_window and is_buffered and has_all_channels:
            coincidence_t = timestamps[n:n+num_channels]
            coincidence_c = channels[n:n+num_channels]
            # Sort timestamps so they match the order of coincidence_channels
            idx = np.argsort(coincidence_c) 
            coincidences.append(coincidence_t[idx])
    
    return coincidences

#%%


# coincidence_channels = (1,2,3,4)
# timestamps = [0, 1, 2, 3,   4, 4.1, 4.2, 4.3, 4.4,   9, 10, 11,   12, 12.1, 12.2, 12.3, 12.4,    16, 17, 18, 19]
# channels =   [2, 1, 2, 1,   4,   3,   2,   1,   4,   4,  2,  1,    3,    3,    2,    1,    4,     3,  3,  3, 4,]
# #                           \______________/                      / \   \___________________/
# #                                \______________/                  |
# #                          Overlapping coincidences          nearby tag    Basic coincidence

# coincidences  = find_coincidences(
#         np.array(timestamps),
#         np.array(channels),
#         coincidence_channels,
#         coincidence_window = 0.5,
#         coincidence_buffer = 0.11,
#     )
# print(coincidences)


def fourfold_coincidences_to_xy(
    coincidences,
    bbox = (-np.inf, np.inf, -np.inf, np.inf) # left right bottom top
    ):
    c = coincidences
    xc = c[:,0] - c[:,1]
    yc = c[:,2] - c[:,3]
    sel_x = (bbox[0] < xc) & (xc < bbox[1])
    sel_y = (bbox[2] < yc) & (yc < bbox[3])
    sel = sel_x & sel_y

    return xc[sel], yc[sel]



import numpy as np
from matplotlib import pyplot as plt
from numba import njit

@njit
def windowed_interarrivals(timetags, window = 1.7):
    """ For each tag, compute all interarrival times of any other tags 
    # within a time window of duration window """
    diffs = np.diff(timetags)
    # Find final tag 
    dt = 0
    final_idx = 0
    while dt < window:
        final_idx -= 1
        dt += diffs[final_idx]

    interarrivals = []
    for n, dt in enumerate(diffs[:final_idx+1]):
        m = 0
        while dt <= window:
            interarrivals.append(dt)
            m += 1
            dt += diffs[n+m]
    return interarrivals


def g2_timetags(
    timetags,
    duration = 300000,
    window = 7,
    resolution = 1e-3,
    ):
    """ Given timetags taken over a time period `duration`, computes
    g2(τ) for a range of τ between (0, window) with resolution """
    interarrivals = windowed_interarrivals(timetags, window = window)
    total_counts = len(timetags)
    num_bins = round(window/resolution)
    bin_size = window/num_bins
    bin_edges = np.linspace(0,window,num_bins+1)
    # duration = timetags[-1]-timetags[0]
    counts, bin_edges = np.histogram(interarrivals, bins = bin_edges)
    g2 = counts*duration/total_counts**2/bin_size
    return g2, bin_edges




# # Make a lot of timetags
# num = 10000000
# timetags = np.random.rand(num)*num*0.3
# timetags.sort()

# # Remove any timetags < 0.3, to simulate dead time
# timetags = timetags[:-1][np.diff(timetags)>0.3]



# g2, bin_edges = g2_timetags(
#     timetags,
#     duration = timetags[-1],
#     window = 7,
#     resolution = 10e-3,
#     )
# plt.plot(bin_edges[:-1],g2)

