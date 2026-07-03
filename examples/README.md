# Examples

This directory contains manuscript-oriented example reports generated from QualiBact E. coli fixtures.

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

The HTML report is self-contained and embeds its stylesheet directly, so there is no companion CSS file to ship alongside it.

## Real QualiBact ATB E. coli panel

The real-panel demonstration uses a small PASS/WARN/FAIL selection from the QualiBact E. coli ATB lists, downloads the assemblies with `atbfetcher`, runs QUAST, converts QualiBact ATB CheckM2/species metrics into `speccheck` parser inputs, and generates a report:

```bash
python scripts/build_qualibact_ecoli_demo.py
```

On a Slurm cluster:

```bash
sbatch scripts/slurm_qualibact_ecoli_demo.sh
```

The generated report is written to:

- `examples/qualibact_ecoli/real_panel/report/report.html`
- `examples/qualibact_ecoli/real_panel/report/report.csv`
- `examples/qualibact_ecoli/real_panel/report/report.xlsx`

Raw downloaded FASTA files and intermediate QUAST outputs are kept under `.demo_work/qualibact_ecoli_real/` and are intentionally not committed. The committed `real_panel/input/` files record the selected accessions and QualiBact metadata used to generate the demonstration.

## Upstream analysis template

For environments where you want to rerun the upstream QC tools before `speccheck collect`, use the Slurm-ready template:

```bash
scripts/upstream_qc_slurm_template.sh
```

It is a site-specific template, not a complete workflow manager. Replace the placeholder Speciator, Sylph, and ARIBA commands with the commands used in your environment.
