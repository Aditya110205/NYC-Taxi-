-- Q1: pickups per borough
SELECT z.borough, COUNT(*) AS trips
FROM raw.yellow_trips t
JOIN raw.zones z ON z.locationid = t.pulocationid
GROUP BY 1 ORDER BY 2 DESC;

-- Q2: top 10 routes (pickup zone -> dropoff zone)
SELECT pz.zone AS pickup, dz.zone AS dropoff, COUNT(*) AS trips
FROM raw.yellow_trips t
JOIN raw.zones pz ON pz.locationid = t.pulocationid
JOIN raw.zones dz ON dz.locationid = t.dolocationid
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10;

-- Q3: busiest hour per borough
WITH hourly AS (
  SELECT z.borough,
         EXTRACT(HOUR FROM t.tpep_pickup_datetime) AS hr,
         COUNT(*) AS trips
  FROM raw.yellow_trips t
  JOIN raw.zones z ON z.locationid = t.pulocationid
  GROUP BY 1, 2
)
SELECT borough, hr, trips
FROM hourly h
WHERE trips = (SELECT MAX(trips) FROM hourly WHERE borough = h.borough);

-- Q4: top 3 pickup zones per borough (RANK)
WITH z AS (
  SELECT zn.borough, zn.zone, COUNT(*) AS trips
  FROM raw.yellow_trips t JOIN raw.zones zn ON zn.locationid = t.pulocationid
  GROUP BY 1, 2
), ranked AS (
  SELECT *, RANK() OVER (PARTITION BY borough ORDER BY trips DESC) AS rnk FROM z
)
SELECT * FROM ranked WHERE rnk <= 3 ORDER BY borough, rnk;

-- Q5: daily trips, day-over-day change, 7-day moving average
WITH d AS (
  SELECT tpep_pickup_datetime::date AS day, COUNT(*) AS trips
  FROM raw.yellow_trips
  WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2024-02-01'
  GROUP BY 1
)
SELECT day, trips,
       trips - LAG(trips) OVER (ORDER BY day) AS change,
       ROUND(AVG(trips) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)) AS ma7
FROM d ORDER BY day;


EXPLAIN ANALYZE
SELECT COUNT(*) FROM raw.yellow_trips
WHERE pulocationid = 132;

CREATE INDEX idx_pu ON raw.yellow_trips(pulocationid);
ANALYZE raw.yellow_trips;
EXPLAIN ANALYZE SELECT COUNT(*) FROM raw.yellow_trips WHERE pulocationid = 132;

