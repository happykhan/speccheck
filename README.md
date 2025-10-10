# speccheck

[![CI](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml/badge.svg)](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml)
[![codecov](https://codecov.io/gh/happykhan/speccheck/branch/main/graph/badge.svg)](https://codecov.io/gh/happykhan/speccheck)
[![GPLv3 License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python->=3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**speccheck** is a modular command-line tool for collecting, validating, and summarizing quality control (QC) metrics from genomic analysis pipelines. It automatically detects and processes outputs from multiple bioinformatics tools, validates them against customizable criteria, and generates comprehensive reports with optional interactive visualizations.

## Features

- 🔍 **Automatic Module Detection**: Supports CheckM, QUAST, Speciator, ARIBA, and Sylph outputs
- ✅ **Flexible QC Validation**: Define organism-specific quality criteria with pass/fail checks
- 📊 **Interactive Reports**: Generate HTML dashboards with Plotly visualizations
- 🔗 **Metadata Integration**: Merge external sample metadata into QC reports
- 📝 **Rich Logging**: Beautiful console output with Rich library
- 🐳 **Docker Support**: Pre-built Docker images available

## Installation


### From Source

Clone the repository and install with pip:

```bash
git clone https://github.com/happykhan/speccheck.git
cd speccheck
pip install -e .
```

### Development Installation

For development with testing and linting tools:

```bash
pip install -e '.[dev]'
```

**Note**: This project uses modern Python packaging with `pyproject.toml` (PEP 517/621). See [MIGRATION.md](MIGRATION.md) for details on the migration from `setup.py`.

### Docker

A Docker image is available for containerized execution:

```bash
docker pull happykhan/speccheck
```

## Quick Start

1. **Collect QC data** from analysis outputs:
```bash
speccheck collect tests/practice_data/Sample_* --output-file results.csv
```

2. **Generate summary report** with visualizations:
```bash
speccheck summary qc_results/ --plot
```

3. **Validate criteria** file:
```bash
speccheck check --criteria-file criteria.csv
```

## Usage

### Command: `collect`

Collect and validate QC metrics from bioinformatics tool outputs.

```bash
speccheck collect [OPTIONS] FILEPATHS...
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `FILEPATHS` | Positional | Required | File paths (supports wildcards like `data/*/*.tsv`) |
| `--organism` | String | Auto-detect | Organism name for criteria matching |
| `--sample` | String | None | Sample identifier |
| `--criteria-file` | Path | `criteria.csv` | CSV file with QC criteria |
| `--output-file` | Path | `qc_results/collected_data.csv` | Output CSV path |
| `--metadata` | Path | None | CSV with additional metadata (requires `sample_id` column) |
| `-v, --verbose` | Flag | False | Enable debug logging |
| `--version` | Flag | - | Show version and exit |

#### Examples

Basic collection:
```bash
speccheck collect data/sample1/*.tsv --sample sample1
```

With organism specification:
```bash
speccheck collect data/ecoli_* --organism "Escherichia coli" --output-file ecoli_qc.csv
```

With metadata merging:
```bash
speccheck collect data/* --metadata sample_info.csv --output-file merged_results.csv
```

#### Supported Modules

The collect command automatically detects outputs from:
- **CheckM**: Completeness, contamination, genome metrics
- **QUAST**: Assembly statistics (N50, contigs, GC content)
- **Speciator**: Species identification and confidence
- **ARIBA**: Antimicrobial resistance gene detection
- **Sylph**: Metagenomic profiling and ANI values

---

### Command: `summary`

Generate consolidated reports from multiple collected QC files.

```bash
speccheck summary [OPTIONS] DIRECTORY
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `DIRECTORY` | Positional | Required | Directory containing CSV QC reports |
| `--output` | Path | `qc_report` | Output directory for summary |
| `--species` | String | `Speciator.speciesName` | Column name for species field |
| `--sample` | String | `sample_id` | Column name for sample identifier |
| `--templates` | Path | `templates/report.html` | HTML template file |
| `--plot` | Flag | False | Generate interactive plots |
| `-v, --verbose` | Flag | False | Enable debug logging |
| `--version` | Flag | - | Show version and exit |

#### Examples

Basic summary:
```bash
speccheck summary qc_results/
```

With plotting enabled:
```bash
speccheck summary qc_results/ --plot --output final_report/
```

Custom field names:
```bash
speccheck summary results/ --sample SampleID --species Species --plot
```

#### Output

- `report.csv`: Consolidated QC metrics with sorted columns (sample_id, all_checks_passed, .check columns, other fields)
- `report.html`: Interactive HTML dashboard (when `--plot` is enabled)

---

### Command: `check`

Validate the structure and content of a criteria file.

```bash
speccheck check [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--criteria-file` | Path | `criteria.csv` | Path to criteria CSV file |
| `-v, --verbose` | Flag | False | Enable debug logging |
| `--version` | Flag | - | Show version and exit |

#### Example

```bash
speccheck check --criteria-file config/custom_criteria.csv
```

---

## Criteria File Format

The criteria file defines organism-specific QC thresholds in CSV format:

```csv
organism,software,field,operator,threshold
Escherichia coli,Checkm,Completeness,>=,95
Escherichia coli,Checkm,Contamination,<=,5
Escherichia coli,Quast,N50,>=,50000
```

**Columns:**
- `organism`: Species or genus name (use "all" for universal criteria)
- `software`: Tool name (CheckM, QUAST, Speciator, ARIBA, Sylph)
- `field`: Metric name from tool output
- `operator`: Comparison operator (`>=`, `<=`, `==`, `>`, `<`)
- `threshold`: Numeric threshold value

---

## Metadata Integration

Add external sample metadata using the `--metadata` option:

**metadata.csv**:
```csv
sample_id,location,sequencing_date,batch
sample1,Lab A,2024-01-15,Batch1
sample2,Lab B,2024-01-16,Batch1
```

```bash
speccheck collect data/* --metadata metadata.csv --output-file results.csv
```

Metadata columns are automatically merged with QC metrics based on `sample_id`.

---

## Output Format

### CSV Column Order

Output files are automatically organized for readability:

1. **Sample identifier** (`sample_id` or `Sample`)
2. **Overall checks** (columns ending with `all_checks_passed`)
3. **Individual checks** (columns ending with `.check`) - sorted alphabetically
4. **Metrics** (remaining columns) - sorted alphabetically

### Example Output

```csv
sample_id,all_checks_passed,Checkm.all_checks_passed,Checkm.Completeness.check,Checkm.Contamination.check,Checkm.Completeness,Checkm.Contamination
sample1,True,True,True,True,98.5,1.2
sample2,False,False,False,True,89.3,0.8
```

---

## Development

### Running Tests

```bash
pytest
pytest --cov=speccheck  # With coverage
```

### Code Quality

```bash
pylint speccheck/
```

### Project Structure

```
speccheck/
├── speccheck/
│   ├── __init__.py
│   ├── main.py              # Core logic
│   ├── collect.py           # File collection & writing
│   ├── criteria.py          # Criteria validation
│   ├── report.py            # Report generation
│   ├── modules/             # Tool-specific parsers
│   │   ├── checkm.py
│   │   ├── quast.py
│   │   ├── speciator.py
│   │   ├── ariba.py
│   │   └── sylph.py
│   └── plot_modules/        # Visualization modules
│       ├── plot_checkm.py
│       ├── plot_quast.py
│       └── ...
├── tests/                   # Pytest test suite
├── templates/               # HTML templates
├── speccheck.py            # CLI entry point
└── setup.py                # Package configuration
```

---

## Dependencies

- **Core**: `rich`, `typer`, `pandas`, `jinja2`, `plotly`
- **Dev**: `pytest`, `pytest-cov`, `pylint`, `coverage`

---

## Version

Check the installed version:

```bash
speccheck --version
```

---

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions are welcome! We appreciate bug reports, feature requests, documentation improvements, and code contributions.

### Quick Start for Contributors

1. Fork the repository
2. Install development dependencies: `pip install -e '.[dev]'`
3. Install pre-commit hooks: `pre-commit install`
4. Create a feature branch: `git checkout -b feature/your-feature`
5. Make your changes and add tests
6. Run checks: `pytest --cov=speccheck && ruff check speccheck/`
7. Submit a pull request

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Code Quality

This project uses:
- **Black** for code formatting
- **Ruff** for fast linting
- **Pylint** for comprehensive code analysis
- **pytest** with coverage reporting
- **pre-commit** hooks for automated checks

All PRs must pass CI checks including tests on Python 3.10, 3.11, and 3.12 across Ubuntu, macOS, and Windows.

---

## Citation

If you use speccheck in your research, please cite:

```
[Citation information to be added]
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/happykhan/speccheck/issues)
- **Documentation**: This README
- **Contact**: See [setup.py](setup.py) for author information
