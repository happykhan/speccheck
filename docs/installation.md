# Installation

## Recommended: PyPI

The PyPI package is named `speccheck-qc`; it installs the `speccheck` command.

```bash
python -m pip install speccheck-qc
speccheck --version
speccheck --help
```

Use a virtual environment unless you are installing into a managed workflow image:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install speccheck-qc
```

## Check the installed package

```bash
speccheck modules
speccheck check
```

`speccheck modules` lists the parser modules available in that installation.
`speccheck check` validates the packaged criteria file.

## Development install

Use this only when modifying the source code:

```bash
git clone git@github.com:happykhan/speccheck.git
cd speccheck
python -m pip install -e '.[dev]'
```

## Docker

If a release image has been published for the version you need:

```bash
docker pull happykhan/speccheck
```

Typical usage:

```bash
docker run --rm \
  -v "$PWD":/data \
  happykhan/speccheck \
  speccheck summary /data/qc_collect --output /data/qc_report --plot
```

## Version note

The PyPI release may lag behind the repository during active development. For
reproducible reports, record both:

- `speccheck --version`;
- the criteria checksum written to `speccheck_criteria_sha256`.
