# Supported Modules and Extensions

`speccheck` recognises upstream QC files through small parser classes. The
current built-in modules are:

| Module | Input | Main purpose |
| --- | --- | --- |
| `Ariba` | ARIBA TSV summaries | MLST/contamination checks |
| `Busco` | `short_summary*.txt` | Orthologue completeness and missingness |
| `Checkm` | CheckM2 quality-report TSV | Completeness, contamination, and assembly metrics |
| `Depth` | GHRU depth TSV | Short-, long-, or hybrid-read depth |
| `Fastp` | fastp JSON report | Short-read Q30 and filtering metrics |
| `Quast` | transposed QUAST `report.tsv` | Assembly size, contigs, N50, GC, and Ns |
| `Speciator` | Speciator TSV | Species assignment and confidence |
| `Sylph` | Sylph profile TSV | Species abundance and ANI profile |

You can inspect a local installation without reading source code:

```bash
speccheck modules
speccheck inspect sample_qc_directory/
```

`modules` lists the parser surface that is installed. `inspect` tests files
without writing outputs, which is useful when wiring a new pipeline into
`speccheck`.

## Adding a Built-in Module

A parser should do only three things:

- decide whether a filename could belong to it;
- decide whether the file content really matches it;
- return a dictionary of normalized metric names and values.

For simple single-row TSV outputs, subclass `SingleRowTsvParser` instead of
reimplementing delimiter handling:

```python
from speccheck.modules.base import SingleRowTsvParser


class MyTool(SingleRowTsvParser):
    software_name = "MyTool"
    description = "Short description shown by speccheck modules"
    supported_filenames = "TSV with sample, score, and status columns"
    required_headers = ("sample", "score", "status")
    exact_headers = False
```

For JSON, text summaries, or multi-row formats, subclass `Parser` directly:

```python
from speccheck.modules.base import Parser


class MyTool(Parser):
    software_name = "MyTool"
    description = "Short description shown by speccheck modules"
    supported_filenames = "mytool*.json"

    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".json")

    @property
    def has_valid_fileformat(self):
        return True

    def fetch_values(self):
        return {"metric": 1.0}
```

Then add the class to `PARSER_CLASSES` in `speccheck/registry.py` and add focused
tests covering detection, rejection of similar non-matching files, and parsed
metric values.

## Third-party Parser Plugins

External packages can register parser classes through the
`speccheck.parsers` entry-point group. The entry point must load a subclass of
`speccheck.modules.base.Parser` and its `software_name` must not duplicate an
installed parser:

```toml
[project.entry-points."speccheck.parsers"]
MyTool = "my_package.speccheck_parsers:MyTool"
```

This keeps local pipeline-specific parsers out of the core repository while
still making them visible to `speccheck modules`, `speccheck inspect`, criteria
validation, and collection.

## Criteria for New Modules

Criteria rows use the parser `software_name` and the metric keys returned by
`fetch_values`:

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
all,all,MyTool,metric,>=,0.95,fail,my-project,
```

Use `severity=fail` for thresholds that fail a sample and `severity=warn` for
review thresholds. Keep parser output names stable once published because those
names become part of reports and manuscript provenance.
