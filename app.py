import fastf1
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os

# ---------------- SETUP ----------------
os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

st.set_page_config(layout="wide")

st.title("🏎️ F1 Live Race Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    session = fastf1.get_session(2024, 'Bahrain', 'R')
    session.load()
    return session

session = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Controls")

lap_number = st.sidebar.slider("Select Lap", 1, int(session.laps['LapNumber'].max()), 10)

selected_driver = st.sidebar.selectbox("Select Driver", session.drivers)

# ---------------- GET TRACK ----------------
lap = session.laps.pick_drivers([session.drivers[0]]).pick_fastest()
tel = lap.get_telemetry()

track_x = tel['X'].to_numpy()
track_y = tel['Y'].to_numpy()

# ---------------- GET POSITIONS ----------------
pos_data = session.pos_data

positions = {}

for driver in session.drivers:
    drv_data = pos_data[driver]
    drv_lap = session.laps.pick_drivers([driver])
    drv_lap = drv_lap[drv_lap['LapNumber'] == lap_number]

    if not drv_lap.empty:
        time = drv_lap.iloc[0]['Time']
        drv_data = drv_data[drv_data['Time'] <= time]

        if not drv_data.empty:
            latest = drv_data.iloc[-1]
            positions[driver] = (latest['X'], latest['Y'])

# ---------------- FIGURE ----------------
driver_map = {}

for drv in session.drivers:
    info = session.get_driver(drv)
    driver_map[drv] = info['Abbreviation']
fig, ax = plt.subplots(figsize=(6, 6))

# Background styling
fig.patch.set_facecolor('#0b0f1a')
ax.set_facecolor('#0b0f1a')

# Draw track (with glow)
ax.plot(track_x, track_y, color='white', linewidth=5, alpha=0.2)
ax.plot(track_x, track_y, color='gray', linewidth=2)

# Plot drivers
team_colors = {
    # Red Bull
    'VER': '#1E41FF',
    'PER': '#1E41FF',

    # Mercedes
    'HAM': '#00D2BE',
    'RUS': '#00D2BE',

    # Ferrari
    'LEC': '#DC0000',
    'SAI': '#DC0000',

    # McLaren
    'NOR': '#FF8700',
    'PIA': '#FF8700',

    # Aston Martin
    'ALO': '#006F62',
    'STR': '#006F62',

    # Alpine
    'OCO': '#0090FF',
    'GAS': '#0090FF',

    # Williams
    'ALB': '#005AFF',
    'SAR': '#005AFF',

    # AlphaTauri / RB
    'TSU': '#2B4562',
    'RIC': '#2B4562',

    # Haas
    'MAG': '#FFFFFF',
    'HUL': '#FFFFFF',

    # Kick Sauber
    'BOT': '#00FF00',
    'ZHO': '#00FF00',
}

for drv, (x, y) in positions.items():
    abbr = driver_map[drv]   # convert '44' → 'HAM'
    color = team_colors.get(abbr, 'white')

    size = 120 if drv == selected_driver else 60

    ax.scatter(x, y, s=size, color=color, edgecolors='black')
    ax.scatter(x, y, s=size, color=color, edgecolors='black', linewidth=1.5)

ax.axis('off')

# ---------------- LAYOUT ----------------
col1, col2, col3 = st.columns([1, 2, 1])

# LEFT PANEL (Driver Info)
with col1:
    st.subheader(f"Driver: {selected_driver}")

    drv_laps = session.laps.pick_drivers([selected_driver]).pick_quicklaps()

    if not drv_laps.empty:
        last_lap = drv_laps.iloc[-1]
        st.write(f"Lap Time: {last_lap['LapTime']}")
        st.write(f"Tyre: {last_lap['Compound']}")

# CENTER (TRACK)
with col2:
    st.pyplot(fig)

# RIGHT PANEL (Leaderboard)
with col3:
    st.subheader("Leaderboard")

    results = session.results.sort_values('Position')

    for i, row in results.iterrows():
        st.write(f"{int(row['Position'])}. {row['Abbreviation']}")