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

## HTML report

The HTML report includes:

- overall QC status table
- top failure reasons
- compact category summary tables
- optional qualifyr-style sample review table
- software-specific charts and tables

Example report generation from the pinned QualiBact E. coli pass/fail fixtures:

```bash
python scripts/generate_qualibact_example_reports.py
```

This creates manuscript-oriented example outputs under `examples/qualibact_ecoli/`.

Real QualiBact ATB E. coli panel generation:

```bash
python scripts/build_qualibact_ecoli_demo.py
```

For Slurm:

```bash
sbatch scripts/slurm_qualibact_ecoli_demo.sh
```

This writes `examples/qualibact_ecoli/real_panel/report/` and keeps raw FASTA
downloads/intermediate QUAST output in `.demo_work/qualibact_ecoli_real/`.

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
