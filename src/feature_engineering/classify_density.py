import polars as pl

df = pl.read_parquet(
    "data/processed/taxi_weather_merged.parquet"
)

# Quantile

df = df.with_columns(

    # =========================
    # DENSITY CLASSIFICATION
    # =========================

    pl.when(pl.col("trip_count") <= 20)
    .then(pl.lit("Low"))

    .when(pl.col("trip_count") <= 80)
    .then(pl.lit("Medium"))

    .otherwise(pl.lit("High"))

    .alias("density_level"),

    # =========================
    # WEATHER CONDITION
    # =========================

    pl.when(
        pl.col("weather_code").is_in(
            [51,53,55,61,63,65,80,81,82]
        )
    )
    .then(pl.lit("Rain"))

    .when(
        pl.col("weather_code").is_in(
            [71,73,75,77]
        )
    )
    .then(pl.lit("Snow"))

    .when(
        pl.col("weather_code") == 95
    )
    .then(pl.lit("Thunderstorm"))

    .otherwise(pl.lit("Clear"))

    .alias("weather_condition")
)

df.write_parquet(
    "data/processed/final_density_dataset.parquet"
)

print("Density classification selesai.")
