# QualiBact Integration

`speccheck` can refresh criteria from the machine-readable QualiBact export:

```text
https://static.qualibact.org/api/v2/thresholds.csv
```

## Current behavior

- thresholds are downloaded from the aggregate CSV export
- each species follows the QualiBact index `preferred_scheme`
- supported metrics are mapped into the internal `speccheck` criteria format
- `Total_Coding_Sequences` is mapped when final bounds are present
- existing unmanaged criteria rows are preserved
- optional compatibility mode adds species-aware, pinned PASS/WARN/FAIL tier columns

QualiBact thresholds are calibrated around CheckM2-derived metrics. In `speccheck`
outputs these still use the historical `Checkm.*` column prefix for compatibility,
but the supported fields are CheckM2-style fields such as `Completeness`,
`Contamination`, `Genome_Size`, `GC_Content`, `Contig_N50`, `Total_Contigs`, and
`Total_Coding_Sequences`. Native CheckM1 tabular reports are also accepted and
normalised to these canonical fields; marker-lineage-only fields are not used
as QualiBact metrics.

## Supported imported metrics

- `Genome_Size`
- `N50`
- `no_of_contigs`
- `GC_Content`
- `Completeness`
- `Contamination`
- `Total_Coding_Sequences`

## QualiBact tier compatibility

All Speccheck criteria use the same `PASS`/`WARN`/`FAIL` vocabulary. `summary`
can additionally apply the release-pinned preferred QualiBact scheme for the
species assigned to each sample:

```bash
speccheck summary qc_results \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --qualibact-compat
```

This adds:

- `qualibact_qc`: `PASS`, `WARN`, `FAIL`, or `NOT_EVALUATED`
- `qualibact_compat_reasons`: threshold reasons such as `no_of_contigs >670.0`
- `qualibact_compat_source`: pinned source label

Each release pins the aggregate threshold snapshot and preferred-scheme map for
reproducibility. The E. coli case-study scheme is:

```text
https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0
```

Speccheck applies this E. coli threshold set to samples assigned to the genus
*Shigella*. The reported species assignment is retained, and the compatibility
source records that E. coli thresholds were applied to that *Shigella* species.

QualiBact `WARN` remains `WARN` in both `qualibact_qc` and `overall_qc`. Speccheck
does not silently convert warnings into failures.

Historical `qualibact_tier` and `qualibact_reasons` input values are emitted as
`historical_qualibact_qc` and comparison reasons. They are comparison
metadata. They do not define `overall_qc` and do not replace freshly computed
compatibility reasons. This separation prevents older assemblies or exports from
silently overriding the current QC verdict.

The completed 100-sample case study found 73% exact tier agreement: 68/70
historical PASS, 1/20 historical WARN, and 4/10 historical FAIL remained in the
same tier. Three samples were `NOT_EVALUATED` because their current species could
not be identified. These are concordance results, not sensitivity or specificity,
because historical tiers are not treated as ground truth.

## Regression fixtures

Pinned E. coli fixtures are kept under `tests/qualibact/`:

- `thresholds_subset.csv`
- `ecoli_pass_subset.csv`
- `ecoli_fail_subset.csv`

These support deterministic tests for importer behaviour and report generation.
Boundary tests verify that exact FINAL and WARN limits use QualiBact's inclusive
semantics. A WARN side is ignored when no corresponding FINAL side exists,
because that side has no defined FAIL region.
