import requests

url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

response = requests.get(url)

with open("data/geo/taxi_zone_lookup.csv", "wb") as f:
    f.write(response.content)

print("Taxi zone lookup downloaded.")