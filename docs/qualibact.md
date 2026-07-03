# QualiBact Integration

`speccheck` can refresh criteria from the machine-readable QualiBact export:

```text
https://static.qualibact.org/api/v2/external/thresholds.csv
```

## Current behavior

- thresholds are downloaded as CSV
- supported metrics are mapped into the internal `speccheck` criteria format
- unsupported metrics are skipped with warnings
- existing unmanaged criteria rows are preserved

## Supported imported metrics

- `Genome_Size`
- `N50`
- `no_of_contigs`
- `GC_Content`
- `Completeness`
- `Contamination`

## Current limitations

- `WARN_*` bands are documented but not turned into a separate runtime verdict tier
- unsupported metrics such as `Total_Coding_Sequences` are not yet mapped into a native `speccheck` check

## Regression fixtures

Pinned E. coli fixtures are kept under `tests/qualibact/`:

- `thresholds_subset.csv`
- `ecoli_pass_subset.csv`
- `ecoli_fail_subset.csv`

These support deterministic tests for importer behavior and report generation.
