import fastf1
import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

# Load session
session = fastf1.get_session(2024, 'Bahrain', 'Q')
session.load()

# Get fastest lap
lap = session.laps.pick_drivers(['HAM']).pick_fastest()
# Get telemetry
tel = lap.get_telemetry()

x = tel['X'].to_numpy()
y = tel['Y'].to_numpy()
speed = tel['Speed'].to_numpy()

# Normalize speed for coloring
speed_norm = (speed - speed.min()) / (speed.max() - speed.min())

# Plot track map
plt.figure(figsize=(8, 8))

for i in range(len(x) - 1):
    plt.plot(x[i:i+2], y[i:i+2], color=plt.cm.plasma(speed_norm[i]))

plt.title("Track Speed Heatmap (HAM Fastest Lap)")
plt.axis('off')
plt.show()