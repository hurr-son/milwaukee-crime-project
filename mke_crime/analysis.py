"""Aggregations shared by the app's charts and summary numbers."""
import pandas as pd

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def last_complete_month(df: pd.DataFrame) -> tuple[int, int]:
    """(year, month) of the last month fully covered by the data. The newest month is assumed partial."""
    latest = df["incident_dt"].max()
    return (latest.year, latest.month - 1) if latest.month > 1 else (latest.year - 1, 12)


def months_comparable(year: int, last_full: tuple[int, int]) -> int:
    """How many months of `year` can be compared with the year before it."""
    return last_full[1] if year == last_full[0] else 12


def yoy_change(df: pd.DataFrame, year: int, last_full: tuple[int, int]) -> dict | None:
    """Same-months comparison so a partial year is never compared with a full one."""
    if (year - 1) not in set(df["year"]):
        return None
    m = months_comparable(year, last_full)
    cur = int(((df["year"] == year) & (df["month"] <= m)).sum())
    prev = int(((df["year"] == year - 1) & (df["month"] <= m)).sum())
    if prev == 0:
        return None
    return {"current": cur, "previous": prev, "pct": (cur - prev) / prev * 100, "months": m}


def monthly_counts(df: pd.DataFrame, last_full: tuple[int, int]) -> pd.DataFrame:
    out = df.groupby(["year", "month"]).size().rename("incidents").reset_index()
    partial = (out["year"] == last_full[0]) & (out["month"] > last_full[1])
    out = out[~partial]
    out["month_name"] = out["month"].map(lambda m: MONTH_NAMES[m - 1])
    return out


def weekday_hour(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby(["weekday", "hour"]).size().rename("incidents").reset_index()
    out["day"] = out["weekday"].map(lambda d: WEEKDAY_NAMES[d])
    return out


def area_counts(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.dropna(subset=[column]).groupby(column).size().rename("incidents").reset_index()


def alder_rates(df: pd.DataFrame, population: pd.DataFrame, years: int) -> pd.DataFrame:
    """Incidents per 1,000 residents per year, by aldermanic district."""
    out = area_counts(df, "alder_district").merge(population, on="alder_district", how="left")
    out["per_1000"] = out["incidents"] / out["population"] * 1000 / max(years, 1)
    return out
