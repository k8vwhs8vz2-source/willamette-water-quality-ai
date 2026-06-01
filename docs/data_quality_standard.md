# Data Quality and Anomaly Handling Standard

## Scope

This standard applies to USGS instantaneous values data for the first-stage MVP station:

- Site number: `14211720`
- Site name: Willamette River at Portland, OR / Morrison Bridge
- Source: USGS NWIS IV service
- Current processed table: `data_processed/willamette_14211720_30min_2009_2024.csv`

The goal is to define how suspicious values should be identified and handled before later forecasting or anomaly detection work. This standard does not define model-based anomaly detection.

## Core Principles

1. Raw data must not be overwritten.
2. Suspicious values should be flagged before they are removed or modified.
3. A cleaned modeling table should be derived from the raw and processed tables, not replace them.
4. Quality-control decisions should be reproducible in code.
5. Physically impossible values should be treated differently from rare but possible environmental events.

## Recommended Data Layers

Use three data layers:

```text
data_raw/usgs/
```

Original downloaded USGS long-format data. Do not manually edit.

```text
data_processed/
```

Time-aligned wide-format data with minimal aggregation, such as 30-minute means.

```text
data_processed/*_qc.csv
```

Quality-controlled modeling data with additional flag columns and optional cleaned value columns.

## Flagging Strategy

For each measured variable, keep the original value and add a matching flag column.

Example:

```text
discharge
discharge_flag
discharge_clean
```

Recommended flag values:

```text
ok
missing
impossible
suspect_range
suspect_spike
gap_filled
```

Definitions:

- `ok`: value passed current checks.
- `missing`: value is absent.
- `impossible`: value violates a hard physical or measurement bound.
- `suspect_range`: value is unusual for this station but not physically impossible.
- `suspect_spike`: value changes abruptly relative to neighboring values.
- `gap_filled`: value was filled by interpolation for modeling use.

## Initial Hard Bounds

These initial bounds are conservative screening rules for this MVP. They should be revisited after visual inspection and domain review.

| Column | Unit | Impossible if |
|---|---:|---|
| `discharge` | `ft3/s` | `< 0` |
| `gage_height` | `ft` | `< -5` or `> 30` |
| `water_temperature` | `deg C` | `< -2` or `> 35` |
| `specific_conductance` | `uS/cm @25C` | `< 0` or `> 1000` |
| `ph` | `std units` | `< 0` or `> 14` |
| `dissolved_oxygen` | `mg/l` | `< 0` or `> 25` |
| `turbidity` | `FNU` | `< 0` |

Important note for the current dataset:

- Negative `discharge` values should be flagged as `impossible`.
- High turbidity should not be automatically removed only because it is large. Storm events can produce high turbidity, so high values should first be flagged as `suspect_range` or reviewed with hydrologic context.

## Initial Suspect-Range Bounds

These are not deletion rules. They are review flags.

| Column | Suspect if |
|---|---|
| `discharge` | `> 250000 ft3/s` |
| `gage_height` | `< 0 ft` or `> 20 ft` |
| `water_temperature` | `< 0 deg C` or `> 30 deg C` |
| `specific_conductance` | `< 20` or `> 300 uS/cm @25C` |
| `ph` | `< 6` or `> 9.5` |
| `dissolved_oxygen` | `< 2` or `> 18 mg/l` |
| `turbidity` | `> 300 FNU` |

## Spike Detection

After hard-bound checks, identify abrupt spikes using a rolling median method:

1. Use a centered rolling window, initially `48` rows for 30-minute data, equal to 24 hours.
2. Compute the rolling median and rolling median absolute deviation.
3. Flag values as `suspect_spike` when they deviate strongly from the local pattern.
4. Do not apply spike rules across long missing gaps.
5. Do not automatically delete spike-flagged values; keep both original and cleaned columns.

This is only a quality-control screen. Formal anomaly detection should be handled later as a separate modeling task.

## Missing Data and Gap Filling

For modeling tables only:

- Leave missing values as missing in the primary processed table.
- Create cleaned columns only when a model requires complete input.
- Interpolate short gaps up to `2 hours` for slowly changing water-quality variables.
- Do not interpolate long gaps by default.
- Do not interpolate across major sensor outages.
- Mark interpolated values as `gap_filled`.

Recommended first-pass interpolation limit for 30-minute data:

```text
limit = 4 rows
```

## Variable-Specific Treatment

`discharge`

- Flag negative values as `impossible`.
- Do not silently convert negative values to zero.
- For modeling, use `discharge_clean` with impossible values set to missing, then optionally short-gap-filled.

`gage_height`

- Small negative values may occur depending on datum and local conditions.
- Treat values below `-5 ft` as impossible.
- Treat values below `0 ft` as suspect, not automatically invalid.

`water_temperature`

- Values outside `-2` to `35 deg C` are impossible for this use case.
- Short gaps may be interpolated for modeling.

`specific_conductance`

- Negative values are impossible.
- Very high values should be reviewed before removal.

`ph`

- Values outside `0` to `14` are impossible.
- Values outside `6` to `9.5` should be flagged for review.

`dissolved_oxygen`

- Negative values are impossible.
- Very low values may be real environmental events and should not be deleted automatically.

`turbidity`

- Negative values are impossible.
- Large values can be real during storms or high-flow events.
- High turbidity should be reviewed alongside discharge and gage height.

## Recommended Next Implementation

Create a script:

```text
scripts/qc_usgs_willamette.py
```

Inputs:

```text
data_processed/willamette_14211720_30min_2009_2024.csv
```

Outputs:

```text
data_processed/willamette_14211720_30min_2009_2024_qc.csv
results/qc_summary.csv
logs/qc_log.txt
```

Minimum output columns:

```text
datetime
discharge
discharge_flag
discharge_clean
gage_height
gage_height_flag
gage_height_clean
...
```

For the first QC version, implement hard-bound flags and missing-data flags first. Add spike detection only after the simpler checks are verified.
