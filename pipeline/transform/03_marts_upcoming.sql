-- What the website shows: for each source, the gigs from its most recent successful
-- scrape, from today onwards. If a source failed today, that is its last good scrape,
-- so its gigs stay on the site - but only for 7 days, after which they are dropped
-- rather than shown stale.
CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE TABLE marts.upcoming_events AS
WITH latest AS (
    SELECT source, max(last_seen) AS last_ok FROM history.events_history GROUP BY source
)
SELECT h.venue, h.title, h.date, h.doors, h.start, h.age_limit, h.url,
       h.access, h.availability
FROM history.events_history h
JOIN latest l ON l.source = h.source
WHERE h.last_seen = l.last_ok
  AND l.last_ok >= DATE '{{today}}' - 7
  AND h.date >= DATE '{{today}}'
ORDER BY h.date, coalesce(h.start, h.doors), h.venue;
