# Project Status Summary

Last updated: 2026-06-01

## 1. Current Project Stage

This project is currently in the **data foundation and architecture stage**.

The project has moved beyond a single-station proof of concept and now has a
first basin-scale pilot network of 35 USGS stations in the Willamette basin.
However, it has **not yet entered the modeling, prediction, anomaly detection,
or ArcGIS analysis stage**. The immediate priority is to turn the downloaded raw
data into a reproducible, maintainable research data system.

The most important current decision is that the large raw USGS archive should be
treated as a local source-of-truth layer, not as the everyday analysis dataset.
Future work should build smaller derived products for ArcGIS, exploratory
analysis, and modeling.

## 2. What Has Been Completed

### 2.1 Initial Single-Station MVP

The project began with a single USGS station:

```text
Site number: 14211720
Site name: WILLAMETTE RIVER AT PORTLAND, OR
Date range: 2009-01-01 to 2024-12-31
```

The first-stage workflow downloaded and processed instantaneous values data for
the Portland station.

Parameters requested:

```text
00060 discharge
00065 gage_height
00010 water_temperature
00095 specific_conductance
00400 pH
00300 dissolved_oxygen
63680 turbidity
99133 nitrate
```

Completed files from this stage include:

```text
data_raw/usgs/willamette_14211720_iv_2009_2024.csv
data_processed/willamette_14211720_30min_2009_2024.csv
results/data_quality_summary.csv
logs/download_log.txt
logs/process_log.txt
```

Completed scripts:

```text
scripts/download_usgs_willamette.py
scripts/process_usgs_willamette.py
```

The single-station processing script creates a 30-minute wide-format table and a
compact data quality summary.

### 2.2 Data Quality Standard

A project-level data quality standard has been created:

```text
docs/data_quality_standard.md
```

It defines:

- Raw data preservation principles.
- Flagging before cleaning.
- Recommended QC flags.
- Initial physical bounds.
- Suspect-range bounds.
- Spike-detection strategy.
- Missing-data and gap-filling principles.

This document is still mostly based on the initial single-station MVP and should
later be expanded for multi-station processing.

### 2.3 Willamette Basin Station Discovery

A basin-scale station discovery workflow has been created:

```text
scripts/discover_usgs_willamette_sites.py
```

This script queries USGS Site Service by Willamette HUC8 subbasin and selected
USGS parameter codes.

It generated:

```text
data_raw/usgs/site_inventory/willamette_usgs_iv_sites.csv
results/usgs_willamette_candidate_sites.csv
```

Current station discovery results:

```text
Raw USGS IV station inventory: 309 sites
Candidate station list: 197 sites
```

The candidate table includes station number, station name, site type,
coordinates, coordinate datum, HUC code, HUC8 name, available parameter list,
parameter count, priority group, and USGS monitoring-location URL.

### 2.4 Core 35-Site Network

A first research network was selected:

```text
results/usgs_willamette_core_sites_35.csv
```

The selection script is:

```text
scripts/select_usgs_willamette_core_sites.py
```

This core network contains:

```text
35 total stations
17 mainstem or fork longitudinal stations
15 major tributary water-quality stations
2 lower-basin tributary stations
1 west-side tributary station
```

The network is intended to serve as the first basin-scale pilot, referred to in
the research strategy as:

```text
core35_v1
```

The 35-site network is designed to support:

- Willamette mainstem upstream-downstream comparison.
- Major tributary comparison.
- ArcGIS station mapping.
- First multi-site coverage assessment.
- Later hourly or daily modeling experiments.

### 2.5 Multi-Site Core Data Download

A multi-site download script has been created:

```text
scripts/download_usgs_willamette_core_sites.py
```

The script downloads USGS instantaneous values for the 35-site core network,
using each site's approved parameter list from:

```text
results/usgs_willamette_core_sites_35.csv
```

The intended date range is:

```text
2009-01-01 to 2024-12-31
```

The output file is:

```text
data_raw/usgs/willamette_core_35_iv_2009_2024.csv
```

Current downloaded raw multi-site data size:

```text
Approximate file size: 12.9 GB
Log-reported final row count: 74,068,321 rows
```

The file is intentionally ignored by Git because it is too large for normal
GitHub storage.

The download log is:

```text
logs/download_core_sites_log.txt
```

The log indicates that most station-parameter combinations completed, but there
were a small number of empty or failed combinations.

