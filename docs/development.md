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
isort --check-only --profile black speccheck tests
```

## Packaging direction

The project uses `pyproject.toml` as the packaging source of truth and aims for installation parity across:

- editable source installs
- standard `pip install`
- Conda/Bioconda style package installs

Runtime defaults such as templates and criteria should always resolve from packaged resources rather than assuming a source checkout.

## Adding input modules

Use `docs/modules.md` as the contributor-facing contract. New parsers should
subclass `Parser` or `SingleRowTsvParser`, expose `software_name`,
`description`, and `supported_filenames`, and include tests for detection,
rejection, and parsed values. Built-in parsers are registered in
`speccheck/registry.py`; third-party parsers can use the `speccheck.parsers`
entry-point group.

Releases are cut manually from the GitHub Actions **Release** workflow after the version has been prepared and merged. Enter the exact version already recorded in `pyproject.toml`, `CHANGELOG.md`, and `CITATION.cff`; the workflow verifies that they agree before creating the tag/release and publishing the Docker image. It intentionally does not run on every push to `main`, so documentation and CI-only commits do not create release churn.

## Upstream QC on Slurm

If you want to rerun upstream QC tools before collecting with `speccheck`, use the Slurm template:

```bash
scripts/upstream_qc_slurm_template.sh
```

It is intentionally a template rather than a rigid workflow engine, because site-specific tool paths and databases usually differ across clusters.
