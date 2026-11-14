# Live Music Turku

## Testing locally

```bash
pip install -r requirements-dev.txt
python -m pytest -q
cp data/warehouse/events_history.csv /tmp/hist.csv
LIVEMUSIC_HISTORY=/tmp/hist.csv LIVEMUSIC_SOURCES=fuuga python -m pipeline.run   # only Fuuga; Logomo is slow
LIVEMUSIC_HISTORY=/tmp/hist.csv python -m site_builder.build   # the site is built from the history CSV
python -m http.server -d site 8000                       # http://localhost:8000/fi/
```

For template/CSS-only changes skip the scrape and just rerun the build step.
