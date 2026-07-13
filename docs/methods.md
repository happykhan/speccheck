# Manuscript Methods Draft

This page provides draft text and implementation details for describing `speccheck` in a manuscript. Edit wording to match journal style.

## Software overview

`speccheck` is a Python command-line application for species-aware bacterial genome quality control. The tool collects outputs from upstream quality-control and species-assignment software, applies a criteria table of expected values for the target organism, and generates merged CSV, HTML, and XLSX reports for review and archiving.

The workflow is organized around three commands:

- `speccheck collect`: parse per-sample QC outputs and apply species-specific criteria
- `speccheck summary`: merge collected sample CSVs and generate report artifacts
- `speccheck collect-pipeline`: collect a recognised published workflow output layout
- `speccheck check`: validate or refresh the criteria table

## Input data

The runtime input is a set of upstream QC output files. Supported parsers currently include:

- QUAST assembly metrics
- CheckM2-style completeness and contamination tables
- Speciator species-assignment output
- Sylph species-abundance output
- ARIBA summary tables
- depth tables
- Fastp JSON reports
- BUSCO short summaries

The parser layer detects recognized file formats from filenames and headers. Parsed values are written to per-sample CSV files, with pass/fail check columns derived from the active criteria file.

For workflow integration, `speccheck` can be run after a pipeline has completed.
The included `ghru` layout collector consumes the published outputs from GHRU
Assembly, a Nextflow workflow that produces QUAST, CheckM2, Speciator, Sylph,
ARIBA, and depth outputs. This demonstrates the intended pattern for other
pipelines: publish stable QC files, collect them into per-sample Speccheck CSVs,
and render a final cohort report.

## Criteria

Criteria are represented as CSV rows with the following core fields:

- `species`
- `assembly_type`
- `software`
- `field`
- `operator`
- `value`
- `special_field`
- `severity`
- `source`

This design keeps runtime checks transparent and reviewable. Criteria can be shipped with the package, supplied by the user, or refreshed from a QualiBact threshold export.

QualiBact-derived criteria are interpreted as CheckM2-calibrated thresholds. The
column prefix `Checkm.*` is retained for compatibility with earlier `speccheck`
outputs, but CheckM1 marker-lineage fields are not part of the supported
QualiBact criteria model.

Metrics outside QualiBact can still be checked through explicit global
Speccheck rows. In the packaged criteria, this includes BactScout-derived Fastp
Q30 policy and Speccheck default BUSCO completeness/missingness policy.

## Demonstration datasets

For manuscript demonstration, a small *Escherichia coli* panel was selected from pinned QualiBact ATB PASS, WARN, and FAIL metadata and then resolved to real short-read data. Those reads were processed through a local `GHRU-assembly` run, and the resulting upstream outputs were consumed with `speccheck`.

The committed demonstration report is available at:

- `examples/qualibact_ecoli/real_panel/report/report.csv`
- `examples/qualibact_ecoli/real_panel/report/report.html`
- `examples/qualibact_ecoli/real_panel/report/report.xlsx`

The report preserves the original QualiBact tier and reason metadata and adds
`qualibact_compat_tier`, a pinned QualiBact E. coli v1 compatibility tier computed from
the report metrics. WARN remains a warning tier by default and does not fail the binary
`all_checks_passed` column unless `--qualibact-warn-as-fail` is used.

The primary case study scaled the same design to 100 read-backed genomes: 70
historical PASS, 20 WARN, and 10 FAIL. Within each tier, rows were traversed in
source order and the first samples resolving to paired *E. coli* ENA reads were
selected. The full accession and historical-metadata table is committed as
`examples/qualibact_ecoli/real_run_100/cohort_accessions.csv`.

Fresh GHRU-derived metrics produced 90 PASS, 6 WARN, and 4 FAIL compatibility
tiers, with exact tier agreement in 73/100 samples. Three samples had an
unidentified Speciator result. These values quantify concordance between
historical labels and current measurements; they are not an accuracy estimate
because the historical labels are not a ground-truth reference.

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
pixi run python scripts/create_real_run_100_assets.py
```

## Reproducibility boundary

The compatibility policy is pinned specifically to QualiBact E. coli v1 at
`https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0`.
The manuscript must not imply equivalent PASS/WARN/FAIL behavior for other
species. The upstream workflow commit, local patch, container inventory, criteria
and environment hashes, exact commands, and downstream benchmark are recorded in
`examples/qualibact_ecoli/real_run_100/analysis/summary.json`.
