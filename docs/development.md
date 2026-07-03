# Development

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Checks

Run tests:

```bash
pytest
```

Build docs:

```bash
mkdocs build
```

Build package artifacts:

```bash
python -m build
```

Lint and format:

```bash
ruff check speccheck tests
black --check speccheck tests
isort --check-only speccheck tests
```

## Packaging direction

The project uses `pyproject.toml` as the packaging source of truth and aims for installation parity across:

- editable source installs
- standard `pip install`
- Conda/Bioconda style package installs

Runtime defaults such as templates and criteria should always resolve from packaged resources rather than assuming a source checkout.

## Upstream QC on Slurm

If you want to rerun upstream QC tools before collecting with `speccheck`, use the Slurm template:

```bash
scripts/upstream_qc_slurm_template.sh
```

It is intentionally a template rather than a rigid workflow engine, because site-specific tool paths and databases usually differ across clusters.
