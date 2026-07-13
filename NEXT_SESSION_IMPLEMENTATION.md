# Publication-readiness implementation handoff

> Status update, 2026-07-13: the real 100-sample run and its compact manuscript
> assets are complete. The older "Immediate Next Steps" below are retained as
> historical context but are superseded by the current release checklist here.

## Current release checklist

1. Run full lint, formatting, tests with coverage, strict docs build, package and
   wheel smoke tests, Docker build, and generated-artifact consistency checks.
2. Reconcile the publication branch with the v1.2.6 version-only commit on
   `origin/main`, then prepare the next minor release metadata.
3. Push `agent/publication-readiness`, open a draft PR, allow CI to complete, and
   merge through the normal review path.
4. Create the archival GitHub/PyPI release and connect the resulting DOI when the
   repository's Zenodo integration is available.

Primary case-study assets now live under
`examples/qualibact_ecoli/real_run_100/`.

This document is the source of truth for the current implementation direction.

## Objective

Finish `speccheck` as a release-ready downstream QC/reporting tool by:

- consuming real upstream outputs from `GHRU-assembly`
- validating current `speccheck` behavior on those outputs
- using real upstream-derived E. coli runs to harden reports, CSVs, and edge-case handling

## Current State

- Repository root: `/well/aanensen/users/rva470/speccheck`
- `speccheck` test environment is now Pixi-first:
  - command: `pixi run pytest -q`
  - current result: `60 passed`
  - current coverage: `82%`
- The real 100-sample E. coli GHRU-backed cohort has completed end-to-end:
  - run root: `.demo_work/ghru_ecoli_cohort/run_100/`
  - upstream producer: `external/GHRU-assembly`
  - downstream consumer: `speccheck collect-ghru`
  - merged report output: `.demo_work/ghru_ecoli_cohort/run_100/report/`
- Fresh upstream GHRU clone added locally:
  - path: `/well/aanensen/users/rva470/speccheck/external/GHRU-assembly`
  - branch: `main`
  - commit: `271e0d9e5593a4e4a59409f12f83e816794ad6a3`
- Fresh-clone BMRC validation run has been completed once:
  - command: `scripts/submit_ghru_short_validation.sh`
  - run work area: `.demo_work/ghru_validation/`
  - completed short-lane jobs included: `23549376` through `23549405`
- Shared cluster copy was not modified:
  - path: `../../../shared/nextflow_workflows/GHRU-assembly`
  - branch: `bmrc`
  - commit seen earlier: `c75b77b`
  - it is behind upstream and has a local modification in `prepare.py`

## Hard Decisions Already Made

- `speccheck` should be the downstream consumer of `GHRU-assembly`, not a replacement for it.
- Do not update the shared GHRU checkout in place until a fresh upstream clone is validated locally on BMRC.
- Use the fresh clone in `external/GHRU-assembly` for validation work.
- Treat GHRU upstream outputs as the canonical interface:
  - `quast_summary`
  - `speciation_summary`
  - `checkm_summary`
  - `sylph_summary`
  - `ariba_summary`
  - depth output where present
- Do not rely on the in-pipeline GHRU `speccheck` step for manuscript or validation outputs.
- Keep `E. coli` as the main validation lane for both manuscript-scale and report-scale testing.

## speccheck State

The following work is already in place in this repo:

- baseline `species=all` sanity criteria
- species-layer criteria precedence support
- concise and full merged summary outputs:
  - `report.csv`
  - `report.full.csv`
  - `report.xlsx`
- large-run-oriented HTML report layout
- packaged criteria provenance artifacts:
  - `speccheck/config/qualibact_snapshot.csv`
  - `speccheck/config/qualibact_snapshot_metadata.csv`
- Pixi project added at:
  - [`pixi.toml`](pixi.toml:1)
- direct GHRU consumer path added:
  - CLI command: `collect-ghru`
  - purpose: collect per-sample `speccheck` CSVs directly from a GHRU output tree

