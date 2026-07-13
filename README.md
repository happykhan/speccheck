# speccheck

[![CI](https://github.com/happykhan/speccheck/actions/workflows/tests.yml/badge.svg)](https://github.com/happykhan/speccheck/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/happykhan/speccheck/branch/main/graph/badge.svg)](https://codecov.io/gh/happykhan/speccheck)
[![GPLv3 License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python->=3.10-blue.svg)](https://www.python.org/)

`speccheck` is a Python command-line tool for collecting, validating, and summarizing genome QC metrics from multiple bioinformatics tools. It is designed for species-aware QC workflows and reproducible reporting.

The publication case study processes 100 real, read-backed *Escherichia coli*
samples through `GHRU-assembly`, then applies a pinned QualiBact E. coli
compatibility policy. The committed case-study outputs include accessions,
provenance, reports, concordance analysis, and manuscript figures under
[`examples/qualibact_ecoli/real_run_100`](examples/qualibact_ecoli/real_run_100/).

## Documentation

Project documentation is built with MkDocs Material and intended for GitHub Pages:

- Docs site: `https://happykhan.github.io/speccheck/`
- Local docs build: `mkdocs build`

Primary docs pages:

- [Installation](docs/installation.md)
- [CLI Usage](docs/cli.md)
- [Modules and Extensions](docs/modules.md)
- [Criteria Format](docs/criteria.md)
- [Reports](docs/reports.md)
- [QualiBact Integration](docs/qualibact.md)
- [GHRU Integration](docs/ghru.md)
- [Manuscript Assets](docs/manuscript.md)
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

If `--organism` is not provided, `speccheck` infers it from species parser outputs and stops if no single species can be resolved. Use `--allow-unknown-organism` only for explicit fallback runs.

Generate a merged report:

```bash
speccheck summary qc_results --plot --qualifyr-style --xlsx-output qc_report/report.xlsx
```

`summary` merges concise collected CSV files, ignores `detailed.*.csv` companions, and rejects duplicate sample IDs.

Refresh criteria from QualiBact:

```bash
speccheck check --criteria-file speccheck/config/criteria.csv --update
```

## Features

- Explicitly registered parsers for CheckM2-style QC tables, QUAST, Speciator, ARIBA, Sylph, depth, Fastp, and BUSCO outputs
- Criteria-driven PASS/WARN/FAIL validation
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

Regenerate manuscript figures and example summary tables:

```bash
python scripts/create_manuscript_assets.py
python scripts/create_real_run_100_assets.py
```

Build a wheel:

```bash
python -m build
```

## Citation

If you use `speccheck` in a manuscript, cite the software and include the repository URL. Structured citation metadata is provided in [`CITATION.cff`](CITATION.cff). Zenodo archive metadata is provided in `.zenodo.json`; after a GitHub Release is archived by Zenodo, cite the release DOI for the exact version used.
