"""Turn raw WIBR rows into one tidy row per incident, and record what was dropped and why."""
import pandas as pd

from . import config, nibrs


def clean_incidents(raw: pd.DataFrame, today: pd.Timestamp | None = None) -> tuple[pd.DataFrame, dict]:
    today = today or pd.Timestamp.now()
    report = {"rows_in": len(raw)}
    df = raw.copy()

    df = df.drop_duplicates("Case_Number")
    report["duplicate_cases"] = report["rows_in"] - len(df)

    df["incident_dt"] = pd.to_datetime(df["Incident_Date"], errors="coerce")
    bad_date = df["incident_dt"].isna()
    future = df["incident_dt"] > today  # e.g. a 2027 date entered in 2026
    report["unparseable_dates"] = int(bad_date.sum())
    report["future_dates"] = int(future.sum())
    df = df[~bad_date & ~future].copy()

    lat = pd.to_numeric(df["Address_Latitude"], errors="coerce")
    lon = pd.to_numeric(df["Address_Longitude"], errors="coerce")
    in_city = lat.between(*config.LAT_RANGE) & lon.between(*config.LON_RANGE)
    df["lat"] = lat.where(in_city)
    df["lon"] = lon.where(in_city)
    report["missing_coordinates"] = int((~in_city).sum())

    codes = df["Offense_All"].map(nibrs.split_codes)
    df["offense_codes"] = codes.map(";".join)
    df["primary_offense"] = codes.map(lambda c: c[0] if c else "")
    df["category"] = pd.Categorical(codes.map(nibrs.categorize_incident), categories=nibrs.CATEGORIES)

    district = pd.to_numeric(df["Police_District"], errors="coerce")
    df["police_district"] = district.where(district.between(1, 7)).astype("Int64")

    dt = df["incident_dt"]
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["weekday"] = dt.dt.day_of_week  # Monday = 0
    df["hour"] = dt.dt.hour
    # Reports with no known time are commonly logged at exactly 00:00
    df["time_is_midnight"] = (dt.dt.hour == 0) & (dt.dt.minute == 0)
    report["exact_midnight_times"] = int(df["time_is_midnight"].sum())

    df["weapon"] = df["Weapon_Used_All"].fillna("").str.strip().replace("", "NOT RECORDED")
    df = df.rename(columns={"Case_Number": "case_number", "Location_All": "location"})

    keep = [
        "case_number", "incident_dt", "year", "month", "weekday", "hour", "time_is_midnight",
        "category", "primary_offense", "offense_codes", "police_district", "weapon", "location", "lat", "lon",
    ]
    report["rows_out"] = len(df)
    return df[keep].reset_index(drop=True), report