### 2.6 Research Data Strategy

A research data architecture and strategy document has been created:

```text
docs/research_data_strategy.md
```

It establishes several important design decisions:

- Do not use the full raw high-frequency archive as the daily working dataset.
- Use layered data products.
- Treat `core35_v1` as the first stable research network.
- Expand stations only through a controlled ingestion process.
- Build metadata tables before further cleaning or modeling.
- Build ArcGIS-ready summaries separately from raw data.
- Use hourly and daily derived products for analysis and modeling.
- Add future data domains such as precipitation, land use, watershed boundaries,
  and river network data as separate data layers.

### 2.7 Metadata Control Tables

A metadata-building script has been created and successfully run:

```text
scripts/build_usgs_core_metadata.py
```

It scans the large raw multi-site CSV in chunks and creates three metadata
tables:

```text
metadata/sites.csv
metadata/parameters.csv
metadata/site_parameters.csv
```

Current metadata table sizes:

```text
metadata/sites.csv: 35 rows
metadata/parameters.csv: 8 rows
metadata/site_parameters.csv: 158 rows
```

#### `metadata/sites.csv`

This table has one row per station. It includes:

- Site number.
- Site name.
- Latitude and longitude.
- Coordinate datum.
- HUC code.
- HUC8 name.
- Site type.
- Selection role.
- Network tier.
- Network version.
- USGS URL.
- First and last observed timestamps.
- Total valid raw record count.
- Observed parameter count.
- Parameter list.
- Active year count.
- Data status.
- Inclusion reason.

#### `metadata/parameters.csv`

This table has one row per parameter. It includes:

- USGS parameter code.
- Parameter name.
- Short name.
- Unit.
- Parameter group.
- Priority.
- Modeling role.
- Initial hard bounds.
- Initial suspect bounds.
- Notes.

Current parameter groups:

```text
Core water-quality parameters:
00010 water_temperature
00300 dissolved_oxygen
63680 turbidity
00095 specific_conductance
00400 pH

Auxiliary hydrology parameters:
00060 discharge
00065 gage_height

Optional future parameter:
99133 nitrate
```

#### `metadata/site_parameters.csv`

This table has one row per site-parameter pair. It includes:

- Site number.
- Parameter code.
- Parameter name.
- Unit.
- Valid raw record count.
- First timestamp.
- Last timestamp.
- Median sampling interval.
- Active year count.
- Hourly coverage percentage.
- Daily coverage percentage.
- Modeling priority.
- Coverage status.

Current coverage status summary:

```text
model_ready: 129 site-parameter combinations
analysis_ready: 27 site-parameter combinations
sparse_context: 1 site-parameter combination
no_valid_data: 1 site-parameter combination
```

Current modeling priority summary:

```text
high: 74
medium: 55
low: 28
exclude: 1
```

Known low/no coverage combinations from the metadata scan:

```text
14144800 + 00060 discharge: no valid data
14150000 + 63680 turbidity: sparse context
```

### 2.8 Current Scripts and Their Status

Existing scripts:

```text
scripts/download_usgs_willamette.py
scripts/process_usgs_willamette.py
scripts/discover_usgs_willamette_sites.py
scripts/select_usgs_willamette_core_sites.py
scripts/download_usgs_willamette_core_sites.py
scripts/process_usgs_willamette_core_sites.py
scripts/build_usgs_core_metadata.py
```

Verified as runnable during current project work:

```text
scripts/download_usgs_willamette.py
scripts/process_usgs_willamette.py
scripts/discover_usgs_willamette_sites.py
scripts/select_usgs_willamette_core_sites.py
scripts/download_usgs_willamette_core_sites.py
scripts/build_usgs_core_metadata.py
```

Syntax checked:

```text
scripts/process_usgs_willamette_core_sites.py
```

Important note:

`scripts/process_usgs_willamette_core_sites.py` exists, but it is not yet the
recommended production path for the current 12.9 GB raw file. It was drafted
before the full data-volume implications were clear. The next production
processing script should use chunked processing and partitioned outputs.

## 3. Current File Structure

Current major directories:

```text
data_raw/usgs/
data_raw/usgs/site_inventory/
data_processed/
docs/
figures/
logs/
metadata/
notebooks/
results/
scripts/
```

Important current files:

```text
README.md
.gitignore
docs/data_quality_standard.md
docs/research_data_strategy.md
project_status_summary.md
```

