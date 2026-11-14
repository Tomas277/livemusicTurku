# Live Music Turku

## Testing locally

```bash
python -m pytest -q
cp data/warehouse/events_history.csv /tmp/hist.csv
LIVEMUSIC_HISTORY=/tmp/hist.csv LIVEMUSIC_SOURCES=fuuga python -m pipeline.run   # only Fuuga; Logomo is slow
python -m site_builder.build
python -m http.server -d site 8000                       # http://localhost:8000/fi/
```

For template/CSS-only changes skip the scrape and just rerun the build step.
