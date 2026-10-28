"""Build the Folium map: basemaps, a shaded area layer, district outlines, heatmap and points."""
import branca.colormap as cm
import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import FastMarkerCluster, HeatMap

from . import config

HEATMAP_MAX_POINTS = 40_000  # keeps the page responsive in the browser


def _shaded_layer(areas: gpd.GeoDataFrame, value_col: str, label_col: str, label: str, value_fmt: str, name: str):
    vals = areas[value_col].fillna(0)
    cmap = cm.linear.Blues_09.scale(0, max(float(vals.max()), 1))
    cmap.caption = label
    layer = folium.GeoJson(
        areas.to_json(),
        name=name,
        style_function=lambda f: {
            "fillColor": cmap(f["properties"].get(value_col) or 0),
            "fillOpacity": 0.65 if f["properties"].get(value_col) else 0.0,
            "color": "#4a5765",
            "weight": 0.6,
        },
        highlight_function=lambda f: {"weight": 2.5, "color": "#0e1720"},
        tooltip=folium.GeoJsonTooltip(fields=[label_col, value_col], aliases=["", value_fmt], localize=True, sticky=True),
    )
    return layer, cmap


def _outline_layer(areas: gpd.GeoDataFrame, label_col: str, prefix: str, name: str, color: str, dash: str, show: bool):
    group = folium.FeatureGroup(name=name, show=show)
    folium.GeoJson(
        areas.to_json(),
        style_function=lambda f: {"fill": False, "color": color, "weight": 2, "dashArray": dash},
        tooltip=folium.GeoJsonTooltip(fields=[label_col], aliases=[prefix]),
    ).add_to(group)
    for _, row in areas.iterrows():
        p = row.geometry.representative_point()
        folium.Marker(
            [p.y, p.x],
            icon=folium.DivIcon(html=f'<div style="font:600 12px system-ui;color:{color};text-shadow:0 0 3px #fff,0 0 3px #fff;white-space:nowrap">{prefix} {row[label_col]}</div>'),
        ).add_to(group)
    return group


def _add_basemaps(m: folium.Map) -> None:
    """Light basemap first and shown; the others are listed in the layer control but hidden."""
    if config.CARTO_API_KEY:
        for style, name, show in [("light_all", "Light basemap", True), ("dark_all", "Dark basemap", False)]:
            folium.TileLayer(
                config.CARTO_TILES.format(style=style, key=config.CARTO_API_KEY),
                attr=config.CARTO_ATTRIBUTION, name=name, show=show,
            ).add_to(m)
    else:
        # No CARTO key: fade OpenStreetMap so the shading and heatmap stand out
        folium.TileLayer("OpenStreetMap", name="Light basemap", opacity=0.45, show=True).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Street basemap", show=False).add_to(m)


def build_map(
    incidents: pd.DataFrame,
    neighborhoods: gpd.GeoDataFrame,
    police: gpd.GeoDataFrame,
    alder: gpd.GeoDataFrame,
    shade_by: str,
    alder_rates: pd.DataFrame | None = None,
    show_heatmap: bool = True,
    show_points: bool = False,
) -> folium.Map:
    m = folium.Map(location=config.MAP_CENTER, zoom_start=11, tiles=None, control_scale=True)
    _add_basemaps(m)

    if shade_by == "Neighborhood":
        counts = incidents.groupby("neighborhood").size().rename("incidents")
        areas = neighborhoods.merge(counts, left_on="neighborhood", right_index=True, how="left")
        layer, cmap = _shaded_layer(areas, "incidents", "neighborhood", "Incidents", "Incidents", "Neighborhoods (shaded)")
    else:  # aldermanic district, per 1,000 residents
        areas = alder.merge(alder_rates[["alder_district", "per_1000", "incidents"]], on="alder_district", how="left")
        areas["per_1000"] = areas["per_1000"].round(1)
        areas["label"] = "District " + areas["alder_district"].astype(str) + " (" + areas["alderperson"].fillna("vacant") + ")"
        layer, cmap = _shaded_layer(areas, "per_1000", "label", "Incidents per 1,000 residents per year", "Per 1,000 / yr", "Aldermanic districts (shaded)")
    layer.add_to(m)
    cmap.add_to(m)

    _outline_layer(police, "police_district", "Police District", "Police district lines", "#b4231b", "6 4", True).add_to(m)
    if shade_by == "Neighborhood":
        _outline_layer(alder, "alder_district", "Ald.", "Aldermanic district lines", "#5b3fa0", "2 4", False).add_to(m)

    pts = incidents.dropna(subset=["lat", "lon"])
    if show_heatmap and len(pts):
        sample = pts.sample(min(len(pts), HEATMAP_MAX_POINTS), random_state=0)
        HeatMap(sample[["lat", "lon"]].values.tolist(), name="Heatmap", radius=9, blur=12, min_opacity=0.25).add_to(m)
    if show_points and len(pts):
        FastMarkerCluster(pts[["lat", "lon"]].values.tolist(), name="Individual incidents").add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
