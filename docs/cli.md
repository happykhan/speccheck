# CLI Usage

## `collect`

Collect and validate QC metrics from detected tool outputs.

```bash
speccheck collect FILEPATHS... --sample SAMPLE_ID
```

Common options:

- `--organism`
- `--sample`
- `--criteria-file`
- `--output-file`
- `--metadata`
- `--assembly-type all|short|long|hybrid`
- `--allow-unknown-organism`
- `--fail-on-not-evaluated / --no-fail-on-not-evaluated`
- `-v`, `--verbose`

If `--organism` is omitted, `speccheck` attempts to infer the species from parser outputs marked as species fields in the criteria file. If no single species can be resolved, collection stops by default. Use `--allow-unknown-organism` only when you explicitly want fallback `Unknown` criteria.

`--assembly-type` controls which criteria rows are evaluated. The default is `short`, which applies `all` and `short` criteria rows. `long` applies `all` and `long` rows, `hybrid` applies `all`, `short`, and `long` rows, and `all` applies only rows explicitly marked `all`. The selected mode is recorded in collected CSV outputs as `speccheck_assembly_type`.

If an expected metric is missing from a detected parser output, the relevant `*.check` column is reported as `NOT_EVALUATED`. By default this is visible review metadata but does not change the parser/sample pass flag. Add `--fail-on-not-evaluated` for strict manuscript or CI runs where incomplete evidence should fail the sample.

Example:

```bash
speccheck collect tests/practice_data/Sample_178db692semb \
  --sample Sample_178db692semb \
  --assembly-type short \
  --criteria-file speccheck/config/criteria.csv \
  --output-file qc_results/Sample_178db692semb.csv
```

## `summary`

Merge collected CSV files and optionally generate HTML and XLSX outputs.

```bash
speccheck summary DIRECTORY --output qc_report --plot
```

Additional reporting options:

- `--xlsx-output PATH`
- `--qualifyr-style / --no-qualifyr-style`
- `--interactive-tables / --no-interactive-tables`
- `--templates PATH`

`summary` reads concise collected CSV files. It ignores sibling `detailed.*.csv` files and skips an existing output directory, but it fails fast on missing sample columns or duplicate sample IDs rather than silently overwriting samples.

Example:

```bash
speccheck summary qc_results \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --qualibact-compat \
  --xlsx-output qc_report/report.xlsx
```

Use `--qualibact-compat` to add pinned *E. coli* QualiBact v1 `PASS`/`WARN`/`FAIL`
tier columns to `report.csv`, `report.html`, and optional XLSX output. WARN remains a
warning tier by default; add `--qualibact-warn-as-fail` if WARN should also fail the
binary `all_checks_passed` summary.

## `check`

Validate or refresh a criteria CSV.

```bash
speccheck check --criteria-file speccheck/config/criteria.csv
```

Refresh from QualiBact:

```bash
speccheck check \
  --criteria-file speccheck/config/criteria.csv \
  --update \
  --update-url https://static.qualibact.org/api/v2/external/thresholds.csv
```
