"""Download USGS instantaneous values for the Willamette River at Portland.

This script fetches each requested parameter separately from the USGS NWIS IV
service and combines successful responses into one long-format CSV.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


SITE_NO = "14211720"
SITE_NAME = "Willamette River at Portland, OR / Morrison Bridge"
START_DATE = "2009-01-01"
END_DATE = "2024-12-31"
NWIS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"

OUTPUT_PATH = Path("data_raw/usgs/willamette_14211720_iv_2009_2024.csv")
LOG_PATH = Path("logs/download_log.txt")

PARAMETERS = {
    "00060": "discharge",
    "00065": "gage height",
    "00010": "water temperature",
    "00095": "specific conductance",
    "00400": "pH",
    "00300": "dissolved oxygen",
    "63680": "turbidity",
    "99133": "nitrate",
}


def log_message(message: str) -> None:
    """Append a timestamped message to the download log."""
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def extract_unit(time_series: dict[str, Any]) -> str:
    """Return the USGS unit code for a time series when available."""
    variable = time_series.get("variable", {})
    unit = variable.get("unit", {})
    return unit.get("unitCode") or unit.get("unitAbbreviation") or ""


def extract_rows(response_json: dict[str, Any], parameter_cd: str, parameter_name: str) -> list[dict[str, Any]]:
    """Convert a USGS IV JSON response into long-format records."""
    rows: list[dict[str, Any]] = []
    time_series_items = response_json.get("value", {}).get("timeSeries", [])

    for time_series in time_series_items:
        source_info = time_series.get("sourceInfo", {})
        site_no = source_info.get("siteCode", [{}])[0].get("value", SITE_NO)
        unit = extract_unit(time_series)

        for value_block in time_series.get("values", []):
            for item in value_block.get("value", []):
                value = item.get("value")
                if value in (None, ""):
                    continue

                rows.append(
                    {
                        "datetime": item.get("dateTime"),
                        "site_no": site_no,
                        "parameter_cd": parameter_cd,
                        "parameter_name": parameter_name,
                        "value": value,
                        "unit": unit,
                    }
                )

    return rows


def download_parameter(parameter_cd: str, parameter_name: str) -> pd.DataFrame:
    """Download and parse one USGS parameter."""
    params = {
        "format": "json",
        "sites": SITE_NO,
        "parameterCd": parameter_cd,
        "startDT": START_DATE,
        "endDT": END_DATE,
        "siteStatus": "all",
    }

    response = requests.get(NWIS_IV_URL, params=params, timeout=120)
    response.raise_for_status()

    rows = extract_rows(response.json(), parameter_cd, parameter_name)
    if not rows:
        return pd.DataFrame(columns=["datetime", "site_no", "parameter_cd", "parameter_name", "value", "unit"])

    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["datetime", "value"])
    return df[["datetime", "site_no", "parameter_cd", "parameter_name", "value", "unit"]]


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    log_message(f"Starting USGS IV download for site {SITE_NO}: {SITE_NAME}")
    log_message(f"Date range: {START_DATE} to {END_DATE}")

    successful_parameters: list[str] = []
    failed_or_empty_parameters: list[str] = []
    frames: list[pd.DataFrame] = []

    for parameter_cd, parameter_name in PARAMETERS.items():
        label = f"{parameter_cd} ({parameter_name})"
        try:
            log_message(f"Requesting parameter {label}")
            df = download_parameter(parameter_cd, parameter_name)

            if df.empty:
                failed_or_empty_parameters.append(label)
                log_message(f"No data returned for parameter {label}")
                continue

            frames.append(df)
            successful_parameters.append(label)
            log_message(f"Downloaded {len(df)} rows for parameter {label}")

        except Exception as exc:
            failed_or_empty_parameters.append(label)
            log_message(f"Failed parameter {label}: {type(exc).__name__}: {exc}")

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values(["datetime", "parameter_cd"]).reset_index(drop=True)
    else:
        combined = pd.DataFrame(columns=["datetime", "site_no", "parameter_cd", "parameter_name", "value", "unit"])

    combined.to_csv(OUTPUT_PATH, index=False)
    log_message(f"Wrote CSV to {OUTPUT_PATH} with shape {combined.shape}")
    log_message("Download script finished")

    print("Successful parameters:")
    print("\n".join(f"- {item}" for item in successful_parameters) or "- None")
    print("\nNo data or failed parameters:")
    print("\n".join(f"- {item}" for item in failed_or_empty_parameters) or "- None")
    print(f"\nOutput CSV shape: {combined.shape[0]} rows x {combined.shape[1]} columns")
    print(f"Output file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
