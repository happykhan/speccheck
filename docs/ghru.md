# Pipeline Integration

`speccheck` is most useful when it is the final reporting step of a workflow.
The upstream pipeline should run QC tools, publish stable per-sample outputs,
and then hand those outputs to `speccheck` for threshold evaluation and cohort
reporting.

The current built-in pipeline layout is `ghru`, based on GHRU Assembly. That is
a worked Nextflow example, not a special rule that limits `speccheck` to GHRU.

## Recommended pattern

For a Nextflow or similar workflow, keep these responsibilities separate:

1. The workflow runs upstream tools such as QUAST, CheckM2, Speciator, Sylph,
   ARIBA, Fastp, BUSCO, or depth calculation.
2. The workflow publishes stable output files with predictable names.
3. `speccheck` collects those files into one CSV per sample.
4. `speccheck summary` builds the final report for the cohort.

This gives a cleaner audit trail than burying all QC logic inside a workflow:
the workflow commit, `speccheck` commit, criteria checksum, and exact commands
can be recorded independently.

## Generic pipeline command

Use `collect-pipeline` for published workflow layouts:

```bash
speccheck collect-pipeline path/to/pipeline/output qc_collect \
  --layout ghru \
  --organism "Escherichia coli" \
  --metadata metadata.csv \
  --work-dir path/to/nextflow/work \
  --fail-on-not-evaluated
```

Then render the final report:

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --qualibact-compat \
  --xlsx-output qc_report/report.xlsx
```

`collect-pipeline --layout ghru` describes the role directly: `speccheck` is
collecting a known workflow output layout.

## GHRU Assembly as the worked Nextflow example

GHRU Assembly routes short-read, long-read, and hybrid inputs through separate
Nextflow workflows. The short-read workflow runs upstream QC and assembly
modules including trimming/FastQC, Shovill, QUAST, Speciator, CheckM2, assembly
depth, and Sylph. Its published TSV outputs provide the metrics that
`speccheck` needs.

The `ghru` layout collector currently searches for:

| Published directory | Example file | Parser |
| --- | --- | --- |
| `quast_summary/` | `ori_SAMPLE.short.report.tsv` | `Quast` |
| `checkm_summary/` | `SAMPLE.short.tsv` | `Checkm` |
| `speciation_summary/` | `SAMPLE.short.tsv` | `Speciator` |
| `sylph_summary/` | `SAMPLE_slyph_report.tsv` | `Sylph` |
| `ariba_summary/` | `SAMPLE_mlst_report.details.tsv` | `Ariba` |
| Nextflow `work/` when supplied | `SAMPLE.shortshort_reads.depth.tsv` | `Depth` |

The `--work-dir` option exists because some depth summaries may be produced in
Nextflow work directories without being published into the final results tree.
Use it only for recovery and provenance; do not commit a Nextflow work directory.

## Suggested output contract for new pipelines

If you are adding `speccheck` to a new workflow, publish a small, stable QC
contract rather than asking users to search the whole work directory:

```text
results/
  quast_summary/ori_SAMPLE.short.report.tsv
  checkm_summary/SAMPLE.short.tsv
  speciation_summary/SAMPLE.short.tsv
  sylph_summary/SAMPLE_slyph_report.tsv
  ariba_summary/SAMPLE_mlst_report.details.tsv
  fastp_summary/SAMPLE.fastp.json
  busco_summary/short_summary.SAMPLE.txt
speccheck/
  collect/
  report/
    report.csv
    report.html
    report.xlsx
```

The exact directory names can differ, but the principle should not: files used
for final QC should be deliberately published, versioned by the workflow, and
documented.

## What to record for a manuscript or release

For a publication-quality run, record:

- sample accessions and selection rules;
- upstream workflow repository, commit, and local patches;
- upstream tool, container, and database versions;
- `speccheck` version and Git commit;
- criteria CSV source and SHA256 checksum;
- exact `collect-pipeline` and `summary` commands;
- runtime and resource use;
- which files were intentionally excluded from version control.

The 100-sample *E. coli* case study follows this pattern in
`examples/qualibact_ecoli/real_run_100/`: compact reports, accessions,
analysis tables, figures, and provenance are committed; raw reads, assemblies,
databases, and workflow work files are not.

## Current limitation

Only the `ghru` published layout has a built-in pipeline collector today. Other
workflows can still use `speccheck collect` directly, or add a new layout
collector once their published output contract is stable.
