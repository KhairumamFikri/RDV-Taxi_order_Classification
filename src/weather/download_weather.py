import requests
import polars as pl
from pathlib import Path

OUTPUT_DIR = "data/interim/weather"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "hourly": [
        "temperature_2m",
        "precipitation",
        "snowfall",
        "weather_code",
        "wind_speed_10m"
    ],
    "timezone": "America/New_York"
}

response = requests.get(URL, params=params)

data = response.json()

hourly = data["hourly"]

df = pl.DataFrame({
    "datetime": hourly["time"],
    "temperature": hourly["temperature_2m"],
    "precipitation": hourly["precipitation"],
    "snowfall": hourly["snowfall"],
    "weather_code": hourly["weather_code"],
    "wind_speed": hourly["wind_speed_10m"]
})

output_path = f"{OUTPUT_DIR}/nyc_weather_2023_2024.parquet"

df.write_parquet(output_path)

print(f"Weather data saved to: {output_path}")
