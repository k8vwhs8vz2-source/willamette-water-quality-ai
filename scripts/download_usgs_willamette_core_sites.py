"""Download USGS IV data for the 35-site Willamette core network."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


CORE_SITES_PATH = Path("results/usgs_willamette_core_sites_35.csv")
OUTPUT_PATH = Path("data_raw/usgs/willamette_core_35_iv_2009_2024.csv")
LOG_PATH = Path("logs/download_core_sites_log.txt")

START_DATE = "2009-01-01"
END_DATE = "2024-12-31"
NWIS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"

PARAMETER_NAMES = {
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


def extract_unit(time_series: dict[str, Any]) -> str:
    variable = time_series.get("variable", {})
    unit = variable.get("unit", {})
    return unit.get("unitCode") or unit.get("unitAbbreviation") or ""


def extract_rows(response_json: dict[str, Any], site: dict[str, Any], parameter_cd: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    parameter_name = PARAMETER_NAMES.get(parameter_cd, parameter_cd)

    for time_series in response_json.get("value", {}).get("timeSeries", []):
        source_info = time_series.get("sourceInfo", {})
        site_no = source_info.get("siteCode", [{}])[0].get("value", site["site_no"])
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
                        "station_nm": site["station_nm"],
                        "core_rank": site["core_rank"],
                        "selection_role": site["selection_role"],
                        "huc8_name": site["huc8_name"],
                        "dec_lat_va": site["dec_lat_va"],
                        "dec_long_va": site["dec_long_va"],
                        "parameter_cd": parameter_cd,
                        "parameter_name": parameter_name,
                        "value": value,
                        "unit": unit,
                    }
                )

    return rows


def download_site_parameter(site: dict[str, Any], parameter_cd: str) -> pd.DataFrame:
    params = {
        "format": "json",
        "sites": site["site_no"],
        "parameterCd": parameter_cd,
        "startDT": START_DATE,
        "endDT": END_DATE,
        "siteStatus": "all",
    }
    response = requests.get(NWIS_IV_URL, params=params, timeout=180)
    response.raise_for_status()

    rows = extract_rows(response.json(), site, parameter_cd)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["datetime", "site_no", "parameter_cd", "value"])
    return df


def load_core_sites() -> list[dict[str, Any]]:
    sites = pd.read_csv(CORE_SITES_PATH, dtype="string").fillna("")
    required = {"site_no", "station_nm", "core_rank", "selection_role", "huc8_name", "dec_lat_va", "dec_long_va", "parameter_codes"}
    missing = required.difference(sites.columns)
    if missing:
        raise ValueError(f"Missing required core-site columns: {', '.join(sorted(missing))}")
    return sites.to_dict("records")


def completed_site_parameters() -> set[tuple[str, str]]:
    if not OUTPUT_PATH.exists():
        return set()

    completed: set[tuple[str, str]] = set()
    for chunk in pd.read_csv(
        OUTPUT_PATH,
        usecols=["site_no", "parameter_cd"],
        dtype={"site_no": "string", "parameter_cd": "string"},
        chunksize=500_000,
    ):
        completed.update((str(row.site_no), str(row.parameter_cd)) for row in chunk.itertuples(index=False))
    return completed


def append_frame(df: pd.DataFrame) -> None:
    header = not OUTPUT_PATH.exists()
    df.to_csv(OUTPUT_PATH, mode="a", header=header, index=False)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    sites = load_core_sites()
    completed = completed_site_parameters()
    successes: list[str] = []
    failures: list[str] = []

    log_message(f"Starting core-site USGS IV download for {len(sites)} sites")
    log_message(f"Date range: {START_DATE} to {END_DATE}")
    log_message(f"Already completed site-parameters in output file: {len(completed)}")

    for site in sites:
        parameter_codes = [item.strip() for item in site["parameter_codes"].split(",") if item.strip()]
        log_message(f"Site {site['site_no']} {site['station_nm']}: {len(parameter_codes)} parameters")

        for parameter_cd in parameter_codes:
            label = f"{site['site_no']} {parameter_cd}"
            key = (str(site["site_no"]), parameter_cd)
            if key in completed:
                log_message(f"Skipping completed {label}")
                print(f"{label}: skipped")
                continue

            try:
                df = download_site_parameter(site, parameter_cd)
                if df.empty:
                    failures.append(f"{label} empty")
                    log_message(f"No rows returned for {label}")
                    continue

                append_frame(df)
                completed.add(key)
                successes.append(label)
                log_message(f"Downloaded {len(df)} rows for {label}")
                print(f"{label}: {len(df)} rows")
            except Exception as exc:
                failures.append(f"{label} {type(exc).__name__}")
                log_message(f"Failed {label}: {type(exc).__name__}: {exc}")
                print(f"{label}: failed ({type(exc).__name__})")

    row_count = 0
    if OUTPUT_PATH.exists():
        row_count = sum(len(chunk) for chunk in pd.read_csv(OUTPUT_PATH, usecols=["site_no"], chunksize=500_000))

    log_message(f"Wrote CSV to {OUTPUT_PATH} with {row_count} rows")
    log_message(f"Successful site-parameters: {len(successes)}")
    log_message(f"Empty or failed site-parameters: {len(failures)}")

    print(f"\nOutput CSV rows: {row_count}")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Successful site-parameters: {len(successes)}")
    print(f"Empty or failed site-parameters: {len(failures)}")


if __name__ == "__main__":
    main()
