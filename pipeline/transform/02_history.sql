-- Merge today's scrape into the history. One row per gig; we remember when it was
-- first and last seen. Gigs that vanish from a venue's site are kept, with an old
-- last_seen, so cancellations stay visible. Sources not scraped today are untouched.
CREATE SCHEMA IF NOT EXISTS history;

CREATE TABLE IF NOT EXISTS history.events_history (
    source VARCHAR, venue VARCHAR, title VARCHAR, date DATE,
    doors VARCHAR, start VARCHAR, age_limit INTEGER, url VARCHAR,
    access VARCHAR, availability VARCHAR, first_seen DATE, last_seen DATE
);

CREATE OR REPLACE TABLE history.events_history AS
SELECT e.source, e.venue, e.title, e.date, e.doors, e.start, e.age_limit, e.url,
       e.access, e.availability,
       coalesce(h.first_seen, DATE '{{today}}') AS first_seen,
       DATE '{{today}}' AS last_seen
FROM int.events e
LEFT JOIN history.events_history h
       ON (h.source, h.venue, h.date, h.title) = (e.source, e.venue, e.date, e.title)
UNION ALL
SELECT h.source, h.venue, h.title, h.date, h.doors, h.start, h.age_limit, h.url,
       h.access, h.availability,
       h.first_seen, h.last_seen
FROM history.events_history h
WHERE NOT EXISTS (
    SELECT 1 FROM int.events e
    WHERE (e.source, e.venue, e.date, e.title) = (h.source, h.venue, h.date, h.title)
);
