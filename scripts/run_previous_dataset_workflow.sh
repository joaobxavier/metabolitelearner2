#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run_previous_dataset_workflow.sh [options]

Options:
  --workspace PATH         Workspace root to stage into and run from.
  --log PATH               Log file path for the workflow output.
  --stage-script PATH      Override the dataset staging script.
  --python-bin PATH        Python executable used to launch the workflow.
  --kfold-learn N          Forwarded to run-workflow.
  --max-components N       Forwarded to run-workflow.
  --nrandomized N          Forwarded to run-workflow.
  --shuffle-test           Forwarded to run-workflow.
  --no-regenerate-peaks    Skip peak regeneration in run-workflow.
  -h, --help               Show this help text.

The default workspace is the repo-local ignored data directory:
  data/original_study
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${REPO_ROOT}/data/original_study}"
LOG_PATH="${LOG_PATH:-${WORKSPACE_ROOT}/run_workflow.log}"
STAGE_SCRIPT="${STAGE_SCRIPT:-${SCRIPT_DIR}/stage_previous_dataset.sh}"
PYTHON_BIN="${PYTHON_BIN:-python}"
K_FOLD_LEARN=0
MAX_COMPONENTS=30
NRANDOMIZED=1000
SHUFFLE_TEST=false
REGENERATE_PEAKS=true

while (($#)); do
  case "$1" in
    --workspace)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --log)
      LOG_PATH="$2"
      shift 2
      ;;
    --stage-script)
      STAGE_SCRIPT="$2"
      shift 2
      ;;
    --python-bin)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --kfold-learn)
      K_FOLD_LEARN="$2"
      shift 2
      ;;
    --max-components)
      MAX_COMPONENTS="$2"
      shift 2
      ;;
    --nrandomized)
      NRANDOMIZED="$2"
      shift 2
      ;;
    --shuffle-test)
      SHUFFLE_TEST=true
      shift
      ;;
    --no-regenerate-peaks)
      REGENERATE_PEAKS=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$LOG_PATH")"
cd "$REPO_ROOT"

"$STAGE_SCRIPT" "$WORKSPACE_ROOT"

workflow_args=(
  -m metabolite_learner.cli run-workflow
  --gcms-csv-dir "$WORKSPACE_ROOT/gcmsCSVs"
  --extracted-peaks-dir "$WORKSPACE_ROOT/extractedPeaks"
  --folds-dir "$WORKSPACE_ROOT/folds"
  --kegg-mat-path "$WORKSPACE_ROOT/kegg/keggCompoundsWithFiehlibSpectrum.mat"
  --kfold-learn "$K_FOLD_LEARN"
  --max-components "$MAX_COMPONENTS"
  --nrandomized "$NRANDOMIZED"
)

if [[ "$REGENERATE_PEAKS" == true ]]; then
  workflow_args+=(--regenerate-peaks)
fi

if [[ "$SHUFFLE_TEST" == true ]]; then
  workflow_args+=(--shuffle-test)
fi

echo "Running previous-dataset workflow in ${WORKSPACE_ROOT}"
echo "Logging output to ${LOG_PATH}"
"$PYTHON_BIN" "${workflow_args[@]}" 2>&1 | tee "$LOG_PATH"
