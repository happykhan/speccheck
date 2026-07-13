# Criteria and Thresholds

Speccheck uses a CSV criteria file to turn parsed metrics into status columns.
The default criteria file is packaged with the Python package, but you can supply
your own with `--criteria-file`.

```bash
speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --criteria-file project_criteria.csv \
  --output-file qc_collect/SAMPLE_001.csv
```

## CSV format

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
```

| Column | Meaning |
| --- | --- |
| `species` | species name, `all`, or a fallback label such as `Unknown` |
| `assembly_type` | `all`, `short`, `long`, or `hybrid` |
| `software` | parser name, for example `Checkm`, `Quast`, `Fastp` |
| `field` | metric emitted by that parser |
| `operator` | `>`, `<`, `>=`, `<=`, `=`, or `regex` |
| `value` | threshold value or regex pattern |
| `severity` | `fail` or `warn`; blank legacy rows are treated as `fail` |
| `source` | provenance label, for example `qualibact-v1.0`, `bactscout-global`, `custom` |
| `special_field` | optional marker such as `species_field` |

## How rows are selected

Speccheck evaluates criteria in layers:

1. Select rows matching the requested assembly type.
2. Prefer species-specific rows for the resolved organism.
3. Use `species=all` generic rows when no species-specific row exists for that
   same parser metric.
4. Record whether species-specific thresholds were available and whether a
   fallback threshold was used.

This lets one criteria file contain all of these at once:

- species-specific QualiBact-derived assembly thresholds;
- generic fallback thresholds;
- global non-QualiBact policies such as Fastp Q30;
- BUSCO policies where no QualiBact species-specific metric exists.

## Worked example: species-specific threshold

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
Escherichia coli,short,Checkm,Contamination,<=,5,fail,qualibact-v1.0,
```

If the organism is resolved as *Escherichia coli*, this row checks
`Checkm.Contamination`.

## Worked example: global Fastp threshold

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
all,short,Fastp,after_filtering_q30_rate,>=,0.70,fail,bactscout-global,
all,short,Fastp,after_filtering_q30_rate,>=,0.80,warn,bactscout-global,
```

These rows are global. They are not assembly-specific QualiBact thresholds and
not species-specific. They apply to short-read Fastp input wherever Fastp output
is supplied, unless a project criteria file adds a more specific row for the
same parser and field.

## Worked example: BUSCO policy

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
all,all,Busco,Complete,>=,95,fail,speccheck-default,
all,all,Busco,Missing,<=,5,warn,speccheck-default,
```

BUSCO is supported as a parser and can be evaluated by Speccheck criteria, but
these packaged rows are Speccheck default policy rows. They should not be
described as official species-specific QualiBact thresholds.

## Assembly type filtering

`speccheck collect --assembly-type` controls which criteria rows are active:

| Mode | Active rows |
| --- | --- |
| `short` | `all` and `short` |
| `long` | `all` and `long` |
| `hybrid` | `all`, `short`, and `long` |
| `all` | only rows marked `all` |

The selected mode is written to collected CSV outputs as
`speccheck_assembly_type`.

Depth criteria also use the parsed `Depth.Read_type`, so a short-read depth file
is not checked against long-read depth thresholds.

## Species resolution

If `--organism` is not supplied, Speccheck attempts to infer the species from
parser outputs marked with `special_field=species_field`.

Collection stops if no single species can be resolved. This prevents accidental
use of broad fallback thresholds. Use `--allow-unknown-organism` only when you
intentionally want fallback criteria.

## Missing metrics

If a parser is detected but an active criteria row references a missing field,
Speccheck writes the corresponding check as `NOT_EVALUATED`.

By default, `NOT_EVALUATED` is review metadata and does not fail the whole
sample. For strict runs:

```bash
speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --fail-on-not-evaluated \
  --output-file qc_collect/SAMPLE_001.csv
```

## Provenance columns

Collected CSV outputs include:

- `speccheck_version`;
- `speccheck_assembly_type`;
- `speccheck_fail_on_not_evaluated`;
- `speccheck_criteria_file`;
- `speccheck_criteria_sha256`;
- `speccheck_input_file_count`;
- `speccheck_not_evaluated_count`;
- `speccheck_threshold_source`;
- `speccheck_threshold_fallback_used`.

These columns are important when comparing runs across tool versions, criteria
versions, or workflow commits.

## Refreshing QualiBact-derived rows

QualiBact thresholds are converted into the internal criteria CSV format:

```bash
speccheck check \
  --criteria-file speccheck/config/criteria.csv \
  --update \
  --update-url https://static.qualibact.org/api/v2/external/thresholds.csv
```

Existing unmanaged rows are preserved. This is how Speccheck can keep global
Fastp/BUSCO policy rows alongside imported QualiBact-derived rows.
