# speccheck

`speccheck` turns outputs from bacterial genome QC tools and workflows into a
single reviewable report. It is intended to sit at the end of an analysis run:
upstream software produces metrics, `speccheck collect` evaluates those metrics
against explicit criteria, and `speccheck summary` produces CSV, HTML, and XLSX
outputs for review, archiving, or manuscript supplements.

## What it is for

- checking many QC outputs with one transparent criteria table;
- using species-specific thresholds where they exist and generic thresholds
  where they do not;
- producing compact reports from large workflow runs without committing raw
  reads, assemblies, databases, or Nextflow work directories;
- documenting exactly which thresholds, software version, and upstream files
  generated a result.

## Main ways to use it

### Single-sample or ad hoc QC

Point `speccheck collect` at the files for one sample, then merge collected CSVs
with `speccheck summary`.

```bash
speccheck collect path/to/sample_qc/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --output-file qc_collect/SAMPLE_001.csv

speccheck summary qc_collect --output qc_report --plot
```

### End-of-pipeline reporting

Use `speccheck` as the final reporting layer for a workflow such as a Nextflow
pipeline. The current built-in pipeline collector supports the published output
layout from GHRU Assembly:

```bash
speccheck collect-pipeline path/to/pipeline/output qc_collect \
  --layout ghru \
  --organism "Escherichia coli" \
  --work-dir path/to/nextflow/work
```

`collect-ghru` is kept as a compatibility alias for the same layout. The
preferred documentation name is now `collect-pipeline` because the concept is
generic: a pipeline publishes recognised QC files, then `speccheck` creates the
final sample-level and cohort-level report.

### Manuscript case study

The repository includes compact assets for a 100-sample *E. coli* case study
derived from real read-backed GHRU Assembly outputs. The committed data are the
accession table, metadata, summary statistics, figures, reports, and provenance,
not the raw reads or 78 GB working directory.

Start with [Quick Start](quickstart.md), then read [Pipeline Integration](ghru.md)
and [Manuscript Assets](manuscript.md) for the publication-facing material.
