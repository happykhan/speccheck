# Manuscript Assets

This page collects the example data, report outputs, and figure-generation commands intended for manuscript preparation.

## Example report sets

The repository includes three E. coli report sets:

| Example | Purpose | Outputs |
| --- | --- | --- |
| `examples/qualibact_ecoli/pass_only/` | minimal passing example | `report.csv`, `report.html`, `report.xlsx` |
| `examples/qualibact_ecoli/fail_only/` | minimal failing example | `report.csv`, `report.html`, `report.xlsx` |
| `examples/qualibact_ecoli/real_panel/` | real QualiBact ATB PASS/WARN/FAIL panel | `report.csv`, `report.html`, `report.xlsx` |

The HTML reports are self-contained and embed the report stylesheet, so they can be attached to manuscript supplements without a companion CSS file.

## Regenerate minimal reports

```bash
python scripts/generate_qualibact_example_reports.py
```

This refreshes the minimal pass/fail reports from pinned fixtures under `tests/qualibact/`.

## Regenerate the real QualiBact panel

```bash
python scripts/build_qualibact_ecoli_demo.py
```

On a Slurm cluster:

```bash
sbatch scripts/slurm_qualibact_ecoli_demo.sh
```

The real-panel workflow:

1. Downloads QualiBact E. coli PASS/WARN/FAIL ATB lists.
2. Selects a small balanced panel.
3. Fetches assemblies with `atbfetcher`.
4. Runs QUAST on the assemblies.
5. Converts QualiBact/ATB CheckM2 and species metrics into `speccheck` parser inputs.
6. Generates CSV, HTML, and XLSX reports.

Raw FASTA and intermediate files stay under `.demo_work/qualibact_ecoli_real/` and should not be committed.

## Export report screenshots

Use the screenshot helper when a headless browser is available:

```bash
scripts/export_report_screenshots.sh
```

By default, screenshots are written to `examples/qualibact_ecoli/figures/`:

- `pass_only_report.png`
- `fail_only_report.png`
- `real_panel_report.png`

The script supports Chromium, Chrome, or Firefox. On some HPC login nodes Firefox headless mode can fail because browser profile and graphics services are restricted; in that case run the script on a workstation or an interactive node with a working headless browser.

## Suggested manuscript figures

- **Figure 1:** `speccheck` workflow diagram: upstream QC tools, `collect`, criteria checks, `summary`, and report outputs.
- **Figure 2:** Real QualiBact E. coli PASS/WARN/FAIL panel report screenshot.
- **Figure 3:** Compact summary tables showing species assignment, assembly quality, completeness/contamination, and coverage/abundance.
- **Supplementary Figure 1:** Passing-only report screenshot.
- **Supplementary Figure 2:** Failing-only report screenshot with failure reasons.

## Suggested manuscript table

Use `examples/qualibact_ecoli/real_panel/report/report.csv` to summarize the real-panel benchmark. Useful columns include:

- `sample_id`
- `qualibact_tier`
- `all_checks_passed`
- `Quast.N50`
- `Quast.# contigs (>= 0 bp)`
- `Checkm.Completeness`
- `Checkm.Contamination`
- `qualibact_reasons`

## Current limitation

The real-panel demonstration currently uses locally generated QUAST metrics and QualiBact/ATB-exported CheckM2/species metrics. For a stricter manuscript validation run, wire a local CheckM2 database into the Slurm workflow and regenerate the panel with CheckM2 executed directly on the downloaded assemblies.
