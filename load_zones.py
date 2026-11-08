import pandas as pd, psycopg2, io

DB = dict(host="127.0.0.1", port=5433, dbname="taxi", user="de", password="de")
df = pd.read_csv("data/taxi_zone_lookup.csv")
df.columns = [c.lower() for c in df.columns]

conn = psycopg2.connect(**DB)
with conn, conn.cursor() as cur:
    cur.execute("""CREATE TABLE IF NOT EXISTS raw.zones (
        locationid INT PRIMARY KEY, borough TEXT, zone TEXT, service_zone TEXT)""")
    cur.execute("TRUNCATE raw.zones")
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)
    cur.copy_expert("COPY raw.zones FROM STDIN WITH (FORMAT csv)", buf)
print(len(df), "zones loaded")