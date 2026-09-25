-- Hourly yellow-taxi demand aggregates (DuckDB dialect).
-- Input views registered by Python:
--   trips  (cleaned TLC rows with pickup_hour, PULocationID, total_amount, ...)
--   zones  (taxi_zone_lookup: LocationID, Borough, Zone, service_zone)
--
-- Produces one row per (pickup_hour, PULocationID) with trip + revenue KPIs.

WITH base AS (
  SELECT
    pickup_hour,
    PULocationID,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS revenue,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(fare_amount) AS avg_fare,
    AVG(passenger_count) AS avg_passengers
  FROM trips
  GROUP BY 1, 2
)
SELECT
  b.pickup_hour,
  b.PULocationID AS location_id,
  COALESCE(z.Borough, 'Unknown') AS borough,
  COALESCE(z.Zone, 'Unknown') AS zone_name,
  COALESCE(z.service_zone, 'Unknown') AS service_zone,
  EXTRACT(hour FROM b.pickup_hour)::INTEGER AS hour_of_day,
  EXTRACT(dow FROM b.pickup_hour)::INTEGER AS day_of_week,  -- DuckDB: 0=Sunday
  b.trip_count,
  ROUND(b.revenue, 2) AS revenue,
  ROUND(b.avg_trip_distance, 3) AS avg_trip_distance,
  ROUND(b.avg_fare, 2) AS avg_fare,
  ROUND(b.avg_passengers, 2) AS avg_passengers
FROM base b
LEFT JOIN zones z ON z.LocationID = b.PULocationID
ORDER BY b.pickup_hour, b.trip_count DESC;
