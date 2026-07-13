# Adding a Module

Use this page when Speccheck needs to read a new upstream output file.

The clean path is:

1. Add a parser.
2. Register it.
3. Add criteria rows for metrics that should be checked.
4. Add focused tests.
5. Optionally add an HTML plot module.

## Worked example: a simple TSV parser

Suppose `mytool.tsv` looks like this:

```tsv
sample	score	status
SAMPLE_001	0.98	ok
```

For a single-row TSV, subclass `SingleRowTsvParser`:

```python
from speccheck.modules.base import SingleRowTsvParser


class MyTool(SingleRowTsvParser):
    software_name = "MyTool"
    description = "Example quality score from MyTool"
    supported_filenames = "mytool*.tsv"
    required_headers = ("sample", "score", "status")
    exact_headers = False
```

For a parser that lives in this repository, register it in
`speccheck/registry.py`:

```python
from speccheck.modules.mytool import MyTool

PARSER_CLASSES = (..., MyTool)
```

For a parser shipped by a separate Python package, expose it through the
`speccheck.parsers` entry point group instead:

```toml
[project.entry-points."speccheck.parsers"]
mytool = "my_package.mytool:MyTool"
```

Speccheck validates entry points at runtime. The entry point must load a
`Parser` subclass and its `software_name` must not duplicate an existing parser.

Add criteria rows:

```csv
species,assembly_type,software,field,operator,value,severity,source,special_field
all,all,MyTool,score,>=,0.95,fail,my-project,
```

Then test:

- the expected file is detected;
- a similar but invalid file is rejected;
- `fetch_values()` returns stable metric names and values;
- the criteria row evaluates as expected.

## Worked example: a JSON parser

For JSON, text summaries, or multi-row formats, subclass `Parser` directly and
make the content validation real:

```python
import json
from pathlib import Path

from speccheck.modules.base import Parser


class MyJsonTool(Parser):
    software_name = "MyJsonTool"
    description = "Example JSON QC parser"
    supported_filenames = "*.mytool.json"

    @property
    def has_valid_filename(self):
        return Path(self.file_path).name.endswith(".mytool.json")

    @property
    def has_valid_fileformat(self):
        try:
            with open(self.file_path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return False
        return {"sample", "score"}.issubset(data)

    def fetch_values(self):
        with open(self.file_path, encoding="utf-8") as handle:
            data = json.load(handle)
        return {"score": float(data["score"])}
```

## Criteria design rules

- Keep metric names stable once published.
- Add criteria only for metrics the parser actually emits.
- Use `severity=fail` for thresholds that should fail a sample.
- Use `severity=warn` for thresholds that should be visible but reviewable.
- Use `species=all` for global policy rows.
- Use a species name only when the threshold is genuinely species-specific.
- Record the source, for example `qualibact-v1.0`, `bactscout-global`, or
  `project-local`.

## Avoid duplication

Before writing a new parser, check whether an existing base class already solves
most of the problem. A good parser usually has:

- one filename rule;
- one content/header validation rule;
- one `fetch_values()` method;
- no threshold logic;
- no plotting logic;
- tests for positive and negative detection.

Threshold logic belongs in the criteria CSV, not in the parser.

## Optional plotting module

Add a plotting module only after parsing and criteria evaluation work. Plotting
should improve the HTML report but must not be required for `collect` or
`summary` to produce CSV/XLSX outputs.

Plot classes live under `speccheck/plot_modules/` and are registered in
`PLOT_CLASSES`.
