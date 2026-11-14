-- Today's scrape of each source, cleaned, one row per gig, music events only.
CREATE SCHEMA IF NOT EXISTS int;

-- Seed: title patterns (regex, matched on lower-case) for events that are not music.
CREATE OR REPLACE TABLE int.non_music_patterns AS
SELECT pattern FROM read_csv('{{seeds_dir}}/non_music_patterns.csv', header = true);

-- A gig's identity: its title in lower case with punctuation and spacing ignored, so a venue
-- fixing a typo or changing "BAND X" to "Band X!" does not turn the gig into a new one.
CREATE OR REPLACE MACRO title_key(t) AS
    trim(regexp_replace(lower(t), '[^\p{L}\p{N}]+', ' ', 'g'));

CREATE OR REPLACE TABLE int.events AS
SELECT
    source,
    venue,
    trim(title) AS title,
    date,
    doors,
    start,
    age_limit,
    url,
    access,
    availability
FROM staging.events_raw r
WHERE scraped_on = DATE '{{today}}'
  AND NOT EXISTS (
      SELECT 1 FROM int.non_music_patterns p WHERE regexp_matches(lower(r.title), p.pattern)
  )
QUALIFY row_number() OVER (
    PARTITION BY source, venue, date, title_key(title)
    ORDER BY url
) = 1;
