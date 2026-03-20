import fastf1
import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Bahrain', 'Q')
session.load()

# Get fastest laps
ver = session.laps.pick_drivers(['VER']).pick_fastest()
ham = session.laps.pick_drivers(['HAM']).pick_fastest()

# Get telemetry
ver_tel = ver.get_telemetry()
ham_tel = ham.get_telemetry()

# Convert to numpy
x1 = ver_tel['X'].to_numpy()
y1 = ver_tel['Y'].to_numpy()
s1 = ver_tel['Speed'].to_numpy()

x2 = ham_tel['X'].to_numpy()
y2 = ham_tel['Y'].to_numpy()
s2 = ham_tel['Speed'].to_numpy()

# Normalize speeds separately
s1_norm = (s1 - s1.min()) / (s1.max() - s1.min())
s2_norm = (s2 - s2.min()) / (s2.max() - s2.min())

fig, axs = plt.subplots(1, 2, figsize=(14, 6))

# ---------------- VER ----------------
for i in range(len(x1) - 1):
    axs[0].plot(
        x1[i:i+2],
        y1[i:i+2],
        color=plt.cm.jet(s1_norm[i]),
        linewidth=2
    )

axs[0].set_title("VER Speed Heatmap")
axs[0].axis('off')


# ---------------- HAM ----------------
for i in range(len(x2) - 1):
    axs[1].plot(
        x2[i:i+2],
        y2[i:i+2],
        color=plt.cm.jet(s2_norm[i]),
        linewidth=2
    )

axs[1].set_title("HAM Speed Heatmap")
axs[1].axis('off')


plt.tight_layout()
plt.show()