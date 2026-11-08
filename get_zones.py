import requests

url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
r = requests.get(url, timeout=30)
r.raise_for_status()
open("data/taxi_zone_lookup.csv", "wb").write(r.content)
print("saved", len(r.content), "bytes")