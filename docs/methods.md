# Manuscript Methods Draft

This page provides draft text and implementation details for describing `speccheck` in a manuscript. Edit wording to match journal style.

## Software overview

`speccheck` is a Python command-line application for species-aware bacterial genome quality control. The tool collects outputs from upstream quality-control and species-assignment software, applies a criteria table of expected values for the target organism, and generates merged CSV, HTML, and XLSX reports for review and archiving.

The workflow is organized around three commands:

- `speccheck collect`: parse per-sample QC outputs and apply species-specific criteria
- `speccheck summary`: merge collected sample CSVs and generate report artifacts
- `speccheck check`: validate or refresh the criteria table

## Input data

The runtime input is a set of upstream QC output files. Supported parsers currently include:

- QUAST assembly metrics
- CheckM2-style completeness and contamination tables
- Speciator species-assignment output
- Sylph species-abundance output
- ARIBA summary tables
- depth tables

The parser layer detects recognized file formats from filenames and headers. Parsed values are written to per-sample CSV files, with pass/fail check columns derived from the active criteria file.

## Criteria

Criteria are represented as CSV rows with the following core fields:

- `species`
- `assembly_type`
- `software`
- `field`
- `operator`
- `value`
- `special_field`

This design keeps runtime checks transparent and reviewable. Criteria can be shipped with the package, supplied by the user, or refreshed from a QualiBact threshold export.

QualiBact-derived criteria are interpreted as CheckM2-calibrated thresholds. The
column prefix `Checkm.*` is retained for compatibility with earlier `speccheck`
outputs, but CheckM1 marker-lineage fields are not part of the supported
QualiBact criteria model.

## Demonstration panel

For manuscript demonstration, a small *Escherichia coli* panel was selected from pinned QualiBact ATB PASS, WARN, and FAIL metadata and then resolved to real short-read data. Those reads were processed through a local `GHRU-assembly` run, and the resulting upstream outputs were consumed with `speccheck`.

The committed demonstration report is available at:

- `examples/qualibact_ecoli/real_panel/report/report.csv`
- `examples/qualibact_ecoli/real_panel/report/report.html`
- `examples/qualibact_ecoli/real_panel/report/report.xlsx`

The report preserves the original QualiBact tier and reason metadata and adds
`qualibact_compat_tier`, a pinned QualiBact E. coli v1 compatibility tier computed from
the report metrics. WARN remains a warning tier by default and does not fail the binary
`all_checks_passed` column unless `--qualibact-warn-as-fail` is used.

## Reproducibility

Minimal pass/fail reports can be regenerated with:

```bash
pixi run python scripts/generate_qualibact_example_reports.py
```

The real-panel report can be regenerated with:

```bash
pixi run python scripts/build_ghru_ecoli_panel_report.py \
  .demo_work/ghru_ecoli_panel/triplet/output \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work
```

Manuscript figures and summary tables can be regenerated with:

```bash
pixi run python scripts/create_manuscript_assets.py
```

## Current validation boundary

The current real-panel workflow is validated on a small GHRU-backed read set rather than
the larger intended cohort. The remaining scale-up work should continue on the same
read-backed `GHRU-assembly` path. The compatibility tier source is pinned to
`https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0`.
