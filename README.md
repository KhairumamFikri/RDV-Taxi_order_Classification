# RDV Taxi Order Classification

Project Rekayasa dan Visualisasi Data untuk menganalisis kepadatan permintaan taksi di New York City berdasarkan lokasi, waktu, dan cuaca.

## Ringkasan Project

Project ini membangun alur data sederhana untuk:

- mengunduh data perjalanan taksi NYC TLC,
- mengambil data cuaca historis dari Open-Meteo,
- menggabungkan keduanya per jam dan per zona,
- memberi label kepadatan zona,
- menampilkan hasilnya dalam dashboard interaktif berbasis peta.

Sumber data yang digunakan:

- NYC TLC Yellow Taxi Trip Data
- Open-Meteo Archive API
- NYC Taxi Zone shapefile / GeoJSON

Output utama yang dihasilkan:

- `data/processed/hourly_zone_density.parquet`
- `data/processed/taxi_weather_merged.parquet`
- `data/processed/final_density_dataset.parquet`
- `data/geo/taxi_zones.geojson`

## Apakah Repo Ini Bisa Dijalankan?

Ya, repo ini bisa dijalankan sebagai pipeline Python lokal dan dashboard Streamlit, dengan beberapa syarat:

- Python sudah terpasang
- dependency di `requirements.txt` sudah di-install
- koneksi internet tersedia untuk mengunduh data
- folder data raw/processed bisa dibuat ulang oleh script

Catatan penting:

- Implementasi saat ini masih memakai pipeline manual, belum Prefect.
- Penyimpanan analitik masih memakai Parquet, belum DuckDB.
- Klasifikasi kepadatan masih berbasis threshold, belum K-Means.
- Data cuaca yang dipakai adalah historis dari Open-Meteo Archive, bukan real-time.

## Struktur Repo

- `src/ingestion/`
  - download data taksi dan lookup zona
- `src/weather/`
  - download data cuaca Open-Meteo
- `src/preprocessing/`
  - bersihkan dan agregasi data taksi per jam dan zona
- `src/feature_engineering/`
  - merge data cuaca dan klasifikasi kepadatan
- `src/visualization/`
  - ekspor zona taksi ke GeoJSON
- `dashboard/`
  - aplikasi Streamlit untuk visualisasi interaktif
- `data/geo/`
  - file shapefile dan GeoJSON zona taksi
- `data/processed/`
  - output hasil olahan data

## Setup Environment

Contoh setup di Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika kamu memakai macOS/Linux, aktifkan virtual environment dengan cara yang sesuai sistem operasimu.

## Cara Menjalankan Pipeline

Urutan eksekusi yang disarankan:

```powershell
python src/ingestion/download_lookup.py
python src/ingestion/download_taxi_data.py
python src/weather/download_weather.py
python src/preprocessing/preprocess_taxi_data.py
python src/feature_engineering/merge_weather.py
python src/feature_engineering/classify_density.py
python src/visualization/export_zones_geojson.py
```

Setelah semua file processed terbentuk, jalankan dashboard:

```powershell
streamlit run dashboard/app.py
```

## Alur Data

1. `download_lookup.py`
   - mengunduh referensi zona taksi ke `data/geo/taxi_zone_lookup.csv`

2. `download_taxi_data.py`
   - mengunduh Yellow Taxi Trip Data ke `data/raw/taxi/`
   - saat ini script menarget tahun 2023 sampai 2024

3. `download_weather.py`
   - mengunduh data cuaca historis NYC ke `data/raw/weather/nyc_weather_2023_2024.parquet`

4. `preprocess_taxi_data.py`
   - mengambil kolom penting
   - menghapus null
   - membulatkan waktu ke per jam
   - menghitung jumlah trip per zona dan jam

5. `merge_weather.py`
   - menggabungkan data trip dengan data cuaca berdasarkan `pickup_hour`

6. `classify_density.py`
   - memberi label `Low`, `Medium`, `High` berdasarkan `trip_count`
   - memberi label kondisi cuaca dari `weather_code`

7. `export_zones_geojson.py`
   - mengubah shapefile zona taksi menjadi GeoJSON agar mudah dipakai dashboard

8. `dashboard/app.py`
   - menampilkan peta zona taksi
   - menyediakan filter tanggal dan jam
   - menampilkan ringkasan cuaca dan kepadatan

## Output yang Diharapkan

Setelah pipeline selesai, file berikut seharusnya tersedia:

- `data/processed/hourly_zone_density.parquet`
- `data/processed/taxi_weather_merged.parquet`
- `data/processed/final_density_dataset.parquet`
- `data/geo/taxi_zones.geojson`

Dashboard kemudian membaca `final_density_dataset.parquet` dan `taxi_zones.geojson` untuk menampilkan peta kepadatan.

## Detail Implementasi Saat Ini

Implementasi yang sudah ada di repo ini:

- ingestion data taksi NYC TLC
- ingestion data cuaca Open-Meteo
- preprocessing dan agregasi per jam
- merge data cuaca
- klasifikasi kepadatan berbasis aturan
- ekspor data geospasial ke GeoJSON
- dashboard Streamlit dengan choropleth map

Hal yang masih menjadi gap terhadap proposal awal:

- Prefect untuk scheduling otomatis
- DuckDB sebagai layer analitik
- K-Means clustering untuk klasifikasi
- dokumentasi runbook yang lebih formal
- validasi data dan automated test
- pemisahan scope data menjadi 1 bulan penuh

## Tips Jika Ingin Menyesuaikan Scope 1 Bulan

Proposal project menyebut batasan 1 bulan data, tetapi script saat ini menarget rentang 2023-2024. Jika ingin mengikuti proposal secara ketat, ubah parameter berikut sebelum menjalankan:

- `START_YEAR` dan `END_YEAR` di `src/ingestion/download_taxi_data.py`
- `start_date` dan `end_date` di `src/weather/download_weather.py`
- filter tanggal di `src/preprocessing/preprocess_taxi_data.py`

## Troubleshooting Singkat

- Jika dashboard tidak menampilkan data, pastikan semua file Parquet dan GeoJSON sudah dibuat.
- Jika dependency belum terpasang, jalankan ulang `pip install -r requirements.txt`.
- Jika download data gagal, cek koneksi internet karena script mengambil data dari sumber eksternal.

## Status Project

Project ini sudah cukup untuk dijalankan sebagai prototype analisis historis dan dashboard interaktif. Untuk menjadikannya lebih kuat sebagai deliverable akhir, langkah berikutnya adalah merapikan scope data, menambah K-Means, dan menambahkan layer penyimpanan/query seperti DuckDB.