Raw and discovered data:

```text
data_raw/usgs/willamette_14211720_iv_2009_2024.csv
data_raw/usgs/willamette_core_35_iv_2009_2024.csv
data_raw/usgs/site_inventory/willamette_usgs_iv_sites.csv
```

Processed or summary data:

```text
data_processed/willamette_14211720_30min_2009_2024.csv
results/data_quality_summary.csv
results/usgs_willamette_candidate_sites.csv
results/usgs_willamette_core_sites_35.csv
```

Metadata:

```text
metadata/sites.csv
metadata/parameters.csv
metadata/site_parameters.csv
```

Logs:

```text
logs/download_log.txt
logs/process_log.txt
logs/download_core_sites_log.txt
logs/build_metadata_log.txt
```

## 4. Known and Possible Problems

### 4.1 Confirmed Issues

#### Large raw data volume

The current 35-site raw file is approximately 12.9 GB.

Impact:

- It is too large for manual inspection.
- It is too large for GitHub.
- It is not suitable as a direct ArcGIS input.
- It should not be repeatedly loaded into memory as one DataFrame.
- Future processing must use chunking, partitioning, or a database format.

#### Interrupted and repeated download runs

The large multi-site download was interrupted by timeouts and then resumed. The
download script was modified to append data and skip completed combinations, but
some earlier runs may have partially overlapped.

Impact:

- The raw file may contain duplicate rows.
- The raw file may contain a small number of malformed rows from interrupted or
  overlapping writes.
- `record_count` values in metadata should currently be interpreted as valid
  raw row counts after basic parsing, not final deduplicated modeling counts.

#### Malformed rows observed during metadata scanning

During previous checks, malformed `parameter_cd` values were observed in the raw
CSV. The metadata scan filters to valid core site IDs and known parameter codes,
so these malformed rows do not enter the metadata tables.

Impact:

- Raw file should not be treated as analysis-ready.
- Structural cleaning must explicitly drop invalid timestamps, invalid site
  numbers, invalid parameter codes, and invalid numeric values.

#### One site-parameter combination has no valid data

From `metadata/site_parameters.csv`:

```text
14144800 + 00060 discharge: no_valid_data
```

Impact:

- This combination should be excluded from modeling.
- If discharge is needed for that site, a nearby hydrologic station or another
  related variable may be required.

#### One site-parameter combination is sparse

From `metadata/site_parameters.csv`:

```text
14150000 + 63680 turbidity: sparse_context
```

Impact:

- It may be useful for context.
- It should not be treated as a reliable modeling feature without further
  review.

#### Time frequency varies by station and parameter

Observed median intervals include 15-minute, 30-minute, and hourly records.

Impact:

- Raw data cannot be compared directly across sites without aggregation.
- A unified hourly and/or daily product is required before network analysis or
  modeling.

#### Parameter coverage is uneven

Some parameters have much higher total record counts than others.

Current approximate valid raw record counts by parameter from metadata:

```text
00065 gage_height: 21,359,188
00060 discharge: 19,875,423
00010 water_temperature: 14,639,246
63680 turbidity: 5,084,375
00095 specific_conductance: 4,434,933
00300 dissolved_oxygen: 4,415,730
00400 pH: 4,259,179
```

Impact:

- Hydrology variables are much more complete than many water-quality variables.
- Modeling should be parameter-specific rather than assuming every station has
  every parameter.

### 4.2 Possible Issues

#### Coordinate datum consistency

Some stations use NAD27 and some use NAD83.

Impact:

- ArcGIS mapping should account for coordinate datum.
- For most broad basin-scale visualization, the difference may be small, but
  precise spatial analysis should standardize coordinates.

#### Time zone interpretation

USGS IV timestamps were parsed as UTC in project scripts.

Impact:

- This is good for consistency, but local-time seasonal or daily analysis may
  require explicit conversion to Pacific time.

#### Physical outliers

Hard-bound and suspect-range QC has been documented but not yet applied to the
35-site dataset.

Impact:

- Raw values may contain impossible or suspicious values.
- Modeling should not begin until QC flags are applied.

#### Missing metadata fields for future spatial analysis

Current metadata includes HUC and coordinates, but not river mile, nearest city,
river network segment ID, land-use attributes, precipitation basin linkage, or
upstream/downstream topology.

Impact:

