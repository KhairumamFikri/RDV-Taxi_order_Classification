# Smart Taxi Radar: NYC Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Smart Taxi Radar** adalah platform Decision Support System (DSS) berbasis geospasial untuk menganalisis kepadatan permintaan taksi di New York City. Proyek ini menggabungkan data perjalanan NYC TLC Yellow Taxi, data cuaca historis Open-Meteo, dan peta zona taksi NYC untuk menampilkan pola demand per jam, tingkat kepadatan zona, serta dampak kondisi cuaca terhadap permintaan taksi.

## Fitur Utama

- **Geospatial Mapping**: peta choropleth dan marker zona taksi NYC berdasarkan tingkat kepadatan.
- **Density Classification**: pelabelan demand menjadi `Sepi`, `Normal`, dan `Sibuk` menggunakan hasil training K-Means.
- **Weather Intelligence**: integrasi suhu, curah hujan, salju, kode cuaca, dan kecepatan angin.
- **Weather Comparison Mode**: perbandingan demand pada kondisi cerah dan hujan untuk jam yang sama.
- **Priority Queue Analytics**: daftar zona dengan demand tertinggi untuk membantu prioritas distribusi armada.
- **24-Hour Statistical Trend**: grafik tren demand per jam dalam satu hari.

## Sumber Data

Proyek ini menggunakan arsitektur data multi-source:

1. **NYC TLC Yellow Taxi Trip Records**  
   Data perjalanan taksi kuning NYC per bulan dalam format Parquet.

2. **Open-Meteo Historical Weather API**  
   Data cuaca historis New York City per jam untuk periode 2023-2024.

3. **NYC Taxi Zones**  
   Data batas wilayah taksi dalam bentuk shapefile/GeoJSON dan lookup zona.

Detail teknis dashboard dapat dilihat di [DASHBOARD_DOCS.md](DASHBOARD_DOCS.md).

## Alur Project

```text
NYC TLC Trip Data + Weather Data + Taxi Zones
        |
        v
Ingestion
        |
        v
Preprocessing & Feature Engineering
        |
        +--> Baseline density dataset + weather features
        |
        v
K-Means Training untuk density cluster
        |
        v
Dashboard adapter
        |
        v
Streamlit Smart Taxi Radar
```

Pipeline utama dashboard memakai hasil training K-Means dari `data/interim/yellow_trip_data/*.parquet`. Pipeline cuaca berjalan paralel untuk menyediakan konteks weather pada dashboard. Semua data staging berada di `data/interim`, sesuai struktur folder repo saat ini.

## Instalasi & Persiapan

1. **Clone Repository**

    ```powershell
    git clone https://github.com/username/RDV-Taxi_order_Classification.git
    cd RDV-Taxi_order_Classification
    ```

2. **Setup Environment**

    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

3. **Siapkan Folder Data**

    ```powershell
    mkdir data\interim\taxi_trip_data
    mkdir data\interim\weather
    mkdir data\interim\yellow_trip_data
    mkdir data\processed\density
    ```

Folder data besar seperti `data/interim` dan `data/processed/density` masuk `.gitignore`, jadi dataset perlu dibuat atau disiapkan secara lokal.

## Menjalankan Pipeline dari Awal

### 1. Download Data Taxi Raw

Script ini mengambil file Yellow Taxi 2023-2024 dari NYC TLC ke `data/interim/taxi_trip_data`.

```powershell
python src/ingestion/download_taxi_data.py
```

Output:

```text
data/interim/taxi_trip_data/yellow_tripdata_2023-01.parquet
data/interim/taxi_trip_data/yellow_tripdata_2023-02.parquet
...
data/interim/taxi_trip_data/yellow_tripdata_2024-12.parquet
```

### 2. Download Data Zona Taxi

```powershell
python src/ingestion/download_lookup.py
python src/visualization/export_zones_geojson.py
```

Output utama:

```text
data/geo/taxi_zone_lookup.csv
data/geo/taxi_zones.geojson
```

Catatan: `export_zones_geojson.py` membutuhkan file shapefile `data/geo/taxi_zones.shp` dan file pendukungnya sudah tersedia di folder `data/geo`.

### 3. Download Data Cuaca

```powershell
python src/weather/download_weather.py
```

Output:

```text
data/interim/weather/nyc_weather_2023_2024.parquet
```

### 4. Preprocessing Taxi Raw

Script ini mengubah data trip hasil download menjadi agregasi demand per jam dan per zona.

```powershell
python src/preprocessing/preprocess_taxi_data.py
```

Output:

```text
data/processed/hourly_zone_density.parquet
```

Kolom utama:

| Kolom | Deskripsi |
| --- | --- |
| `pickup_hour` | waktu pickup yang sudah dibulatkan per jam |
| `PULocationID` | ID zona pickup NYC Taxi |
| `trip_count` | jumlah trip pada zona dan jam tersebut |

### 5. Merge Taxi dengan Weather

```powershell
python src/feature_engineering/merge_weather.py
```

Output:

```text
data/processed/taxi_weather_merged.parquet
```

Dataset ini dipakai dashboard untuk panel cuaca dan mode perbandingan cuaca.

### 6. Baseline Density Classification

```powershell
python src/feature_engineering/classify_density.py
```

Output:

```text
data/processed/final_density_dataset.parquet
```

Script ini memberi label `Low`, `Medium`, dan `High` berdasarkan threshold `trip_count`. Dataset ini berguna untuk analisis eksploratif, sedangkan dashboard utama memakai label density dari training K-Means.

## Training Density Cluster

Training K-Means berada di:

```text
src/feature_engineering/train_density_clusters.py
```

Input training:

```text
data/interim/yellow_trip_data/*.parquet
```

Folder ini berbeda dari `data/interim/taxi_trip_data`. `taxi_trip_data` berisi file TLC hasil download mentah, sedangkan `yellow_trip_data` berisi data interim yang sudah disiapkan untuk training density.

Schema minimum yang dibutuhkan:

| Kolom | Deskripsi |
| --- | --- |
| `trip_id` | ID unik trip |
| `time_id` | waktu dalam format `YYYYMMDDHH` |
| `weather_id` | ID referensi cuaca |
| `location_id` | ID zona pickup |
| `passenger_count` | jumlah penumpang pada trip |

Jalankan training:

```powershell
python src/feature_engineering/train_density_clusters.py
```

Output training:

| File | Fungsi |
| --- | --- |
| `data/processed/density/temp_cluster_labels.parquet` | agregasi `location_id` + `time_id` dengan total penumpang dan label `Sepi`, `Normal`, `Sibuk` |
| `data/processed/density/fact_density_final.parquet` | fact table level trip yang sudah ditempeli `density_cluster` |

Training menggunakan `KMeans(n_clusters=3, random_state=42)`. Centroid diurutkan dari demand terendah ke tertinggi agar label konsisten:

```text
cluster rendah  -> Sepi
cluster tengah  -> Normal
cluster tinggi  -> Sibuk
```

## Build Dataset Dashboard

Setelah training selesai, jalankan adapter dashboard:

```powershell
python src/feature_engineering/build_dashboard_dataset.py
```

Input:

```text
data/processed/density/temp_cluster_labels.parquet
```

Output:

```text
data/processed/dashboard_density_dataset.parquet
```

Dataset ini adalah data utama untuk peta, statistik demand, filter tanggal/jam, dan Priority Queue di dashboard.

## Data yang Ditampilkan Dashboard

Dashboard Streamlit membaca tiga file utama:

| Dataset | Dipakai Untuk | Kolom Penting |
| --- | --- | --- |
| `data/processed/dashboard_density_dataset.parquet` | peta density, statistik demand, priority queue, tren 24 jam | `pickup_hour`, `PULocationID`, `trip_count`, `density_label` |
| `data/processed/taxi_weather_merged.parquet` | panel weather dan weather comparison | `pickup_hour`, `temperature`, `precipitation`, `weather_code`, `wind_speed` |
| `data/geo/taxi_zones.geojson` | bentuk polygon zona taksi NYC | `LocationID`, `zone`, `borough`, `geometry` |

Contoh isi `dashboard_density_dataset.parquet`:

| pickup_hour | time_id | PULocationID | trip_count | total_passengers | density_level | density_label |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 2023-01-01 00:00:00 | 2023010100 | 100 | 7 | 7.0 | Low | Sepi |
| 2023-01-01 00:00:00 | 2023010100 | 107 | 267 | 267.0 | Medium | Normal |
| 2023-01-01 00:00:00 | 2023010100 | 113 | 96 | 96.0 | Medium | Normal |
| 2023-01-01 00:00:00 | 2023010100 | 114 | 159 | 159.0 | Medium | Normal |
| 2023-01-01 00:00:00 | 2023010100 | 116 | 4 | 4.0 | Low | Sepi |

Snapshot dataset lokal saat README ini dirapikan:

| Dataset | Baris | Ukuran | Kolom |
| --- | ---: | ---: | --- |
| `data/interim/yellow_trip_data/*.parquet` | 79,479,946 | 294.09 MB | `trip_id`, `time_id`, `weather_id`, `location_id`, `passenger_count` |
| `data/processed/density/temp_cluster_labels.parquet` | 1,752,634 | 7.43 MB | `location_id`, `time_id`, `total_passengers`, `density_cluster` |
| `data/processed/density/fact_density_final.parquet` | 73,094,999 | 395.16 MB | `trip_id`, `time_id`, `weather_id`, `location_id`, `passenger_count`, `density_cluster` |
| `data/processed/dashboard_density_dataset.parquet` | 1,752,526 | 6.79 MB | `pickup_hour`, `time_id`, `PULocationID`, `trip_count`, `total_passengers`, `density_level`, `density_label`, `density_cluster` |
| `data/processed/taxi_weather_merged.parquet` | 1,949,093 | 4.30 MB | `pickup_hour`, `PULocationID`, `trip_count`, `temperature`, `precipitation`, `snowfall`, `weather_code`, `wind_speed` |
| `data/processed/final_density_dataset.parquet` | 1,949,093 | 4.62 MB | taxi + weather + `density_level`, `weather_condition` |

Distribusi label density pada dataset dashboard lokal:

| Label | Jumlah Baris |
| --- | ---: |
| `Sepi` | 1,384,081 |
| `Normal` | 290,655 |
| `Sibuk` | 77,790 |

Rentang waktu dataset dashboard:

```text
2023-01-01 00:00:00 sampai 2024-12-31 23:00:00
```

## Menjalankan Dashboard

Pastikan file berikut tersedia:

```text
data/processed/dashboard_density_dataset.parquet
data/processed/taxi_weather_merged.parquet
data/geo/taxi_zones.geojson
```

Jalankan aplikasi Streamlit dari root repository:

```powershell
python -m streamlit run dashboard/app.py
```

Mode dashboard:

| Mode | Fungsi |
| --- | --- |
| `Standard Analytics` | memilih tanggal, jam, dan filter density untuk melihat peta demand, statistik, priority queue, dan tren harian |
| `Weather Comparison` | membandingkan demand pada kondisi cerah dan hujan pada jam yang sama |

## Struktur Project

```text
.
|-- dashboard/
|   `-- app.py                         # Aplikasi utama Streamlit
|-- data/
|   |-- geo/                           # Taxi zones, lookup, GeoJSON
|   |-- interim/                       # Data staging taxi, weather, dan training ML
|   |   |-- taxi_trip_data/             # Yellow Taxi TLC hasil download
|   |   |-- weather/                   # Weather Open-Meteo hasil download
|   |   `-- yellow_trip_data/          # Dataset interim siap training K-Means
|   `-- processed/                     # Dataset hasil olahan
|       `-- density/                   # Output training K-Means
|-- src/
|   |-- feature_engineering/
|   |   |-- train_density_clusters.py  # Training K-Means density
|   |   |-- build_dashboard_dataset.py # Adapter dataset dashboard
|   |   |-- merge_weather.py           # Join taxi hourly dengan weather
|   |   `-- classify_density.py        # Baseline density threshold
|   |-- ingestion/                     # Script download data
|   |-- preprocessing/                 # Script cleaning dan agregasi taxi
|   |-- utils/                         # Utility pengecekan dataset
|   |-- visualization/                 # Export GeoJSON zona taxi
|   `-- weather/                       # Download data cuaca
|-- DASHBOARD_DOCS.md                  # Dokumentasi teknis dashboard
|-- README.md                          # Panduan utama project
`-- requirements.txt                   # Daftar dependency Python
```

## Urutan Command Ringkas

Untuk menyiapkan data taxi-weather:

```powershell
python src/ingestion/download_taxi_data.py
python src/ingestion/download_lookup.py
python src/weather/download_weather.py
python src/preprocessing/preprocess_taxi_data.py
python src/feature_engineering/merge_weather.py
python src/feature_engineering/classify_density.py
```

Untuk menyiapkan data dashboard berbasis K-Means:

```powershell
python src/feature_engineering/train_density_clusters.py
python src/feature_engineering/build_dashboard_dataset.py
```

Untuk menjalankan dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

Catatan: `train_density_clusters.py` membutuhkan file `data/interim/yellow_trip_data/*.parquet`. Folder ini bukan output dari `download_taxi_data.py`; siapkan dulu data interim training dengan schema yang dijelaskan pada bagian training.

## Kelompok 3 - RDV 2026

* **Project Lead**: perancangan skema dan dokumentasi.
* **Data Engineer**: pipeline ingestion dan preprocessing.
* **ML Engineer**: K-Means clustering dan pelabelan density.
* **Data Analyst**: dashboard, visualisasi, dan interpretasi hasil.

---

(c) 2026 Proyek Rekayasa dan Visualisasi Data.
