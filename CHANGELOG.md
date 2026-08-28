# Changelog

## 1.3.0 - 2026-08-28

- added direct collection from canonical `GHRU-assembly` output trees
- added a completed, reproducible 100-sample read-backed E. coli case study
- added pinned QualiBact E. coli v1 PASS/WARN/FAIL compatibility tiers
- added a stable 19-column concise CSV, a canonical-first full CSV,
  self-contained HTML, and multi-sheet XLSX reports
- standardised user-facing QC fields on `PASS`, `WARN`, `FAIL`, and
  `NOT_EVALUATED`, with no Boolean verdicts in cohort reports
- added an exception-first HTML review queue, sample details, species filters,
  persistent navigation, and accessible status-coloured inline SVG charts
- added strict missing-metric mode, criteria precedence, assembly-type
  filtering, conflict detection, and collection provenance
- added deterministic concordance, metric-distribution, and report snapshot
  figures for the worked E. coli case study
- replaced dynamic parser/plot discovery with explicit registries and centralized
  CheckM2 metric aliases
- split collection and summary orchestration into focused workflow modules
- prevented historical comparison labels from overriding current QC status
- isolated criteria snapshot writes so tests do not mutate packaged provenance
- normalised Sylph abundance to the explicit `top_abundance_percent` field
- expanded tests, CI, documentation, packaging, and manual release controls
