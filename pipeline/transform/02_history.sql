-- Merge today's scrape into the history. One row per gig; we remember when it was
-- first and last seen. Gigs that vanish from a venue's site are kept, with an old
-- last_seen, so cancellations stay visible. Sources not scraped today are untouched.
-- history.events_history is created by history.restore() before this runs.
CREATE SCHEMA IF NOT EXISTS history;

-- A gig is the same gig when source, venue, date and title_key(title) match (see 01_int_events.sql).
-- It keeps the venue's current title and the earliest first_seen.
CREATE OR REPLACE TABLE history.events_history AS
WITH known AS (
    SELECT source, venue, date, title_key(title) AS key, min(first_seen) AS first_seen
    FROM history.events_history
    GROUP BY source, venue, date, title_key(title)
)
SELECT e.source, e.venue, e.title, e.date, e.doors, e.start, e.age_limit, e.url,
       e.access, e.availability,
       coalesce(k.first_seen, DATE '{{today}}') AS first_seen,
       DATE '{{today}}' AS last_seen
FROM int.events e
LEFT JOIN known k
       ON (k.source, k.venue, k.date, k.key) = (e.source, e.venue, e.date, title_key(e.title))
UNION ALL
SELECT h.source, h.venue, h.title, h.date, h.doors, h.start, h.age_limit, h.url,
       h.access, h.availability,
       h.first_seen, h.last_seen
FROM history.events_history h
WHERE NOT EXISTS (
    SELECT 1 FROM int.events e
    WHERE (e.source, e.venue, e.date, title_key(e.title)) = (h.source, h.venue, h.date, title_key(h.title))
);
