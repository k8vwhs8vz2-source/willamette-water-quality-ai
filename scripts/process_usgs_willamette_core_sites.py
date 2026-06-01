"""Clean 35-site Willamette IV data and prepare ArcGIS-friendly outputs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


RAW_PATH = Path("data_raw/usgs/willamette_core_35_iv_2009_2024.csv")
CORE_SITES_PATH = Path("results/usgs_willamette_core_sites_35.csv")
CLEAN_LONG_PATH = Path("data_processed/willamette_core_35_iv_clean_long_2009_2024.csv")
ARCGIS_SITE_SUMMARY_PATH = Path("results/usgs_willamette_core_35_arcgis_site_summary.csv")
PARAMETER_QUALITY_PATH = Path("results/usgs_willamette_core_35_parameter_quality.csv")
LOG_PATH = Path("logs/process_core_sites_log.txt")

PARAMETER_COLUMNS = {
    "00060": "discharge",
    "00065": "gage_height",
    "00010": "water_temperature",
    "00095": "specific_conductance",
    "00400": "ph",
    "00300": "dissolved_oxygen",
    "63680": "turbidity",
    "99133": "nitrate",
}


def log_message(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def infer_median_interval(series: pd.Series) -> str:
    timestamps = series.dropna().sort_values().drop_duplicates()
    if len(timestamps) < 2:
        return ""
    return str(timestamps.diff().dropna().median())


def load_clean_long() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw input file not found: {RAW_PATH}")

    raw = pd.read_csv(
        RAW_PATH,
        dtype={
            "site_no": "string",
            "station_nm": "string",
            "core_rank": "Int64",
            "selection_role": "string",
            "huc8_name": "string",
            "parameter_cd": "string",
            "parameter_name": "string",
            "unit": "string",
        },
    )

    raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce", utc=True)
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw["dec_lat_va"] = pd.to_numeric(raw["dec_lat_va"], errors="coerce")
    raw["dec_long_va"] = pd.to_numeric(raw["dec_long_va"], errors="coerce")
    raw = raw.dropna(subset=["datetime", "site_no", "parameter_cd", "value", "dec_lat_va", "dec_long_va"])
    raw = raw.drop_duplicates(subset=["datetime", "site_no", "parameter_cd", "value"])
    raw["column_name"] = raw["parameter_cd"].map(PARAMETER_COLUMNS).fillna(raw["parameter_name"])
    raw["year"] = raw["datetime"].dt.year
    raw["month"] = raw["datetime"].dt.month

    return raw.sort_values(["site_no", "parameter_cd", "datetime"]).reset_index(drop=True)


def build_parameter_quality(clean: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (site_no, parameter_cd), group in clean.groupby(["site_no", "parameter_cd"], sort=True):
        rows.append(
            {
                "site_no": site_no,
                "station_nm": group["station_nm"].iloc[0],
                "selection_role": group["selection_role"].iloc[0],
                "huc8_name": group["huc8_name"].iloc[0],
                "parameter_cd": parameter_cd,
                "parameter_name": group["parameter_name"].iloc[0],
                "column_name": group["column_name"].iloc[0],
                "unit": group["unit"].iloc[0],
                "rows": len(group),
                "first_datetime": group["datetime"].min(),
                "last_datetime": group["datetime"].max(),
                "min_value": group["value"].min(),
                "max_value": group["value"].max(),
                "mean_value": group["value"].mean(),
                "median_raw_interval": infer_median_interval(group["datetime"]),
            }
        )
    return pd.DataFrame(rows)


def build_arcgis_site_summary(clean: pd.DataFrame) -> pd.DataFrame:
    site_meta = pd.read_csv(CORE_SITES_PATH, dtype={"site_no": "string"})
    site_meta["core_rank"] = pd.to_numeric(site_meta["core_rank"], errors="coerce").astype("Int64")

    latest_rows = (
        clean.sort_values("datetime")
        .groupby(["site_no", "column_name"], as_index=False)
        .tail(1)
        .pivot_table(index="site_no", columns="column_name", values="value", aggfunc="first")
        .add_prefix("latest_")
    )

    latest_dates = (
        clean.sort_values("datetime")
        .groupby(["site_no", "column_name"], as_index=False)
        .tail(1)
        .pivot_table(index="site_no", columns="column_name", values="datetime", aggfunc="first")
        .add_prefix("latest_datetime_")
    )

    means = (
        clean.groupby(["site_no", "column_name"])["value"]
        .mean()
        .unstack("column_name")
        .add_prefix("mean_")
    )

    counts = (
        clean.groupby(["site_no", "column_name"])["value"]
        .size()
        .unstack("column_name")
        .fillna(0)
        .astype(int)
        .add_prefix("rows_")
    )

    coverage = clean.groupby("site_no").agg(
        total_observations=("value", "size"),
        first_datetime=("datetime", "min"),
        last_datetime=("datetime", "max"),
        observed_parameter_count=("parameter_cd", "nunique"),
    )

    summary = site_meta.set_index("site_no").join([coverage, means, latest_rows, latest_dates, counts]).reset_index()
    summary = summary.sort_values("core_rank").reset_index(drop=True)
    return summary


def main() -> None:
    CLEAN_LONG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARCGIS_SITE_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    log_message(f"Reading raw data from {RAW_PATH}")
    clean = load_clean_long()
    log_message(f"Clean long shape: {clean.shape}")

    parameter_quality = build_parameter_quality(clean)
    arcgis_summary = build_arcgis_site_summary(clean)

    clean.to_csv(CLEAN_LONG_PATH, index=False)
    parameter_quality.to_csv(PARAMETER_QUALITY_PATH, index=False)
    arcgis_summary.to_csv(ARCGIS_SITE_SUMMARY_PATH, index=False)

    log_message(f"Wrote clean long data to {CLEAN_LONG_PATH} with shape {clean.shape}")
    log_message(f"Wrote parameter quality to {PARAMETER_QUALITY_PATH} with shape {parameter_quality.shape}")
    log_message(f"Wrote ArcGIS site summary to {ARCGIS_SITE_SUMMARY_PATH} with shape {arcgis_summary.shape}")

    print(f"Clean long shape: {clean.shape[0]} rows x {clean.shape[1]} columns")
    print(f"Clean long file: {CLEAN_LONG_PATH}")
    print(f"Parameter quality shape: {parameter_quality.shape[0]} rows x {parameter_quality.shape[1]} columns")
    print(f"Parameter quality file: {PARAMETER_QUALITY_PATH}")
    print(f"ArcGIS summary shape: {arcgis_summary.shape[0]} rows x {arcgis_summary.shape[1]} columns")
    print(f"ArcGIS summary file: {ARCGIS_SITE_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
