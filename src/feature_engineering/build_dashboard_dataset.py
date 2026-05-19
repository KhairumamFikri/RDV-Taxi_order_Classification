from pathlib import Path

import pandas as pd


SOURCE_PATH = Path("data/processed/density/temp_cluster_labels.parquet")
OUTPUT_PATH = Path("data/processed/dashboard_density_dataset.parquet")

START_DATE = "2023-01-01"
END_DATE = "2025-01-01"

DENSITY_LEVEL_MAP = {
    "Sepi": "Low",
    "Normal": "Medium",
    "Sibuk": "High",
}

DENSITY_LABEL_MAP = {
    "Low": "Sepi",
    "Medium": "Normal",
    "High": "Sibuk",
}


def build_dashboard_dataset(
    source_path: Path = SOURCE_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    if not source_path.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {source_path}. "
            "Expected data from data analyst pipeline."
        )

    df = pd.read_parquet(source_path)

    required_columns = {
        "location_id",
        "time_id",
        "total_passengers",
        "density_cluster",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns in {source_path}: "
            f"{sorted(missing_columns)}"
        )

    result = df.copy()
    result["pickup_hour"] = pd.to_datetime(
        result["time_id"].astype("int64").astype(str),
        format="%Y%m%d%H",
        errors="coerce",
    )

    result = result.dropna(subset=["pickup_hour", "location_id", "total_passengers"])
    result = result[
        (result["pickup_hour"] >= pd.Timestamp(START_DATE))
        & (result["pickup_hour"] < pd.Timestamp(END_DATE))
    ]

    result["PULocationID"] = result["location_id"].astype("int64").astype(str)
    result["trip_count"] = result["total_passengers"].round().astype("int64")
    result["density_level"] = result["density_cluster"].map(DENSITY_LEVEL_MAP)
    result = result.dropna(subset=["density_level"])
    result["density_label"] = result["density_level"].map(DENSITY_LABEL_MAP)

    result = result[
        [
            "pickup_hour",
            "time_id",
            "PULocationID",
            "trip_count",
            "total_passengers",
            "density_level",
            "density_label",
            "density_cluster",
        ]
    ].sort_values(["pickup_hour", "PULocationID"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)

    print(f"Dashboard dataset saved to: {output_path}")
    print(f"Rows: {len(result):,}")
    print(f"Date range: {result['pickup_hour'].min()} to {result['pickup_hour'].max()}")
    print("Density distribution:")
    print(result["density_label"].value_counts().to_string())

    return result


if __name__ == "__main__":
    build_dashboard_dataset()
