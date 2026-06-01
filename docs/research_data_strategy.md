# Willamette Basin Data Strategy

## Purpose

This project should not treat the full USGS instantaneous-values archive as the
main working dataset. The 35-site pilot already produces tens of millions of
rows for 2009-2024, which is useful as a reproducible raw source but too large
and noisy for routine ArcGIS mapping, exploratory analysis, or early modeling.

The research workflow should use a layered design:

1. Preserve raw downloads locally.
2. Build compact, documented analysis products.
3. Use ArcGIS-ready spatial summaries for mapping.
4. Use time-windowed, quality-controlled tables for modeling.
5. Expand sites only through a repeatable station-selection rule.

## Research Questions

The first full-basin phase should answer practical questions before attempting
complex forecasting:

- How do water-quality conditions vary along the Willamette mainstem?
- Which major tributaries show distinct water-quality signatures?
- Which parameters have enough spatial and temporal coverage for modeling?
- Which stations are suitable as target sites, predictor sites, or context-only
  sites?
- What time resolution is realistic after missing-data and coverage checks?

Forecasting and anomaly detection should come after these questions are
answered.

## Site Network Design

Use three station tiers.

### Tier 1: Core Network

Current file:

```text
results/usgs_willamette_core_sites_35.csv
```

Purpose:

- Basin-scale ArcGIS visualization.
- Data coverage assessment.
- First multi-site modeling experiments.

Design:

- Mainstem longitudinal coverage from upper basin to Portland.
- Major tributary coverage for McKenzie, Santiam, Clackamas, Tualatin,
  Molalla-Pudding, and Yamhill.
- Preference for stations with multiple water-quality parameters.

### Tier 2: Extended Network

Candidate source:

```text
results/usgs_willamette_candidate_sites.csv
```

Purpose:

- Add local spatial detail after the core network is understood.
- Support subbasin-specific maps.
- Add tributary or urban-area context where needed.

Expansion rule:

- Add stations by subbasin, not randomly.
- Add only if the station improves spatial coverage or parameter coverage.
- Prefer stations with latitude/longitude and at least two useful parameters.
- Keep each expansion batch small, such as 10-20 stations.

### Tier 3: Context Stations

Purpose:

- Hydrologic context, flow-only stations, or sparse historical stations.
- Useful for maps and interpretation, but not necessarily for modeling.

These stations should not be mixed into modeling tables unless they pass the
same temporal coverage checks as the core network.

## New Site Ingestion Standard

New stations should enter the project through a controlled ingestion workflow,
not by ad hoc download.

### Ingestion Steps

1. Discover candidate stations from USGS Site Service or another documented
   source.
2. Add candidate station metadata to a staging table.
3. Assign a station tier:

```text
core
extended_candidate
context_only
excluded
```

4. Record the reason for inclusion or exclusion.
5. Download only the approved parameters for the approved date window.
6. Store raw observations in the same partitioned structure as existing data.
7. Rebuild metadata coverage tables.
8. Rebuild ArcGIS and modeling products only from approved data layers.

### Minimum Metadata for New Sites

Every new site must have:

```text
site_no
site_name
latitude
longitude
coord_datum
huc_cd
huc8_name
site_type
source
site_web_url
selection_role
network_tier
inclusion_reason
```

Optional but recommended:

```text
river_name
river_mile
nearest_city
mainstem_or_tributary
upstream_downstream_role
notes
```

### Inclusion Rules

Promote a site to the core or extended network only if it satisfies at least one
of these conditions:

- Improves upstream-downstream coverage on the Willamette mainstem.
- Represents a major tributary or tributary mouth.
- Fills a spatial gap visible in ArcGIS.
- Adds a high-quality parameter record that is missing nearby.
- Supports a defined modeling target or research question.

Do not add a site only because data are available.

### Batch Size Rule

Expand in small batches:

```text
10-20 sites per expansion batch
```

After each batch:

- Rebuild coverage metadata.
- Review spatial distribution in ArcGIS.
- Check data volume and processing time.
- Decide whether the batch improves the research design.

### Versioning Rule

Each network should have a named version:

```text
core35_v1
extended50_v1
extended75_v1
```

Derived files should include the network version in the filename where useful.
This prevents confusion when stations are added later.

## Parameter Priority

Use parameters in groups.

### Primary Modeling Parameters

These are most useful for prediction and anomaly detection:

```text
00010 water_temperature
00300 dissolved_oxygen
00095 specific_conductance
00400 pH
63680 turbidity
```

### Hydrologic Context Parameters

These explain changes in water quality and should be kept as predictors:

```text
00060 discharge
00065 gage_height
```

### Optional Nutrient Parameters

Nitrate should be included where available, but it should not define the core
network because coverage is usually sparse:

```text
99133 nitrate
```

## Data Layers

Use these durable layers.

### Raw Local Layer

Examples:

```text
data_raw/usgs/willamette_core_35_iv_2009_2024.csv
data_raw/usgs/site_inventory/willamette_usgs_iv_sites.csv
```

Rules:

- Local only when files are large.
- Do not upload large raw CSV files to GitHub.
- Do not manually edit.
- Regenerate with scripts when needed.

Recommended long-term structure:

```text
data_raw/usgs/core35_v1/site_no=14211720/year=2020.csv.gz
data_raw/usgs/core35_v1/site_no=14211720/year=2021.csv.gz
```

This avoids maintaining a single very large raw CSV.

### Clean Long Layer

Example:

```text
data_processed/willamette_core_35_iv_clean_long_2009_2024.csv
```

Purpose:

