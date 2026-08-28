# Reports

`speccheck` reports are designed to be both human-reviewable and easy to archive.
The important rule is that collected per-sample CSVs are small and reproducible;
large upstream files stay in the workflow output area.

## Files written by `collect`

For each sample, `collect` writes a concise CSV containing:

- parsed metrics from recognised tools;
- `PASS`/`WARN`/`FAIL` status columns generated from the active criteria;
- provenance columns such as `speccheck_version`,
  `speccheck_criteria_sha256`, and `speccheck_input_file_count`;
- metadata columns when `--metadata` is supplied.

For some wide upstream outputs, a `detailed.*.csv` companion may also be written.
`summary` ignores these detailed companions by default so the merged cohort
report remains stable.

## Files written by `summary`

`summary` writes:

- `report.csv`: merged concise cohort table;
- `report.full.csv`: human-ordered parser, compatibility, metadata, and provenance table;
- `report.html`: self-contained HTML review report when `--plot` is enabled;
- `report.xlsx`: optional workbook when `--xlsx-output` is supplied.

When merging inputs, `summary` rejects duplicate or missing sample IDs instead
of silently overwriting samples. Sample IDs are read as strings, so identifiers
such as `00123` retain their leading zeroes. Blank IDs, surrounding whitespace,
embedded-ID mismatches, and conflicting canonical/alias metric values stop the
merge with an actionable error.

## Key report columns

Start review with these columns:

| Column | Meaning |
| --- | --- |
| `overall_qc` | Worst current evaluated status across Speccheck and optional QualiBact QC. |
| `speccheck_qc` | Native Speccheck status, including criteria not derived from QualiBact. |
| `qualibact_qc` | Current QualiBact evaluation when `--qualibact-compat` is enabled. |
| `historical_qualibact_qc` | Imported comparison label; never used as the current verdict. |
| `reason_summary` | Compact explanation of failures, warnings, and missing checks. |
| `speccheck_warning_count` | Number of warning-level criteria triggered. |
| `speccheck_failure_count` | Number of failure-level criteria triggered. |
| `speccheck_not_evaluated_count` | Number of expected metrics missing from detected parser outputs. |
| `species` / `species_confidence` | Resolved species information where parser outputs provide it. |
| `top_abundance_percent` | Highest Sylph taxonomic abundance, always on a 0–100 scale. |
| `report_schema_version` | Version of the stable cohort-report column contract (`1.0`). |

Tool-specific `*.status` columns use the same vocabulary:

- `PASS`: evaluated and passed;
- `WARN`: evaluated and triggered at least one warning criterion;
- `FAIL`: evaluated and triggered at least one failure criterion;
- `NOT_EVALUATED`: expected evidence was missing.

CSV QC fields never use booleans or `PASSED`/`FAILED`. Legacy input `*.check`
columns are normalised to `*.status` in `report.full.csv`. Missing evidence can
remain `NOT_EVALUATED` at metric level, while non-strict missing evidence makes
the sample-level Speccheck result `WARN`.

The concise report is ordered as identifiers, current statuses and reasons,
species assignment, core assembly metrics, taxonomic abundance, then threshold
source. Its 19 version-1.0 columns are always present; optional unavailable
values are blank rather than removing columns. `report.full.csv` begins with
exactly the same columns, followed by
tool-level and metric statuses, tool metrics grouped by parser, compatibility
details, provenance, and metadata. Proven-equivalent aliases such as
`Checkm.GC`/`Checkm.GC_Content` are collapsed to the parser-native canonical
column in the cohort report, but only after verifying that populated aliases
agree. Raw per-sample `detailed.*.csv` files retain the original fields.

The exact concise order is:

```text
sample_id, overall_qc, speccheck_qc, qualibact_qc,
historical_qualibact_qc, reason_summary, species, species_confidence,
n50, contigs, genome_size, gc_percent, completeness, contamination,
depth, top_species, top_abundance_percent, threshold_source,
report_schema_version
```

## QualiBact compatibility columns

When `--qualibact-compat` is used, `summary` adds a species-aware evaluation
from the packaged, release-pinned QualiBact snapshot, including:

- `qualibact_qc`;
- `qualibact_compat_reasons`;
- `qualibact_compat_source`.

The packaged snapshot covers 317 QualiBact-indexed species and records the
preferred scheme used for each species. This is threshold-behaviour alignment,
not a claim that Speccheck reproduces the entire QualiBact web application.

`top_abundance_percent` is always expressed on a 0–100 percentage scale.

## HTML report

The HTML report includes:

- cohort-level PASS/WARN/FAIL counts;
- clickable KPI filters and a review queue that shows exceptions by default;
- a focused sample-detail dialog containing key metrics, tool statuses, and failed checks;
- top warning and failure reasons;
- collapsed cohort-level metric summaries with all-species and per-species views;
- collapsed per-tool diagnostics with exception-only result tables;
- lightweight inline SVG charts with hover values and sample-detail links;
- a collapsible data and provenance area for citations and the full-width table;
- persistent desktop navigation and a compact mobile jump menu.

Generate an HTML report with:

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --xlsx-output qc_report/report.xlsx
```

Select FAIL, WARN, NOT_EVALUATED, PASS, or all samples using the review tabs.
Interactive tables can be sorted by clicking headers, filtered with the search
box, and paged in groups of at most 25 rows. Opening one tool diagnostic closes
the others, so charts and secondary evidence do not dominate the page. Chart
points use the same PASS/WARN/FAIL/NOT_EVALUATED colours as the rest of the report;
selecting a point opens that sample's detail view. The HTML contains its CSS,
JavaScript and SVG charts, so it can be stored with a release artifact or shared
for review without a server.

For large runs, start with:

1. select the FAIL or WARN KPI, or use the default needs-review queue;
2. open an individual sample row to inspect its key evidence;
3. open a tool diagnostic only when the reason needs investigation;
4. use cohort metrics for distribution-level checks;
5. open data and provenance only when you need exports, citations, or raw parser columns.

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
