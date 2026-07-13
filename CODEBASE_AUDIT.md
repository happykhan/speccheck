# speccheck Deep Codebase Audit

Date: 2026-07-04

Scope: repository source, tests, documentation, packaging, workflows, example reports, and public GitHub state available during review.

## Executive Summary

`speccheck` is now a credible manuscript-stage prototype: it has a Typer CLI, parser modules for common microbial QC outputs, criteria-based pass/fail evaluation, MkDocs Material documentation, CI, packaged templates, single-file HTML reports, XLSX export, and QualiBact E. coli examples.

The main remaining scientific boundary is scope clarity. The generic criteria engine validates outputs against binary internal criteria, while the dedicated `--qualibact-compat` summary mode now provides a pinned QualiBact E. coli v1 PASS/WARN/FAIL comparison tier for the manuscript panel. The current real-panel report verifies 3 PASS, 3 WARN, and 3 FAIL samples against that pinned E. coli source; broader multi-species QualiBact tier parity remains future work.

The second major risk is architectural brittleness. The runtime is still driven by dynamic module discovery, filename/header conventions, loosely typed dictionaries, and CSV column names. That is acceptable for a small tool, but it needs a typed parser/criteria/report model before the software is robust enough for long-term open-source maintenance, Bioconda packaging, and manuscript claims about reproducibility.

## Highest Priority Findings

### 1. QualiBact tier equivalence is pinned for E. coli v1 only

Severity: high

The real-panel demonstration includes QualiBact PASS/WARN/FAIL metadata and can now compute `qualibact_compat_tier` from a pinned E. coli v1 compatibility layer. The generic importer still maps `FINAL_lower` and `FINAL_upper` thresholds into binary criteria rows in `speccheck/update_criteria.py:146`; WARN bands are not part of that binary engine.

Consequence: the manuscript can make a specific E. coli v1 compatibility claim, but should not imply full QualiBact parity for every species or every future QualiBact threshold source.

Recommended fix:

- Define the claim precisely: "`speccheck` includes a pinned QualiBact E. coli v1 compatibility tier for manuscript examples."
- Extend compatibility to additional species only with pinned source URLs and parity tests.
- Keep generic `FINAL_*` criteria import documented as binary pass/fail.

### 2. Assembly type criteria now have an explicit runtime mode, but the model is still lightweight

Severity: medium

Criteria rows include `assembly_type`, and `speccheck collect --assembly-type {all,short,long,hybrid}` now filters criteria rows before evaluation. The selected mode is recorded in collected CSV outputs as `speccheck_assembly_type`, and tests cover all/short/long/hybrid selection.

Consequence: the immediate criteria-selection risk is fixed, but assembly type is still a string option rather than a typed sample/report property. Future workflow integration should infer or validate this from upstream analysis provenance.

Recommended fix:

- Keep the explicit CLI option documented as the stable public behavior.
- Add workflow-level inference/validation when a Nextflow/Snakemake upstream demo is introduced.
- Move assembly type into a typed sample provenance model.

### 3. CheckM2 metric naming still needs a canonical registry

Severity: medium

The `Checkm` parser name is retained for backward-compatible output columns, but the supported QualiBact-derived criteria are CheckM2-calibrated. The parser expects CheckM2-style headers such as `Genome_Size`, `GC_Content`, `Contig_N50`, and `Total_Contigs` in `speccheck/modules/checkm.py:16`. Runtime aliasing maps those fields to legacy display names before evaluation, and report plotting also aliases the display fields. Legacy CheckM1 marker-lineage criteria have been removed from the QualiBact-derived packaged criteria.

Consequence: the immediate CheckM2 mismatch is fixed, but the alias map still lives in workflow code rather than a canonical metric registry. Future parser additions can still drift if aliases are not declared centrally.

Recommended fix:

- Introduce a canonical metric registry with aliases per parser.
- Keep parser-output aliases, report labels, and criteria names in one declarative place.
- Add tests that prove each criteria row is either evaluated or reported as unsupported.

