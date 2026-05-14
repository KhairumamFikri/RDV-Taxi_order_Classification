import polars as pl

df = pl.read_parquet(
    "data/processed/hourly_zone_density.parquet"
)

print(df.head())
print(df.shape)
print(df.describe())