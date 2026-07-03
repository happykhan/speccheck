# GitHub Issue Closeout

Recommended issue state updates after this pass:

## Close

- `#14` QualiBact criteria ingestion
  - Implemented via machine-readable import from QualiBact thresholds and pinned regression fixtures.

- `#10` Remove species names from violin plot tooltips
  - Plot hover data now excludes species labels while retaining metric values.

- `#9` Fix aspect ratio of Quast graphs
  - Quast plots were made taller for readability.

- `#8` Simplify Speciator table to species + confidence
  - Dedicated Speciator report table now renders only those two columns.

- `#7` Client-side sorting for tables
  - HTML report tables are sortable and filterable when interactive tables are enabled.

- `#6` Small summary tables for multiple metrics
  - Added compact metric summary tables grouped by category.

- `#5` Qualifyr-style HTML component
  - Implemented as native built-in qualifyr-like compact report tables rather than an external dependency.

- `#4` Export full results as Excel
  - `summary` now supports optional XLSX export.

- `#3` Small tables for different metric categories
  - Covered by the grouped compact summary-table implementation.

## Keep open only if you want follow-on scope

- None required for the implemented backlog.

Optional follow-on issues could be opened separately for:

- a true Nextflow workflow if you want one instead of the Slurm template
- warning-tier support from QualiBact `WARN_*` thresholds
- a Bioconda recipe submission in a separate packaging/release issue
