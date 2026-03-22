#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${1:-data/original_study}"
SOURCE_REPO="${SOURCE_REPO:-/Users/jxavier/dev/metaboliteLearner}"
REMOTE_URL="${REMOTE_URL:-https://github.com/joaobxavier/learn_metabolic_rewiring_matlab.git}"

mkdir -p "$(dirname "$TARGET_ROOT")"
TARGET_ROOT="$(cd "$(dirname "$TARGET_ROOT")" && pwd)/$(basename "$TARGET_ROOT")"
mkdir -p "$TARGET_ROOT"

cleanup() {
  if [[ -n "${TMPDIR_STAGE:-}" && -d "${TMPDIR_STAGE}" ]]; then
    rm -rf "${TMPDIR_STAGE}"
  fi
}
trap cleanup EXIT

if [[ -d "${SOURCE_REPO}/gcmsCSVs" && -d "${SOURCE_REPO}/kegg" ]]; then
  SOURCE_ROOT="${SOURCE_REPO}"
  echo "Using local source repo at ${SOURCE_ROOT}"
else
  TMPDIR_STAGE="$(mktemp -d)"
  SOURCE_ROOT="${TMPDIR_STAGE}/learn_metabolic_rewiring_matlab"
  echo "Downloading dataset source from ${REMOTE_URL}"
  git clone --depth 1 --filter=blob:none --sparse "${REMOTE_URL}" "${SOURCE_ROOT}"
  git -C "${SOURCE_ROOT}" sparse-checkout set gcmsCSVs kegg
fi

mkdir -p "${TARGET_ROOT}/gcmsCSVs" "${TARGET_ROOT}/kegg"
rsync -a "${SOURCE_ROOT}/gcmsCSVs/" "${TARGET_ROOT}/gcmsCSVs/"
rsync -a "${SOURCE_ROOT}/kegg/" "${TARGET_ROOT}/kegg/"

echo "Staged dataset into ${TARGET_ROOT}"
du -sh "${TARGET_ROOT}/gcmsCSVs" "${TARGET_ROOT}/kegg"
