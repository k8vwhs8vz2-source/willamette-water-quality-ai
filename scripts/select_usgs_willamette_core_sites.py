"""Select a compact 35-site Willamette basin network for mapping and download."""

from __future__ import annotations

import csv
from pathlib import Path


CANDIDATE_PATH = Path("results/usgs_willamette_candidate_sites.csv")
CORE_PATH = Path("results/usgs_willamette_core_sites_35.csv")

CORE_SITE_IDS = [
    # Willamette mainstem and forks, ordered roughly upper basin to Portland.
    "14145500",
    "14144800",
    "14148000",
    "14150000",
    "14152000",
    "14157500",
    "14158100",
    "14158050",
    "14166000",
    "14171600",
    "14174000",
    "14191000",
    "14197900",
    "14207770",
    "450808123004200",
    "453027122400000",
    "14211720",
    # Major tributary coverage.
    "14158850",
    "14162500",
    "14163900",
    "14182500",
    "14181500",
    "444728122450000",
    "14187500",
    "14185000",
    "14187200",
    "14210000",
    "14211010",
    "14209710",
    "14206241",
    "14203500",
    "14207200",
    "14198500",
    "14200000",
    "14194150",
]


def selection_role(row: dict[str, str]) -> str:
    if row["priority_group"] == "1_mainstem":
        return "mainstem_longitudinal"
    if row["huc8_name"] in {"McKenzie", "North Santiam", "South Santiam", "Clackamas", "Tualatin"}:
        return "major_tributary_water_quality"
    if row["huc8_name"] == "Molalla-Pudding":
        return "lower_basin_tributary"
    if row["huc8_name"] == "Yamhill":
        return "west_side_tributary"
    return "basin_context"


def main() -> None:
    with CANDIDATE_PATH.open(encoding="utf-8", newline="") as file:
        candidates = {row["site_no"]: row for row in csv.DictReader(file)}

    missing = [site_no for site_no in CORE_SITE_IDS if site_no not in candidates]
    if missing:
        raise ValueError(f"Core site IDs missing from candidate table: {', '.join(missing)}")

    rows = []
    for rank, site_no in enumerate(CORE_SITE_IDS, start=1):
        row = candidates[site_no].copy()
        row["core_rank"] = str(rank)
        row["selection_role"] = selection_role(row)
        rows.append(row)

    CORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "core_rank",
        "selection_role",
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
    with CORE_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote core site network: {CORE_PATH} ({len(rows)} sites)")
    print("Site roles:")
    for role in sorted({row["selection_role"] for row in rows}):
        count = sum(row["selection_role"] == role for row in rows)
        print(f"- {role}: {count}")


if __name__ == "__main__":
    main()
