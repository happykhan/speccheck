# Criteria Format

The runtime criteria format is a CSV with these headers:

```csv
species,assembly_type,software,field,operator,value,special_field
```

## Column meanings

- `species`: species name or `all`
- `assembly_type`: `all`, `short`, or `long`
- `software`: module name such as `Checkm`, `Quast`, `Speciator`, `Sylph`
- `field`: metric field to evaluate
- `operator`: `>`, `<`, `>=`, `<=`, `=`, or `regex`
- `value`: threshold value or regex pattern
- `special_field`: currently used for `species_field`

## Notes

- Regex-based rows are used for species-identification checks.
- Numeric rows are used for threshold comparisons.
- Default packaged criteria live at `speccheck/config/criteria.csv`.

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
