# Reports

## CSV outputs

`collect` writes:

- a concise sample CSV
- a `detailed.*.csv` companion when the output looks like a full QC report

`summary` writes:

- `report.csv`
- `report.html` when `--plot` is enabled
- `report.html` is self-contained, with embedded report styles
- `report.xlsx` when `--xlsx-output` is supplied

When merging inputs, `summary` uses concise collected CSVs, ignores `detailed.*.csv` companions, and rejects duplicate or missing sample IDs.

## HTML report

The HTML report includes:

- overall QC status table
- top failure reasons
- compact category summary tables
- optional qualifyr-style sample review table
- software-specific charts and tables

Example report generation from the pinned QualiBact E. coli pass/fail fixtures:

```bash
pixi run python scripts/generate_qualibact_example_reports.py
```

This creates manuscript-oriented example outputs under `examples/qualibact_ecoli/`.

Real QualiBact ATB E. coli panel generation:

```bash
pixi run python scripts/build_ghru_ecoli_panel_report.py \
  .demo_work/ghru_ecoli_panel/triplet/output \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work
```

This writes `examples/qualibact_ecoli/real_panel/report/` from real upstream
`GHRU-assembly` outputs.

Interactive table behavior:

- click headers to sort
- use the filter box to narrow rows

## Excel workbook

The workbook currently includes:

- merged `report` sheet
- `qc_status` sheet
- one sheet per compact metric summary category when available

## Docker usage

Typical Docker summary run:

```bash
docker run --rm \
  -v $(pwd):/data \
  -v $(pwd)/output:/output \
  happykhan/speccheck \
  speccheck summary /data --output /output --plot
```
