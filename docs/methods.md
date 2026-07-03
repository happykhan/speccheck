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
- CheckM/CheckM2-style completeness and contamination tables
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

## Demonstration panel

For manuscript demonstration, a small *Escherichia coli* panel was selected from QualiBact ATB PASS, WARN, and FAIL lists. Assemblies were downloaded with `atbfetcher`; QUAST metrics were generated locally; and QualiBact/ATB CheckM2 and species metrics were converted into `speccheck` parser-compatible tables.

The committed demonstration report is available at:

- `examples/qualibact_ecoli/real_panel/report/report.csv`
- `examples/qualibact_ecoli/real_panel/report/report.html`
- `examples/qualibact_ecoli/real_panel/report/report.xlsx`

The report preserves the original QualiBact tier and reason metadata while also showing the current binary `speccheck` QC verdict.

## Reproducibility

Minimal pass/fail reports can be regenerated with:

```bash
python scripts/generate_qualibact_example_reports.py
```

The real-panel report can be regenerated with:

```bash
python scripts/build_qualibact_ecoli_demo.py
```

On a Slurm cluster:

```bash
sbatch scripts/slurm_qualibact_ecoli_demo.sh
```

Manuscript figures and summary tables can be regenerated with:

```bash
python scripts/create_manuscript_assets.py
```

## Current validation boundary

The current real-panel workflow runs QUAST locally. CheckM2 and species-assignment values are taken from the QualiBact/ATB exported metrics and converted into parser-compatible tables. A stricter validation run should install a local CheckM2 database and run CheckM2 directly on the downloaded assemblies before regenerating the manuscript panel.
