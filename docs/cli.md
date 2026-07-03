# CLI Usage

## `collect`

Collect and validate QC metrics from detected tool outputs.

```bash
speccheck collect FILEPATHS... --sample SAMPLE_ID
```

Common options:

- `--organism`
- `--sample`
- `--criteria-file`
- `--output-file`
- `--metadata`
- `-v`, `--verbose`

Example:

```bash
speccheck collect tests/practice_data/Sample_178db692semb \
  --sample Sample_178db692semb \
  --criteria-file speccheck/config/criteria.csv \
  --output-file qc_results/Sample_178db692semb.csv
```

## `summary`

Merge collected CSV files and optionally generate HTML and XLSX outputs.

```bash
speccheck summary DIRECTORY --output qc_report --plot
```

Additional reporting options:

- `--xlsx-output PATH`
- `--qualifyr-style / --no-qualifyr-style`
- `--interactive-tables / --no-interactive-tables`
- `--templates PATH`

Example:

```bash
speccheck summary qc_results \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --xlsx-output qc_report/report.xlsx
```

## `check`

Validate or refresh a criteria CSV.

```bash
speccheck check --criteria-file speccheck/config/criteria.csv
```

Refresh from QualiBact:

```bash
speccheck check \
  --criteria-file speccheck/config/criteria.csv \
  --update \
  --update-url https://static.qualibact.org/api/v2/external/thresholds.csv
```
