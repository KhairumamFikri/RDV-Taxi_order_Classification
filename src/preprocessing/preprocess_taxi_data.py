import polars as pl
from pathlib import Path
from datetime import datetime

RAW_DIR = "data/raw/taxi"
OUTPUT_DIR = "data/processed"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

files = sorted(Path(RAW_DIR).glob("*.parquet"))

all_results = []

for file in files:

    print(f"Processing {file.name}")

    df = pl.read_parquet(file)

    # Ambil kolom penting dan samakan schema
    df = df.select([
        pl.col("tpep_pickup_datetime")
        .cast(pl.Datetime("us")),

        pl.col("PULocationID")
        .cast(pl.Int64)
    ])

    # Buang null
    df = df.drop_nulls()

    df = df.filter(
        (pl.col("tpep_pickup_datetime") >= datetime(2023, 1, 1)) &
        (pl.col("tpep_pickup_datetime") < datetime(2025, 1, 1))
    )   

    # Truncate datetime ke per jam
    df = df.with_columns([

        pl.col("tpep_pickup_datetime")
        .dt.truncate("1h")
        .cast(pl.Datetime("us"))
        .alias("pickup_hour")

    ])

    # Aggregation
    agg = (
        df.group_by([
            "pickup_hour",
            "PULocationID"
        ])
        .agg([
            pl.len().alias("trip_count")
        ])
        .sort("pickup_hour")
    )

    all_results.append(agg)

# Concat semua hasil
final_df = pl.concat(
    all_results,
    how="vertical_relaxed"
)

# Save hasil
final_df.write_parquet(
    "data/processed/hourly_zone_density.parquet"
)

print("Preprocessing selesai.")