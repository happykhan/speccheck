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
ruff format --check speccheck tests scripts docker/build_docker.py
ruff check speccheck tests scripts docker/build_docker.py
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

Releases are cut manually from the GitHub Actions **Release** workflow after the version has been prepared and merged. Enter the exact version already recorded in `pyproject.toml`, `CHANGELOG.md`, and `CITATION.cff`; the workflow verifies that they agree before creating the tag/release, publishing to PyPI, and publishing the Docker image. It intentionally does not run on every push to `main`, so documentation and CI-only commits do not create release churn.

The manual release workflow publishes PyPI directly. Do not rely on a second
release-event workflow being triggered by the automated GitHub Release: events
created with the repository `GITHUB_TOKEN` do not start most other workflows.
The standalone **Publish to PyPI** workflow is kept as a fallback for releases
created manually outside the release workflow.

## Archival DOI

Zenodo is not a CI job in this repository. It is normally enabled once in the
Zenodo web interface for the GitHub repository. After that, each GitHub Release
is archived by Zenodo and receives a DOI. The repository includes `.zenodo.json`
so the archived release has useful title, creator, license, keyword, and
description metadata.

Release sequence:

1. Merge the release-prepared branch to `main`.
2. Confirm GitHub Actions are green and GitHub Pages has deployed.
3. Run the read-only release preflight:

   ```bash
   pixi run release-preflight 1.3.0
   ```

4. Run the manual GitHub Actions **Release** workflow with the prepared version.
5. Confirm PyPI, Docker Hub, and the GitHub Release show the same version.
6. Confirm Zenodo archived the GitHub Release and minted a DOI.
7. Cite that exact version DOI in any downstream paper, report, or release note.

## Pipeline layout collectors

Use [Pipeline Integration](ghru.md) as the contract for workflow-facing work.
New collectors should be added only after the upstream workflow has a stable
published output layout. Prefer a generic command name and a layout selector,
for example:

```bash
speccheck collect-pipeline results/ qc_collect --layout ghru
```

Avoid requiring users to search a full Nextflow work directory for routine use.
Work-directory recovery is acceptable for backward compatibility or provenance
when a workflow has not yet published all needed compact files.
