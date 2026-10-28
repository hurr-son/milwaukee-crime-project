"""Milwaukee Crime Atlas, Streamlit app.   Run:  streamlit run app.py"""
import json

import altair as alt
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from mke_crime import analysis, config, maps, nibrs

st.set_page_config(page_title="Milwaukee Crime Atlas", page_icon="🗺️", layout="wide")

YEAR_COLORS = {2024: "#2a78d6", 2025: "#eb6834", 2026: "#1baf7a"}


@st.cache_data
def load():
    if not config.INCIDENTS_PARQUET.exists():
        return None
    incidents = pd.read_parquet(config.INCIDENTS_PARQUET)
    nb = gpd.read_file(config.NEIGHBORHOODS_GEOJSON)
    police = gpd.read_file(config.POLICE_GEOJSON)
    alder = gpd.read_file(config.ALDER_GEOJSON)
    population = pd.read_csv(config.POPULATION_CSV)
    report = json.loads(config.REPORT_JSON.read_text())
    return incidents, nb, police, alder, population, report


data = load()
if data is None:
    st.error("No processed data yet. Run `python scripts/build_data.py` first, then reload this page.")
    st.stop()
incidents, nb, police, alder, population, report = data
last_full = analysis.last_complete_month(incidents)
years = sorted(incidents["year"].unique())

# ---------- Sidebar filters ----------
with st.sidebar:
    st.header("Filters")
    year = st.selectbox("Year", years[::-1], format_func=lambda y: f"{y} to date" if y == years[-1] else str(y))
    cats = st.multiselect("Offense group", nibrs.CATEGORIES, default=["Violent"])
    st.header("Map")
    shade_by = st.radio("Shade areas by", ["Neighborhood", "Aldermanic district (per 1,000 residents)"])
    show_heat = st.toggle("Heatmap", value=True)
    show_points = st.toggle("Individual incidents (clustered)", value=False)
    st.caption(f"Data through {report['latest_incident']} · built {report['built']}")

if not cats:
    st.info("Pick at least one offense group in the sidebar.")
    st.stop()

by_cat = incidents[incidents["category"].isin(cats)]
sel = by_cat[by_cat["year"] == year]
cat_label = ", ".join(cats)

# ---------- Header and summary ----------
st.title("Milwaukee Crime Atlas")
st.write(
    f"Every incident reported to the Milwaukee Police Department since January {years[0]}, "
    f"from the city's [WIBR open dataset]({config.WIBR_DATASET_URL}). Showing **{cat_label.lower()}** incidents in **{year}**."
)

yoy = analysis.yoy_change(by_cat, year, last_full)
nb_counts = analysis.area_counts(sel, "neighborhood").sort_values("incidents", ascending=False)
days = (sel["incident_dt"].max() - pd.Timestamp(year, 1, 1)).days + 1 if len(sel) else 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Incidents", f"{len(sel):,}")
if yoy:
    span = "full year" if yoy["months"] == 12 else f"Jan–{analysis.MONTH_NAMES[yoy['months'] - 1]}"
    c2.metric(f"vs {year - 1} ({span})", f"{yoy['current']:,}", f"{yoy['pct']:+.1f}%", delta_color="inverse")
else:
    c2.metric("Year over year", "–", help="No earlier year in this dataset")
c3.metric("Per day", f"{len(sel) / days:,.0f}")
if len(nb_counts):
    c4.metric(
        "Most incidents (neighborhood)", nb_counts.iloc[0]["neighborhood"],
        f"{int(nb_counts.iloc[0]['incidents']):,} incidents", delta_color="off", delta_arrow="off",
    )

