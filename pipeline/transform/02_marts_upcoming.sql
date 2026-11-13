-- What the website shows: gigs from today onwards, in date order.
CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE TABLE marts.upcoming_events AS
SELECT venue, title, date, doors, start, age_limit, url
FROM int.events
WHERE date >= DATE '{{today}}'
ORDER BY date, coalesce(start, doors), venue;
