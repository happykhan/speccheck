# Reports

`speccheck` reports are designed to be both human-reviewable and easy to archive.
The important rule is that collected per-sample CSVs are small and reproducible;
large upstream files stay in the workflow output area.

## Files written by `collect`

For each sample, `collect` writes a concise CSV containing:

- parsed metrics from recognised tools;
- status/check columns generated from the active criteria;
- provenance columns such as `speccheck_version`,
  `speccheck_criteria_sha256`, and `speccheck_input_file_count`;
- metadata columns when `--metadata` is supplied.

For some wide upstream outputs, a `detailed.*.csv` companion may also be written.
`summary` ignores these detailed companions by default so the merged cohort
report remains stable.

## Files written by `summary`

`summary` writes:

- `report.csv`: merged concise cohort table;
- `report.full.csv`: full wide table where available;
- `report.html`: self-contained HTML review report when `--plot` is enabled;
- `report.xlsx`: optional workbook when `--xlsx-output` is supplied.

When merging inputs, `summary` rejects duplicate or missing sample IDs instead
of silently overwriting samples.

## Key report columns

Start review with these columns:

| Column | Meaning |
| --- | --- |
| `overall_qc` | Four-state sample status: `PASS`, `WARN`, `FAIL`, or `NOT_EVALUATED`. |
| `all_checks_passed` | Boolean convenience column for strict pass/fail handling. |
| `baseline_qc` | Core Speccheck QC state before optional compatibility overlays. |
| `reason_summary` | Compact explanation of failures, warnings, and missing checks. |
| `speccheck_warning_count` | Number of warning-level criteria triggered. |
| `speccheck_failure_count` | Number of failure-level criteria triggered. |
| `speccheck_not_evaluated_count` | Number of expected metrics missing from detected parser outputs. |
| `species` / `species_confidence` | Resolved species information where parser outputs provide it. |

Tool-specific `*.status` columns use the same vocabulary:

- `PASS`: evaluated and passed;
- `WARN`: evaluated and triggered at least one warning criterion;
- `FAIL`: evaluated and triggered at least one failure criterion;
- `NOT_EVALUATED`: expected evidence was missing.

Legacy `*.check` columns may contain booleans or status values depending on the
parser and criteria generation path. Prefer `*.status`, `overall_qc`, and
`reason_summary` for new analyses.

## QualiBact compatibility columns

When `--qualibact-compat` is used, `summary` adds pinned *E. coli* QualiBact v1
compatibility columns such as:

- `qualibact_compat_tier`;
- `qualibact_compat_reasons`;
- `qualibact_compat_warn_policy`.

These columns are an explicit compatibility overlay for the *E. coli* threshold
version used in the 100-sample case study. They should not be described as
general multi-species QualiBact parity.

## HTML report

The HTML report includes:

- cohort-level PASS/WARN/FAIL counts;
- a concise sample review table;
- top warning and failure reasons;
- compact category summary tables;
- overall QC status matrix;
- software-specific charts and tables where plot modules exist.
- a collapsible full-detail table for wide parser/provenance columns.

Generate an HTML report with:

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --xlsx-output qc_report/report.xlsx
```

Interactive tables can be sorted by clicking headers, filtered with the search
box, and paged so large cohorts are easier to review. The HTML is
self-contained, so it can be stored with a release artifact or shared for review
without a server.

For large runs, start with:

1. the KPI cards at the top;
2. the sample review table;
3. the warning/failure reason panels;
4. the compact metric summary tables;
5. the full-detail table only when you need every raw parser column.

## Example report generation

Minimal fixture-based examples:

```bash
pixi run python scripts/generate_qualibact_example_reports.py
```

Real GHRU-derived panel:

```bash
pixi run python scripts/build_ghru_ecoli_panel_report.py \
  .demo_work/ghru_ecoli_panel/triplet/output \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work
```

100-sample case-study assets:

```bash
pixi run python scripts/create_real_run_100_assets.py
```

## Docker usage

Typical Docker summary run:

```bash
docker run --rm \
  -v $(pwd):/data \
  -v $(pwd)/output:/output \
  happykhan/speccheck \
  summary /data --output /output --plot
```
