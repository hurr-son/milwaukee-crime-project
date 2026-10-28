# Milwaukee Crime Atlas

An interactive map of every crime incident reported in Milwaukee since January 2024 (about 113,000 incidents), with neighborhood, police district and aldermanic district layers on a real basemap.

**Live app:** _add your Streamlit Community Cloud link here_

![Screenshot](docs/screenshot.png) <!-- add after first deploy -->

## Features

- **Map** with light, dark and street basemaps, and layers you can switch on and off:
  - neighborhoods shaded by incident count, or aldermanic districts shaded by incidents per 1,000 residents
  - police district and aldermanic district boundaries with labels
  - a heatmap and clustered individual incidents
- **Filters** by year and offense group (violent, weapons, property, drugs, other)
- **Year-over-year comparison** that matches complete months, so a partial year is never compared with a full one
- **Charts**: monthly trend by year, day-of-week by hour, top neighborhoods, top offenses by FBI NIBRS code
- **Data notes** listing every record dropped during cleaning and why

## Built with

Python · pandas · GeoPandas · Shapely · Folium / Leaflet · Streamlit · Altair · pytest

## Skills demonstrated

| Skill | Where |
|---|---|
| API ingestion (paged CKAN API, ArcGIS REST) | `mke_crime/fetch.py` |
| Data cleaning with an audit trail | `mke_crime/clean.py` |
| Spatial joins (points in polygons) | `mke_crime/geo.py` |
| Domain modeling (NIBRS offense hierarchy) | `mke_crime/nibrs.py` |
| Fair comparisons and per-capita rates | `mke_crime/analysis.py` |
| Interactive web mapping | `mke_crime/maps.py`, `app.py` |
| Testing | `tests/` |

## Run it locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts/build_data.py
streamlit run app.py
```

## Deploy (free public link)

1. Push this repo to GitHub, including `data/processed/`.
2. Go to share.streamlit.io, choose **New app**, pick the repo, and set the main file to `app.py`.

## Data sources

All from the City of Milwaukee:

- [WIBR Crime Data (Current)](https://data.milwaukee.gov/dataset/wibr), the Milwaukee Police Department's incident data
- [Neighborhoods](https://data.milwaukee.gov/dataset/neighborhoods), [Police Districts](https://data.milwaukee.gov/dataset/milwaukee-police-district) and [Alder Districts](https://data.milwaukee.gov/dataset/aldermanic-districts), from the city's ArcGIS services
- [Aldermanic District Demographics](https://data.milwaukee.gov/dataset/aldermanic-district-demographics) (2024 population only)

These are incidents reported to police, not all crime that occurs.
