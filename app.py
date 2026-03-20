import fastf1
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
import time

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

# ---------------- PREP DATA ----------------

# Track (use fastest lap for layout)
lap = session.laps.pick_drivers([session.drivers[0]]).pick_fastest()
tel = lap.get_telemetry()

track_x = tel['X'].to_numpy()
track_y = tel['Y'].to_numpy()

# Position data
pos_data = session.pos_data

# Driver number → abbreviation map
driver_map = {}
for drv in session.drivers:
    info = session.get_driver(drv)
    driver_map[drv] = info['Abbreviation']

# Team colors
team_colors = {
    'VER': '#1E41FF','PER': '#1E41FF',
    'HAM': '#00D2BE','RUS': '#00D2BE',
    'LEC': '#DC0000','SAI': '#DC0000',
    'NOR': '#FF8700','PIA': '#FF8700',
    'ALO': '#006F62','STR': '#006F62',
    'OCO': '#0090FF','GAS': '#0090FF',
    'ALB': '#005AFF','SAR': '#005AFF',
    'TSU': '#2B4562','RIC': '#2B4562',
    'MAG': '#FFFFFF','HUL': '#FFFFFF',
    'BOT': '#00FF00','ZHO': '#00FF00',
}

# ---------------- SIDEBAR ----------------
st.sidebar.header("Controls")

lap_number = st.sidebar.slider(
    "Select Lap",
    1,
    int(session.laps['LapNumber'].max()),
    10
)

selected_driver = st.sidebar.selectbox("Select Driver", session.drivers)

play = st.sidebar.button("▶ Play Animation")

# ---------------- LAYOUT ----------------
col1, col2, col3 = st.columns([1, 2, 1])

# ---------------- LEFT PANEL ----------------
with col1:
    st.subheader(f"Driver: {selected_driver}")

    drv_laps = session.laps.pick_drivers([selected_driver]).pick_quicklaps()

    if not drv_laps.empty:
        last_lap = drv_laps.iloc[-1]
        st.write(f"Lap Time: {last_lap['LapTime']}")
        st.write(f"Tyre: {last_lap['Compound']}")

# ---------------- CENTER PANEL ----------------
with col2:

    placeholder = st.empty()

    # ---------- ANIMATION ----------
    if play:
        for frame in range(50, 300, 3):

            fig, ax = plt.subplots(figsize=(6, 6))

            fig.patch.set_facecolor('#0b0f1a')
            ax.set_facecolor('#0b0f1a')

            # Track glow
            ax.plot(track_x, track_y, color='white', linewidth=5, alpha=0.2)
            ax.plot(track_x, track_y, color='gray', linewidth=2)

            # Plot cars
            for drv in session.drivers:
                drv_data = pos_data[drv]
                drv_data = drv_data[drv_data['Time'] <= session.laps['Time'].iloc[frame]]

                if not drv_data.empty:
                    latest = drv_data.iloc[-1]
                    x, y = latest['X'], latest['Y']

                    abbr = driver_map[drv]
                    color = team_colors.get(abbr, 'white')

                    size = 140 if drv == selected_driver else 70

                    ax.scatter(
                        x, y,
                        s=size,
                        color=color,
                        edgecolors='black',
                        linewidth=1.5
                    )

            ax.axis('off')

            placeholder.pyplot(fig)
            time.sleep(0.05)

    # ---------- STATIC VIEW ----------
    else:
        fig, ax = plt.subplots(figsize=(6, 6))

        fig.patch.set_facecolor('#0b0f1a')
        ax.set_facecolor('#0b0f1a')

        # Track
        ax.plot(track_x, track_y, color='white', linewidth=5, alpha=0.2)
        ax.plot(track_x, track_y, color='gray', linewidth=2)

        # Get positions for selected lap
        for drv in session.drivers:
            drv_data = pos_data[drv]

            drv_lap = session.laps.pick_drivers([drv])
            drv_lap = drv_lap[drv_lap['LapNumber'] == lap_number]

            if not drv_lap.empty:
                time_point = drv_lap.iloc[0]['Time']
                drv_data = drv_data[drv_data['Time'] <= time_point]

                if not drv_data.empty:
                    latest = drv_data.iloc[-1]
                    x, y = latest['X'], latest['Y']

                    abbr = driver_map[drv]
                    color = team_colors.get(abbr, 'white')

                    size = 140 if drv == selected_driver else 70

                    ax.scatter(
                        x, y,
                        s=size,
                        color=color,
                        edgecolors='black',
                        linewidth=1.5
                    )

        ax.axis('off')
        st.pyplot(fig)

# ---------------- RIGHT PANEL ----------------
with col3:
    st.subheader("Leaderboard")

    results = session.results.sort_values('Position')

    for _, row in results.iterrows():
        st.write(f"{int(row['Position'])}. {row['Abbreviation']}")