### 4. Parser discovery is convention-driven and brittle

Severity: high

Runtime parsers are loaded dynamically from `speccheck/modules` using filename/class-name conventions in `speccheck/util.py:44`. Plot modules use a parallel dynamic convention in `speccheck/report.py:51`. Most parsers declare broad filename matches such as `.tsv` and then rely on exact header equality: CheckM in `speccheck/modules/checkm.py:40`, Speciator in `speccheck/modules/speciator.py:40`, Sylph in `speccheck/modules/sylph.py:43`, and ARIBA in `speccheck/modules/ariba.py:26`.

Consequence: valid upstream files with extra columns or harmless header ordering changes may be rejected, while ambiguous `.tsv` files must be resolved by full header matching. The duplicate-parser guard in `speccheck/collect.py:20` is good, but the parser contract itself remains implicit.

Recommended fix:

- Replace dynamic discovery with an explicit parser registry.
- Use parser schemas that define required columns, optional columns, version compatibility, cardinality, canonical metric names, and display names.
- Treat extra columns as allowed unless the upstream format truly requires exact equality.

### 5. The data model is stringly typed and spread across CSV columns

Severity: high

Core functions pass dictionaries and pandas frames with keys like `Quast.N50.check`, `Checkm.Completeness`, and `all_checks_passed`. CSV writing relies on hard-coded concise column names in `speccheck/collect.py:180`, report composition builds frames directly from dictionaries in `speccheck/report.py:112`, and status interpretation is repeated around normalized strings in `speccheck/report_tables.py:10`.

Consequence: adding a parser, changing a metric name, or adding a verdict state requires editing multiple string lists. This increases regression risk and makes scientific provenance hard to reason about.

Recommended fix:

- Add dataclasses or Pydantic models for `ParsedMetric`, `Criterion`, `CriterionResult`, `SampleReport`, and `SummaryReport`.
- Keep CSV/HTML column names as serializers, not the internal data model.
- Add a schema version to report outputs.

## Architecture Overview

Current runtime shape:

```text
CLI (speccheck/cli.py)
  |
  +-- collect command
  |     |
  |     +-- main.collect (speccheck/main.py)
  |           |
  |           +-- discover files (speccheck/util.py)
  |           +-- dynamic parser loading (speccheck/util.py)
  |           +-- parser modules (speccheck/modules/*.py)
  |           +-- criteria loading/checking (speccheck/criteria.py, speccheck/collect.py)
  |           +-- concise + detailed CSV output (speccheck/collect.py)
  |
  +-- summary command
  |     |
  |     +-- main.summary (speccheck/main.py)
  |           |
  |           +-- merge collected CSV files
  |           +-- write report.csv
  |           +-- report context (speccheck/report.py)
  |           +-- plot modules (speccheck/plot_modules/*.py)
  |           +-- HTML/XLSX tables (speccheck/report_tables.py)
  |           +-- template render (speccheck/templates/report.html)
  |
  +-- check command
        |
        +-- validate/update criteria (speccheck/main.py, speccheck/update_criteria.py)
```

Recommended target shape:

```text
CLI
  |
  +-- workflows/
  |     +-- collect_workflow.py
  |     +-- summary_workflow.py
  |     +-- criteria_workflow.py
  |
  +-- core/
  |     +-- models.py
  |     +-- parser_registry.py
  |     +-- criteria_engine.py
  |     +-- metric_aliases.py
  |     +-- provenance.py
  |
  +-- parsers/
  |     +-- checkm2.py
  |     +-- quast.py
  |     +-- speciator.py
  |     +-- sylph.py
  |
  +-- reports/
        +-- html.py
        +-- csv.py
        +-- xlsx.py
        +-- multiqc.py
```

## Area Review

### Python Code Quality

Strengths:

- CLI entrypoints are now centralized in `speccheck/cli.py`.
- Build metadata is canonical in `pyproject.toml`.
- CSV writing uses `csv.DictWriter` in `speccheck/collect.py:280`.
- Summary merging rejects duplicate sample identifiers in `speccheck/main.py:271`.
- QUAST parsing is now key-based instead of positional in `speccheck/modules/quast.py:63`.

Risks:

- `speccheck/main.py` still mixes validation, workflow orchestration, dataframe merging, plotting calls, and criteria update logic.
- `speccheck/collect.py` mixes parser dispatch, criteria evaluation, report shaping, CSV serialization, and Sylph accession cleanup.
- Exceptions are inconsistent: some paths raise `ValueError`, while others log and `return`, for example missing criteria file handling in `speccheck/main.py:35`.
- Numeric conversion is ad hoc; negative numbers and scientific notation are only partly handled in `speccheck/criteria.py:158` and `speccheck/modules/quast.py:71`.

### Bioinformatics Engineering

Strengths:

- The tool covers a useful bioinformatics niche: species-specific QC report consolidation across QUAST, CheckM2-style QC tables, Speciator, Sylph, ARIBA, and coverage/depth.
- QualiBact ingestion from the public thresholds endpoint is implemented in `speccheck/update_criteria.py:9`.
- Pinned E. coli v1 QualiBact compatibility is implemented through `summary --qualibact-compat`.
- The real E. coli demonstration flow now records pinned QualiBact tier metadata alongside a GHRU-backed report path and regenerates compatibility-tier report columns from merged report data.

Risks:

- Upstream tool versions are not captured in report provenance, except optional static descriptions in plot modules.
- The remaining real-panel scale-up work should stay on the GHRU-backed read pipeline so that demonstration and validation artifacts continue to reflect real upstream outputs rather than synthetic parser inputs.
- There is no Nextflow/Snakemake/nf-core style workflow that pins CheckM2, QUAST, Sylph, Speciator, and databases.
- There is no formal distinction between "raw upstream output", "derived parser input", and "metadata imported from QualiBact".

### Algorithmic and Scientific Robustness

Strengths:

- Criteria validation checks headers, supported software names, operators, regexes, and numeric values in `speccheck/criteria.py:17`.
- Species fallback is now strict by default in `speccheck/main.py:94`.
- Duplicate parser matches are rejected in `speccheck/collect.py:20`.

Risks:

- Generic criteria pass/fail remains binary, while `--qualibact-compat` models E. coli v1 WARN as a first-class report tier.
- Multiple thresholds for the same biological concept can be duplicated across QUAST and CheckM without a clear aggregation policy.
- Missing fields are silently skipped by `_result_has_field` in `speccheck/main.py:158`; this avoids crashes but can make incomplete analyses look cleaner than they are.
- The criteria validator does not prove that each criterion is executable by at least one current parser.

### CLI and UX

Strengths:

- Typer gives discoverable commands and help text in `speccheck/cli.py:30`.
- `summary` supports HTML, CSV, XLSX, interactive-table toggles, and qualifyr-style layout options in `speccheck/cli.py:119`.

Risks:

- User-facing errors can still appear as Python tracebacks for uncaught `ValueError`.
- `collect` requires users to know which upstream files belong to one sample.
- There is no `--json`, `--fail-on-warn`, `--schema-version`, `--provenance`, or `--explain` output.
- The command name `check` validates criteria, while `collect` actually evaluates sample checks; this can be confusing.

### Reporting and UX

Strengths:

- Generated reports embed CSS and no longer require a loose Bulma file.
- Tables support static single-file output and optional client-side sorting/filtering.
- Compact summary tables and qualifyr-style sample review are implemented in `speccheck/report_tables.py:261` and `speccheck/report_tables.py:293`.

Risks:

- Plot modules directly concatenate HTML strings, for example `speccheck/plot_modules/plot_quast.py:82`.
- Table escaping is handled in shared helpers, but not all plot-module HTML paths escape every cell.
- Plot failures for missing optional columns should degrade into visible report warnings rather than exceptions.

