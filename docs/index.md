# speccheck

`speccheck` collects QC outputs from multiple bioinformatics tools, applies species-aware criteria, and produces merged CSV, HTML, and XLSX summaries.

It is designed for:

- routine genome QC review
- manuscript-ready reproducible reporting
- packaging-friendly installation through `pip`, Conda, and eventually Bioconda

## Core workflow

1. Run `speccheck collect` on a sample directory or file set.
2. Repeat for multiple samples.
3. Run `speccheck summary` on the collected CSV directory.
4. Review the merged `report.csv`, optional `report.xlsx`, and optional `report.html`.

## Highlights

- automatic module detection
- packaged default criteria and templates
- QualiBact-derived species thresholds with generic fallback rows
- global Fastp Q30 and BUSCO defaults for tools outside QualiBact
- interactive tables in HTML reports
- compact qualifyr-style summary tables
- manuscript-ready E. coli example reports and static figures

Start with the CLI page for routine use, the modules page for supported inputs
and parser extensions, and the manuscript pages for the 100-sample E. coli case
study.