## GHRU Integration State

The old generic template script was removed:

- removed: `scripts/upstream_qc_slurm_template.sh`

The new local validation path is:

- fresh upstream clone:
  - [`external/GHRU-assembly`](external/GHRU-assembly/README.md:1)
- local BMRC config overlay:
  - [`scripts/ghru_assembly_bmrc_local.config`](scripts/ghru_assembly_bmrc_local.config:1)
- asset/image staging script:
  - [`scripts/stage_ghru_validation_assets.sh`](scripts/stage_ghru_validation_assets.sh:1)
- short-read validation launcher:
  - [`scripts/submit_ghru_short_validation.sh`](scripts/submit_ghru_short_validation.sh:1)

### Important local patch in the fresh clone

The fresh upstream clone was patched locally to support:

- `params.run_speccheck = false`

This was necessary because:

- the fresh upstream workflow still hard-wires its own `speccheck` stage
- the cluster-local `.sif` inventory does not match the newest upstream `speccheck` image expectations
- for current validation we only want upstream outputs, then we run current repo `speccheck` ourselves

Patched files:

- [`external/GHRU-assembly/nextflow.config`](external/GHRU-assembly/nextflow.config:1)
- [`external/GHRU-assembly/workflows/sr_assembly.nf`](external/GHRU-assembly/workflows/sr_assembly.nf:1)
- [`external/GHRU-assembly/workflows/lr_assembly.nf`](external/GHRU-assembly/workflows/lr_assembly.nf:1)
- [`external/GHRU-assembly/workflows/hybrid_assembly.nf`](external/GHRU-assembly/workflows/hybrid_assembly.nf:1)

## Runtime Constraints

- Compute nodes do not have internet access.
- Apptainer cache and temp must stay inside workspace/local scratch, not `~/`.
- Shared local `.sif` images already exist under:
  - `../../../shared/singularity/GHRU-assembly/`

### Known validation constraint

Fresh upstream GHRU uses `checkm2 predict` for contamination.

The shared cluster image stash under `../../../shared/singularity/GHRU-assembly/` does not currently include a `checkm2` `.sif`, so the BMRC overlay must stage a local `checkm2` image into:

- `.demo_work/ghru_images/checkm2_0.1.0.sif`

That local image should be pulled on the login node by:

- [`scripts/stage_ghru_validation_assets.sh`](scripts/stage_ghru_validation_assets.sh:1)

The BMRC overlay now expects:

- [`scripts/ghru_assembly_bmrc_local.config`](scripts/ghru_assembly_bmrc_local.config:1)

## Immediate Next Steps

These are the remaining implementation tasks in order:

1. Inspect the completed 100-sample report and decide which artifacts should become committed examples/manuscript fixtures:
   - `.demo_work/ghru_ecoli_cohort/run_100/report/report.csv`
   - `.demo_work/ghru_ecoli_cohort/run_100/report/report.full.csv`
   - `.demo_work/ghru_ecoli_cohort/run_100/report/report.html`
   - `.demo_work/ghru_ecoli_cohort/run_100/report/report.xlsx`

2. Decide how the committed `examples/qualibact_ecoli/real_panel/` artifacts should be sourced:
   - either keep the older direct-assembly/QUAST demo path as a separate compatibility fixture
   - or replace it with the new GHRU-derived triplet outputs now living under `.demo_work/ghru_ecoli_panel/triplet/`

3. If the examples/manuscript lane should now follow GHRU, wire the committed example/manuscript asset generation scripts to consume:
   - `.demo_work/ghru_ecoli_panel/triplet/output/`
   - `.demo_work/ghru_ecoli_panel/triplet/metadata.csv`
   - `pixi run python -m speccheck.cli collect-ghru ...`
   - `pixi run python -m speccheck.cli summary ...`

