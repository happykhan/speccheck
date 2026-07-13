# GHRU Assembly Integration

`speccheck` can be used after `GHRU-assembly` in two ways:

- as a downstream command that collects canonical GHRU outputs with
  `speccheck collect-ghru`;
- as an optional GHRU pipeline module when the workflow is configured to run
  `speccheck` itself.

The publication case study uses the first route so the manuscript can cite the
exact local `speccheck` version, criteria checksum, and downstream commands.

## Downstream Collection

After a GHRU run has completed, collect per-sample CSVs directly from the output
tree:

```bash
speccheck collect-ghru \
  path/to/ghru/output \
  qc_collect \
  --organism "Escherichia coli" \
  --metadata metadata.csv \
  --work-dir path/to/nextflow/work \
  --fail-on-not-evaluated
```

Then merge and render the report:

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --qualifyr-style \
  --qualibact-compat \
  --xlsx-output qc_report/report.xlsx
```

`collect-ghru` searches for the GHRU outputs that `speccheck` currently knows
how to parse: QUAST, CheckM2, Speciator, Sylph, ARIBA, and depth summaries. The
`--work-dir` option lets it recover depth files that were produced by Nextflow
but not published into the final output tree.

## Recommended Output Layout

For publication or routine review, keep the raw pipeline outputs separate from
the compact downstream report:

```text
ghru_run/
  output/                 # GHRU-published outputs
  work/                   # Nextflow work directory, not committed
speccheck_case_study/
  collect/                # per-sample speccheck CSVs
  report/
    report.csv
    report.full.csv
    report.html
    report.xlsx
```

Raw reads, assemblies, databases, and Nextflow work files should not be committed
to the `speccheck` repository. Commit the compact report, accession table,
analysis tables, figures, and provenance.

## Provenance to Record

For a manuscript or release validation run, record:

- sample accessions and selection rules;
- GHRU commit and any local workflow patch;
- upstream container, tool, and database versions;
- `speccheck` version and Git commit;
- criteria snapshot source and SHA256 checksum;
- exact `collect-ghru` and `summary` commands;
- runtime and resource use where available.

The 100-sample case study stores this material in
`examples/qualibact_ecoli/real_run_100/analysis/summary.json`.

## Current Limitation

The upstream GHRU workflow is a separate repository. Changes to how it publishes
or labels `speccheck` outputs should be made and reviewed in that repository.
This repository keeps the downstream collector and the publication assets needed
to show that the integration works.
