# Changelog

## Unreleased

- added direct collection from canonical `GHRU-assembly` output trees
- added a completed, reproducible 100-sample read-backed E. coli case study
- added pinned QualiBact E. coli v1 PASS/WARN/FAIL compatibility tiers
- added concise/full CSV, self-contained HTML, and multi-sheet XLSX reports
- added visible `NOT_EVALUATED` statuses, strict missing-metric mode, criteria
  precedence, assembly-type filtering, and collection provenance
- added deterministic manuscript concordance, metric-distribution, and report
  snapshot figures
- replaced dynamic parser/plot discovery with explicit registries and centralized
  CheckM2 metric aliases
- split collection and summary orchestration into focused workflow modules
- prevented historical comparison labels from overriding current QC status
- isolated criteria snapshot writes so tests do not mutate packaged provenance
- expanded tests, CI, documentation, packaging, and manual release controls
