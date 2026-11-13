-- Latest scrape of each source, cleaned, one row per gig, music events only.
CREATE SCHEMA IF NOT EXISTS int;

-- Seed: title patterns (regex, matched on lower-case) for events that are not music.
CREATE OR REPLACE TABLE int.non_music_patterns AS
SELECT pattern FROM read_csv('{{seeds_dir}}/non_music_patterns.csv', header = true);

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
  AND NOT EXISTS (
      SELECT 1 FROM int.non_music_patterns p WHERE regexp_matches(lower(r.title), p.pattern)
  )
QUALIFY row_number() OVER (
    PARTITION BY source, venue, date, lower(trim(title))
    ORDER BY url
) = 1;
