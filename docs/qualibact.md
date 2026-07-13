# QualiBact Integration

`speccheck` can refresh criteria from the machine-readable QualiBact export:

```text
https://static.qualibact.org/api/v2/external/thresholds.csv
```

## Current behavior

- thresholds are downloaded as CSV
- supported metrics are mapped into the internal `speccheck` criteria format
- `Total_Coding_Sequences` is mapped when final bounds are present
- existing unmanaged criteria rows are preserved
- optional report-level compatibility mode adds pinned QualiBact E. coli PASS/WARN/FAIL tier columns

QualiBact thresholds are calibrated around CheckM2-derived metrics. In `speccheck`
outputs these still use the historical `Checkm.*` column prefix for compatibility,
but the supported fields are CheckM2-style fields such as `Completeness`,
`Contamination`, `Genome_Size`, `GC_Content`, `Contig_N50`, `Total_Contigs`, and
`Total_Coding_Sequences`. CheckM1 marker-lineage output is not supported for
QualiBact-derived criteria.

## Supported imported metrics

- `Genome_Size`
- `N50`
- `no_of_contigs`
- `GC_Content`
- `Completeness`
- `Contamination`
- `Total_Coding_Sequences`

## QualiBact tier compatibility

Generic criteria checks remain binary. For the E. coli case study and comparable audits, `summary` can add a pinned QualiBact E. coli v1 compatibility tier:

```bash
speccheck summary qc_results \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --qualibact-compat
```

This adds:

- `qualibact_compat_tier`: `PASS`, `WARN`, or `FAIL`
- `qualibact_compat_passed`: binary pass/fail after applying the warning policy
- `qualibact_compat_reasons`: threshold reasons such as `no_of_contigs >670.0`
- `qualibact_compat_warn_policy`: `warn-as-warn` by default
- `qualibact_compat_source`: pinned source label

The compatibility source is pinned to:

```text
https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0
```

Default warning policy is `warn-as-warn`: WARN remains visible as a tier but does not fail `all_checks_passed`. Use `--qualibact-warn-as-fail` when WARN should fail the binary summary status.

Historical `qualibact_tier` and `qualibact_reasons` values are comparison
metadata. They do not define `overall_qc` and do not replace freshly computed
compatibility reasons. This separation prevents older assemblies or exports from
silently overriding the current QC verdict.

The completed 100-sample case study found 69% exact tier agreement: 64/70
historical PASS, 1/20 historical WARN, and 4/10 historical FAIL remained in the
same tier. Seven samples were `NOT_AVAILABLE` under the pinned E. coli
compatibility policy because current species assignment fell outside that policy
or could not be identified. These are concordance results, not sensitivity or
specificity, because historical tiers are not treated as ground truth.

## Regression fixtures

Pinned E. coli fixtures are kept under `tests/qualibact/`:

- `thresholds_subset.csv`
- `ecoli_pass_subset.csv`
- `ecoli_fail_subset.csv`

These support deterministic tests for importer behavior and report generation.
