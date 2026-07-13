#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pixi >/dev/null 2>&1; then
  export PATH="$HOME/.pixi/bin:$PATH"
fi

COHORT_NAME="${1:-run_100}"
RUN_ROOT="${PWD}/.demo_work/ghru_ecoli_cohort/${COHORT_NAME}"

scripts/stage_ghru_ecoli_run_100.sh "${COHORT_NAME}"

mkdir -p .demo_work/slurm

export NXF_HOME="${PWD}/.demo_work/nextflow"
export NXF_WORK="${RUN_ROOT}/work"
export APPTAINER_CACHEDIR="${PWD}/.demo_work/apptainer/cache"
export APPTAINER_TMPDIR="${PWD}/.demo_work/apptainer/tmp"
export SINGULARITY_CACHEDIR="${APPTAINER_CACHEDIR}"
export SINGULARITY_TMPDIR="${APPTAINER_TMPDIR}"

rm -f \
  "${RUN_ROOT}/trace.tsv" \
  "${RUN_ROOT}/nextflow-report.html"

pixi run nextflow run external/GHRU-assembly/main.nf \
  -profile bmrc \
  -c scripts/ghru_assembly_bmrc_local.config \
  --samplesheet "${RUN_ROOT}/samplesheet.csv" \
  --outdir "${RUN_ROOT}/output" \
  -with-report "${RUN_ROOT}/nextflow-report.html" \
  -with-trace "${RUN_ROOT}/trace.tsv" \
  -resume
