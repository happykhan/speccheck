# speccheck

[![CI](https://github.com/happykhan/speccheck/actions/workflows/tests.yml/badge.svg)](https://github.com/happykhan/speccheck/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/happykhan/speccheck/branch/main/graph/badge.svg)](https://codecov.io/gh/happykhan/speccheck)
[![GPLv3 License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python->=3.10-blue.svg)](https://www.python.org/)

`speccheck` is a Python command-line tool for collecting, validating, and summarizing genome QC metrics from multiple bioinformatics tools. It is designed for species-aware QC workflows and reproducible reporting.

## Documentation

Project documentation is built with MkDocs Material and intended for GitHub Pages:

- Docs site: `https://happykhan.github.io/speccheck/`
- Local docs build: `mkdocs build`

Primary docs pages:

- [Installation](docs/installation.md)
- [CLI Usage](docs/cli.md)
- [Criteria Format](docs/criteria.md)
- [Reports](docs/reports.md)
- [QualiBact Integration](docs/qualibact.md)
- [Manuscript Assets](docs/manuscript.md)
- [Code Quality Audit](docs/code-quality.md)
- [Development](docs/development.md)

## Quick Start

Install from source in a Python `3.10+` environment:

```bash
git clone https://github.com/happykhan/speccheck.git
cd speccheck
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Collect QC metrics:

```bash
speccheck collect tests/practice_data/Sample_178db692semb --sample Sample_178db692semb
```

Generate a merged report:

```bash
speccheck summary qc_results --plot --qualifyr-style --xlsx-output qc_report/report.xlsx
```

Refresh criteria from QualiBact:

```bash
speccheck check --criteria-file speccheck/config/criteria.csv --update
```

## Features

- Automatic module detection for CheckM, QUAST, Speciator, ARIBA, Sylph, and DepthParser outputs
- Criteria-driven pass/fail validation
- HTML reporting with Plotly charts and interactive sortable/filterable tables
- Compact qualifyr-style summary tables
- Optional Excel workbook export from merged reports
- Packaged default criteria and templates for pip/conda style installs
- QualiBact threshold import workflow for manuscript validation and regression testing

## Development

Run tests:

```bash
pytest
```

Build docs:

```bash
mkdocs build
```

Build a wheel:

```bash
python -m build
```

## Citation

If you use `speccheck` in a manuscript, cite the software and include the repository URL. Structured citation metadata is provided in [`CITATION.cff`](CITATION.cff).
