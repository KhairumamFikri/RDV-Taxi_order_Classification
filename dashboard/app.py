import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from pyproj import Transformer
from copy import deepcopy

# --- CONFIG & PATHS ---
DATASET_PATH = Path("data/processed/dashboard_density_dataset.parquet")
WEATHER_PATH = Path("data/processed/taxi_weather_merged.parquet")
GEOJSON_PATH = Path("data/geo/taxi_zones.geojson")
NYC_ZONE_TRANSFORMER = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)

DENSITY_COLOR_MAP = {
    "Sepi": "#10B981",    # Emerald 500
    "Normal": "#F59E0B",  # Amber 500
    "Sibuk": "#EF4444",   # Red 500
}

WEATHER_DESC = {
    0: "Cerah", 1: "Cerah Berawan", 2: "Berawan", 3: "Mendung",
    51: "Gerimis", 53: "Gerimis", 55: "Hujan Ringan",
    61: "Hujan", 63: "Hujan Sedang", 65: "Hujan Lebat",
    71: "Salju", 73: "Salju", 75: "Badai Salju"
}

st.set_page_config(
    page_title="Smart Taxi Radar",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING (Midnight Modern v2) ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono&display=swap');
        
        /* Layout Reset */
        .stApp {
            background-color: #0F172A;
            color: #F1F5F9;
            font-family: 'Inter', sans-serif;
        }
        
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2rem !important;
            max-width: 95% !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        
        .sidebar-header {
            padding: 1.5rem 0;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 1.5rem;
        }

        /* Header Fix */
        .header-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 0;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .brand-text h1 {
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, #F8FAFC 0%, #38BDF8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Compact Cards */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .card {
            background: #1E293B;
            border: 1px solid rgba(255,255,255,0.05);
            padding: 1.25rem;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 120px;
        }

        .card-label {
            color: #94A3B8;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .card-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #FFFFFF;
            font-family: 'JetBrains Mono', monospace;
            margin: 0.5rem 0;
        }

        .card-sub {
            font-size: 0.7rem;
            color: #38BDF8;
        }

        /* Weather Panel */
        .weather-panel {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.1) 0%, rgba(15, 23, 42, 0) 100%);
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 2rem;
            margin-bottom: 1.5rem;
        }

        /* Comparison Mode UI */
        .compare-header {
            background: #0F172A;
            border: 1px solid #38BDF8;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            text-align: center;
            color: #38BDF8;
            font-weight: 600;
        }

        /* Global Overrides */
        [data-testid="stMetricValue"] { color: white !important; }
        .stDataFrame { border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; }
        
        /* Panel Title */
        .section-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: #CBD5E1;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Fix whitespace at top */
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- DATA LOGIC ---
def normalize_density_df(df: pd.DataFrame) -> pd.DataFrame:
    score_map = {"Low": 1, "Medium": 2, "High": 3, "Sepi": 1, "Normal": 2, "Sibuk": 3}
    if "density_score" not in df.columns:
        source_col = next((c for c in ["density_level", "density_label"] if c in df.columns), None)
        df["density_score"] = df[source_col].map(score_map).fillna(1) if source_col else 1
    if "density_label" not in df.columns and "density_level" in df.columns:
        df["density_label"] = df["density_level"].map({"Low": "Sepi", "Medium": "Normal", "High": "Sibuk"})
    return df

@st.cache_data
def load_all_data():
    if not DATASET_PATH.exists(): raise FileNotFoundError("Dataset missing.")
    d_df = pd.read_parquet(DATASET_PATH)
    d_df = normalize_density_df(d_df)
    d_df["pickup_hour"] = pd.to_datetime(d_df["pickup_hour"])
    d_df["date"] = d_df["pickup_hour"].dt.date
    d_df["hour"] = d_df["pickup_hour"].dt.hour
    
    w_df = pd.read_parquet(WEATHER_PATH) if WEATHER_PATH.exists() else pd.DataFrame()
    if not w_df.empty:
        w_df["pickup_hour"] = pd.to_datetime(w_df["pickup_hour"])
        w_df["date"] = w_df["pickup_hour"].dt.date
        w_df["hour"] = w_df["pickup_hour"].dt.hour
    return d_df, w_df

