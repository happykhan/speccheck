# Criteria Format

The runtime criteria format is a CSV with these headers:

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
```

## Column meanings

- `species`: species name or `all`
- `assembly_type`: `all`, `short`, `long`, or `hybrid`
- `software`: module name such as `Checkm`, `Quast`, `Speciator`, `Sylph`
- `field`: metric field to evaluate
- `operator`: `>`, `<`, `>=`, `<=`, `=`, or `regex`
- `value`: threshold value or regex pattern
- `severity`: `fail` or `warn`; omitted legacy rows are treated as `fail`
- `source`: provenance label such as `qualibact-v1.0`, `speccheck-default`, or `custom`
- `special_field`: currently used for `species_field`

## Threshold model

`speccheck` evaluates criteria in layers:

1. Species-specific rows are used when they exist for the resolved organism,
   software, and field.
2. Generic `species=all` rows are used when no species-specific row exists for
   that metric.
3. Project criteria files can add rows for tools or metrics that are outside
   QualiBact.

This is why the criteria table contains both QualiBact-derived assembly metrics
and global Speccheck policies such as Fastp Q30 and BUSCO completeness.

## Notes

- Regex-based rows are used for species-identification checks.
- Numeric rows are used for threshold comparisons.
- Default packaged criteria live at `speccheck/config/criteria.csv`.
- Species-specific criteria override generic `species=all` rows for the same
  `software` and `field`.
- Generic rows still apply when no species-specific row exists for that metric.
- Tool support and threshold support are separate. A parser can exist before a
  public species-specific threshold exists for that parser.

## Species resolution

If `--organism` is not supplied, `speccheck` attempts to infer the species from rows marked with `special_field=species_field`.

Collection now fails if no single organism can be resolved. This avoids applying broad fallback thresholds by accident. For legacy or exploratory runs, pass `--allow-unknown-organism` to use the packaged `Unknown` fallback criteria explicitly.

## Assembly type filtering

Collection applies criteria rows according to `speccheck collect --assembly-type`:

- `short`: evaluates `all` and `short` rows
- `long`: evaluates `all` and `long` rows
- `hybrid`: evaluates `all`, `short`, and `long` rows
- `all`: evaluates only rows marked `all`

The default is `short` to preserve the historical packaged-criteria behavior. The selected mode is written to collected CSV outputs as `speccheck_assembly_type`.

Depth criteria use `DepthParser.short` and `DepthParser.long` in the criteria table. These rows are applied to parsed `Depth` outputs according to the row `Read_type`, so a short-read depth file is not evaluated against long-read depth thresholds.

## Missing metrics

If a parser is detected but an applicable criteria row references a field that is not present in that parser output, the collected CSV reports the corresponding `*.check` column as `NOT_EVALUATED`. The row also includes `speccheck_not_evaluated_count` so missing expected metrics are visible during review.

`NOT_EVALUATED` means the metric was expected by the selected criteria but could not be checked from the available upstream output. It is not the same as a threshold failure. By default it is reported without changing `all_checks_passed`; use `speccheck collect --fail-on-not-evaluated` when incomplete evidence should fail the parser-level and sample-level checks.

## Provenance columns

Collected CSV outputs include basic speccheck provenance:

- `speccheck_version`
- `speccheck_assembly_type`
- `speccheck_fail_on_not_evaluated`
- `speccheck_criteria_file`
- `speccheck_criteria_sha256`
- `speccheck_input_file_count`
- `speccheck_not_evaluated_count`

## QualiBact import

QualiBact thresholds are not consumed directly at runtime. They are converted into this internal CSV format so the rest of the validation engine remains stable.

QualiBact assembly-quality thresholds used here are calibrated around CheckM2-style metrics. The `Checkm` parser name is retained for backward compatibility in column names, but the supported QualiBact criteria use CheckM2 fields such as `Completeness`, `Contamination`, `Genome_Size`, `GC_Content`, `Contig_N50`, `Total_Contigs`, and `Total_Coding_Sequences`. Legacy CheckM1 marker-lineage criteria are not generated or packaged for QualiBact-derived thresholds.

## Non-QualiBact global thresholds

Some supported tools do not have species-specific QualiBact metrics. These use
explicit global criteria rows:

- `Fastp.after_filtering_q30_rate`: BactScout-derived global short-read Q30
  policy, `FAIL` below 70% and `WARN` below 80%.
- `Busco.Complete` and `Busco.Missing`: Speccheck default orthologue
  completeness policy, not an official universal BUSCO species threshold.

These rows have `species=all` and remain active for every organism unless a
project-supplied species row overrides the same software and field.
