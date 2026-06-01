"""Build metadata control tables for the Willamette core35_v1 network."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd


NETWORK_VERSION = "core35_v1"

CORE_SITES_PATH = Path("results/usgs_willamette_core_sites_35.csv")
RAW_PATH = Path("data_raw/usgs/willamette_core_35_iv_2009_2024.csv")
METADATA_DIR = Path("metadata")
SITES_PATH = METADATA_DIR / "sites.csv"
PARAMETERS_PATH = METADATA_DIR / "parameters.csv"
SITE_PARAMETERS_PATH = METADATA_DIR / "site_parameters.csv"
LOG_PATH = Path("logs/build_metadata_log.txt")

PARAMETERS = {
    "00010": {
        "parameter_name": "water_temperature",
        "short_name": "water_temperature",
        "unit": "deg C",
        "parameter_group": "water_quality",
        "priority": "core",
        "modeling_role": "target_or_predictor",
        "hard_min": -2,
        "hard_max": 35,
        "suspect_min": 0,
        "suspect_max": 30,
        "notes": "Primary temperature signal for forecasting and anomaly detection.",
    },
    "00300": {
        "parameter_name": "dissolved_oxygen",
        "short_name": "dissolved_oxygen",
        "unit": "mg/L",
        "parameter_group": "water_quality",
        "priority": "core",
        "modeling_role": "target_or_predictor",
        "hard_min": 0,
        "hard_max": 25,
        "suspect_min": 2,
        "suspect_max": 18,
        "notes": "Primary ecological water-quality signal.",
    },
    "63680": {
        "parameter_name": "turbidity",
        "short_name": "turbidity",
        "unit": "FNU",
        "parameter_group": "water_quality",
        "priority": "core",
        "modeling_role": "target_or_predictor",
        "hard_min": 0,
        "hard_max": "",
        "suspect_min": "",
        "suspect_max": 300,
        "notes": "Storm-sensitive signal; high values should be reviewed with flow context.",
    },
    "00095": {
        "parameter_name": "specific_conductance",
        "short_name": "specific_conductance",
        "unit": "uS/cm @25C",
        "parameter_group": "water_quality",
        "priority": "core",
        "modeling_role": "target_or_predictor",
        "hard_min": 0,
        "hard_max": 1000,
        "suspect_min": 20,
        "suspect_max": 300,
        "notes": "Useful for source and seasonal water-quality differences.",
    },
    "00400": {
        "parameter_name": "ph",
        "short_name": "ph",
        "unit": "standard units",
        "parameter_group": "water_quality",
        "priority": "core",
        "modeling_role": "target_or_predictor",
        "hard_min": 0,
        "hard_max": 14,
        "suspect_min": 6,
        "suspect_max": 9.5,
        "notes": "Core water-quality parameter where coverage is sufficient.",
    },
    "00060": {
        "parameter_name": "discharge",
        "short_name": "discharge",
        "unit": "ft3/s",
        "parameter_group": "hydrology",
        "priority": "auxiliary",
        "modeling_role": "predictor",
        "hard_min": 0,
        "hard_max": "",
        "suspect_min": "",
        "suspect_max": 250000,
        "notes": "Hydrologic context and predictor, not a water-quality target.",
    },
    "00065": {
        "parameter_name": "gage_height",
        "short_name": "gage_height",
        "unit": "ft",
        "parameter_group": "hydrology",
        "priority": "auxiliary",
        "modeling_role": "predictor",
        "hard_min": -5,
        "hard_max": 30,
        "suspect_min": 0,
        "suspect_max": 20,
        "notes": "Hydrologic context and predictor.",
    },
    "99133": {
        "parameter_name": "nitrate",
        "short_name": "nitrate",
        "unit": "",
        "parameter_group": "nutrient",
        "priority": "optional",
        "modeling_role": "future_topic",
        "hard_min": 0,
        "hard_max": "",
        "suspect_min": "",
        "suspect_max": "",
        "notes": "Keep as optional until coverage supports a nutrient-focused analysis.",
    },
}


@dataclass
class CoverageStats:
    record_count: int = 0
    first_datetime: pd.Timestamp | None = None
    last_datetime: pd.Timestamp | None = None
    active_years: set[int] = field(default_factory=set)
    active_days: set[object] = field(default_factory=set)
    active_hours: set[object] = field(default_factory=set)
    unit_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    sample_datetimes: list[pd.Timestamp] = field(default_factory=list)


def log_message(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def update_timestamp_range(stats: CoverageStats, datetimes: pd.Series) -> None:
    chunk_min = datetimes.min()
    chunk_max = datetimes.max()
    if pd.isna(chunk_min) or pd.isna(chunk_max):
        return
    if stats.first_datetime is None or chunk_min < stats.first_datetime:
        stats.first_datetime = chunk_min
    if stats.last_datetime is None or chunk_max > stats.last_datetime:
        stats.last_datetime = chunk_max


def choose_coverage_status(daily_coverage_pct: float, active_year_count: int) -> str:
    if active_year_count >= 3 and daily_coverage_pct >= 0.70:
        return "model_ready"
    if active_year_count >= 1 and daily_coverage_pct >= 0.20:
        return "analysis_ready"
    if active_year_count >= 1:
        return "sparse_context"
    return "no_valid_data"


def choose_modeling_priority(parameter_cd: str, coverage_status: str) -> str:
    priority = PARAMETERS.get(parameter_cd, {}).get("priority", "optional")
    if coverage_status == "model_ready" and priority == "core":
        return "high"
    if coverage_status in {"model_ready", "analysis_ready"} and priority == "auxiliary":
        return "medium"
    if coverage_status in {"analysis_ready", "sparse_context"}:
        return "low"
    return "exclude"


def median_interval_text(datetimes: list[pd.Timestamp]) -> str:
    if len(datetimes) < 2:
        return ""
    series = pd.Series(datetimes).dropna().drop_duplicates().sort_values()
    if len(series) < 2:
        return ""
    return str(series.diff().dropna().median())


def scan_raw_coverage(core_sites: pd.DataFrame) -> dict[tuple[str, str], CoverageStats]:
    core_site_ids = set(core_sites["site_no"].astype(str))
    allowed_parameters = set(PARAMETERS)
    coverage: dict[tuple[str, str], CoverageStats] = defaultdict(CoverageStats)

    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw core data not found: {RAW_PATH}")

    usecols = ["datetime", "site_no", "parameter_cd", "value", "unit"]
    chunk_index = 0
    for chunk in pd.read_csv(
        RAW_PATH,
        usecols=usecols,
        dtype={"datetime": "string", "site_no": "string", "parameter_cd": "string", "unit": "string"},
        chunksize=500_000,
        on_bad_lines="skip",
    ):
        chunk_index += 1
        chunk["datetime"] = pd.to_datetime(chunk["datetime"], errors="coerce", utc=True)
        chunk["value"] = pd.to_numeric(chunk["value"], errors="coerce")
        chunk = chunk.dropna(subset=["datetime", "site_no", "parameter_cd", "value"])
        chunk = chunk[chunk["site_no"].isin(core_site_ids)]
        chunk = chunk[chunk["parameter_cd"].isin(allowed_parameters)]
        if chunk.empty:
            continue

        chunk["date"] = chunk["datetime"].dt.date
        chunk["hour"] = chunk["datetime"].dt.floor("h")
        chunk["year"] = chunk["datetime"].dt.year

        for (site_no, parameter_cd), group in chunk.groupby(["site_no", "parameter_cd"], sort=False):
            stats = coverage[(str(site_no), str(parameter_cd))]
            stats.record_count += len(group)
            update_timestamp_range(stats, group["datetime"])
            stats.active_years.update(int(year) for year in group["year"].dropna().unique())
            stats.active_days.update(group["date"].dropna().unique())
            stats.active_hours.update(group["hour"].dropna().unique())
            for unit, count in group["unit"].fillna("").value_counts().items():
                stats.unit_counts[str(unit)] += int(count)
            if len(stats.sample_datetimes) < 5000:
                sample_remaining = 5000 - len(stats.sample_datetimes)
                stats.sample_datetimes.extend(group["datetime"].head(sample_remaining).tolist())

        if chunk_index % 20 == 0:
            log_message(f"Scanned {chunk_index} chunks")

    return coverage


def build_parameters_table() -> pd.DataFrame:
    rows = []
    for parameter_cd, values in PARAMETERS.items():
        rows.append({"parameter_cd": parameter_cd, **values})
    return pd.DataFrame(rows)


def build_site_parameter_table(
    core_sites: pd.DataFrame, coverage: dict[tuple[str, str], CoverageStats]
) -> pd.DataFrame:
    rows = []
    for _, site in core_sites.iterrows():
        site_no = str(site["site_no"])
        parameter_codes = [item.strip() for item in str(site["parameter_codes"]).split(",") if item.strip()]
        for parameter_cd in parameter_codes:
            stats = coverage.get((site_no, parameter_cd), CoverageStats())
            if stats.first_datetime is not None and stats.last_datetime is not None:
                expected_days = max((stats.last_datetime.date() - stats.first_datetime.date()).days + 1, 1)
                expected_hours = max(int((stats.last_datetime - stats.first_datetime).total_seconds() // 3600) + 1, 1)
            else:
                expected_days = 0
                expected_hours = 0

            daily_coverage_pct = len(stats.active_days) / expected_days if expected_days else 0.0
            hourly_coverage_pct = len(stats.active_hours) / expected_hours if expected_hours else 0.0
            active_year_count = len(stats.active_years)
            coverage_status = choose_coverage_status(daily_coverage_pct, active_year_count)
            unit = max(stats.unit_counts, key=stats.unit_counts.get) if stats.unit_counts else PARAMETERS[parameter_cd]["unit"]

            rows.append(
                {
                    "site_no": site_no,
                    "parameter_cd": parameter_cd,
                    "parameter_name": PARAMETERS[parameter_cd]["parameter_name"],
                    "unit": unit,
                    "record_count": stats.record_count,
                    "first_datetime": stats.first_datetime,
                    "last_datetime": stats.last_datetime,
                    "median_interval": median_interval_text(stats.sample_datetimes),
                    "active_year_count": active_year_count,
                    "hourly_coverage_pct": round(hourly_coverage_pct, 4),
                    "daily_coverage_pct": round(daily_coverage_pct, 4),
                    "modeling_priority": choose_modeling_priority(parameter_cd, coverage_status),
                    "coverage_status": coverage_status,
                    "notes": "",
                }
            )

    return pd.DataFrame(rows)


def build_sites_table(core_sites: pd.DataFrame, site_parameters: pd.DataFrame) -> pd.DataFrame:
    site_summary = site_parameters.groupby("site_no").agg(
        first_datetime=("first_datetime", "min"),
        last_datetime=("last_datetime", "max"),
        total_record_count=("record_count", "sum"),
        observed_parameter_count=("record_count", lambda series: int((series > 0).sum())),
        active_year_count=("active_year_count", "max"),
    )
    parameter_lists = (
        site_parameters[site_parameters["record_count"] > 0]
        .groupby("site_no")["parameter_name"]
        .apply(lambda series: ",".join(sorted(series.unique())))
    )

    rows = []
    for _, site in core_sites.iterrows():
        site_no = str(site["site_no"])
        summary = site_summary.loc[site_no] if site_no in site_summary.index else None
        rows.append(
            {
                "site_no": site_no,
                "site_name": site["station_nm"],
                "latitude": site["dec_lat_va"],
                "longitude": site["dec_long_va"],
                "coord_datum": site["coord_datum_cd"],
                "huc_cd": site["huc_cd"],
                "huc8_name": site["huc8_name"],
                "site_type": site["site_tp_cd"],
                "selection_role": site["selection_role"],
                "network_tier": "core",
                "network_version": NETWORK_VERSION,
                "site_web_url": site["site_web_url"],
                "first_datetime": "" if summary is None else summary["first_datetime"],
                "last_datetime": "" if summary is None else summary["last_datetime"],
                "total_record_count": 0 if summary is None else int(summary["total_record_count"]),
                "observed_parameter_count": 0 if summary is None else int(summary["observed_parameter_count"]),
                "parameter_list": parameter_lists.get(site_no, ""),
                "active_year_count": 0 if summary is None else int(summary["active_year_count"]),
                "data_status": "active",
                "inclusion_reason": "Selected for core35_v1 network coverage.",
                "notes": "",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")

    core_sites = pd.read_csv(CORE_SITES_PATH, dtype="string").fillna("")
    log_message(f"Loaded core sites: {len(core_sites)}")

    parameters = build_parameters_table()
    coverage = scan_raw_coverage(core_sites)
    site_parameters = build_site_parameter_table(core_sites, coverage)
    sites = build_sites_table(core_sites, site_parameters)

    parameters.to_csv(PARAMETERS_PATH, index=False)
    site_parameters.to_csv(SITE_PARAMETERS_PATH, index=False)
    sites.to_csv(SITES_PATH, index=False)

    log_message(f"Wrote {PARAMETERS_PATH} with shape {parameters.shape}")
    log_message(f"Wrote {SITE_PARAMETERS_PATH} with shape {site_parameters.shape}")
    log_message(f"Wrote {SITES_PATH} with shape {sites.shape}")

    print(f"Parameters: {parameters.shape[0]} rows -> {PARAMETERS_PATH}")
    print(f"Site parameters: {site_parameters.shape[0]} rows -> {SITE_PARAMETERS_PATH}")
    print(f"Sites: {sites.shape[0]} rows -> {SITES_PATH}")


if __name__ == "__main__":
    main()
