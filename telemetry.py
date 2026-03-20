import fastf1
import matplotlib.pyplot as plt
import os

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Bahrain', 'Q')  # Qualifying (better for fastest laps)
session.load()

# Get fastest laps
ver_lap = session.laps.pick_driver('VER').pick_fastest()
ham_lap = session.laps.pick_driver('HAM').pick_fastest()

# Get telemetry
ver_tel = ver_lap.get_telemetry()
ham_tel = ham_lap.get_telemetry()

# Plot speed vs distance
plt.plot(ver_tel['Distance'], ver_tel['Speed'], label='VER')
plt.plot(ham_tel['Distance'], ham_tel['Speed'], label='HAM')

plt.xlabel("Distance")
plt.ylabel("Speed")
plt.title("Speed vs Distance (Telemetry)")
plt.legend()
plt.show()