# Manuscript Assets

This page collects the example data, report outputs, and figure-generation commands intended for manuscript preparation.

## Example report sets

The repository includes three compact examples and one primary case study:

| Example | Purpose | Outputs |
| --- | --- | --- |
| `examples/qualibact_ecoli/pass_only/` | minimal passing example | `report.csv`, `report.html`, `report.xlsx` |
| `examples/qualibact_ecoli/fail_only/` | minimal failing example | `report.csv`, `report.html`, `report.xlsx` |
| `examples/qualibact_ecoli/real_panel/` | real QualiBact ATB PASS/WARN/FAIL panel | `report.csv`, `report.html`, `report.xlsx` |
| `examples/qualibact_ecoli/real_run_100/` | completed 100-sample read-backed case study | reports, accessions, analyses, provenance, figures |

The HTML reports are self-contained and embed the report stylesheet, so they can be attached to manuscript supplements without a companion CSS file.

## Regenerate minimal reports

```bash
python scripts/generate_qualibact_example_reports.py
```

This refreshes the minimal pass/fail reports from pinned fixtures under `tests/qualibact/`.

## Regenerate the real QualiBact panel

Rebuild the committed `real_panel` report directly from a finished local GHRU run:

```bash
pixi run python scripts/build_ghru_ecoli_panel_report.py \
  .demo_work/ghru_ecoli_panel/triplet/output \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work
```

This route preserves the real upstream `GHRU-assembly` metrics that `speccheck` should consume in production.

## Regenerate the 100-sample case-study assets

After the upstream cohort and downstream report have been rebuilt as documented
in `examples/qualibact_ecoli/real_run_100/README.md`, export the compact committed
assets with:

```bash
pixi run python scripts/create_real_run_100_assets.py
```

The committed cohort contains 70 historical PASS, 20 WARN, and 10 FAIL samples.
Current GHRU-derived metrics produce 90 PASS, 6 WARN, and 4 FAIL compatibility
tiers; exact tier agreement is 73%. This is a concordance analysis, not an
accuracy benchmark against ground truth.

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
- **Figure 2:** Historical-versus-current tier concordance in 100 real genomes.
- **Figure 3:** GHRU-derived metric distributions by historical tier.
- **Figure 4:** Static snapshot of samples requiring current review.
- **Supplementary Figure 1:** Passing-only report screenshot.
- **Supplementary Figure 2:** Failing-only report screenshot with failure reasons.

### Figure 1: workflow

![speccheck workflow](assets/figures/speccheck_workflow.svg)

Source files:

- `examples/qualibact_ecoli/manuscript_assets/speccheck_workflow.svg`
- `examples/qualibact_ecoli/manuscript_assets/speccheck_workflow.png`

### Figure 2: 100-sample tier concordance

![Historical and current E. coli QC tiers](assets/figures/real_run_100_tier_concordance.svg)

Source files:

- `examples/qualibact_ecoli/real_run_100/figures/tier_concordance.svg`
- `examples/qualibact_ecoli/real_run_100/figures/tier_concordance.png`

### Figure 3: metric distributions

![Observed metrics by historical tier](assets/figures/real_run_100_metric_distributions.svg)

Source files:

- `examples/qualibact_ecoli/real_run_100/figures/metric_distributions.svg`
- `examples/qualibact_ecoli/real_run_100/figures/metric_distributions.png`

### Figure 4: report snapshot

![100-sample report snapshot](assets/figures/real_run_100_report_snapshot.svg)

Source files:

- `examples/qualibact_ecoli/real_run_100/figures/report_snapshot.svg`
- `examples/qualibact_ecoli/real_run_100/figures/report_snapshot.png`

## Suggested manuscript table

Use `examples/qualibact_ecoli/real_panel/report/report.csv` to summarize the real-panel benchmark. Useful columns include:

- `sample_id`
- `qualibact_tier`
- `qualibact_compat_tier`
- `qualibact_compat_reasons`
- `qualibact_compat_warn_policy`
- `all_checks_passed`
- `Quast.N50`
- `Quast.# contigs (>= 0 bp)`
- `Checkm.Completeness`
- `Checkm.Contamination`
- `qualibact_reasons`

A paper-ready subset is generated here:

- `examples/qualibact_ecoli/manuscript_assets/real_panel_summary_table.csv`
- `examples/qualibact_ecoli/manuscript_assets/real_panel_summary_table.md`

Preview:

--8<-- "examples/qualibact_ecoli/manuscript_assets/real_panel_summary_table.md"

## Interpretation boundary

Historical QualiBact tiers and reasons are retained as comparison metadata and
never override current QC status. Differences can arise from upstream reads,
assemblies, tool/database versions, or threshold semantics. The pinned
PASS/WARN/FAIL compatibility claim applies only to E. coli v1. CheckM1
marker-lineage output is not used because these metrics are CheckM2-calibrated.