- One row per site, timestamp, and parameter.
- Best format for flexible analysis and filtering.
- Should include site metadata, coordinates, parameter code, value, unit, and
  quality flags.

### ArcGIS Site Summary Layer

Example:

```text
results/usgs_willamette_core_35_arcgis_site_summary.csv
```

Purpose:

- One row per station.
- Direct ArcGIS import.
- X field: `dec_long_va`.
- Y field: `dec_lat_va`.
- Includes latest values, mean values, observation counts, date coverage, and
  station role.

### Modeling Layer

Recommended future files:

```text
data_processed/modeling/willamette_core_35_daily_2015_2024.csv
data_processed/modeling/willamette_core_35_30min_selected_2020_2024.csv
```

Purpose:

- Compact enough for repeated experiments.
- Wide or panel format depending on model type.
- Includes only stations and parameters that pass coverage checks.

## Time Strategy

Do not use 2009-2024 high-frequency data for every task.

### ArcGIS Mapping

Recommended products:

- Latest observed value by station and parameter.
- Annual or seasonal means.
- Selected drought, storm, or summer low-flow periods.

Suggested initial windows:

```text
2015-2024 annual summaries
2020-2024 seasonal summaries
selected event windows after inspection
```

### Exploratory Analysis

Use daily aggregation first:

```text
site_no
date
parameter
daily_mean
daily_min
daily_max
daily_observation_count
```

Daily tables are much smaller and more stable than raw high-frequency data.

### Forecasting

Start with a small, defensible modeling window:

```text
2020-2024
```

Then expand backward only if coverage and computational cost are acceptable.

## Quality Control Rules

Apply quality control in stages.

### Stage 1: Structural Cleaning

- Parse timestamps as UTC.
- Parse numeric values.
- Drop rows with invalid timestamp, site number, parameter code, or value.
- Drop malformed rows from interrupted writes.
- Drop exact duplicate rows.
- Preserve raw data separately.

### Stage 2: Physical Bounds

Use the rules from:

```text
docs/data_quality_standard.md
```

Add flags instead of silently deleting values:

```text
ok
missing
impossible
suspect_range
suspect_spike
gap_filled
```

### Stage 3: Coverage Screening

For each site-parameter pair, compute:

- First timestamp.
- Last timestamp.
- Observation count.
- Median sampling interval.
- Number of active years.
- Missingness after aggregation.

Only site-parameter pairs that pass coverage thresholds should enter modeling.

## Recommended Coverage Thresholds

For first-pass modeling:

- At least 3 active years.
- At least 70 percent daily coverage within the selected modeling window.
- No major unexplained outage across the target season.
- At least one hydrologic context variable available nearby or at the same site.

For ArcGIS visualization:

- Thresholds can be lower.
- Sparse stations should be labeled as context or historical stations.

## ArcGIS Products

Prepare three ArcGIS-ready products.

### Station Inventory Layer

One row per station:

```text
site_no
station_nm
selection_role
huc8_name
dec_lat_va
dec_long_va
parameter_names
site_web_url
```

### Site Summary Layer

One row per station with coverage and summary values:

```text
total_observations
first_datetime
last_datetime
observed_parameter_count
mean_water_temperature
mean_dissolved_oxygen
mean_turbidity
latest_water_temperature
latest_dissolved_oxygen
latest_turbidity
```

### Seasonal Parameter Layer

One row per station, parameter, year, and season:

```text
site_no
station_nm
dec_lat_va
dec_long_va
parameter
year
season
mean_value
min_value
max_value
observation_count
```

This is the best ArcGIS format for symbolizing one parameter at a time.

## Modeling Products

Use two modeling formats.

### Panel Long Format

Best for statistical models and machine learning with station metadata:

```text
site_no
datetime
parameter
value_clean
quality_flag
huc8_name
selection_role
dec_lat_va
dec_long_va
```

### Wide Time Series Format

Best for single-target forecasting:

```text
datetime
target_site_water_temperature
target_site_dissolved_oxygen
target_site_turbidity
upstream_discharge
nearby_gage_height
seasonal_features
```

Start with one target station, such as Portland, then add upstream predictors.

## Metadata Tables

Create dedicated metadata files before expanding further.

### `metadata/sites.csv`

One row per station:

```text
site_no
site_name
latitude
longitude
coord_datum
huc_cd
huc8_name
site_type
selection_role
network_tier
network_version
site_web_url
first_datetime
last_datetime
total_record_count
observed_parameter_count
parameter_list
active_year_count
data_status
inclusion_reason
notes
```

### `metadata/parameters.csv`

One row per parameter:

```text
parameter_cd
parameter_name
short_name
unit
parameter_group
priority
modeling_role
hard_min
hard_max
suspect_min
suspect_max
notes
```

### `metadata/site_parameters.csv`

One row per site-parameter pair:

```text
site_no
parameter_cd
parameter_name
unit
record_count
first_datetime
last_datetime
median_interval
active_year_count
hourly_coverage_pct
daily_coverage_pct
modeling_priority
coverage_status
notes
```

These metadata tables should become the control panel for downloading,
cleaning, ArcGIS export, and modeling.

## Recommended Next Steps

1. Clean the current 35-site raw file and produce compact summaries.
2. Build daily and seasonal aggregate tables.
3. Inspect ArcGIS maps for spatial gaps.
4. Decide whether to expand by subbasin in small batches.
5. Choose one target prediction problem.
6. Build a first modeling table for that target only.

## Practical Rule

Raw high-frequency USGS data are the source of truth, not the everyday working
dataset. The everyday working datasets should be smaller, documented, and tied
to a specific research purpose.
