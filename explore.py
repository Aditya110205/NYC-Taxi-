import pandas as pd

df = pd.read_parquet("data/yellow_tripdata_2024-01.parquet")
print(df.shape)
print(df.dtypes)
print(df.isna().sum())
print(df.describe().T)

# Sanity checks: real data is dirty
print("negative fares:", (df.fare_amount < 0).sum())
print("dropoff before pickup:", (df.tpep_dropoff_datetime < df.tpep_pickup_datetime).sum())
print("pickups outside Jan 2024:",
      (~df.tpep_pickup_datetime.between("2024-01-01", "2024-02-01")).sum())