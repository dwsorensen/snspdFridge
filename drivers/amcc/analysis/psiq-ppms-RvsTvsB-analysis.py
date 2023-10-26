#%%
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import datetime

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

# Import the .dat file from the PPMS
fn = r'C:\Users\anm16\Downloads\PsiQ_RvsTvsB.dat'
df = pd.read_csv(fn, skiprows=17)


# Setup data
df['Field (T)'] = np.round(df['Magnetic Field (Oe)']/1e4)

# Get 50% resistance mark
R = np.array(df['Channel 1 Resistance'])
Rmin = np.median(np.sort(R)[:50])
Rmax = np.median(np.sort(R)[-50:])
R50 = (Rmin+Rmax)/2


# Iterate through each field setting and extract & plot
fig,axs = plt.subplots(1,2,figsize=(10,5))
Tc_list = []
B_list = []
for B,df2 in df.groupby('Field (T)'):
    T = np.array(df2[ 'Temperature (K)'])
    R = np.array(df2['Channel 1 Resistance'])
    idx,val = find_nearest(R, R50)
    Tc = T[idx]
    Tc_list.append(Tc)
    B_list.append(B)
    axs[0].plot(T,R)
    axs[0].plot(Tc,R50,'*')
    if B == 0:
        Tc0 = Tc

# Analyze slope from Zhang 2016 https://doi.org/10.1103/PhysRevB.94.174509
weights = B_list # Apply weighting to avoid fitting near 0 field
slope, offset = np.polyfit(Tc_list, B_list, 1, w = B_list)
xfit = np.linspace(min(Tc_list),max(Tc_list), 100)
yfit = slope*xfit + offset

# Plot slope
axs[1].plot(Tc_list, B_list, '^-', label = 'data')
axs[1].plot(xfit,yfit,'r--', label = f'fit')
axs[1].legend()

# Labeling
axs[0].set_xlabel('Temperature (K)')
axs[0].set_ylabel('Resistance (Ohms)')
axs[1].set_ylabel('Field (T)')
axs[1].set_xlabel('Tc (K)')
plt.tight_layout()
fig.suptitle('Parameter extraction using Tc = 50% resistance')
fig.subplots_adjust(top=0.9) # Add supertitle over all subplots

# Save figure
filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.png')
plt.savefig('C:\\Users\\anm16\Downloads\\' + filename)


# Print our derived values
print(f'Slope dB_c2/dT @ Tc = {slope:0.3f} T/K')
print(f'Zero field Tc0 measurement = {Tc0:0.2f} K')
B_c2_0 = -0.69*slope*Tc0
print(f'Critical field B_c2(0) (WHH approximation) = {B_c2_0:0.3f} T')
print(f'Energy gap Δ(0) = {2.08*1.38e-23*Tc0/1.6e-19*1000:0.3f} meV')
print(f'GL coherence length ξ(0) = {np.sqrt(2.07e-15/(2*np.pi*B_c2_0))*1e9:0.2f} nm')
print(f'Electron diffusion constant D_e = {-4*1.38e-23/(np.pi*1.6e-19*slope)*1e4:0.3f} cm^2/s')