4. Document the observed mismatch between metadata-pinned QualiBact tiers and current GHRU-derived compatibility outcomes:
   - native `speccheck` binary QC now passes for all three triplet samples
   - `qualibact_tier` metadata remains `PASS/WARN/FAIL`
   - `qualibact_compat_tier` computed from current GHRU assemblies is `PASS/PASS/PASS`

5. Do not reintroduce the older assembly-only builder path; the direct assembly/QUAST demo scripts have been removed and the remaining scale-up work should stay GHRU-backed.
6. Use the generic read-backed staging path for future cohorts:
   - `scripts/stage_ghru_ecoli_cohort.py`
   - `scripts/stage_ghru_ecoli_run_100.sh`
   - `scripts/submit_ghru_ecoli_run_100.sh`

## Real E. coli Plan

The E. coli manuscript/report dataset should now be built from real upstream GHRU outputs, not only from synthetic parser inputs.

The order should be:

1. validate fresh GHRU on bundled test data
2. fetch a minimal real E. coli short-read set
3. run that sample through fresh GHRU with the BMRC local config
4. consume those upstream outputs with current repo `speccheck`
5. inspect:
   - merged CSV behavior
   - HTML report look and feel
   - failure/warning summaries
   - parser/filename edge cases
6. then scale up toward the manuscript fixtures and the 100-sample run

### Completed single real-sample lane

A minimal real read-backed E. coli lane has been completed for:

- BioSample: `SAMN42765982`
- ENA run accession: `SRR29931410`
- run root: `.demo_work/ghru_ecoli_real/SAMN42765982/`
- status: complete

Stage command:

```bash
scripts/stage_ghru_ecoli_real_sample.sh SAMN42765982
```

Submit command:

```bash
scripts/submit_ghru_ecoli_real_sample.sh SAMN42765982
```

This stage step:

- resolves ENA FASTQ links on the login node
- downloads paired reads locally under `.demo_work/ghru_ecoli_real/SAMN42765982/reads/`
- writes `.demo_work/ghru_ecoli_real/SAMN42765982/samplesheet.csv`
- reuses the local `.demo_work/ghru_images/checkm2_0.1.0.sif`

Downstream commands used:

```bash
pixi run python -m speccheck.cli collect-ghru \
  .demo_work/ghru_ecoli_real/SAMN42765982/output \
  .demo_work/ghru_ecoli_real/SAMN42765982/collect \
  --organism "Escherichia coli" \
  --work-dir .demo_work/ghru_ecoli_real/SAMN42765982/work
```

```bash
pixi run python -m speccheck.cli summary \
  .demo_work/ghru_ecoli_real/SAMN42765982/collect \
  --output .demo_work/ghru_ecoli_real/SAMN42765982/report \
  --plot \
  --xlsx-output .demo_work/ghru_ecoli_real/SAMN42765982/report/report.xlsx \
  --qualifyr-style \
  --qualibact-compat \
  --no-interactive-tables
```

Observed result:

- the sample now passes native `speccheck` QC after `checkm2` GC normalization
- it remains a useful real FAIL-labeled QualiBact metadata point because the original selected row carried:
  - `no_of_contigs >670.0`
  - `Total_Coding_Sequences >5800.0`
  - `Genome_Size >5700000.0`

### Completed real GHRU triplet panel

The first real upstream-derived E. coli validation panel is now complete.

Panel members:

- `SAMN42766885` with expected metadata tier `PASS`
- `SAMN42764706` with expected metadata tier `WARN`
- `SAMN42765982` with expected metadata tier `FAIL`

Rejected candidate:

- `SAMD00006077` was excluded because ENA resolved it as `Shigella dysenteriae`, not `Escherichia coli`

Run root:

- `.demo_work/ghru_ecoli_panel/triplet/`

Stage command:

```bash
scripts/stage_ghru_ecoli_panel.sh triplet
```

Submit command:

```bash
scripts/submit_ghru_ecoli_panel.sh triplet
```

Artifacts:

- GHRU output tree:
  - `.demo_work/ghru_ecoli_panel/triplet/output/`
- metadata used for downstream comparison:
  - `.demo_work/ghru_ecoli_panel/triplet/metadata.csv`
- downstream collect output:
  - `.demo_work/ghru_ecoli_panel/triplet/collect/`
- downstream report output:
  - `.demo_work/ghru_ecoli_panel/triplet/report/`

Downstream commands used:

```bash
pixi run python -m speccheck.cli collect-ghru \
  .demo_work/ghru_ecoli_panel/triplet/output \
  .demo_work/ghru_ecoli_panel/triplet/collect \
  --organism "Escherichia coli" \
  --work-dir .demo_work/ghru_ecoli_panel/triplet/work \
  --metadata .demo_work/ghru_ecoli_panel/triplet/metadata.csv
```

```bash
pixi run python -m speccheck.cli summary \
  .demo_work/ghru_ecoli_panel/triplet/collect \
  --output .demo_work/ghru_ecoli_panel/triplet/report \
  --plot \
  --xlsx-output .demo_work/ghru_ecoli_panel/triplet/report/report.xlsx \
  --qualifyr-style \
  --qualibact-compat \
  --no-interactive-tables
```

Triplet outcome after the `checkm2` parser fix:

- `SAMN42766885`: native `all_checks_passed=PASSED`, metadata `qualibact_tier=PASS`, computed `qualibact_compat_tier=PASS`
- `SAMN42764706`: native `all_checks_passed=PASSED`, metadata `qualibact_tier=WARN`, computed `qualibact_compat_tier=PASS`
- `SAMN42765982`: native `all_checks_passed=PASSED`, metadata `qualibact_tier=FAIL`, computed `qualibact_compat_tier=PASS`

Interpretation:

- the earlier triplet-wide native failure was a real parser bug, not a biology result
- `checkm2` `GC_Content` from GHRU is emitted as a fraction such as `0.50` or `0.51`
- `speccheck` criteria expect percent units such as `50.0` or `51.0`
- `speccheck/modules/checkm.py` now normalizes `0 <= GC_Content <= 1` to percentage scale before evaluation
- after normalization, `Checkm.GC.check` passes for all three samples
- the remaining metadata-tier mismatch looks genuine: current GHRU assemblies for the WARN/FAIL-labeled samples no longer reproduce the older ATB thresholds that assigned those labels

### Generic GHRU-backed cohort staging path

The E. coli read-backed staging logic is now centralized in:

- [`scripts/stage_ghru_ecoli_cohort.py`](scripts/stage_ghru_ecoli_cohort.py:1)

Supported uses:

- pinned panel selection from committed metadata:
  - `scripts/stage_ghru_ecoli_panel.sh triplet`
- generic count-based cohort staging direct from QualiBact metadata and ENA:
  - `scripts/stage_ghru_ecoli_run_100.sh`

What the generic stage script does:

1. choose the E. coli sample set from QualiBact metadata
2. resolve each sample to ENA paired-end read runs
3. download the reads on a login node
4. write:
   - `samplesheet.csv`
   - `metadata.csv`
   - `selection/selected_qualibact_ecoli.csv`
   - `selection/speccheck_metadata.csv`
   - `ena_resolutions.csv`
5. hand those inputs to `external/GHRU-assembly`

Smoke validation completed for count-based mode:

```bash
pixi run python scripts/stage_ghru_ecoli_cohort.py \
  --run-root .demo_work/ghru_ecoli_cohort/counts_smoke \
  --pass-count 1 \
  --warn-count 1 \
  --fail-count 1 \
  --no-download-reads
```

This wrote:

- `.demo_work/ghru_ecoli_cohort/counts_smoke/samplesheet.csv`
- `.demo_work/ghru_ecoli_cohort/counts_smoke/metadata.csv`
- `.demo_work/ghru_ecoli_cohort/counts_smoke/selection/selected_qualibact_ecoli.csv`

