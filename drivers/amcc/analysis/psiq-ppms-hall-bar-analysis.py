#%%
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import datetime

# Import the file
fn = r'C:\Users\anm16\Downloads\ETO_basic__00001.dat'
df = pd.read_csv(fn, skiprows=16)

# Grab the data
T = np.round(df['Temperature (K)'].median())
I = df['AC Current Ch2 (mA)'].median()*1e-3
R = df['Resistance Ch2 (Ohms)']
V_hall = I*R
B = df['Field (Oe)']/10000

# Extract the slope and carrier density using V_hall = I_x*B_z/(n*t*e)
# Since we don't know the thickness of the films, we'll report the n*t
# which is the (carrier density)*(film thickness)
slope, offset = np.polyfit(B, V_hall, 1)
B_fit = np.linspace(min(B),max(B), 100)
V_hall_fit = slope*B_fit + offset
fig = plt.figure(); fig.set_size_inches([8,6])

# Plot everything
plt.plot(B,V_hall, label = 'data')
plt.plot(B_fit,V_hall_fit,'r--', label = f'fit')
plt.xlabel('Field (T)')
plt.ylabel('Hall voltage (V)')
plt.title(f'Hall bar carrier density extraction @ {T}K\n' + 
          f'slope={slope:0.2e} V/T\n' + 
          f'n*t={I/(slope*1.6e-19):0.2e} e/m^2')
plt.legend()
plt.tight_layout()
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.png')
plt.savefig('C:\\Users\\anm16\Downloads\\' + filename)