## NYC TAXI DATA ENGINEERING PROJECT ##


Phase1:Created a Raw Ingestion layer

# Taxi-DE: NYC Yellow Taxi Data Engineering Project

Hands-on data engineering project using NYC Yellow Taxi 2024 data.
Current stage: **Batch pipelines and orchestration**.

## Architecture

```
local Parquet -> S3-compatible object storage (RustFS) -> Postgres (raw schema)
```

- **Landing zone:** raw Parquet files stored untouched, partitioned by month:
  `s3://taxi-raw/yellow/year=YYYY/month=MM/yellow_tripdata_YYYY-MM.parquet`
- **Warehouse:** Postgres in Docker, tables `raw.yellow_trips` and `raw.zones`.

## Project structure

```
Taxi-DE/
├── data/            # source Parquet + taxi_zone_lookup.csv (not committed)
├── etl/
│   ├── config.py    # paths, S3 endpoint, Postgres DSN
│   └── pipeline.py  # land() and load() functions + run()
├── venv/            # not committed
└── README.md
```

## Setup

**Requirements:** Windows, Docker Desktop, Python 3.x

```powershell
python -m venv venv
venv\Scripts\activate
pip install boto3 pyarrow pandas psycopg2-binary
```

**Start services**

```powershell
# Postgres (127.0.0.1:5433, user/pass de/de, db taxi): already created, just start it
docker start <postgres-container-name>

# Object storage (S3-compatible; MinIO images were unavailable, so RustFS is used)
docker run -d --name rustfs -p 9000:9000 -p 9001:9001 `
  -e RUSTFS_ACCESS_KEY=minioadmin -e RUSTFS_SECRET_KEY=minioadmin `
  -v rustfs_data:/data rustfs/rustfs:latest
# next time: docker start rustfs
```

Console: http://127.0.0.1:9001 (minioadmin / minioadmin)

## Run

```powershell
python etl\pipeline.py
```

## How it works

| Step | Function | Behavior |
|------|----------|----------|
| Land | `land(path)` | Uploads file to the bucket; skips if an object of the same size exists |
| Load | `load(key)` | Reads Parquet from storage, lowercases columns, casts integer columns, adds `source_file`, then `DELETE WHERE source_file = X` + `COPY` in **one transaction** |

**Idempotency:** re-running gives identical results. Uploads are overwrite-or-skip, and loads replace a month atomically, so a failure never leaves partial data.

**File filter:** only exact `yellow_tripdata_2024-MM.parquet` names with size > 0 are processed.

## Verify

```sql
SELECT source_file, count(*) FROM raw.yellow_trips GROUP BY 1 ORDER BY 1;
```
Expect 12 rows (one per month), with the same counts after every re-run.

## Known issues

- Every run reloads all months, even unchanged ones (fix planned with per-partition runs).
- Loading via pandas is memory-heavy; fine for ~3M rows per month.
- Credentials are hardcoded for local dev only. Never reuse them in production.

## Roadmap

- [x] Stage 1: Foundations (SQL, joins, CTEs, windows, indexes)
- [x] Day 3: Object storage landing + idempotent ETL
- [ ] Day 4: Orchestration (Dagster or Airflow): partitions, retries, backfills
- [ ] dbt modeling
- [ ] PySpark
- [ ] Kafka streaming
- [ ] Production hardening