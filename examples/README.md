# Examples

This directory contains manuscript-oriented example reports generated from pinned QualiBact E. coli pass/fail fixtures.

## Generate the example reports

```bash
python scripts/generate_qualibact_example_reports.py
```

This creates:

- `examples/qualibact_ecoli/pass_only/report/`
- `examples/qualibact_ecoli/fail_only/report/`

Each report directory contains:

- `report.csv`
- `report.html`
- `report.xlsx`
- `bulma.css`

## Upstream analysis template

For environments where you want to rerun the upstream QC tools before `speccheck collect`, use the Slurm-ready template:

```bash
scripts/upstream_qc_slurm_template.sh
```

It is a site-specific template, not a complete workflow manager. Replace the placeholder Speciator, Sylph, and ARIBA commands with the commands used in your environment.
