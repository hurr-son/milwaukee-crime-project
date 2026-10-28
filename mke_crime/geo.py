"""Spatial joins: tag each incident with the neighborhood and aldermanic district it falls in."""
import geopandas as gpd
import pandas as pd


def tidy_boundaries(neighborhoods: gpd.GeoDataFrame, police: gpd.GeoDataFrame, alder: gpd.GeoDataFrame):
    """Rename source fields to the names the app uses and lightly simplify for fast map rendering."""
    nb = neighborhoods.rename(columns={"NEIGHBORHD": "neighborhood"})[["neighborhood", "geometry"]].copy()
    nb["neighborhood"] = nb["neighborhood"].str.strip().str.title()
    pd_ = police.rename(columns={"POLICE": "police_district"})[["police_district", "geometry"]].copy()
    pd_["police_district"] = pd_["police_district"].astype(int)
    al = alder.rename(columns={"DISTRICT": "alder_district", "ALDERPERSON": "alderperson"})
    al = al[["alder_district", "alderperson", "geometry"]].copy()
    al["alder_district"] = al["alder_district"].astype(int)
    for g in (nb, pd_, al):
        g["geometry"] = g.geometry.simplify(0.00005, preserve_topology=True)
    return nb, pd_, al


def _join_one(points: gpd.GeoDataFrame, areas: gpd.GeoDataFrame, column: str) -> pd.Series:
    joined = gpd.sjoin(points, areas[[column, "geometry"]], how="left", predicate="within")
    # A point on a shared border can match two polygons; keep the first
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined[column]


def assign_areas(incidents: pd.DataFrame, neighborhoods: gpd.GeoDataFrame, alder: gpd.GeoDataFrame) -> pd.DataFrame:
    df = incidents.copy()
    has_xy = df["lat"].notna() & df["lon"].notna()
    pts = gpd.GeoDataFrame(
        df.loc[has_xy, []],
        geometry=gpd.points_from_xy(df.loc[has_xy, "lon"], df.loc[has_xy, "lat"]),
        crs="EPSG:4326",
    )
    df["neighborhood"] = _join_one(pts, neighborhoods, "neighborhood").reindex(df.index)
    df["alder_district"] = _join_one(pts, alder, "alder_district").reindex(df.index).astype("Int64")
    return df
