#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_DIR="${PWD}/.demo_work/ghru_images"
APPTAINER_CACHE="${PWD}/.demo_work/apptainer/cache"
APPTAINER_TMP="${PWD}/.demo_work/apptainer/tmp"
SHARED_SIF_DIR="${PWD}/../../../shared/singularity/GHRU-assembly"
mkdir -p "${IMAGE_DIR}" "${APPTAINER_CACHE}" "${APPTAINER_TMP}" "${PWD}/.demo_work/ghru_validation"

export APPTAINER_CACHEDIR="${APPTAINER_CACHE}"
export APPTAINER_TMPDIR="${APPTAINER_TMP}"
export SINGULARITY_CACHEDIR="${APPTAINER_CACHEDIR}"
export SINGULARITY_TMPDIR="${APPTAINER_TMPDIR}"

for image in \
  ariba_contam_0.1.1.sif \
  bash_ghru.sif \
  cgps_dragonflye_medaka.sif \
  fastqc_0.12.1--hdfd78af_0.sif \
  lrge_0.1.3--h9f13da3_1.sif \
  nanoplot_1.42.0--pyhdfd78af_0.sif \
  porechop_0.2.4--py310h84f13bb_8.sif \
  python.sif \
  quast_5.2.0--py312pl5321hc60241a_4.sif \
  shovill_1.1.0-2022Dec.sif \
  speccheck_0.2.1.sif \
  speciator_4.0.0.sif \
  sylph_0.1.0.sif \
  trimmomatic_0.36--3.sif \
  unicycler_0.5.0--py39heaaa4ec_5.sif
do
  ln -sfn "${SHARED_SIF_DIR}/${image}" "${IMAGE_DIR}/${image}"
done

CHECKM2_IMAGE="${IMAGE_DIR}/checkm2_0.1.0.sif"
if [[ ! -f "${CHECKM2_IMAGE}" ]]; then
  apptainer pull "${CHECKM2_IMAGE}" docker://happykhan/checkm2:0.1.0
fi

cat > "${PWD}/.demo_work/ghru_validation/samplesheet.short.csv" <<EOF
sample_id,short_reads1,short_reads2,long_reads,genome_size
test_sample_short,${PWD}/external/GHRU-assembly/test_data/GCA_000292405.1_R1.fastq.gz,${PWD}/external/GHRU-assembly/test_data/GCA_000292405.1_R2.fastq.gz,,
EOF

echo "Staged GHRU validation assets in ${PWD}/.demo_work/ghru_validation"
