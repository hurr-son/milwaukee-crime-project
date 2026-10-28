"""Download everything and write the processed files the app reads.

    python scripts/build_data.py            # use cached raw incidents if present
    python scripts/build_data.py --refresh  # re-download incidents
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mke_crime import clean, config, fetch, geo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download incidents even if cached")
    args = ap.parse_args()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = config.RAW_DIR / "wibr.csv"
    if args.refresh or not raw_path.exists():
        print("Downloading incidents from data.milwaukee.gov ...")
        fetch.fetch_incidents().to_csv(raw_path, index=False)
    raw = pd.read_csv(raw_path, dtype=str)

    print("Cleaning ...")
    incidents, report = clean.clean_incidents(raw)

    print("Downloading boundaries ...")
    nb, police, alder = geo.tidy_boundaries(
        fetch.fetch_boundary(config.NEIGHBORHOODS_LAYER),
        fetch.fetch_boundary(config.POLICE_LAYER),
        fetch.fetch_boundary(config.ALDER_LAYER),
    )
    print("Joining incidents to neighborhoods and aldermanic districts ...")
    incidents = geo.assign_areas(incidents, nb, alder)
    report["no_neighborhood"] = int(incidents["neighborhood"].isna().sum())
    report["built"] = pd.Timestamp.now().strftime("%Y-%m-%d")
    report["latest_incident"] = incidents["incident_dt"].max().strftime("%Y-%m-%d")

    incidents.to_parquet(config.INCIDENTS_PARQUET, index=False)
    nb.to_file(config.NEIGHBORHOODS_GEOJSON, driver="GeoJSON")
    police.to_file(config.POLICE_GEOJSON, driver="GeoJSON")
    alder.to_file(config.ALDER_GEOJSON, driver="GeoJSON")
    fetch.fetch_alder_population().to_csv(config.POPULATION_CSV, index=False)
    config.REPORT_JSON.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"Wrote {config.PROCESSED_DIR}")


if __name__ == "__main__":
    main()
