# speccheck

[![Run Pytest](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml/badge.svg)](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml)
[![GPLv3 License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python->=3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)

**speccheck** is a command-line tool for processing, collecting, and summarizing QC reports. It supports extracting metadata and QC outcomes for specific organisms across datasets, validating QC criteria, and generating summaries with optional plotting.

## Features

- **Collect** metadata and QC results from file paths using flexible wildcards.
- **Summarize** multiple collected reports into a clean HTML and CSV summary.
- **Check** criteria files for correctness and consistency.
- Built-in verbose logging and version tracking.

## Installation

Clone the repository and install any required dependencies:

```bash
git clone https://github.com/yourusername/speccheck.git
cd speccheck
pip install -e .        
```

For the development tools as well, use:

```bash
pip install -e '.[dev]'        
```

There is a docker image available for this project. 

## Usage

The tool has three main subcommands:

### 1. `collect`: Collect and process QC data

```bash
python speccheck.py collect [OPTIONS] <filepaths>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--organism` | Organism name (optional, extracted from filenames if not specified) |
| `--sample` | Sample name (optional) |
| `--criteria-file` | Path to criteria CSV file (default: `criteria.csv`) |
| `--output-file` | Output CSV file path (default: `qc_results/collected_data.csv`) |
| `-v`, `--verbose` | Enable debug-level logging |
| `--version` | Print the version number |

**Example:**

```bash
python speccheck.py collect --organism ecoli --sample sample1 data/*/*.json
```

---

### 2. `summary`: Summarize reports

```bash
python speccheck.py summary [OPTIONS] <directory>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output` | Output directory for the summary (default: `qc_report`) |
| `--species` | Field name for species in report (default: `Speciator.speciesName`) |
| `--sample` | Field name for sample name (default: `Sample`) |
| `--templates` | Path to the HTML template (default: `templates/report.html`) |
| `--plot` | Enable plotting (default: `False`) |
| `-v`, `--verbose` | Enable debug-level logging |
| `--version` | Print the version number |

**Example:**

```bash
python speccheck.py summary --plot reports/
```

---

### 3. `check`: Validate the criteria file

```bash
python speccheck.py check [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--criteria-file` | Path to criteria file (default: `criteria.csv`) |
| `-v`, `--verbose` | Enable debug-level logging |
| `--version` | Print the version number |

**Example:**

```bash
python speccheck.py check --criteria-file config/my_criteria.csv
```

---

## Output

- **Collected data**: CSV file with all relevant metrics per file.
- **Summary report**: CSV and optionally an HTML dashboard with species/sample breakdowns and visualizations.
- **Logging**: Console messages (INFO or DEBUG) for tracking the process.

## Version

Display version using:

```bash
python speccheck.py <subcommand> --version
```

## License

GPLv3
