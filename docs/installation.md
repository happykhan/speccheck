# Installation

## Requirements

- Python `>=3.10`
- `pip`

## Install from source

```bash
git clone https://github.com/happykhan/speccheck.git
cd speccheck
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Development install

```bash
pip install -e '.[dev]'
```

## Docker

```bash
docker pull happykhan/speccheck
```

See [Reports](reports.md) and [CLI Usage](cli.md) for example commands.

## Packaging notes

`speccheck` now packages its default template and default criteria inside the Python package so installs behave consistently across source checkouts and packaged environments.