# ---------- Map ----------
rates = analysis.alder_rates(sel, population, years=1)
rates["per_1000"] = rates["per_1000"] / (days / 365)  # annualize a partial year
m = maps.build_map(
    sel, nb, police, alder,
    shade_by="Neighborhood" if shade_by == "Neighborhood" else "Alder",
    alder_rates=rates, show_heatmap=show_heat, show_points=show_points,
)
st_folium(m, height=640, use_container_width=True, returned_objects=[])
st.caption(
    "Neighborhood shading shows raw counts, so large or busy commercial areas stand out. "
    "Aldermanic districts have similar populations (about 38,000 each), so their per-resident rates compare fairly."
)

# ---------- Charts ----------
tab_trend, tab_time, tab_areas, tab_offenses, tab_notes = st.tabs(
    ["Trend", "Day and hour", "Neighborhoods", "Offenses", "Data notes"]
)

with tab_trend:
    monthly = analysis.monthly_counts(by_cat, last_full)
    chart = (
        alt.Chart(monthly)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("month_name:N", sort=analysis.MONTH_NAMES, title=None),
            y=alt.Y("incidents:Q", title="Incidents per month"),
            color=alt.Color("year:N", title="Year", scale=alt.Scale(domain=list(YEAR_COLORS), range=list(YEAR_COLORS.values()))),
            tooltip=["year:N", "month_name:N", alt.Tooltip("incidents:Q", format=",")],
        )
        .properties(height=340)
    )
    st.altair_chart(chart, width="stretch")
    st.caption(f"{cat_label}. The current month is partial and not plotted.")

with tab_time:
    wh = analysis.weekday_hour(sel)
    heat = (
        alt.Chart(wh)
        .mark_rect()
        .encode(
            x=alt.X("hour:O", title="Hour of day"),
            y=alt.Y("day:N", sort=analysis.WEEKDAY_NAMES, title=None),
            color=alt.Color("incidents:Q", scale=alt.Scale(scheme="blues"), title="Incidents"),
            tooltip=["day:N", "hour:O", alt.Tooltip("incidents:Q", format=",")],
        )
        .properties(height=260)
    )
    st.altair_chart(heat, width="stretch")
    share = sel["time_is_midnight"].mean() * 100 if len(sel) else 0
    st.caption(f"{share:.1f}% of these incidents are logged at exactly 00:00, which usually means the time is unknown.")

with tab_areas:
    st.dataframe(
        nb_counts.head(25),
        hide_index=True,
        width="stretch",
        column_config={
            "neighborhood": "Neighborhood",
            "incidents": st.column_config.ProgressColumn("Incidents", format="%d", min_value=0, max_value=int(nb_counts["incidents"].max()) if len(nb_counts) else 1),
        },
    )

with tab_offenses:
    codes = sel["offense_codes"].str.split(";").explode()
    codes = codes[codes.str.len() > 0]
    top = codes.value_counts().head(15).rename_axis("code").rename("incidents").reset_index()
    top["offense"] = top["code"].map(nibrs.offense_name)
    st.dataframe(top[["code", "offense", "incidents"]], hide_index=True, width="stretch",
                 column_config={"code": "NIBRS code", "offense": "Offense", "incidents": "Incidents"})
    st.caption("An incident with several offenses counts once under each one.")

with tab_notes:
    st.markdown(
        f"""
- **Source:** City of Milwaukee Open Data Portal, [WIBR Crime Data (Current)]({config.WIBR_DATASET_URL}); boundaries from the city's ArcGIS map services; 2024 population by aldermanic district.
- **Reported incidents only.** This is not a count of all crime that occurs.
- **Offense groups:** each incident takes the most serious group among its NIBRS offense codes (violent, then weapons, property, drugs, other).
- **Year-over-year** compares the same complete months, so a partial year is never compared with a full one.
- **Cleaning:** {report['rows_in']:,} rows received; {report['future_dates']} with a future date and {report['unparseable_dates']} with an unreadable date were dropped; {report['missing_coordinates']:,} had no usable coordinates and are left off the map; {report['no_neighborhood']:,} could not be placed in a neighborhood.
"""
    )
