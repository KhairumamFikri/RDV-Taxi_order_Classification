import duckdb
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_GLOB = PROJECT_ROOT / "data" / "interim" / "yellow_trip_data" / "*.parquet"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "density"
TEMP_CLUSTER_LABELS_PATH = OUTPUT_DIR / "temp_cluster_labels.parquet"
FACT_DENSITY_PATH = OUTPUT_DIR / "fact_density_final.parquet"

source_glob_sql = SOURCE_GLOB.as_posix()
temp_cluster_labels_sql = TEMP_CLUSTER_LABELS_PATH.as_posix()
fact_density_sql = FACT_DENSITY_PATH.as_posix()

# ==========================================
# FASE 1: AGREGASI SUPER CEPAT DENGAN DUCKDB
# ==========================================
con = duckdb.connect()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Kueri disesuaikan dengan nama kolom asli NYC TLC Parquet
# Mengubah tpep_pickup_datetime menjadi format TahunBulanTanggalJam (contoh: 2024060115)
query_agregasi = f"""
    SELECT 
        location_id, 
        time_id, 
        SUM(CAST(passenger_count AS INT)) as total_passengers
    FROM '{source_glob_sql}'
    WHERE passenger_count IS NOT NULL 
      AND passenger_count > 0
    GROUP BY location_id, time_id
"""

print("Mulai membaca dan agregasi data mentah TLC...")
df_agg = con.execute(query_agregasi).df()

# ==========================================
# FASE 2: MACHINE LEARNING (K-MEANS)
# ==========================================
print("Melatih model K-Means Clustering...")
kmeans = KMeans(n_clusters=3, random_state=42)
df_agg['cluster_number'] = kmeans.fit_predict(df_agg[['total_passengers']])

# Mengurutkan Centroid untuk memastikan pelabelan konsisten
centroids = kmeans.cluster_centers_.flatten()
sorted_indices = centroids.argsort()

# Indeks 0 (paling sedikit penumpang) = Sepi, Indeks 2 (paling banyak) = Sibuk
cluster_map = {
    sorted_indices[0]: 'Sepi',
    sorted_indices[1]: 'Normal',
    sorted_indices[2]: 'Sibuk'
}
df_agg['density_cluster'] = df_agg['cluster_number'].map(cluster_map)
df_agg.drop('cluster_number', axis=1, inplace=True)

# Simpan tabel mapping ke Parquet sementara
df_agg.to_parquet(TEMP_CLUSTER_LABELS_PATH)


# ==========================================
# FASE 3: JOIN & BENTUK TABEL FAKTA FINAL
# ==========================================
# Kueri ini akan membaca ulang file mentah, membersihkannya, membuat trip_id (menggunakan MD5 hash),
# dan menempelkan 'density_cluster' dari tabel sementara yang baru kita buat.
query_final = f"""
    COPY (
        SELECT 
            mentah.trip_id,
            mentah.time_id,
            mentah.weather_id,
            mentah.location_id,
            CAST(mentah.passenger_count AS INT) AS passenger_count,
            label.density_cluster
        FROM '{source_glob_sql}' AS mentah
        LEFT JOIN '{temp_cluster_labels_sql}' AS label
            ON mentah.location_id = label.location_id 
            AND mentah.time_id = label.time_id
        WHERE mentah.passenger_count IS NOT NULL 
          AND mentah.passenger_count > 0
    ) TO '{fact_density_sql}' (FORMAT PARQUET)
"""

print("Membuat fact table final dan menyimpan ke Parquet...")
con.execute(query_final)

con.close()
print(f"Proses Selesai! {FACT_DENSITY_PATH} siap dikirim ke Data Analyst.")
