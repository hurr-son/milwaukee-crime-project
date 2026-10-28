"""Source URLs and file paths. Every external endpoint the project touches is listed here."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

INCIDENTS_PARQUET = PROCESSED_DIR / "incidents.parquet"
NEIGHBORHOODS_GEOJSON = PROCESSED_DIR / "neighborhoods.geojson"
POLICE_GEOJSON = PROCESSED_DIR / "police_districts.geojson"
ALDER_GEOJSON = PROCESSED_DIR / "alder_districts.geojson"
POPULATION_CSV = PROCESSED_DIR / "alder_population.csv"
REPORT_JSON = PROCESSED_DIR / "report.json"

# City of Milwaukee Open Data Portal (CKAN). WIBR = Wisconsin Incident Based Reporting.
CKAN_DATASTORE = "https://data.milwaukee.gov/api/3/action/datastore_search"
WIBR_RESOURCE_ID = "87843297-a6fa-46d4-ba5d-cb342fb2d3bb"  # "WIBR Crime Data (Current)", 2024 to present
WIBR_DATASET_URL = "https://data.milwaukee.gov/dataset/wibr"
WIBR_FIELDS = [
    "Case_Number", "Incident_Date", "Police_District", "Offense_All",
    "Location_All", "Address_Latitude", "Address_Longitude", "Weapon_Used_All",
]
CKAN_PAGE_SIZE = 32000

# City ArcGIS MapServer layers (queried as GeoJSON in WGS84)
ARCGIS = "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services"
NEIGHBORHOODS_LAYER = f"{ARCGIS}/planning/special_districts/MapServer/4"  # field NEIGHBORHD, 190 areas
POLICE_LAYER = f"{ARCGIS}/MPD/MPD_geography/MapServer/2"                  # field POLICE, 7 districts
ALDER_LAYER = f"{ARCGIS}/election/alderman/MapServer/0"                    # fields DISTRICT, ALDERPERSON, 15 districts

# 2024 population by aldermanic district (used for rates per 1,000 residents)
ALDER_POPULATION_CSV = (
    "https://data.milwaukee.gov/dataset/7466c225-7e79-4bf3-9260-81f451cb2b59/resource/"
    "b9b3018b-8742-4f13-af4b-40dd2043925d/download/aldermanicdistrictdemographics2024.csv"
)

# Coordinates outside this box are treated as missing (Milwaukee city limits plus a margin)
LAT_RANGE = (42.84, 43.22)
LON_RANGE = (-88.10, -87.82)
MAP_CENTER = (43.05, -87.95)

# Basemaps. CARTO's light/dark tiles need a free API key (carto.com/basemaps/apikey); set
# CARTO_API_KEY as an environment variable or a Streamlit secret to use them. Without a key
# the map uses OpenStreetMap, faded for the light basemap.
CARTO_API_KEY = os.environ.get("CARTO_API_KEY", "")
CARTO_TILES = "https://basemaps.cartocdn.com/rastertiles/{style}/{{z}}/{{x}}/{{y}}.png?key={key}"
CARTO_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors '
    '&copy; <a href="https://carto.com/attributions">CARTO</a>'
)