### Completed real 100-sample GHRU-backed E. coli cohort

The full read-backed 100-sample E. coli cohort has now been generated through upstream GHRU and consumed by local `speccheck`.

Run root:

- `.demo_work/ghru_ecoli_cohort/run_100/`

Stage command:

```bash
scripts/stage_ghru_ecoli_run_100.sh run_100
```

GHRU submit command:

```bash
scripts/submit_ghru_ecoli_run_100.sh run_100
```

GHRU completion facts:

- pipeline version: `4.1.0`
- Nextflow version: `24.10.3`
- completed at: `2026-07-07T09:36:03.890245653+01:00`
- duration: `23m 40s`
- success: `true`
- exit code: `0`
- succeeded Slurm tasks: `900`
- all active short-read stages completed `100/100`

Inputs written by staging:

- `.demo_work/ghru_ecoli_cohort/run_100/samplesheet.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/metadata.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/ena_resolutions.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/selection/selected_qualibact_ecoli.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/selection/speccheck_metadata.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/reads/`

GHRU artifacts:

- output tree: `.demo_work/ghru_ecoli_cohort/run_100/output/`
- work tree: `.demo_work/ghru_ecoli_cohort/run_100/work/`
- trace: `.demo_work/ghru_ecoli_cohort/run_100/trace.tsv`
- Nextflow report: `.demo_work/ghru_ecoli_cohort/run_100/nextflow-report.html`

Downstream collect command:

```bash
pixi run python -m speccheck.cli collect-ghru \
  .demo_work/ghru_ecoli_cohort/run_100/output \
  .demo_work/ghru_ecoli_cohort/run_100/collect \
  --organism "Escherichia coli" \
  --work-dir .demo_work/ghru_ecoli_cohort/run_100/work \
  --metadata .demo_work/ghru_ecoli_cohort/run_100/metadata.csv
```

Collect result:

- wrote 100 concise per-sample CSVs
- wrote 100 detailed per-sample CSVs
- output directory: `.demo_work/ghru_ecoli_cohort/run_100/collect/`

Downstream summary command:

```bash
pixi run python -m speccheck.cli summary \
  .demo_work/ghru_ecoli_cohort/run_100/collect \
  --output .demo_work/ghru_ecoli_cohort/run_100/report \
  --plot \
  --xlsx-output .demo_work/ghru_ecoli_cohort/run_100/report/report.xlsx \
  --qualifyr-style \
  --qualibact-compat \
  --no-interactive-tables
```

Summary result:

- `.demo_work/ghru_ecoli_cohort/run_100/report/report.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/report/report.full.csv`
- `.demo_work/ghru_ecoli_cohort/run_100/report/report.html`
- `.demo_work/ghru_ecoli_cohort/run_100/report/report.xlsx`
- `report.csv` rows: `100`
- `report.full.csv` rows: `100`
- computed `overall_qc`: `90 PASS`, `6 WARN`, `4 FAIL`
- `all_checks_passed`: `91 PASSED`, `9 FAILED`
- metadata `qualibact_tier`: `70 PASS`, `20 WARN`, `10 FAIL`
- computed `qualibact_compat_tier`: `90 PASS`, `6 WARN`, `4 FAIL`
- species calls: `93 Escherichia coli`, `3 Unidentified`, `2 Shigella flexneri`, `1 Shigella sonnei`, `1 Shigella dysenteriae`

Spot-check result:

- first sample: `SAMD00000699`
- `overall_qc=PASS`
- `all_checks_passed=PASSED`
- `qualibact_tier=PASS`
- `qualibact_compat_tier=PASS`
- `species=Escherichia coli`
- `species_confidence=good`
- `Checkm.GC_Content=51.0`
- `Checkm.GC.check=PASSED`

Post-run targeted validation:

```bash
pixi run pytest -q tests/test_ghru_collect.py tests/test_module_checkm.py tests/test_qualibact_compat.py
```

