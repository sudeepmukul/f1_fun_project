import pandas as pd
import fastf1
from sklearn.ensemble import RandomForestRegressor

# load data
session = fastf1.get_session(2024, 'Bahrain', 'R')
session.load()

laps = session.laps

data = []

for drv in session.drivers:
    drv_laps = laps.pick_drivers(drv)

    if drv_laps.empty:
        continue

    avg_lap = drv_laps['LapTime'].dt.total_seconds().mean()
    best_lap = drv_laps['LapTime'].dt.total_seconds().min()

    result = session.results[session.results['DriverNumber'] == drv]['Position'].values

    if len(result) == 0:
        continue

    data.append({
        "driver": drv,
        "avg_lap": avg_lap,
        "best_lap": best_lap,
        "result": int(result[0])
    })

df = pd.DataFrame(data)

X = df[['avg_lap', 'best_lap']]
y = df['result']

model = RandomForestRegressor()
model.fit(X, y)

print("Model trained")