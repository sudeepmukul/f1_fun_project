import fastf1
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import os
from streamlit_autorefresh import st_autorefresh
# ---------------- SETUP ----------------
os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')
st.set_page_config(layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    session = fastf1.get_session(2024, 'Bahrain', 'R')
    session.load()
    return session

session = load_data()
pos_data = session.pos_data

# ---------------- DRIVER MAP ----------------
driver_map = {drv: session.get_driver(drv)['Abbreviation'] for drv in session.drivers}


# ---------------- TEAM COLORS ----------------
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

# ---------------- TRACK ----------------
lap = session.laps.pick_drivers([session.drivers[0]]).pick_fastest()
tel = lap.get_telemetry()
track_x = tel['X'].to_numpy()
track_y = tel['Y'].to_numpy()
# ---------------- TRACK DISTANCE (FOR OVERTAKES) ----------------
from scipy.spatial import cKDTree

tel['dist'] = ((tel['X'].diff()**2 + tel['Y'].diff()**2)**0.5).cumsum()
tel['dist_norm'] = tel['dist'] / tel['dist'].max()

track_tree = cKDTree(tel[['X', 'Y']].values)


def get_progress(x, y, tel, tree):
    _, idx = tree.query([x, y])
    return tel.iloc[idx]['dist_norm']

# ---------------- SIDEBAR ----------------
st.sidebar.title("Controls")

mode = st.sidebar.selectbox("Mode", ["Manual", "Auto Play"])
frame_index = st.sidebar.slider("Timeline", 50, 300, 100)
selected_driver = st.sidebar.selectbox("Driver", session.drivers)
follow_cam = st.sidebar.checkbox("Follow Camera")

# ---------------- FUNCTION: GET FRAME DATA ----------------
def get_positions(frame):
    positions = []
    for drv in session.drivers:
        drv_data = pos_data[drv]
        drv_data = drv_data[drv_data['Time'] <= session.laps['Time'].iloc[frame]]

        if not drv_data.empty:
            latest = drv_data.iloc[-1]
            positions.append({
                "drv": drv,
                "abbr": driver_map[drv],
                "x": latest['X'],
                "y": latest['Y']
            })
    return positions

# ---------------- FUNCTION: BUILD FIG ----------------
def build_figure(positions, focus=None):

    x_coords = [p['x'] for p in positions]
    y_coords = [p['y'] for p in positions]
    colors = [team_colors.get(p['abbr'], 'white') for p in positions]
    labels = [p['abbr'] for p in positions]

    track_trace = go.Scatter(
        x=track_x,
        y=track_y,
        mode='lines',
        line=dict(color='gray', width=4),
        showlegend=False
    )

    car_trace = go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        text=labels,
        textposition="top center",
        marker=dict(size=12, color=colors),
        showlegend=False
    )

    fig = go.Figure(data=[track_trace, car_trace])

    if focus:
        fig.update_layout(
            xaxis=dict(range=[focus[0]-1000, focus[0]+1000]),
            yaxis=dict(range=[focus[1]-1000, focus[1]+1000])
        )
    else:
        fig.update_layout(
            xaxis=dict(scaleanchor="y"),
            yaxis=dict(scaleanchor="x")
        )

    fig.update_layout(
        plot_bgcolor='black',
        paper_bgcolor='black',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig

# ---------------- LAYOUT ----------------
col1, col2, col3 = st.columns([1.2, 3, 1.5])

# ---------------- LEFT PANEL ----------------
with col1:
    st.markdown("## Lap Info")

    lap_number = int(session.laps['LapNumber'].iloc[frame_index])
    race_time = session.laps['Time'].iloc[frame_index]

    st.write(f"Lap: {lap_number}")
    st.write(f"Race Time: {race_time}")

    st.markdown("---")

    st.markdown("### Driver Info")

    drv_laps = session.laps.pick_drivers([selected_driver]).pick_quicklaps()

    if not drv_laps.empty:
        last = drv_laps.iloc[-1]
        st.write(f"Driver: {driver_map[selected_driver]}")
        st.write(f"Tyre: {last['Compound']}")
        st.write(f"Lap Time: {last['LapTime']}")
# ---------------- REAL INTERPOLATION (TIME-BASED) ----------------
def interpolate_driver(df, t_now):

    if t_now <= df['t'].iloc[0]:
        return df.iloc[0]['X'], df.iloc[0]['Y']

    if t_now >= df['t'].iloc[-1]:
        return df.iloc[-1]['X'], df.iloc[-1]['Y']

    before = df[df['t'] <= t_now].iloc[-1]
    after  = df[df['t'] >= t_now].iloc[0]

    t1, t2 = before['t'], after['t']

    if t1 == t2:
        return before['X'], before['Y']

    alpha = (t_now - t1) / (t2 - t1)

    x = before['X'] + alpha * (after['X'] - before['X'])
    y = before['Y'] + alpha * (after['Y'] - before['Y'])

    return x, y
# ---------------- BUILD DRIVER DATA (TIME-BASED) ----------------
driver_data = {}
drivers = session.drivers

for drv in drivers:
    df = pos_data[drv].copy()

    # normalize time → seconds
    df['t'] = (df['Time'] - df['Time'].min()).dt.total_seconds()

    # remove NaNs just in case
    df = df.dropna(subset=['X', 'Y', 't'])

    driver_data[drv] = df.reset_index(drop=True)
# ---------------- CENTER PANEL ----------------
with col2:

    FPS = 20
    interval = int(1000 / FPS)  # milliseconds

    if mode == "Auto Play":
        st_autorefresh(interval=interval, key="f1_animation")

    # --- INIT TIME ---
    if "t_now" not in st.session_state:
        st.session_state.t_now = 0

    # --- TOTAL TIME ---
    total_time = driver_data[selected_driver]['t'].max()

    # --- COMPUTE POSITIONS ---
    positions = []
    for drv in drivers:
        df = driver_data[drv]
        x, y = interpolate_driver(df, st.session_state.t_now)

        positions.append({
            "drv": drv,
            "x": x,
            "y": y,
            "abbr": driver_map[drv]
        })

    # --- FOLLOW CAMERA ---
    focus = None
    if follow_cam:
        for p in positions:
            if p["drv"] == selected_driver:
                focus = (p["x"], p["y"])
                break

    # --- BUILD FIG ---
    fig = build_figure(positions, focus)

    st.plotly_chart(fig, use_container_width=True)

    # --- ADVANCE TIME (ONLY IN AUTOPLAY) ---
    if mode == "Auto Play":
        st.session_state.t_now += (1 / FPS)

        if st.session_state.t_now >= total_time:
            st.session_state.t_now = 0
# ---------------- RIGHT PANEL ----------------
with col3:
    st.markdown("## Leaderboard")

    results = session.results.sort_values('Position')

    for _, row in results.iterrows():
        abbr = row['Abbreviation']
        color = team_colors.get(abbr, 'white')

        st.markdown(
            f"<span style='color:{color}; font-size:18px'>{int(row['Position'])}. {abbr}</span>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### Gaps")

    driver_times = {}
    for drv in session.drivers:
        drv_laps = session.laps.pick_drivers([drv])
        if not drv_laps.empty:
            driver_times[drv] = drv_laps.iloc[-1]['LapTime'].total_seconds()

    leader = min(driver_times.values())

    for drv in driver_times:
        gap = round(driver_times[drv] - leader, 2)
        st.write(f"{driver_map[drv]}: +{gap}s")