Result:

- `9 passed`

## What Not To Do

- Do not treat the shared GHRU checkout as the editable source of truth.
- Do not overwrite the shared checkout until the fresh clone is validated.
- Do not depend on compute-node internet access.
- Do not assume the upstream in-pipeline `speccheck` stage is the artifact we want to trust.
- Do not use `checkm1` as an accepted upstream contamination source.

## Deferred TODOs

- Add explicit `speccheck` detection for legacy `checkm1`-format inputs.
- If a user supplies `checkm1` output, emit a warning that `checkm1` is legacy/unsupported and keep `checkm2` as the required contamination path.
- Do not implement `checkm1` compatibility as a fallback parser unless there is a separate deliberate decision to support it.
- Decide whether `qualibact_compat_tier` should remain purely computed from current observed metrics, or whether report/example material also needs a clearer distinction between:
  - expected metadata tier from QualiBact selection
  - computed compatibility tier from current GHRU-derived assemblies

## Validation Commands

`speccheck`:

```bash
pixi run pytest -q
```

GHRU validation asset staging:

```bash
scripts/stage_ghru_validation_assets.sh
```

Fresh upstream short-read validation:

```bash
scripts/submit_ghru_short_validation.sh
```

## Latest Validation Result

The short-read validation lane now completes successfully with upstream `checkm2`.

Final successful run facts:

- resumed command: `scripts/submit_ghru_short_validation.sh`
- completed at: `2026-07-06 13:14:42+01:00`
- Slurm contamination task: `23549881`
- successful contamination output:
  - `.demo_work/ghru_validation/output/checkm_summary/test_sample_short.short.tsv`

Additional current validation result:

- the real GHRU E. coli triplet panel also completes successfully end-to-end
- downstream `collect-ghru` and `summary` both run successfully on that panel
- targeted tests for the `checkm2` normalization and GHRU collector path pass:
  - `pixi run pytest -q tests/test_module_checkm.py tests/test_ghru_collect.py tests/test_qualibact_compat.py`
- full test suite currently passes:
  - `pixi run pytest -q`
  - `60 passed`

The validated short-lane output set now includes:

- assembly output
- `quast_summary`
- `speciation_summary`
- `checkm_summary`
- `sylph_summary`
- trimmed reads and FastQC outputs

Notable `checkm2` result for the bundled test sample:

- completeness: `93.2`
- contamination: `0.09`

This means the fresh clone + local BMRC overlay is now good enough to use as the upstream producer for downstream `speccheck` integration work.

## Verified Downstream Consumption

The new direct GHRU intake path has been implemented and exercised on the validated short-read run.

Verified command to collect per-sample CSVs from GHRU output:

```bash
pixi run python -m speccheck.cli collect-ghru \
  .demo_work/ghru_validation/output \
  .demo_work/ghru_validation/collect \
  --organism "Mycoplasma genitalium" \
  --work-dir .demo_work/ghru_validation/work
```

This wrote:

- `.demo_work/ghru_validation/collect/test_sample_short.csv`
- `.demo_work/ghru_validation/collect/detailed.test_sample_short.csv`

Verified command to produce a downstream report from those collected CSVs:

```bash
pixi run python -m speccheck.cli summary \
  .demo_work/ghru_validation/collect \
  --output .demo_work/ghru_validation/report \
  --plot \
  --xlsx-output .demo_work/ghru_validation/report/report.xlsx \
  --qualifyr-style \
  --no-interactive-tables
```

This produced:

- `.demo_work/ghru_validation/report/report.csv`
- `.demo_work/ghru_validation/report/report.full.csv`
- `.demo_work/ghru_validation/report/report.html`
- `.demo_work/ghru_validation/report/report.xlsx`

Implementation note:

- `--work-dir` is currently useful because GHRU does not publish the depth TSV into `outdir`; `collect-ghru` searches the work directory only for unpublished depth files and uses the published `outdir` for the rest.
