# Examples

This directory contains manuscript-oriented example reports generated from QualiBact E. coli fixtures.

## Generate the example reports

```bash
pixi run python scripts/generate_qualibact_example_reports.py
```

This creates:

- `examples/qualibact_ecoli/pass_only/report/`
- `examples/qualibact_ecoli/fail_only/report/`

Each report directory contains:

- `report.csv`
- `report.html`
- `report.xlsx`

The HTML report is self-contained and embeds its stylesheet directly, so there is no companion CSS file to ship alongside it.

## Real QualiBact ATB E. coli panel

The committed `real_panel` example is now sourced from real upstream `GHRU-assembly` outputs plus the pinned QualiBact selection metadata in:

- `examples/qualibact_ecoli/real_panel/input/selected_qualibact_ecoli.csv`
- `examples/qualibact_ecoli/real_panel/input/speccheck_metadata.csv`

Rebuild the committed report from a finished local GHRU output tree with:

```bash
pixi run python scripts/build_ghru_ecoli_panel_report.py \
  .demo_work/ghru_ecoli_panel/triplet/output \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work
```

This is the preferred route when the goal is to validate `speccheck` against real upstream `GHRU-assembly` outputs rather than synthetic parser inputs.

## Real 100-sample E. coli run

The old assembly-based 100-sample builder has been removed. The remaining 100-sample path is GHRU-backed:

```bash
scripts/stage_ghru_ecoli_run_100.sh
scripts/submit_ghru_ecoli_run_100.sh
```

That route:

- chooses the 70 PASS / 20 WARN / 10 FAIL cohort from QualiBact metadata
- resolves each selected sample to ENA paired-end reads
- downloads reads on a login node
- writes a GHRU `samplesheet.csv` plus metadata
- runs `external/GHRU-assembly`
- leaves the output ready for `speccheck collect-ghru` and `summary`

The generic staging logic lives in `scripts/stage_ghru_ecoli_cohort.py`.

## Manuscript screenshots

To export deterministic manuscript figures, PNGs, SVGs, and the real-panel summary table:

```bash
python scripts/create_manuscript_assets.py
```

This writes committed manuscript assets to `examples/qualibact_ecoli/manuscript_assets/` and mirrors figure files into `docs/assets/figures/` for MkDocs.

To export browser screenshots of the full example HTML reports:

```bash
scripts/export_report_screenshots.sh
```

The script writes screenshots to `examples/qualibact_ecoli/figures/`. It requires a working headless Chromium, Chrome, or Firefox installation.

## GHRU validation helpers

For the BMRC-backed validation route used in this repo:

```bash
scripts/stage_ghru_validation_assets.sh
scripts/submit_ghru_short_validation.sh
scripts/stage_ghru_ecoli_panel.sh triplet
scripts/submit_ghru_ecoli_panel.sh triplet
scripts/stage_ghru_ecoli_run_100.sh
scripts/submit_ghru_ecoli_run_100.sh
```
