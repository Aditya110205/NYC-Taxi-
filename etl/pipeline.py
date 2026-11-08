import io, logging, re, sys
import boto3
import psycopg2
import pyarrow.parquet as pq
from botocore.exceptions import ClientError
from config import *

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("etl")

s3 = boto3.client("s3", **MINIO)

INT_COLS = ["vendorid", "passenger_count", "ratecodeid",
            "pulocationid", "dolocationid", "payment_type"]

def object_key(path):
    m = re.search(r"(\d{4})-(\d{2})", path.name)
    return f"yellow/year={m[1]}/month={m[2]}/{path.name}"

def ensure_bucket():
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        log.info("created bucket %s", BUCKET)

def land(path):
    """Local file -> object storage. Skips if same size already there."""
    key = object_key(path)
    try:
        head = s3.head_object(Bucket=BUCKET, Key=key)
        if head["ContentLength"] == path.stat().st_size:
            log.info("skip upload (exists): %s", key)
            return key
    except ClientError:
        pass
    s3.upload_file(str(path), BUCKET, key)
    log.info("uploaded %s", key)
    return key

def load(key):
    """Object storage -> Postgres raw.yellow_trips, idempotent per source_file."""
    fname = key.split("/")[-1]
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    df = pq.read_table(io.BytesIO(body)).to_pandas()

    df.columns = [c.lower() for c in df.columns]
    for c in INT_COLS:
        if c in df.columns:
            df[c] = df[c].astype("Int64")
    df["source_file"] = fname
    cols = list(df.columns)

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)

    with psycopg2.connect(PG_DSN) as conn:   # one transaction
        with conn.cursor() as cur:
            cur.execute("DELETE FROM raw.yellow_trips WHERE source_file = %s", (fname,))
            deleted = cur.rowcount
            cur.copy_expert(
                f"COPY raw.yellow_trips ({', '.join(cols)}) FROM STDIN WITH CSV", buf)
            loaded = cur.rowcount
    conn.close()
    log.info("%s: deleted %d, loaded %d", fname, deleted, loaded)
    return loaded

def run():
    ensure_bucket()
    files = sorted(f for f in DATA_DIR.glob("yellow_tripdata_2024-*.parquet")
                   if re.fullmatch(r"yellow_tripdata_2024-\d{2}\.parquet", f.name)
                   and f.stat().st_size > 0)
    log.info("found %d files", len(files))
    for f in files:
        try:
            load(land(f))
        except Exception:
            log.exception("failed: %s", f.name)
            sys.exit(1)

if __name__ == "__main__":
    run()