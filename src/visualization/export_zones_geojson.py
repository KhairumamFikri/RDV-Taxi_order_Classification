import geopandas as gpd

# Load shapefile
zones = gpd.read_file(
    "data/geo/taxi_zones.shp"
)

# Simpan geojson ringan
zones.to_file(
    "data/geo/taxi_zones.geojson",
    driver="GeoJSON"
)

print("Taxi zones geojson berhasil dibuat.")