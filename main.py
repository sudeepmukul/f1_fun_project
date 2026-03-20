import fastf1
import matplotlib.pyplot as plt

# Enable cache
fastf1.Cache.enable_cache('cache')

# Load session
session = fastf1.get_session(2024, 'Bahrain', 'R')  # use 2024 (stable data)
session.load()

# Pick 2 drivers
laps = session.laps.pick_drivers(['VER', 'HAM'])
laps = laps.pick_quicklaps()

# Plot lap times
for driver in laps['Driver'].unique():
    driver_laps = laps[laps['Driver'] == driver]
    plt.plot(driver_laps['LapNumber'], driver_laps['LapTime'], label=driver)

plt.xlabel("Lap Number")
plt.ylabel("Lap Time")
plt.title("Lap Time Comparison")
plt.legend()
plt.show()