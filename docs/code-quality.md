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

`speccheck` has three main runtime layers:

- CLI entrypoints in `speccheck/cli.py`
- workflow orchestration in `speccheck/main.py`
- parser modules in `speccheck/modules/`
- HTML/XLSX reporting in `speccheck/report.py`, `speccheck/report_tables.py`, and `speccheck/plot_modules/`

The largest remaining modules are:

- `speccheck/main.py`: CLI workflow orchestration
- `speccheck/collect.py`: parser dispatch, criteria checks, CSV writing
- `speccheck/report.py`: report context and HTML template rendering
- `speccheck/report_tables.py`: status normalization, HTML tables, summary tables, workbook export
- `speccheck/update_criteria.py`: QualiBact threshold import

No source file is near the 1000-line threshold, but `main.py` and `collect.py` still carry mixed responsibilities and should be the next decomposition targets.

## Completed in this pass

- Split report table/status/workbook helpers out of `speccheck/report.py` into `speccheck/report_tables.py`.
- Reduced `speccheck/report.py` from a mixed rendering/table utility module into a report-composition module.
- Fixed duplicated failure-reason list rendering and added a regression test.
- Kept Python 3.10 compatibility explicit with a `tomli` fallback for `tomllib`.
- Kept report CSS embedded in generated HTML so example reports are single-file artifacts.

## Remaining high-value refactors

1. Split `speccheck/main.py` into smaller workflow services.

   `collect`, `summary`, and `check` currently share one file. The clean split is `collect_workflow.py`, `summary_workflow.py`, and `criteria_workflow.py`, with `main.py` kept as a thin compatibility layer.

2. Replace dynamic parser overwrite behavior with an explicit parser registry.

   `collect_files` currently stores one result per parser class name. That is simple, but it silently overwrites when multiple files match the same parser. A registry that records parser ownership, expected cardinality, and merge behavior would be safer.

3. Make summary input validation explicit.

   `summary` should fail fast on duplicate sample IDs, missing sample columns, and mixed concise/detailed CSV inputs instead of relying on dictionary overwrite semantics.

4. Introduce typed report models.

   The report layer still passes loosely-shaped dictionaries and dataframes between stages. A small `ReportContext` dataclass would make required fields explicit and reduce accidental key drift.

5. Normalize CheckM/CheckM2 naming.

   Runtime parsers and report labels use `Checkm`, while manuscript language often uses CheckM/CheckM2. The code should preserve parser identity but expose consistent display names.

6. Add a generated-artifact hygiene check.

   CI should fail if `.demo_work/`, `htmlcov/`, `site/`, `dist/`, or local virtual environments are accidentally staged.

## Manuscript readiness status

The project now has the core OSS/manuscript baseline:

- MkDocs Material documentation
- README quick start
- reproducible QualiBact E. coli examples
- HTML, CSV, and XLSX report artifacts
- Slurm-ready real-panel workflow
- test coverage for report generation and QualiBact conversion

The main remaining manuscript risk is upstream-tool reproducibility for the real panel: QUAST is run locally, while CheckM2/species metrics are currently converted from QualiBact/ATB exports unless a site-local CheckM2 database is installed and wired into the workflow.
