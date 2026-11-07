import io
import sys
import pyarrow.parquet as pq
import psycopg2

DB = dict(host="localhost", port=5433, dbname="taxi", user="de", password="de")
BATCH_SIZE = 100_000


def load_file(path: str):
    source = path.split("/")[-1]
    pf = pq.ParquetFile(path)
    conn = psycopg2.connect(**DB)

    try:
        with conn, conn.cursor() as cur:
            # Idempotency: remove any previous load of this file first.
            # Delete + insert in ONE transaction, so it either fully
            # succeeds or fully rolls back.
            cur.execute("DELETE FROM raw.yellow_trips WHERE source_file = %s", (source,))

            total = 0
            for batch in pf.iter_batches(batch_size=BATCH_SIZE):
                df = batch.to_pandas()
                df.columns = [c.lower() for c in df.columns]
                df["source_file"] = source

                buf = io.StringIO()
                df.to_csv(buf, index=False, header=False)
                buf.seek(0)

                cols = ",".join(df.columns)
                cur.copy_expert(
                    f"COPY raw.yellow_trips ({cols}) FROM STDIN WITH (FORMAT csv)", buf
                )
                total += len(df)
                print(f"  loaded {total:,} rows")
    finally:
        conn.close()
    print(f"Done: {source}, {total:,} rows")


if __name__ == "__main__":
    load_file(sys.argv[1])