- The current metadata supports station screening and basic ArcGIS point maps.
- More advanced watershed or network analysis will require additional spatial
  joins.

#### Download completeness should be audited

The log indicates most combinations completed, but because of interrupted runs,
the final raw file should be audited against `metadata/site_parameters.csv` and
the expected site-parameter list.

Impact:

- Before final processing, create a reproducible download audit table.

## 5. Work That Has Not Started

The following areas should be considered **0% or near-0% complete** for the
multi-site research system.

### Multi-site data cleaning

Not started as a production workflow.

Needed:

- Chunked structural cleaning.
- Deduplication.
- Invalid-row removal.
- QC flags.
- Partitioned clean outputs.

### Multi-site hourly and daily products

Not started.

Needed:

- Hourly aggregation table.
- Daily aggregation table.
- Counts, min, max, mean, and coverage indicators.

### ArcGIS data products

Not started as final products.

Needed:

- Station inventory layer.
- Site summary layer.
- Seasonal parameter summary layer.
- Potential GeoJSON or shapefile exports.

### Visualization

Not started.

Needed:

- Basic maps.
- Coverage charts.
- Parameter time series plots.
- Station network diagrams.

### Anomaly detection

Not started.

Needed:

- QC flags first.
- Baseline seasonal patterns.
- Rule-based anomaly screening.
- Later model-based anomaly detection.

### Forecasting and prediction models

Not started.

Needed:

- Target variable selection.
- Target station selection.
- Modeling time window.
- Predictor construction.
- Train/test split.
- Baseline models.

### Watershed network analysis

Not started.

Needed:

- River network data.
- Watershed boundaries.
- Upstream/downstream topology.
- Site-to-reach linkage.

### External environmental data integration

Not started.

Potential future inputs:

- Precipitation.
- Air temperature.
- Land use.
- Elevation.
- Watershed boundaries.
- River network structure.

## 6. Recommended Roadmap

### Step 1: Freeze `core35_v1` as the pilot network

Reason:

The current 35 stations are enough to design and test the data system. Expanding
now would increase cost and complexity before the processing pipeline is stable.

Expected output:

```text
results/usgs_willamette_core_sites_35.csv remains the control list
metadata/sites.csv remains the network registry
```

Supports:

- Stable processing.
- Reproducible ArcGIS outputs.
- Clear future expansion rules.

### Step 2: Create a download audit table

Reason:

The raw file was created through long-running and interrupted downloads. Before
processing, the project needs a clear audit of expected vs observed
site-parameter combinations.

Expected output:

```text
metadata/download_audit_core35_v1.csv
```

Possible fields:

```text
site_no
parameter_cd
expected_from_core_list
observed_in_raw
record_count
download_status
notes
```

Supports:

- Trustworthy processing.
- Identification of missing or partial combinations.
- Future reproducible ingestion.

### Step 3: Build a chunked structural cleaning workflow

Reason:

The raw file is too large and too messy for normal in-memory processing.

Expected output:

```text
data_interim/usgs/core35_v1_clean_long/
```

Recommended structure:

```text
data_interim/usgs/core35_v1_clean_long/site_no=14211720/year=2020.csv.gz
```

Cleaning should:

- Parse timestamps.
- Parse numeric values.
- Keep only valid core site IDs.
- Keep only valid parameter codes.
- Drop malformed rows.
- Drop exact duplicates.
- Preserve source metadata.

Supports:

- Hourly aggregation.
- Daily aggregation.
- ArcGIS summaries.
- Future modeling tables.

### Step 4: Build hourly and daily aggregation products

Reason:

Stations and parameters have different sampling intervals. A common time scale
is required for comparison and modeling.

Expected outputs:

```text
data_processed/usgs/core35_v1_hourly/
data_processed/usgs/core35_v1_daily/
```

Recommended fields:

```text
site_no
datetime_hour or date
parameter_cd
value_mean
value_min
value_max
value_count
unit
coverage_flag
```

Supports:

- Cross-site comparison.
- Seasonal summaries.
- ArcGIS products.
- First modeling experiments.

### Step 5: Apply QC flags

Reason:

Raw and aggregated values may contain impossible, suspicious, or missing values.
Research tables should preserve original values while adding quality flags.

Expected output:

```text
data_processed/usgs/core35_v1_hourly_qc/
data_processed/usgs/core35_v1_daily_qc/
results/qc_summary_core35_v1.csv
```

