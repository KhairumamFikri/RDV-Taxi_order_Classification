import os
import requests
from tqdm import tqdm

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

START_YEAR = 2023
END_YEAR = 2024

OUTPUT_DIR = "data/interim/taxi_trip_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_file(url, output_path):
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        print(f"Gagal download: {url}")
        return

    total_size = int(response.headers.get("content-length", 0))

    with open(output_path, "wb") as file:
        with tqdm(
            desc=output_path,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:

            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
                bar.update(len(chunk))

def main():

    for year in range(START_YEAR, END_YEAR + 1):

        for month in range(1, 13):

            month_str = f"{month:02d}"

            filename = f"yellow_tripdata_{year}-{month_str}.parquet"

            url = f"{BASE_URL}/{filename}"

            output_path = os.path.join(OUTPUT_DIR, filename)

            if os.path.exists(output_path):
                print(f"Sudah ada: {filename}")
                continue

            print(f"Downloading {filename}...")
            download_file(url, output_path)

if __name__ == "__main__":
    main()
