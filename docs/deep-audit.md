# Deep Audit

This page summarizes the expert audit captured in `CODEBASE_AUDIT.md`.

## Bottom line

`speccheck` is now a publication-candidate implementation with a usable CLI,
explicit parser/plot registries, focused collection and summary workflows,
MkDocs documentation, CI, packaged templates, single-file HTML reports, XLSX
export, and a completed 100-sample read-backed E. coli case study.

The main remaining risks are:

- Scientific scope clarity: generic QualiBact-derived `FINAL_*` checks remain binary, while `--qualibact-compat` now provides a verified pinned E. coli v1 PASS/WARN/FAIL comparison tier for the manuscript panel.
- Runtime architecture: criteria and report data are still represented primarily
  as CSV columns/dataframes rather than typed domain models.
- Reproducibility: the E. coli case study is pinned and complete, but broader
  species-level QualiBact compatibility has not been claimed or validated.

## Priority fixes

1. Define the exact QualiBact claim in the manuscript and docs.
2. Extend the new compatibility mode beyond the pinned E. coli v1 manuscript panel when additional species are needed.
3. Move the explicit `--assembly-type` criteria filter into a typed sample/report provenance model.
4. Introduce typed internal models for parsed metrics, criteria, check results, reports, and provenance.
5. Decide when manuscript and CI workflows should enable `--fail-on-not-evaluated`.
6. Remove or deprecate legacy root assets before Bioconda preparation.
7. Extend automated malformed-input and parser-version compatibility tests.

## Readiness scores

| Area | Score | Rationale |
| --- | ---: | --- |
| Scientific clarity | 8/10 | Useful binary criteria model plus verified pinned E. coli compatibility tier; broader species parity remains future work. |
| Parser robustness | 6/10 | Works for expected fixtures and CheckM2 aliases; needs schemas, registry, and version handling. |
| Architecture | 8/10 | Workflows and registries are explicit; the internal data model remains dataframe/string based. |
| CLI UX | 7/10 | Typer CLI is usable; error handling and output modes need polish. |
| Reports | 7/10 | Single-file HTML and XLSX are good; plot modules need safer rendering boundaries. |
| Tests | 8/10 | Strong regression and case-study checks; malformed input and parser-version matrices can expand. |
| Packaging | 7/10 | Modern pyproject and wheel smoke test; cleanup needed for Bioconda readiness. |
| CI | 7/10 | Strong job coverage; release/security workflows need modernization. |
| Docs | 7/10 | MkDocs site exists; needs architecture, parser guide, provenance/methods caveats. |
| Reproducibility | 8/10 | Accessions, upstream commit/patch, containers, hashes, commands, outputs, and benchmarks are recorded. |

## Architecture direction

Current shape:

```text
CLI -> main workflows -> dynamic parser modules -> criteria checks -> CSV/HTML/XLSX reports
```

Target shape:

```text
CLI
  -> workflow modules
  -> parser registry
  -> typed parsed metrics
  -> criteria engine
  -> report serializers
  -> provenance-aware outputs
```

See `CODEBASE_AUDIT.md` in the repository root for the full severity-ranked findings, file references, and implementation roadmap.
