# Deep Audit

This page summarizes the expert audit captured in `CODEBASE_AUDIT.md`.

## Bottom line

`speccheck` is now a credible manuscript-stage prototype with a usable CLI, MkDocs Material documentation, CI, packaged templates, single-file HTML reports, XLSX export, and QualiBact E. coli examples.

The main remaining risks are:

- Scientific scope clarity: generic QualiBact-derived `FINAL_*` checks remain binary, while `--qualibact-compat` now provides a verified pinned E. coli v1 PASS/WARN/FAIL comparison tier for the manuscript panel.
- Runtime architecture: parser discovery, criteria evaluation, and report generation are still driven by dynamic conventions and CSV column names.
- Reproducibility: the real-panel demo includes real QualiBact selections and local QUAST, but full upstream CheckM2/Sylph/Speciator execution needs a pinned workflow.

## Priority fixes

1. Define the exact QualiBact claim in the manuscript and docs.
2. Extend the new compatibility mode beyond the pinned E. coli v1 manuscript panel when additional species are needed.
3. Move the explicit `--assembly-type` criteria filter into a typed sample/report provenance model.
4. Move the current CheckM2 metric aliases into a canonical registry.
5. Replace dynamic parser discovery with an explicit parser registry.
6. Introduce typed internal models for parsed metrics, criteria, check results, reports, and provenance.
7. Decide when manuscript and CI workflows should enable `--fail-on-not-evaluated`.
8. Remove or deprecate legacy root assets before Bioconda preparation.
9. Add static manuscript screenshots generated from the example reports.
10. Pin the upstream demonstration workflow and extend provenance from current speccheck/criteria metadata to upstream tool and database versions.

## Readiness scores

| Area | Score | Rationale |
| --- | ---: | --- |
| Scientific clarity | 8/10 | Useful binary criteria model plus verified pinned E. coli compatibility tier; broader species parity remains future work. |
| Parser robustness | 6/10 | Works for expected fixtures and CheckM2 aliases; needs schemas, registry, and version handling. |
| Architecture | 6/10 | Clear modules exist; orchestration and data model are still mixed/stringly typed. |
| CLI UX | 7/10 | Typer CLI is usable; error handling and output modes need polish. |
| Reports | 7/10 | Single-file HTML and XLSX are good; plot modules need safer rendering boundaries. |
| Tests | 7/10 | Good base coverage; missing parity, malformed input, performance, and CLI UX tests. |
| Packaging | 7/10 | Modern pyproject and wheel smoke test; cleanup needed for Bioconda readiness. |
| CI | 7/10 | Strong job coverage; release/security workflows need modernization. |
| Docs | 7/10 | MkDocs site exists; needs architecture, parser guide, provenance/methods caveats. |
| Reproducibility | 5/10 | Good examples; upstream tool/database provenance not fully pinned. |

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