@st.cache_data
def load_geo():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f: data = json.load(f)
    # CRS transform
    for feat in data["features"]:
        coords = feat["geometry"]["coordinates"]
        def tr(c):
            if isinstance(c[0], (int, float)): return list(NYC_ZONE_TRANSFORMER.transform(c[0], c[1]))
            return [tr(sub) for sub in c]
        feat["geometry"]["coordinates"] = tr(coords)
    
    # Centroids
    centroids = []
    for feat in data["features"]:
        props = feat["properties"]
        def flat(c):
            if isinstance(c[0], (int, float)): yield c
            else:
                for s in c: yield from flat(s)
        pts = list(flat(feat["geometry"]["coordinates"]))
        centroids.append({
            "LocationID": str(props["LocationID"]),
            "zone": props["zone"], "borough": props["borough"],
            "lon": sum(p[0] for p in pts)/len(pts), "lat": sum(p[1] for p in pts)/len(pts)
        })
    return data, pd.DataFrame(centroids)

d_df, w_df = load_all_data()
geo_data, centroids_df = load_geo()

# --- SIDEBAR (CONTROL CENTER) ---
with st.sidebar:
    st.markdown("<div class='sidebar-header'><h2 style='margin:0; color:#38BDF8;'>RADAR CORE</h2><small style='color:#64748B;'>V2.0 STABLE</small></div>", unsafe_allow_html=True)
    
    analysis_mode = st.radio("Sistem Mode", ["Standard Analytics", "Weather Comparison"], index=0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if analysis_mode == "Standard Analytics":
        sel_date = st.date_input("Analytic Date", d_df["date"].min())
        sel_hour = st.slider("Time Window", 0, 23, 10)
        sel_density = st.multiselect("Density Filter", ["Sepi", "Normal", "Sibuk"], ["Sepi", "Normal", "Sibuk"])
    else:
        st.info("Mode Perbandingan: Bandingkan kondisi Cerah vs Hujan pada jam yang sama.")
        sel_hour = st.slider("Target Hour", 0, 23, 10)
        sel_density = ["Sepi", "Normal", "Sibuk"]

    st.markdown("---")
    st.markdown("<div class='section-title'>Table Configuration</div>", unsafe_allow_html=True)
    pq_limit = st.select_slider("Priority Queue Limit", options=[3, 5, 10, 25], value=10)
    
    st.markdown("---")
    if not w_df.empty:
        st.success("Weather Engine: Linked")
    else:
        st.warning("Weather Engine: Offline")

# --- CORE LOGIC ---
def get_snapshot(date, hour, density_list):
    snap = d_df[(d_df["date"] == date) & (d_df["hour"] == hour)].copy()
    # Apply density filter AFTER snapshot to ensure map only shows filtered zones
    snap = snap[snap["density_label"].isin(density_list)]
    return snap.merge(centroids_df, left_on="PULocationID", right_on="LocationID", how="inner")

def get_weather(date, hour):
    if w_df.empty: return None
    m = w_df[(w_df["date"] == date) & (w_df["hour"] == hour)]
    return m.iloc[0] if not m.empty else None

# --- UI RENDERING ---
st.markdown("<div class='header-section'><div class='brand-text'><h1>SMART TAXI RADAR</h1><small style='color:#64748B;'>New York City Geospasial Intelligence</small></div></div>", unsafe_allow_html=True)

if analysis_mode == "Standard Analytics":
    # Snapshot
    snap = get_snapshot(sel_date, sel_hour, sel_density)
    weather = get_weather(sel_date, sel_hour)
    
    # Weather Panel
    if weather is not None:
        st.markdown(f"""
        <div class="weather-panel">
            <div style="font-size:2rem; font-family:'JetBrains Mono'; color:#38BDF8;">{weather['temperature']}°C</div>
            <div style="flex-grow:1;">
                <div style="font-weight:700; font-size:1.1rem;">{WEATHER_DESC.get(int(weather['weather_code']), 'Kondisi Normal')}</div>
                <div style="color:#94A3B8; font-size:0.8rem;">Prec: {weather['precipitation']}mm | Wind: {weather['wind_speed']}km/h</div>
            </div>
            <div style="text-align:right; font-family:'JetBrains Mono'; font-size:0.8rem; color:#64748B;">{sel_date} | {sel_hour:02d}:00</div>
        </div>
        """, unsafe_allow_html=True)

    # Stat Grid
    total_pax = snap["trip_count"].sum()
    busy_z = snap[snap["density_score"] == 3]["PULocationID"].nunique()
    top_row = snap.sort_values("trip_count", ascending=False).iloc[0] if not snap.empty else None
    
    st.markdown(f"""
    <div class="stat-grid">
        <div class="card"><div class="card-label"><div style="width:6px; height:6px; background:#38BDF8; border-radius:50%;"></div>Total Demand</div><div class="card-value">{total_pax:,}</div><div class="card-sub">Passengers Detected</div></div>
        <div class="card"><div class="card-label"><div style="width:6px; height:6px; background:#10B981; border-radius:50%;"></div>Active Zones</div><div class="card-value">{snap['PULocationID'].nunique()}</div><div class="card-sub">Coverage Area</div></div>
        <div class="card"><div class="card-label"><div style="width:6px; height:6px; background:#EF4444; border-radius:50%;"></div>Critical Hubs</div><div class="card-value">{busy_z}</div><div class="card-sub">High Density Clusters</div></div>
        <div class="card"><div class="card-label"><div style="width:6px; height:6px; background:#F59E0B; border-radius:50%;"></div>Peak Zone</div><div class="card-value">{top_row['zone'][:12] if top_row is not None else 'N/A'}</div><div class="card-sub">Highest Demand</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Visuals
    c1, c2 = st.columns([2, 1], gap="medium")
    with c1:
        st.markdown("<div class='section-title'>Spatial Density Distribution</div>", unsafe_allow_html=True)
        if not snap.empty:
            fig = go.Figure()
            # Choropleth restricted to filtered data
            fig.add_trace(go.Choroplethmap(
                geojson=geo_data, locations=snap["PULocationID"], z=snap["density_score"],
                featureidkey="properties.LocationID", colorscale=[[0,"#10B981"],[0.5,"#F59E0B"],[1,"#EF4444"]],
                showscale=False, marker_opacity=0.5, marker_line_width=0.3
            ))
            # Markers restricted to filtered data
            snap["m_size"] = 8 + (snap["trip_count"] / snap["trip_count"].max() * 20)
            for l in ["Sepi", "Normal", "Sibuk"]:
                sub = snap[snap["density_label"] == l]
                if sub.empty: continue
                fig.add_trace(go.Scattermap(
                    lat=sub["lat"], lon=sub["lon"], mode="markers", name=l,
                    marker=dict(size=sub["m_size"], color=DENSITY_COLOR_MAP[l], opacity=0.9),
                    text=sub["zone"] + "<br>Demand: " + sub["trip_count"].astype(str)
                ))
            fig.update_layout(map=dict(style="carto-darkmatter", center={"lat":40.7128,"lon":-74.006}, zoom=10),
                              margin=dict(l=0,r=0,t=0,b=0), height=500, paper_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", y=0.02, x=0.02, bgcolor="rgba(15,23,42,0.8)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data matches current filters.")

    with c2:
        st.markdown("<div class='section-title'>Priority Queue Analytics</div>", unsafe_allow_html=True)
        pq = snap.sort_values("trip_count", ascending=False).head(pq_limit).copy()
        
        if not pq.empty:
            # Visual Bar Chart for Top Zones
            fig_pq = px.bar(pq, x="trip_count", y="zone", orientation="h",
                             color="trip_count", color_continuous_scale="Blues",
                             template="plotly_dark", height=180)
            fig_pq.update_layout(showlegend=False, coloraxis_showscale=False,
                                 margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)",
                                 plot_bgcolor="rgba(0,0,0,0)", xaxis_visible=False,
                                 yaxis_autorange="reversed", yaxis_title="")
            st.plotly_chart(fig_pq, use_container_width=True, config={'displayModeBar': False})
            
            # Data Table
            pq_table = pq[["zone", "trip_count"]].rename(columns={"zone": "Area", "trip_count": "Pax"})
            st.dataframe(pq_table, hide_index=True, use_container_width=True, height=250)
        else:
            st.info("No areas meet current criteria.")

    # --- HOURLY TREND INSIDE ANALYTICS ---
    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Statistical Hourly Demand (00:00 - 23:00)</div>", unsafe_allow_html=True)
    day_data = d_df[d_df["date"] == sel_date].groupby("hour")["trip_count"].sum().reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=day_data["hour"], y=day_data["trip_count"],
        mode='lines', line=dict(color='#38BDF8', width=3),
        fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.1)',
        name="Total Demand"
    ))
    fig_trend.add_vline(x=sel_hour, line_dash="dash", line_color="#EF4444", 
                        annotation_text=f"Selected ({sel_hour:02d}:00)", annotation_position="top right")

    fig_trend.update_layout(
        height=300, margin=dict(l=10,r=10,t=40,b=20),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Hour", tickmode="linear", tick0=0, dtick=1),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Pax"),
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    # WEATHER COMPARISON MODE
    st.markdown("<div class='compare-header'>WEATHER IMPACT ANALYSIS: CLEAR SKY VS HEAVY PRECIPITATION</div>", unsafe_allow_html=True)
    
    # Identify sample dates (Cerah vs Hujan)
    # Search for precipitation > 2.0 (Hujan) and precipitation == 0 (Cerah) at the same hour
    rainy_samples = w_df[(w_df["hour"] == sel_hour) & (w_df["precipitation"] > 2.0)].head(1)
    clear_samples = w_df[(w_df["hour"] == sel_hour) & (w_df["precipitation"] == 0)].head(1)
    
    if rainy_samples.empty or clear_samples.empty:
        st.error("Insufficient historical weather data for comparison at this hour.")
    else:
        rd = rainy_samples.iloc[0]["date"]
        cd = clear_samples.iloc[0]["date"]
        
        col_c, col_r = st.columns(2)
        
        for col, date, title, color in zip([col_c, col_r], [cd, rd], ["CLEAR CONDITION", "RAINY CONDITION"], ["#10B981", "#EF4444"]):
            with col:
                st.markdown(f"<div style='text-align:center; padding:10px; border-bottom:2px solid {color}; margin-bottom:15px; font-weight:800;'>{title} ({date})</div>", unsafe_allow_html=True)
                s = get_snapshot(date, sel_hour, ["Sepi", "Normal", "Sibuk"])
                w = get_weather(date, sel_hour)
                
                # Small weather stats
                st.markdown(f"<small>{w['temperature']}°C | Prec: {w['precipitation']}mm</small>", unsafe_allow_html=True)
                
                # Metrics
                st.metric("Total Passengers", f"{s['trip_count'].sum():,}")
                
                # Simplified Map
                f = go.Figure(go.Choroplethmap(
                    geojson=geo_data, locations=s["PULocationID"], z=s["density_score"],
                    featureidkey="properties.LocationID", colorscale=[[0,"#10B981"],[0.5,"#F59E0B"],[1,"#EF4444"]],
                    showscale=False, marker_opacity=0.6
                ))
                f.update_layout(map=dict(style="carto-darkmatter", center={"lat":40.75,"lon":-73.98}, zoom=10.5),
                                margin=dict(l=0,r=0,t=0,b=0), height=350, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(f, use_container_width=True)
                
                # Top 3
                st.markdown("<div style='font-size:0.8rem; margin-top:10px;'>Top 3 Critical Hubs:</div>", unsafe_allow_html=True)
                st.dataframe(s.sort_values("trip_count", ascending=False).head(3)[["zone", "trip_count"]], hide_index=True)

st.markdown("<div style='text-align:center; padding:2rem; color:#64748B; font-size:0.7rem;'>PROYEK RDV KELOMPOK 3 | ANALISIS SPASIAL NYC 2026</div>", unsafe_allow_html=True)