Supports:

- Reliable modeling.
- Transparent anomaly screening.
- Documentation of data decisions.

### Step 6: Build ArcGIS-ready products

Reason:

ArcGIS should not ingest the 12.9 GB raw CSV. It should receive compact spatial
summary tables.

Expected outputs:

```text
results/arcgis/core35_v1_site_summary.csv
results/arcgis/core35_v1_latest_values.csv
results/arcgis/core35_v1_seasonal_summary.csv
```

Supports:

- Station maps.
- Parameter-specific maps.
- Seasonal comparisons.
- Spatial gap analysis for future station expansion.

### Step 7: Select a first modeling target

Reason:

Modeling should start with a narrow, defensible question rather than all
stations and parameters at once.

Possible first targets:

```text
Water temperature at Portland
Dissolved oxygen at Portland
Turbidity at selected mainstem station
```

Expected output:

```text
data_processed/modeling/core35_v1_target_<target>_2020_2024.csv
```

Supports:

- Baseline forecasting.
- Predictor selection.
- Train/test evaluation.

### Step 8: Expand stations only after the pipeline is stable

Reason:

The current 35-site download already produced a very large file. Expansion must
be based on demonstrated need.

Expected output for future expansion:

```text
results/usgs_willamette_extended_sites_<N>.csv
metadata/sites.csv updated with a new network_version
```

Supports:

- Controlled growth.
- ArcGIS-guided station selection.
- Avoiding unmanageable raw data growth.

## 7. Data Architecture Recommendation

### Current organization

The current project has a useful beginning, but the large raw multi-site CSV is
not a good long-term primary format.

Current raw file:

```text
data_raw/usgs/willamette_core_35_iv_2009_2024.csv
```

Assessment:

- Useful as a temporary raw archive.
- Too large for direct analysis.
- Too fragile as a single file.
- Not suitable for repeated processing without chunking.

### Recommended long-term raw organization

Use partitioned storage by network version, site, and year:

```text
data_raw/usgs/core35_v1/site_no=14211720/year=2020.csv.gz
data_raw/usgs/core35_v1/site_no=14211720/year=2021.csv.gz
```

Benefits:

- Easier to rerun one station or one year.
- Easier to audit.
- Easier to replace bad partitions.
- Easier to scale when adding stations.

### Metadata tables

The project should treat metadata as a central control system.

Current tables:

```text
metadata/sites.csv
metadata/parameters.csv
metadata/site_parameters.csv
```

These should be maintained and regenerated whenever data are added or changed.

### Unified time scale

The project should use multiple time scales:

```text
Raw instantaneous: source-of-truth only
Hourly: main comparison and anomaly-detection scale
Daily: stable research, maps, and seasonal analysis
```

Hourly data should be the first common modeling scale. Daily data should be the
first common reporting and ArcGIS trend scale.

### Research database direction

The project should eventually become a small watershed data system rather than a
collection of CSV files.

Recommended future layout:

```text
metadata/
data_raw/
data_interim/
data_processed/
results/arcgis/
results/modeling/
data_external/
```

Future external domains:

```text
data_external/precipitation/
data_external/watershed_boundaries/
data_external/river_network/
data_external/land_use/
```

The observation table should remain logically simple:

```text
site_no
datetime
parameter_cd
value
unit
quality_flag
```

Spatial and watershed attributes should live in metadata or external spatial
join tables, not be repeatedly duplicated into every raw observation.

## 8. Recommended Research Unit

The project should support three research scales.

### Single-station time series

Purpose:

- Understand one station's trends, gaps, and sensor behavior.
- Build first forecasting models.
- Validate QC rules.

### Multi-station network panel

Purpose:

- Compare stations.
- Model upstream/downstream relationships.
- Study tributary effects.
- Build network-aware predictors.

This should be the central long-term research unit:

```text
site_no + time + parameter
```

### Basin-scale spatial summary

Purpose:

- ArcGIS mapping.
- Watershed comparison.
- Spatial gap analysis.
- Communication and reporting.

This should be based on summarized products, not raw high-frequency records.

## 9. Immediate Recommendation

Do not expand stations yet.

Do not start modeling yet.

Do not use the 12.9 GB raw CSV directly in ArcGIS.

The next best step is to design and implement a chunked structural cleaning and
partitioning workflow, guided by the metadata tables already created. This will
turn the current raw archive into a maintainable research data system.
