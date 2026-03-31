import fastf1
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os

# ---------------- SETUP ----------------
os.makedirs("cache", exist_ok=True)
fastf1.Cache.enable_cache("cache")

# ---------------- RACES TO LOAD ----------------
races = [
    'Bahrain', 'Saudi Arabia', 'Australia',
    'Japan', 'China', 'Miami', 'Imola', 'Monaco'
]

YEAR = 2024

data = []

# ---------------- DATA COLLECTION ----------------
for race in races:
    print(f"\nLoading {race}...")

    try:
        session = fastf1.get_session(YEAR, race, 'R')
        session.load()

        laps = session.laps

        for drv in session.drivers:

            drv_laps = laps.pick_drivers(drv)

            if drv_laps.empty:
                continue

            # ---------------- FEATURES ----------------
            avg_lap = drv_laps['LapTime'].dt.total_seconds().mean()
            best_lap = drv_laps['LapTime'].dt.total_seconds().min()

            # Pit stops
            pit_count = drv_laps['PitInTime'].count()

            # ---------------- TARGET ----------------
            result_row = session.results[
                session.results['DriverNumber'] == drv
            ]

            if result_row.empty:
                continue

            position = int(result_row['Position'].values[0])

            # Grid position
            grid = result_row['GridPosition'].values[0]

            data.append({
                "driver": drv,
                "race": race,
                "avg_lap": avg_lap,
                "best_lap": best_lap,
                "pit_count": pit_count,
                "grid": grid,
                "result": position
            })

    except Exception as e:
        print(f"Skipping {race} due to error: {e}")

# ---------------- CREATE DATAFRAME ----------------
df = pd.DataFrame(data)

print("\nDataset Preview:")
print(df.head())

# ---------------- CLEAN DATA ----------------
df = df.dropna()

# ---------------- FEATURES & TARGET ----------------
X = df[['avg_lap', 'best_lap', 'pit_count', 'grid']]
y = df['result']

# ---------------- TRAIN MODEL ----------------
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X, y)

print("\n✅ Model trained successfully!")

# ---------------- EVALUATION ----------------
preds = model.predict(X)

df['predicted'] = preds

print("\nSample Predictions:")
print(df[['race', 'driver', 'result', 'predicted']].head(20))

# ---------------- WINNER PREDICTION FUNCTION ----------------
def predict_race_winner(race_name):

    print(f"\nPredicting for {race_name}...")

    session = fastf1.get_session(YEAR, race_name, 'R')
    session.load()

    laps = session.laps

    race_data = []

    for drv in session.drivers:

        drv_laps = laps.pick_drivers(drv)

        if drv_laps.empty:
            continue

        avg_lap = drv_laps['LapTime'].dt.total_seconds().mean()
        best_lap = drv_laps['LapTime'].dt.total_seconds().min()
        pit_count = drv_laps['PitInTime'].count()

        result_row = session.results[
            session.results['DriverNumber'] == drv
        ]

        if result_row.empty:
            continue

        grid = result_row['GridPosition'].values[0]

        race_data.append({
            "driver": drv,
            "avg_lap": avg_lap,
            "best_lap": best_lap,
            "pit_count": pit_count,
            "grid": grid
        })

    race_df = pd.DataFrame(race_data)

    # Predict
    race_df['predicted'] = model.predict(
        race_df[['avg_lap', 'best_lap', 'pit_count', 'grid']]
    )

    race_df = race_df.sort_values('predicted')

    print("\n🏁 Predicted Standings:")
    print(race_df[['driver', 'predicted']])

    winner = race_df.iloc[0]['driver']

    print(f"\n🔥 Predicted Winner: {winner}")

    return race_df


# ---------------- TEST PREDICTION ----------------
predict_race_winner("Monaco")