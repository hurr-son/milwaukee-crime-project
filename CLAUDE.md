# Milwaukee Crime Atlas

Portfolio project: an interactive, public web map of reported crime in Milwaukee (2024 to present), aimed at recruiters for data analyst / data science roles. It must be easy to open from a link (Streamlit Community Cloud) and easy to read in under a minute.

## Status

Runs end to end (checked 2026-10-28 on Python 3.12, pandas 3.1, Streamlit 1.66): tests and ruff pass, the pipeline builds `data/processed/`, and the app renders every filter combination without errors. Not yet deployed. In WSL/Linux the venv is `.venv/bin/python` instead of `.venv\Scripts\python.exe`.

Basemaps: CARTO tiles now need a free API key. Without `CARTO_API_KEY` (env var or Streamlit secret) the map uses a faded OpenStreetMap as the light basemap; with it, CARTO light and dark come back.

## Commands (Windows, PowerShell)

```powershell
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest                                  # unit tests
python scripts/build_data.py            # download + process (~1-2 min); add --refresh to re-download incidents
streamlit run app.py                    # http://localhost:8501
ruff check .
```

## Layout

- `mke_crime/config.py`: every URL and file path. Change endpoints here only.
- `mke_crime/fetch.py`: downloads. WIBR incidents via the CKAN datastore API (paged, 32k rows/page); boundaries via ArcGIS MapServer `/query?f=geojson&outSR=4326`; population CSV.
- `mke_crime/clean.py`: raw rows to one tidy row per incident, plus a `report` dict of what was dropped and why.
- `mke_crime/nibrs.py`: NIBRS offense code names and the offense-group hierarchy.
- `mke_crime/geo.py`: boundary tidying and spatial joins (incident to neighborhood and aldermanic district).
- `mke_crime/analysis.py`: aggregations used by the app (YoY, monthly, weekday×hour, area counts, rates).
- `mke_crime/maps.py`: the Folium map (basemaps, shaded layer, district outlines, heatmap, clustered points).
- `app.py`: Streamlit UI. Reads only `data/processed/`.
- `scripts/build_data.py`: the pipeline entry point. Writes `data/processed/`.

## Data facts (verified 2026-10-28)

- WIBR resource `87843297-a6fa-46d4-ba5d-cb342fb2d3bb`: ~112.8k rows, Jan 2024 to present, updated daily. All fields are strings.
- `Offense_All` is semicolon-separated NIBRS codes, e.g. `13B;290`. `Weapon_Used_All` is often blank.
- Known quirks: one incident dated 2027 (dropped as future); ~800 rows without coordinates; the 00:00 hour is inflated (unknown times logged at midnight); `FIREARM` and `HANDGUN` are separate weapon values.
- Boundary fields: neighborhoods `NEIGHBORHD` (190, uppercase names), police `POLICE` (7), aldermanic `DISTRICT` + `ALDERPERSON` (15).
- Population exists only per aldermanic district (~38k each), so per-capita rates are only shown for aldermanic districts. Neighborhood shading is raw counts and the UI says so.

## Conventions

- Offense group = most serious among the incident's codes: Violent > Weapons > Property > Drugs > Other. Keep `nibrs.CATEGORIES` order as the single source of truth.
- Year-over-year always compares the same complete months (`analysis.yoy_change`). Never compare a partial year with a full one.
- Year colors are fixed everywhere: 2024 `#2a78d6`, 2025 `#eb6834`, 2026 `#1baf7a`. Magnitude uses a single-hue blue ramp.
- Keep `app.py` thin; put logic in `mke_crime/` with a test.
- `data/raw/` is gitignored; `data/processed/` is committed so the deployed app works without running the pipeline.

## Framing and ethics

- Say "reported incidents", not "crime". Data reflects what is reported to MPD.
- Don't label neighborhoods "dangerous" or rank them as places to avoid.
- Don't place crime counts beside race or ethnicity data, even though the population CSV contains those columns. Use only `Total Population`.
- Don't show street addresses in a way that identifies victims; clustered points without popups is the current choice.

## Ideas / next steps

1. Get it running locally and fix bugs (see Status).
2. Deploy to Streamlit Community Cloud; put the link and a screenshot in README.md.
3. Neighborhood rates using Census tract population (areal interpolation of tracts to neighborhoods).
4. Change-over-time map: neighborhood YoY change on a diverging scale.
5. GitHub Action to rebuild `data/processed/` weekly.
6. Add the WIBR archive (2005–2023) for a long-run trend.
