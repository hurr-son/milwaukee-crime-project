import pandas as pd

from mke_crime import analysis, clean


def raw_rows():
    # Shaped like the WIBR API output: every column is a string
    return pd.DataFrame([
        {"Case_Number": "A1", "Incident_Date": "2025-03-01 14:30:00", "Police_District": "3", "Offense_All": "13B;290",
         "Location_All": "100 N MAIN ST", "Address_Latitude": "43.04", "Address_Longitude": "-87.91", "Weapon_Used_All": "PERSONAL WEAPON"},
        {"Case_Number": "A2", "Incident_Date": "2027-06-16 14:51:00", "Police_District": "6", "Offense_All": "120",
         "Location_All": "", "Address_Latitude": "42.99", "Address_Longitude": "-87.89", "Weapon_Used_All": ""},
        {"Case_Number": "A3", "Incident_Date": "2026-02-10 00:00:00", "Police_District": "", "Offense_All": "240",
         "Location_All": "", "Address_Latitude": "0", "Address_Longitude": "0", "Weapon_Used_All": ""},
        {"Case_Number": "A1", "Incident_Date": "2025-03-01 14:30:00", "Police_District": "3", "Offense_All": "13B",
         "Location_All": "", "Address_Latitude": "43.04", "Address_Longitude": "-87.91", "Weapon_Used_All": ""},
    ])


def test_clean_drops_future_and_duplicates_and_flags_bad_coords():
    df, report = clean.clean_incidents(raw_rows(), today=pd.Timestamp("2026-10-28"))
    assert report["duplicate_cases"] == 1
    assert report["future_dates"] == 1
    assert list(df["case_number"]) == ["A1", "A3"]
    assert df.loc[df["case_number"] == "A3", "lat"].isna().all()
    assert df.loc[df["case_number"] == "A3", "time_is_midnight"].all()
    assert df.loc[df["case_number"] == "A1", "category"].item() == "Violent"
    assert pd.isna(df.loc[df["case_number"] == "A3", "police_district"].item())


def test_yoy_compares_same_months_only():
    df = pd.DataFrame({
        "incident_dt": pd.to_datetime(["2025-01-15", "2025-11-01", "2026-01-20", "2026-02-03", "2026-03-02"]),
    })
    df["year"], df["month"] = df["incident_dt"].dt.year, df["incident_dt"].dt.month
    last_full = analysis.last_complete_month(df)  # March 2026 is partial -> Feb
    assert last_full == (2026, 2)
    yoy = analysis.yoy_change(df, 2026, last_full)
    assert yoy["months"] == 2
    assert (yoy["current"], yoy["previous"]) == (2, 1)  # Nov 2025 is not counted
