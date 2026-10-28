"""Download incidents, boundaries and population from the City of Milwaukee."""
import io

import geopandas as gpd
import pandas as pd
import requests

from . import config


def fetch_incidents(session: requests.Session | None = None) -> pd.DataFrame:
    """Page through the WIBR datastore API. Returns raw string columns as published."""
    s = session or requests.Session()
    rows, offset = [], 0
    while True:
        r = s.get(
            config.CKAN_DATASTORE,
            params={
                "resource_id": config.WIBR_RESOURCE_ID,
                "limit": config.CKAN_PAGE_SIZE,
                "offset": offset,
                "fields": ",".join(config.WIBR_FIELDS),
            },
            timeout=300,
        )
        r.raise_for_status()
        records = r.json()["result"]["records"]
        if not records:
            break
        rows.extend(records)
        offset += len(records)
        print(f"  fetched {offset:,} incidents")
    return pd.DataFrame(rows, columns=config.WIBR_FIELDS)


def fetch_boundary(layer_url: str) -> gpd.GeoDataFrame:
    """Query an ArcGIS MapServer layer as GeoJSON in WGS84 (EPSG:4326)."""
    r = requests.get(
        f"{layer_url}/query",
        params={"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": 4326, "f": "geojson"},
        timeout=120,
    )
    r.raise_for_status()
    return gpd.GeoDataFrame.from_features(r.json()["features"], crs="EPSG:4326")


def fetch_alder_population() -> pd.DataFrame:
    """Columns: alder_district (int), population (int). Numbers are published as ' 38,566 '."""
    r = requests.get(config.ALDER_POPULATION_CSV, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]
    out = pd.DataFrame({
        "alder_district": pd.to_numeric(df["Ald. District"], errors="coerce"),
        "population": pd.to_numeric(df["Total Population"].astype(str).str.replace(",", "").str.strip(), errors="coerce"),
    })
    return out.dropna().astype(int)
