# Real 100-sample E. coli case study

This directory contains the compact, publication-facing outputs from a completed
read-backed `GHRU-assembly` run. Raw FASTQ files, assemblies, Nextflow work files,
and databases are intentionally excluded from Git.

## Cohort

The cohort contains 100 *Escherichia coli* samples selected from the pinned
QualiBact v1 lists: 70 historical PASS, 20 WARN, and 10 FAIL. Within each tier,
the staging script selected the first rows that resolved to paired *E. coli* ENA
reads. `cohort_accessions.csv` records the BioSample and ENA run accessions,
historical metrics, labels, and reasons.

## Results

Fresh GHRU-derived measurements produced 90 PASS, 6 WARN, and 4 FAIL compatibility
tiers. Exact tier agreement with the historical labels was 73/100. Three samples
had an unidentified Speciator result. This comparison measures concordance, not
accuracy: historical labels are not treated as ground truth, and differences can
reflect changed reads, assemblies, tools, databases, or threshold interpretation.

Committed outputs include:

- `report/`: concise/full CSV, self-contained HTML, and XLSX reports;
- `analysis/tier_concordance.csv`: historical-by-current tier matrix;
- `analysis/discordant_samples.csv`: all 27 tier-discordant samples;
- `analysis/current_reason_counts.csv`: current WARN/FAIL reason counts;
- `analysis/metric_distributions.csv`: five-number summaries by historical tier;
- `analysis/summary.json`: results, hashes, upstream provenance, and benchmarks;
- `figures/`: deterministic SVG and PNG manuscript figures.

## Rebuild

After staging and completing the upstream run:

```bash
scripts/stage_ghru_ecoli_run_100.sh
scripts/submit_ghru_ecoli_run_100.sh

pixi run python -m speccheck.cli collect-ghru \
  .demo_work/ghru_ecoli_cohort/run_100/output \
  .demo_work/publication_100_final/collect \
  --organism "Escherichia coli" \
  --metadata .demo_work/ghru_ecoli_cohort/run_100/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_cohort/run_100/work

pixi run python -m speccheck.cli summary \
  .demo_work/publication_100_final/collect \
  --output .demo_work/publication_100_final/report \
  --plot --qualifyr-style --qualibact-compat --no-interactive-tables \
  --xlsx-output .demo_work/publication_100_final/report/report.xlsx

pixi run python scripts/create_real_run_100_assets.py
```

The upstream checkout is pinned to commit
`271e0d9e5593a4e4a59409f12f83e816794ad6a3`. Apply
`scripts/ghru_disable_upstream_speccheck.patch` so GHRU produces its canonical
outputs without running its bundled downstream `speccheck` stage.
