import polars as pl

# Load taxi data
taxi_df = pl.read_parquet(
    "data/processed/hourly_zone_density.parquet"
)

# Load weather
weather_df = pl.read_parquet(
    "data/interim/weather/nyc_weather_2023_2024.parquet"
)

# Convert datetime weather
weather_df = weather_df.with_columns(

    pl.col("datetime")
    .str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M")
    .alias("pickup_hour")

)

# Drop old datetime
weather_df = weather_df.drop("datetime")

# Merge
merged_df = taxi_df.join(
    weather_df,
    on="pickup_hour",
    how="left"
)

# Save
merged_df.write_parquet(
    "data/processed/taxi_weather_merged.parquet"
)

print("Taxi + weather merge selesai.")
