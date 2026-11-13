-- Latest scrape of each source, cleaned, one row per gig.
CREATE SCHEMA IF NOT EXISTS int;

CREATE OR REPLACE TABLE int.events AS
SELECT
    source,
    venue,
    trim(title) AS title,
    date,
    doors,
    start,
    age_limit,
    url
FROM staging.events_raw r
WHERE scraped_on = (SELECT max(scraped_on) FROM staging.events_raw WHERE source = r.source)
QUALIFY row_number() OVER (
    PARTITION BY source, venue, date, lower(trim(title))
    ORDER BY url
) = 1;
