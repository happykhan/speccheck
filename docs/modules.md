# Supported Modules

Speccheck recognises upstream outputs through parser modules. A parser does not
run the upstream tool; it reads the files the tool already produced and returns a
stable set of metric names.

The criteria CSV then decides which metrics are checked and what threshold is
used. This separation is deliberate:

- parser support means Speccheck can read the file;
- criteria support means a metric is actively evaluated;
- plotting support means the HTML report can show a richer diagnostic section.

## Built-in parsers

| Parser | Upstream software | Input recognised | Typical checks |
| --- | --- | --- | --- |
| `Ariba` | [ARIBA](https://github.com/sanger-pathogens/ariba) | ARIBA TSV summaries | MLST or contamination summary values |
| `Busco` | [BUSCO](https://busco.ezlab.org/) | `short_summary*.txt` | Complete and missing orthologues |
| `Checkm` | [CheckM2](https://github.com/chklovski/CheckM2) / CheckM-style TSVs | quality-report TSV | Completeness, contamination, genome size, N50, contigs |
| `Depth` | Workflow depth table | GHRU-style depth TSV | Short-, long-, or hybrid-read depth |
| `Fastp` | [fastp](https://github.com/OpenGene/fastp) | fastp JSON report | Q30 and filtering metrics |
| `Quast` | [QUAST](http://quast.sourceforge.net/) | transposed `report.tsv` | Assembly length, contigs, N50, GC, Ns |
| `Speciator` | [Speciator](https://github.com/cgps-discovery/speciator) | Speciator TSV | Species assignment and confidence |
| `Sylph` | [Sylph](https://github.com/bluenote-1577/sylph) | Sylph profile TSV | Top species, abundance, ANI, number of genomes |

Inspect your installed parser surface:

```bash
speccheck modules
```

Preview what will be recognised in a directory:

```bash
speccheck inspect path/to/qc_outputs/
```

!!! tip "Use inspect before collect"

    `inspect` is read-only. It is the fastest way to debug “why did this file
    not appear in my report?” without creating output files.

## How parser output becomes QC status

For a sample with QUAST, CheckM2, Speciator, Sylph, and depth files:

```bash
speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --output-file qc_collect/SAMPLE_001.csv
```

Speccheck does this:

1. Detects which parser can read each file.
2. Prefixes emitted metrics with the parser name, for example `Quast.N50`.
3. Selects criteria rows matching the species and assembly type.
4. Adds status/check columns and provenance columns.
5. Writes one compact CSV for the sample.

The summary step then merges those compact CSVs:

```bash
speccheck summary qc_collect --output qc_report --plot
```

## Criteria rows connect parsers to thresholds

Criteria rows use the parser name and metric name:

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
all,short,Fastp,after_filtering_q30_rate,>=,0.70,fail,bactscout-global,
all,all,Busco,Complete,>=,95,fail,speccheck-default,
Escherichia coli,short,Checkm,Contamination,<=,5,fail,qualibact-v1.0,
```

This means a parser can exist before a species-specific public threshold exists.
For example, Fastp and BUSCO have global Speccheck policy rows; they are not
QualiBact species-specific assembly thresholds.

## Plotting modules

HTML plots are optional. If a parser has no plotting module, Speccheck can still:

- detect the file;
- parse metrics;
- apply criteria;
- write CSV/XLSX outputs.

Plot modules currently exist for ARIBA, CheckM, QUAST, Speciator, and Sylph.

To add support for new software, see [Adding a Module](extending.md).