### Tests

Strengths:

- The suite includes parser tests, report tests, criteria import tests, summary tests, and an end-to-end collect-to-summary regression.
- Recent local verification reported 48 passing tests in Python 3.11.
- CI runs Python 3.10, 3.11, and 3.12 across Linux, with 3.11 smoke on macOS and Windows in `.github/workflows/tests.yml:29`.

Risks:

- There are no property-based tests for parser schemas or criteria evaluation.
- There are no large-cohort performance tests.
- There are no CLI runner tests proving clean non-traceback errors.
- The real upstream analysis path depends on site-local tools and is not CI-executable.
- Tests now prove pinned E. coli v1 PASS/WARN/FAIL compatibility. Broader species parity tests are still missing.

### Packaging and Bioconda Readiness

Strengths:

- `pyproject.toml` is canonical and uses Hatchling in `pyproject.toml:1`.
- `setup.py` is a compatibility shim in `setup.py:1`.
- Package data includes templates, CSS, and default criteria in `pyproject.toml:64`.
- The wheel build and install smoke test are present in `.github/workflows/tests.yml:78`.

Risks:

- The repo still tracks legacy root-level assets: `speccheck.py`, `criteria.csv`, `templates/`, `output/report.csv`, `collect.sh`, `bump_version.py`, and `MANIFEST.in`. These are not necessarily packaged, but they weaken source clarity.
- The license field uses `license = {text = "GPLv3"}` in `pyproject.toml:16`; prefer an SPDX expression such as `GPL-3.0-only` or `GPL-3.0-or-later` depending on intent.
- Dependency upper bounds are mostly absent, which is normal for libraries but can hurt reproducible CLI deployments.
- There is no Bioconda recipe stub or documented external-tool dependency strategy.

### CI and GitHub Health

Strengths:

- Public GitHub showed 0 open issues and 0 open PRs during this review.
- GitHub Actions workflows exist for docs, Docker PR checks, PyPI publish, release, and tests.
- The tests workflow has distinct lint, test, docs, build, integration, and security jobs.

Risks:

- `gh` was not installed locally, so live check conclusions could not be inspected from the shell.
- The public Actions HTML listed recent runs but did not expose reliable pass/fail status in text.
- The release workflow commits directly to `main` and tags from CI in `.github/workflows/release.yml:97`; that can conflict with branch protection and is less clean than release-from-tag.
- The PyPI workflow requests OIDC permission but still passes an API token in `.github/workflows/publish.yml:49`.
- Security scanning uses deprecated `safety check` in `.github/workflows/tests.yml:140`; migrate to the current Safety command or another maintained scanner.

### Documentation and Manuscript Readiness

Strengths:

- MkDocs Material is configured in `mkdocs.yml:1`.
- Docs pages cover installation, CLI, criteria, reports, QualiBact, manuscript assets, methods, code quality, and development.
- Example HTML/CSV/XLSX reports exist under `examples/qualibact_ecoli/`.

Risks:

- The public documentation should keep distinguishing generic binary criteria checks from pinned E. coli v1 QualiBact compatibility mode.
- The docs need an architecture page and parser-author guide.
- The manuscript assets should include static PNG/SVG screenshots generated from reports, not only HTML files.
- There should be a methods appendix that describes exactly which upstream metrics are raw, transformed, or imported.

### Security and Reproducibility

Strengths:

- Downloads generally use subprocess lists, not shell strings.
- QualiBact threshold downloads use a request timeout in `speccheck/update_criteria.py:52`.

Risks:

- The current GHRU-backed staging scripts still depend on network-fetched public inputs and should keep explicit provenance for any downloaded read selection metadata.
- External bioinformatics tools and databases are not version-pinned in an executable environment file.
- Reports do not yet include complete command, version, reference database, threshold source, and input checksum provenance.

