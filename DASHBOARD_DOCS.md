# Technical Documentation: Smart Taxi Radar Dashboard

Dokumen ini menjelaskan arsitektur, sumber data, dan alur logika yang digunakan dalam pengembangan dashboard **Smart Taxi Radar**.

## 1. Arsitektur Data Pipeline

Dashboard ini merupakan tahap akhir (Visualisasi) dari pipeline data yang terdiri dari:

1.  **Ingestion**: Pengambilan data internal (NYC TLC Trip Records) dan data eksternal (Open-Meteo API).
2.  **Preprocessing**: Pembersihan data, konversi koordinat (NYC State Plane ke Lat/Lon), dan agregasi per jam per zona.
3.  **Clustering (ML)**: Proses pelabelan tingkat kepadatan (Sepi, Normal, Sibuk) menggunakan algoritma K-Means berdasarkan fitur jumlah penumpang.
4.  **Adapter**: Transformasi hasil clustering menjadi dataset ringan yang siap dikonsumsi oleh Streamlit.
5.  **Visualization**: Dashboard interaktif untuk Decision Support System (DSS).

---

## 2. Sumber Data & Dataset

Dashboard menggunakan dua sumber data utama untuk menyeimbangkan performa dan kedalaman informasi:

### A. Data Kepadatan (Density Engine)
*   **File Utama**: `data/processed/dashboard_density_dataset.parquet`
*   **Sumber Asli**: `data/processed/density/temp_cluster_labels.parquet`
*   **Konten**: `location_id`, `time_id`, `total_passengers`, `density_cluster`.
*   **Fungsi**: Digunakan untuk menampilkan peta choropleth, marker zona, dan tabel Priority Queue. Ini adalah data hasil training model K-Means.

### B. Data Cuaca (Weather Engine)
*   **File Utama**: `data/processed/taxi_weather_merged.parquet`
*   **Konten**: `pickup_hour`, `temperature`, `precipitation`, `weather_code`, `trip_count`.
*   **Fungsi**: Digunakan untuk fitur **Weather Comparison** (membandingkan kondisi cerah vs hujan) dan widget informasi cuaca real-time pada dashboard.

---

## 3. Alur Logika Kode (dashboard/app.py)

Kode dashboard dirancang dengan urutan eksekusi sebagai berikut:

1.  **Initialization**: 
    *   Konfigurasi tema "Midnight Modern" (CSS Injection).
    *   Setup `pyproj` untuk reproyeksi koordinat GeoJSON agar zona taksi NYC tampil tepat di atas peta Mapbox/Plotly.
2.  **Data Loading**:
    *   Fungsi `load_data` membaca dataset secara *cached* untuk efisiensi.
    *   **Data Resilience**: Terdapat fungsi `normalize_density_df` untuk menangani jika ada kolom yang hilang, sehingga dashboard tidak *crash*.
3.  **Control Center (Sidebar)**:
    *   Menerima input user (Tanggal, Jam, Filter Kepadatan).
    *   Switching Mode: Antara "Standard Analytics" (eksplorasi harian) dan "Weather Comparison" (analisis dampak cuaca).
4.  **Processing Snapshot**:
    *   Sistem melakukan *filtering* pada jam yang dipilih.
    *   Khusus mode **Comparison**, sistem mencari dua sampel tanggal berbeda pada jam yang sama: satu dengan `precipitation == 0` (Cerah) dan satu dengan `precipitation > 2.0` (Hujan).
5.  **Rendering**:
    *   **Map Mapping**: Menggunakan `go.Choroplethmap` untuk area zona dan `go.Scattermap` untuk marker interaktif.
    *   **Priority Queue**: Visualisasi bar chart + table untuk area dengan demand tertinggi.
    *   **Hourly Stats**: Grafik tren 24 jam menggunakan `go.Scatter` dengan area fill.

---

## 4. Cara Interpretasi Visual

*   **Warna Hijau (Sepi)**: Demand rendah, ketersediaan taksi kemungkinan tinggi.
*   **Warna Oranye (Normal)**: Kondisi pasar stabil.
*   **Warna Merah (Sibuk)**: Demand sangat tinggi. Jika disertai info cuaca "Hujan", ini adalah sinyal bagi operator untuk mendistribusikan lebih banyak armada ke zona tersebut.

---
*Dokumentasi ini dibuat untuk Proyek RDV Kelompok 3 - 2026*
