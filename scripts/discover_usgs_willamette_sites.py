"""Discover USGS instantaneous-value stations in the Willamette basin.

The script queries the USGS NWIS Site Service by Willamette HUC8 subbasin and
water-quality parameter, then writes ArcGIS-friendly CSV inventories.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


SITE_SERVICE_URL = "https://waterservices.usgs.gov/nwis/site/"

HUC8_CODES = {
    "17090001": "Coast Fork Willamette",
    "17090002": "Middle Fork Willamette",
    "17090003": "Upper Willamette",
    "17090004": "McKenzie",
    "17090005": "North Santiam",
    "17090006": "South Santiam",
    "17090007": "Middle Willamette",
    "17090008": "Yamhill",
    "17090009": "Molalla-Pudding",
    "17090010": "Tualatin",
    "17090011": "Clackamas",
    "17090012": "Lower Willamette",
}

PARAMETER_CODES = {
    "00060": "discharge",
    "00065": "gage_height",
    "00010": "water_temperature",
    "00095": "specific_conductance",
    "00400": "ph",
    "00300": "dissolved_oxygen",
    "63680": "turbidity",
    "99133": "nitrate",
}

RAW_SITE_PATH = Path("data_raw/usgs/site_inventory/willamette_usgs_iv_sites.csv")
CANDIDATE_PATH = Path("results/usgs_willamette_candidate_sites.csv")


def fetch_rdb_rows(huc8: str, parameter_cd: str) -> list[dict[str, str]]:
    query = {
        "format": "rdb",
        "huc": huc8,
        "siteType": "ST",
        "hasDataTypeCd": "iv",
        "parameterCd": parameter_cd,
        "siteStatus": "all",
        "siteOutput": "expanded",
    }
    url = f"{SITE_SERVICE_URL}?{urlencode(query)}"

    try:
        with urlopen(url, timeout=60) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            return []
        raise

    data_lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    if len(data_lines) < 3:
        return []

    reader = csv.DictReader(data_lines, delimiter="\t")
    rows = []
    for index, row in enumerate(reader):
        if index == 0:
            continue
        rows.append(row)
    return rows


def station_priority(station_name: str, parameter_count: int, huc_name: str) -> str:
    name = station_name.lower()
    if "willamette river" in name:
        return "1_mainstem"
    if any(token in name for token in ["mckenzie", "santiam", "clackamas", "tualatin", "yamhill", "pudding", "molalla"]):
        return "2_major_tributary"
    if parameter_count >= 4:
        return "3_multi_parameter"
    return f"4_{huc_name.lower().replace(' ', '_')}"


def build_inventory() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sites: dict[str, dict[str, str]] = {}
    site_params: dict[str, set[str]] = defaultdict(set)

    for huc8, huc_name in HUC8_CODES.items():
        for parameter_cd, parameter_name in PARAMETER_CODES.items():
            print(f"Querying HUC {huc8} {huc_name}: {parameter_cd} {parameter_name}")
            for row in fetch_rdb_rows(huc8, parameter_cd):
                site_no = row.get("site_no", "").strip()
                if not site_no:
                    continue

                sites.setdefault(
                    site_no,
                    {
                        "site_no": site_no,
                        "station_nm": row.get("station_nm", "").strip(),
                        "site_tp_cd": row.get("site_tp_cd", "").strip(),
                        "dec_lat_va": row.get("dec_lat_va", "").strip(),
                        "dec_long_va": row.get("dec_long_va", "").strip(),
                        "coord_datum_cd": row.get("coord_datum_cd", "").strip(),
                        "huc_cd": row.get("huc_cd", huc8).strip(),
                        "huc8_name": huc_name,
                        "site_web_url": f"https://waterdata.usgs.gov/monitoring-location/{site_no}/",
                    },
                )
                site_params[site_no].add(parameter_cd)

    raw_rows = []
    candidate_rows = []
    for site_no, site in sites.items():
        params = sorted(site_params[site_no])
        parameter_names = [PARAMETER_CODES[param] for param in params]
        parameter_count = len(params)

        output = {
            **site,
            "parameter_count": str(parameter_count),
            "parameter_codes": ",".join(params),
            "parameter_names": ",".join(parameter_names),
            "priority_group": station_priority(site["station_nm"], parameter_count, site["huc8_name"]),
        }
        raw_rows.append(output)
        if parameter_count >= 2 or output["priority_group"].startswith(("1_", "2_")):
            candidate_rows.append(output)

    sort_key = lambda row: (row["priority_group"], -int(row["parameter_count"]), row["station_nm"])
    return sorted(raw_rows, key=sort_key), sorted(candidate_rows, key=sort_key)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "priority_group",
        "site_no",
        "station_nm",
        "site_tp_cd",
        "dec_lat_va",
        "dec_long_va",
        "coord_datum_cd",
        "huc_cd",
        "huc8_name",
        "parameter_count",
        "parameter_codes",
        "parameter_names",
        "site_web_url",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    raw_rows, candidate_rows = build_inventory()
    write_csv(RAW_SITE_PATH, raw_rows)
    write_csv(CANDIDATE_PATH, candidate_rows)

    print(f"Wrote raw site inventory: {RAW_SITE_PATH} ({len(raw_rows)} sites)")
    print(f"Wrote candidate site list: {CANDIDATE_PATH} ({len(candidate_rows)} sites)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Site discovery failed: {exc}", file=sys.stderr)
        sys.exit(1)
