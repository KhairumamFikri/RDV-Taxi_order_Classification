import streamlit as st
import geopandas as gpd
import polars as pl
import pandas as pd
import json
import plotly.graph_objects as go

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="NYC Taxi Density Dashboard",
    layout="wide"
)

st.title("NYC Taxi Density Dashboard")

# =========================
# LOAD GEO ZONES
# =========================

zones = gpd.read_file(
    "data/geo/taxi_zones.geojson"
).to_crs(epsg=4326)

# =========================
# LOAD DENSITY DATA
# =========================

df = pl.read_parquet(
    "data/processed/final_density_dataset.parquet"
)

df = df.to_pandas()

# Mapping label density
density_map = {
    "Low": "Sepi",
    "Medium": "Sedang",
    "High": "Padat"
}

df["density_label"] = df["density_level"].map(
    density_map
)

# =========================
# DATETIME CONVERSION
# =========================

df["pickup_hour"] = pd.to_datetime(
    df["pickup_hour"]
)

# =========================
# TYPE NORMALIZATION
# =========================

zones["LocationID"] = zones["LocationID"].astype(str)

df["PULocationID"] = df["PULocationID"].astype(str)

# =========================
# SIDEBAR
# =========================

selected_date = st.sidebar.date_input(
    "Select Date",
    df["pickup_hour"].dt.date.min()
)

selected_hour = st.sidebar.slider(
    "Select Hour",
    0,
    23,
    8
)

# Weather info
st.sidebar.markdown("---")

weather_info = filtered = df[
    (df["pickup_hour"].dt.date == selected_date)
    &
    (df["pickup_hour"].dt.hour == selected_hour)
]

if len(weather_info) > 0:

    temp = weather_info["temperature"].mean()
    rain = weather_info["precipitation"].mean()
    wind = weather_info["wind_speed"].mean()

    st.sidebar.subheader("Weather")

    st.sidebar.write(f"🌡 Temperature: {temp:.1f} °C")
    st.sidebar.write(f"🌧 Rain: {rain:.2f} mm")
    st.sidebar.write(f"💨 Wind: {wind:.1f} km/h")

    weather_condition = weather_info[
        "weather_condition"
    ].iloc[0]

    st.sidebar.write(
        f"☁️ Condition: {weather_condition}"
    )
# =========================
# FILTER
# =========================

filtered = df[
    (df["pickup_hour"].dt.date == selected_date)
    &
    (df["pickup_hour"].dt.hour == selected_hour)
]

# =========================
# MERGE
# =========================

merged = zones.merge(
    filtered,
    left_on="LocationID",
    right_on="PULocationID",
    how="inner"
)

# =========================
# DEBUG
# =========================

st.sidebar.write(f"Rows: {merged.shape[0]}")

# =========================
# CREATE UNIQUE ID
# =========================

merged = merged.reset_index(drop=True)

merged["map_id"] = merged.index.astype(str)

# Convert datetime columns ke string
merged["pickup_hour"] = merged["pickup_hour"].astype(str)

# =========================
# GEOJSON
# =========================

geojson_data = json.loads(
    merged.to_json()
)

# =========================
# MAP
# =========================

# Numeric density mapping
density_numeric_map = {
    "Sepi": 1,
    "Sedang": 2,
    "Padat": 3
}

merged["density_numeric"] = merged[
    "density_label"
].map(density_numeric_map)

fig = go.Figure()

fig.add_trace(
    go.Choroplethmapbox(
        geojson=geojson_data,

        locations=merged["map_id"],

        z=merged["density_numeric"],

        featureidkey="properties.map_id",

        colorscale=[
            [0.0, "#2ecc71"],   # Sepi = hijau
            [0.5, "#f1c40f"],   # Sedang = kuning
            [1.0, "#e74c3c"]    # Padat = merah
        ],

        marker_opacity=0.7,

        marker_line_width=0.5,

        text=merged["zone"],
        hovertext=(
            "Zone: " + merged["zone"].astype(str)
            + "<br>Kepadatan: " + merged["density_label"].astype(str)
            + "<br>Trips: " + merged["trip_count"].astype(str)
            + "<br>Suhu: " + merged["temperature"].round(1).astype(str) + " °C"
            + "<br>Hujan: " + merged["precipitation"].astype(str) + " mm"
            + "<br>Angin: " + merged["wind_speed"].astype(str) + " km/h"
        ),
        hoverinfo="text",
        zmin=1,
        zmax=3,
    )
)

fig.update_layout(

    mapbox=dict(
        style="carto-positron",
        zoom=9,
        center={
            "lat": 40.7128,
            "lon": -74.0060
        }
    ),

    margin={
        "r":0,
        "t":0,
        "l":0,
        "b":0
    }
)

# =========================
# RENDER
# =========================

st.plotly_chart(
    fig,
    use_container_width=True
)