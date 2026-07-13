# Code Quality Audit

This page records the maintainability review standard used for the manuscript-readiness pass and the current codebase status.

## Review standard

The audit prioritizes structural quality over cosmetic cleanup:

- keep behavior-preserving refactors if they delete concepts or branches
- keep feature-specific logic out of shared orchestration paths
- split modules before files approach unreviewable size
- prefer explicit data boundaries over silent fallback behavior
- keep generated artifacts and scratch work out of source control

## Current architecture

`speccheck` has focused runtime layers:

- CLI entrypoints in `speccheck/cli.py`
- collection orchestration in `speccheck/collect_workflow.py`
- summary orchestration in `speccheck/summary_workflow.py`
- backward-compatible workflow exports in the thin `speccheck/main.py` façade
- explicit parser/plot and metric-alias ownership in `speccheck/registry.py`
- parser modules in `speccheck/modules/`
- HTML/XLSX reporting in `speccheck/report.py`, `speccheck/report_tables.py`, and `speccheck/plot_modules/`

The largest remaining modules are:

- `speccheck/collect.py`: parser dispatch, criteria checks, CSV writing
- `speccheck/report.py`: report context and HTML template rendering
- `speccheck/report_tables.py`: status normalization, HTML tables, summary tables, workbook export
- `speccheck/update_criteria.py`: QualiBact threshold import

No source file is near the 1000-line threshold. Workflow decomposition and
explicit registries now keep new integration logic out of the shared façade.

## Completed in this pass

- Split report table/status/workbook helpers out of `speccheck/report.py` into `speccheck/report_tables.py`.
- Reduced `speccheck/report.py` from a mixed rendering/table utility module into a report-composition module.
- Fixed duplicated failure-reason list rendering and added a regression test.
- Kept Python 3.10 compatibility explicit with a `tomli` fallback for `tomllib`.
- Kept report CSS embedded in generated HTML so example reports are single-file artifacts.
- Made parser collection fail on duplicate parser matches instead of silently overwriting outputs.
- Made summary input loading reject duplicate sample IDs and missing sample columns while ignoring generated `detailed.*.csv` files.
- Replaced manual CSV string joining with `csv.DictWriter` so metadata values with commas, quotes, or newlines remain valid CSV.
- Made unresolved organism handling strict by default, with `--allow-unknown-organism` as an explicit fallback.
- Made QUAST parsing key-based so optional row ordering changes do not break valid reports.
- Fixed DepthParser criteria application against parsed `Depth` outputs.
- Added pinned QualiBact E. coli v1 compatibility output with PASS/WARN/FAIL tiers.
- Added CheckM2 metric aliases before criteria evaluation.
- Removed legacy CheckM1 marker-lineage criteria from QualiBact-derived packaged criteria because QualiBact thresholds are CheckM2-calibrated.
- Added `Total_Coding_Sequences` to criteria import and concise report outputs.
- Added explicit `--assembly-type` criteria filtering with provenance in collected CSV outputs.
- Added visible `NOT_EVALUATED` check statuses for expected metrics missing from detected parser outputs, with opt-in strict failure via `--fail-on-not-evaluated`.
- Added basic collection provenance fields: speccheck version, assembly type, criteria path/hash, input file count, and `NOT_EVALUATED` count.
- Replaced dynamic parser and plotting discovery with explicit registries.
- Centralized CheckM2/legacy metric equivalence groups.
- Split collection and summary workflows out of `main.py`.
- Kept historical QualiBact metadata separate from current QC ownership.
- Isolated criteria-update snapshot writes so tests cannot mutate package data.
- Added a complete, provenance-backed 100-sample GHRU case study.

## Remaining high-value refactors

1. Introduce typed report models.

   The report layer still passes loosely-shaped dictionaries and dataframes between stages. A small `ReportContext` dataclass would make required fields explicit and reduce accidental key drift.

2. Add a generated-artifact hygiene check.

   CI should fail if `.demo_work/`, `htmlcov/`, `site/`, `dist/`, or local virtual environments are accidentally staged.

3. Extend strict-mode policy for `NOT_EVALUATED`.

   Missing expected metrics are now visible in collected outputs and reports, and `collect --fail-on-not-evaluated` can make them fail parser/sample checks. The next step is deciding whether example manuscript workflows should always enable that strict mode.

## Manuscript readiness status

The project now has the core OSS/manuscript baseline:

- MkDocs Material documentation
- README quick start
- reproducible QualiBact E. coli examples
- pinned QualiBact E. coli v1 compatibility tiers for PASS/WARN/FAIL manuscript examples
- HTML, CSV, and XLSX report artifacts
- Slurm-ready real-panel workflow
- test coverage for report generation and QualiBact conversion

The primary manuscript case study now uses real reads and canonical GHRU outputs
for QUAST, CheckM2, Speciator, Sylph, and depth. Its accession table, upstream
commit/patch, container inventory, hashes, reports, analyses, and figures are
committed. Broader species-level compatibility remains outside the current claim.
