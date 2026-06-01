# willamette-water-quality-ai

High-frequency water quality data foundation for the Willamette River basin,
using USGS instantaneous-values monitoring data.

## Current Status

The project is in the data foundation and architecture stage. It has moved
beyond the original single-station MVP and now includes a first basin-scale
pilot network:

- Network version: `core35_v1`
- Core stations: 35 USGS monitoring locations
- Candidate stations discovered: 197
- Metadata tables: 35 sites, 8 parameters, 158 site-parameter combinations
- Raw multi-site archive: approximately 12.9 GB, stored locally and ignored by
  Git

The project has not yet started production modeling, forecasting, anomaly
detection, or ArcGIS-ready final products. The next priority is chunked
structural cleaning and partitioned derived datasets.

## Data Source

Data are downloaded from the USGS National Water Information System
instantaneous values service:

```text
https://waterservices.usgs.gov/nwis/iv/
```

Station discovery uses USGS Site Service:

```text
https://waterservices.usgs.gov/nwis/site/
```

## Current Network

The active pilot network is:

```text
results/usgs_willamette_core_sites_35.csv
```

It contains:

- 17 mainstem or fork longitudinal stations
- 15 major tributary water-quality stations
- 2 lower-basin tributary stations
- 1 west-side tributary station

The network is intended for station mapping, basin-scale coverage assessment,
and later hourly or daily modeling experiments.

## Parameters

The project currently tracks these USGS parameter codes:

```text
00010 water_temperature
00300 dissolved_oxygen
63680 turbidity
00095 specific_conductance
00400 pH
00060 discharge
00065 gage_height
99133 nitrate
```

Water temperature, dissolved oxygen, turbidity, specific conductance, and pH are
treated as primary water-quality parameters. Discharge and gage height are
hydrologic context variables. Nitrate is retained as an optional future topic
where coverage exists.

## Project Structure

```text
data_raw/usgs/                 Local raw USGS downloads
data_raw/usgs/site_inventory/  USGS site discovery inventory
data_processed/                Processed single-station outputs and future products
docs/                          Data quality and research strategy documents
logs/                          Script logs
metadata/                      Control tables for sites, parameters, and coverage
results/                       Candidate lists, core network lists, summaries
scripts/                       Reproducible project scripts
```

Large raw CSV files under `data_raw/usgs/*.csv` are intentionally ignored by
Git.

## Important Files

Project status and strategy:

```text
project_status_summary.md
docs/research_data_strategy.md
docs/data_quality_standard.md
```

Station and metadata outputs:

```text
results/usgs_willamette_candidate_sites.csv
results/usgs_willamette_core_sites_35.csv
metadata/sites.csv
metadata/parameters.csv
metadata/site_parameters.csv
```

Local raw archives:

```text
data_raw/usgs/willamette_14211720_iv_2009_2024.csv
data_raw/usgs/willamette_core_35_iv_2009_2024.csv
```

The second file is large and should remain local.

## Scripts

Single-station MVP:

```bash
python scripts/download_usgs_willamette.py
python scripts/process_usgs_willamette.py
```

Basin-scale discovery and network selection:

```bash
python scripts/discover_usgs_willamette_sites.py
python scripts/select_usgs_willamette_core_sites.py
```

Core 35-site download and metadata:

```bash
python scripts/download_usgs_willamette_core_sites.py
python scripts/build_usgs_core_metadata.py
```

There is also a draft script:

```text
scripts/process_usgs_willamette_core_sites.py
```

Do not treat this as the recommended production path for the 12.9 GB raw core
file. Future production processing should use chunked cleaning and partitioned
outputs instead of loading the full file into memory.

## Current Metadata Summary

The metadata build produced:

```text
metadata/sites.csv: 35 rows
metadata/parameters.csv: 8 rows
metadata/site_parameters.csv: 158 rows
```

Coverage status summary:

```text
model_ready: 129
analysis_ready: 27
sparse_context: 1
no_valid_data: 1
```

Known low/no coverage combinations:

```text
14144800 + 00060 discharge: no_valid_data
14150000 + 63680 turbidity: sparse_context
```

## Known Caveats

- The 35-site raw archive was created through long-running and resumed
  downloads, so duplicate or malformed rows may exist.
- Raw high-frequency data are not analysis-ready.
- Station and parameter sampling intervals vary between 15 minutes, 30 minutes,
  and hourly.
- Physical and suspect-range QC rules are documented but have not yet been
  applied to the multi-site dataset.
- The raw core file should not be loaded directly into ArcGIS or into memory as
  one DataFrame.

## Recommended Next Steps

1. Create a download audit table for expected vs observed site-parameter pairs.
2. Build a chunked structural cleaning workflow.
3. Partition clean long data by site and year.
4. Build hourly and daily aggregate products.
5. Apply QC flags from `docs/data_quality_standard.md`.
6. Build compact ArcGIS-ready summary tables.
7. Select one narrow first modeling target after coverage checks.

See `project_status_summary.md` for the detailed current-state report and
roadmap.
