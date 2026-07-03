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

## QualiBact import

QualiBact thresholds are not consumed directly at runtime. They are converted into this internal CSV format so the rest of the validation engine remains stable.
