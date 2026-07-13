# Quick Start

## 1. Inspect recognised inputs

Before collecting anything, check which files `speccheck` will parse:

```bash
speccheck inspect path/to/qc_outputs/
speccheck modules
```

`inspect` is deliberately read-only. Use it when wiring a new workflow into
`speccheck` or when a file is missing from a report.

## 2. Collect one sample

```bash
speccheck collect path/to/qc_outputs/SAMPLE_001/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --assembly-type short \
  --output-file qc_collect/SAMPLE_001.csv
```

If `--organism` is omitted, `speccheck` tries to infer the species from parser
outputs configured as species fields in the criteria file. If no single species
can be resolved, collection stops by default. Use `--allow-unknown-organism`
only when generic fallback thresholds are the intended policy.

## 3. Summarise a cohort

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --xlsx-output qc_report/report.xlsx
```

The summary directory contains:

- `report.csv`: merged machine-readable result;
- `report.full.csv`: full wide report where available;
- `report.html`: self-contained review report when `--plot` is enabled;
- `report.xlsx`: optional workbook when `--xlsx-output` is supplied.

## 4. Run after a Nextflow pipeline

For a published pipeline output layout, use the pipeline collector:

```bash
speccheck collect-pipeline results/ qc_collect \
  --layout ghru \
  --organism "Escherichia coli" \
  --work-dir work/
```

This currently supports the GHRU Assembly output layout.

## 5. Interpret status columns

At report level, start with:

- `overall_qc`: review status summarised as `PASS`, `WARN`, `FAIL`, or
  `NOT_EVALUATED`;
- `all_checks_passed`: binary convenience column for strict pass/fail handling;
- `reason_summary`: compact explanation of warnings, failures, and missing
  checks.

Tool-specific columns ending in `.status` carry the same four-state vocabulary.
`NOT_EVALUATED` means the criteria expected a metric that was not present in the
available upstream output; it is not the same as a failed threshold.
