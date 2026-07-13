#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pixi >/dev/null 2>&1; then
  export PATH="$HOME/.pixi/bin:$PATH"
fi

scripts/stage_ghru_validation_assets.sh

mkdir -p .demo_work/slurm

export NXF_HOME="${PWD}/.demo_work/nextflow"
export NXF_WORK="${PWD}/.demo_work/ghru_validation/work"
export APPTAINER_CACHEDIR="${PWD}/.demo_work/apptainer/cache"
export APPTAINER_TMPDIR="${PWD}/.demo_work/apptainer/tmp"
export SINGULARITY_CACHEDIR="${APPTAINER_CACHEDIR}"
export SINGULARITY_TMPDIR="${APPTAINER_TMPDIR}"

rm -f \
  "${PWD}/.demo_work/ghru_validation/trace.tsv" \
  "${PWD}/.demo_work/ghru_validation/nextflow-report.html"

pixi run nextflow run external/GHRU-assembly/main.nf \
  -profile bmrc \
  -c scripts/ghru_assembly_bmrc_local.config \
  --samplesheet "${PWD}/.demo_work/ghru_validation/samplesheet.short.csv" \
  --outdir "${PWD}/.demo_work/ghru_validation/output" \
  -with-report "${PWD}/.demo_work/ghru_validation/nextflow-report.html" \
  -with-trace "${PWD}/.demo_work/ghru_validation/trace.tsv" \
  -resume
