# willamette-water-quality-ai

High-frequency water quality prediction and anomaly detection using USGS Willamette River monitoring data.

## Project goal

This project studies high-frequency water quality time series from the USGS Willamette River monitoring station at Portland, Oregon. Later phases may add water quality forecasting and anomaly detection workflows.

The current first-stage MVP only sets up the project structure and downloads/organizes single-station USGS instantaneous values data. It does not include machine learning, anomaly detection, or plotting.

## Data source

Data are downloaded from the USGS National Water Information System instantaneous values service:

https://waterservices.usgs.gov/nwis/iv/

## Current station

- Site number: `14211720`
- Site name: Willamette River at Portland, OR / Morrison Bridge
- Date range: `2009-01-01` to `2024-12-31`

The first-stage download script attempts to retrieve these parameters:

- `00060`: discharge
- `00065`: gage height
- `00010`: water temperature
- `00095`: specific conductance
- `00400`: pH
- `00300`: dissolved oxygen
- `63680`: turbidity
- `99133`: nitrate

## Project structure

```text
data_raw/usgs/       Raw USGS download outputs
data_processed/      Processed datasets for later analysis
scripts/             Reproducible project scripts
notebooks/           Exploratory notebooks
figures/             Generated figures for later phases
results/             Modeling or analysis outputs for later phases
logs/                Script logs
```

## Run the download script

From the repository root, run:

```bash
python scripts/download_usgs_willamette.py
```

The script requests each parameter separately, continues if a parameter has no data or fails, and writes a combined long-format CSV to:

```text
data_raw/usgs/willamette_14211720_iv_2009_2024.csv
```

The download log is written to:

```text
logs/download_log.txt
```

The output CSV includes at least these fields:

- `datetime`
- `site_no`
- `parameter_cd`
- `parameter_name`
- `value`
- `unit`

## Process the downloaded data

After downloading the raw USGS data, create a 30-minute wide-format table:

```bash
python scripts/process_usgs_willamette.py
```

The processed data are written to:

```text
data_processed/willamette_14211720_30min_2009_2024.csv
```

The data quality summary is written to:

```text
results/data_quality_summary.csv
```

## Data quality standard

An initial anomaly-handling and quality-control standard is documented here:

```text
docs/data_quality_standard.md
```

The standard recommends preserving raw data, flagging suspicious values before cleaning, and creating separate QC-ready modeling files instead of overwriting downloaded or minimally processed data.