## Comparison With Similar Tooling

- MultiQC: stronger plugin ecosystem, mature report rendering, broad parser support. `speccheck` can complement it by focusing on species-specific verdicts and criteria traceability, but should consider exporting MultiQC-compatible data.
- QUAST and CheckM2: upstream metric producers. `speccheck` should never obscure their versions or raw outputs; it should treat them as provenance-bearing inputs. CheckM1 marker-lineage output is not part of the QualiBact-derived criteria path.
- QualiBact: threshold source and scientific comparator. `speccheck` now implements a pinned E. coli v1 compatibility mode and still presents QualiBact external thresholds as one source of generic binary criteria.
- nf-core pipelines: stronger reproducibility conventions. `speccheck` would benefit from a minimal Nextflow/Snakemake wrapper and a pinned environment.
- Bioconda packages: expect clean source layout, clear license, no generated artifacts, installable console script, and reproducible tests without network.

## Scorecard

Scores are readiness estimates for manuscript/open-source release, not a judgement of scientific usefulness.

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

## Top 20 Improvements

1. Keep the QualiBact relationship explicit: generic criteria-derived validation versus pinned E. coli v1 tier compatibility.
2. Extend `qualibact_compat` beyond the pinned E. coli v1 manuscript panel only when source URLs and parity fixtures are pinned.
3. Move the current `assembly_type` CLI string into a typed sample/report provenance model.
4. Move parser metric aliases into a canonical registry.
5. Replace dynamic parser discovery with an explicit parser registry.
6. Add typed dataclasses/Pydantic models for parsed metrics, criteria, checks, reports, and provenance.
7. Decide when manuscript and CI workflows should enable the new `--fail-on-not-evaluated` strict mode.
8. Split `speccheck/main.py` into collect, summary, and criteria workflow modules.
9. Split `speccheck/collect.py` into parser dispatch, criteria engine, and CSV serializers.
10. Remove or deprecate tracked legacy root assets: `speccheck.py`, root `templates/`, root `criteria.csv`, and `output/report.csv`.
11. Add CLI runner tests for all commands and common failure paths.
12. Add parser schema tests with extra columns, reordered columns, malformed values, and empty files.
13. Add broader QualiBact parity tests for additional species and known disagreement cases.
14. Extend provenance fields beyond the current speccheck version, assembly type, `NOT_EVALUATED` policy/count, criteria path/hash, and input count to include upstream tool versions, input checksums, and command line.
15. Add static manuscript screenshots generated from example reports.
16. Add a Nextflow or Snakemake demo workflow plus a Slurm profile/script for upstream analyses.
17. Add MultiQC-compatible export or a MultiQC module.
18. Modernize release/PyPI workflows: release from tag and use either OIDC trusted publishing or token publishing, not both.
19. Replace deprecated `safety check` with maintained dependency scanning.
20. Add a Bioconda-readiness checklist and recipe draft.

## Suggested Next Implementation Pass

Phase 1: criteria engine and explicit evaluation status.

- Move current CheckM2 aliases into a canonical metric registry.
- Decide when to enable current `--fail-on-not-evaluated` behavior in manuscript examples and CI.
- Extend QualiBact compatibility tests beyond the pinned E. coli manuscript panel when needed.

Phase 2: parser registry and typed model.

- Introduce parser registry metadata.
- Convert parser outputs into canonical metric objects.
- Keep current CSV output stable through serializers.

Phase 3: reproducible manuscript demo.

- Pin any external staging helpers and downloaded selection metadata by explicit version or snapshot.
- Add a workflow that runs QUAST, CheckM2, Sylph, and Speciator where available.
- Generate static report screenshots and figure panels.

Phase 4: release hygiene.

- Remove legacy root assets or mark them deprecated.
- Add Bioconda recipe draft.
- Modernize release/security workflows.
- Run clean wheel/sdist install tests from a fresh checkout.
