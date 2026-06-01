"""Process raw USGS Willamette IV data into a 30-minute wide table.

The raw download is kept in long format for traceability. This script creates a
model-ready MVP table with one row per timestamp and one column per parameter,
plus a compact data quality summary.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


RAW_PATH = Path("data_raw/usgs/willamette_14211720_iv_2009_2024.csv")
PROCESSED_PATH = Path("data_processed/willamette_14211720_30min_2009_2024.csv")
SUMMARY_PATH = Path("results/data_quality_summary.csv")
LOG_PATH = Path("logs/process_log.txt")

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
    """Return the median sampling interval for one parameter as text."""
    timestamps = series.dropna().sort_values().drop_duplicates()
    if len(timestamps) < 2:
        return ""

    median_delta = timestamps.diff().dropna().median()
    return str(median_delta)


def build_raw_quality_summary(raw: pd.DataFrame) -> pd.DataFrame:
    summaries = []

    for parameter_cd, group in raw.groupby("parameter_cd", sort=True):
        parameter_name = group["parameter_name"].iloc[0]
        unit = group["unit"].iloc[0] if "unit" in group else ""

        summaries.append(
            {
                "parameter_cd": parameter_cd,
                "parameter_name": parameter_name,
                "column_name": PARAMETER_COLUMNS.get(parameter_cd, parameter_name),
                "unit": unit,
                "raw_rows": len(group),
                "raw_start": group["datetime"].min(),
                "raw_end": group["datetime"].max(),
                "raw_min_value": group["value"].min(),
                "raw_max_value": group["value"].max(),
                "median_raw_interval": infer_median_interval(group["datetime"]),
            }
        )

    return pd.DataFrame(summaries)


def add_wide_quality_summary(raw_summary: pd.DataFrame, wide: pd.DataFrame) -> pd.DataFrame:
    total_rows = len(wide)
    enriched = raw_summary.copy()

    wide_observed = []
    wide_missing = []
    wide_missing_pct = []
    wide_first_valid = []
    wide_last_valid = []

    for column_name in enriched["column_name"]:
        if column_name not in wide.columns:
            wide_observed.append(0)
            wide_missing.append(total_rows)
            wide_missing_pct.append(1.0 if total_rows else 0.0)
            wide_first_valid.append(pd.NaT)
            wide_last_valid.append(pd.NaT)
            continue

        observed = wide[column_name].notna().sum()
        missing = total_rows - observed
        valid_index = wide.index[wide[column_name].notna()]

        wide_observed.append(int(observed))
        wide_missing.append(int(missing))
        wide_missing_pct.append(float(missing / total_rows) if total_rows else 0.0)
        wide_first_valid.append(valid_index.min() if len(valid_index) else pd.NaT)
        wide_last_valid.append(valid_index.max() if len(valid_index) else pd.NaT)

    enriched["wide_rows"] = total_rows
    enriched["wide_observed_rows"] = wide_observed
    enriched["wide_missing_rows"] = wide_missing
    enriched["wide_missing_pct"] = wide_missing_pct
    enriched["wide_first_valid"] = wide_first_valid
    enriched["wide_last_valid"] = wide_last_valid

    return enriched


def main() -> None:
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw input file not found: {RAW_PATH}")

    log_message(f"Reading raw data from {RAW_PATH}")
    raw = pd.read_csv(
        RAW_PATH,
        dtype={"site_no": "string", "parameter_cd": "string", "parameter_name": "string", "unit": "string"},
    )

    raw["datetime"] = pd.to_datetime(raw["datetime"], errors="coerce", utc=True)
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna(subset=["datetime", "parameter_cd", "value"])
    raw["column_name"] = raw["parameter_cd"].map(PARAMETER_COLUMNS).fillna(raw["parameter_name"])

    log_message(f"Clean raw shape after parsing: {raw.shape}")

    raw_summary = build_raw_quality_summary(raw)

    wide = raw.pivot_table(
        index="datetime",
        columns="column_name",
        values="value",
        aggfunc="mean",
    ).sort_index()

    wide_30min = wide.resample("30min").mean()

    ordered_columns = [column for column in PARAMETER_COLUMNS.values() if column in wide_30min.columns]
    extra_columns = [column for column in wide_30min.columns if column not in ordered_columns]
    wide_30min = wide_30min[ordered_columns + extra_columns]

    summary = add_wide_quality_summary(raw_summary, wide_30min)

    wide_30min.reset_index().to_csv(PROCESSED_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)

    log_message(f"Wrote processed data to {PROCESSED_PATH} with shape {wide_30min.shape}")
    log_message(f"Wrote quality summary to {SUMMARY_PATH} with shape {summary.shape}")
    log_message("Processing script finished")

    print(f"Processed data shape: {wide_30min.shape[0]} rows x {wide_30min.shape[1] + 1} columns")
    print(f"Processed file: {PROCESSED_PATH}")
    print(f"Quality summary shape: {summary.shape[0]} rows x {summary.shape[1]} columns")
    print(f"Quality summary file: {SUMMARY_PATH}")
    print("\nColumns:")
    print("\n".join(f"- {column}" for column in ["datetime", *wide_30min.columns]))


if __name__ == "__main__":
    main()
