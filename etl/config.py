from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BUCKET = "taxi-raw"
MINIO = dict(endpoint_url="http://127.0.0.1:9000",
             aws_access_key_id="minioadmin",
             aws_secret_access_key="minioadmin")
PG_DSN = "host=127.0.0.1 port=5433 user=de password=de dbname=taxi"