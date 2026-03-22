# Reproducibility

## Repo Policy

This repository now commits a reproducible snapshot of the original study's Python workflow workspace under `data/original_study/`.

Still excluded by design:

- raw Agilent `.D` directories
- ad hoc local rerun logs
- unrelated future large datasets unless intentionally promoted

## Why

The 2.0 repo is meant to stay automation-friendly while still carrying one canonical baseline dataset for development and regression checks. The committed snapshot is limited to processed matrix CSVs, KEGG references, and regenerated workflow outputs. Raw vendor directories remain out of git.

## Expected Reproducibility Pattern

1. install the package in editable mode
2. use the committed baseline dataset in `data/original_study/` or restage it with the helper script
3. run the workflow or experiment scripts
4. compare results against the committed baseline outputs

## Data Documentation Standard

Any future dataset integration should document:

- source URL or DOI
- expected directory structure
- checksum or version identifier when available
- exact command to regenerate intermediate and final outputs

## Default Testing Policy

The default test suite must remain self-contained and runnable without full external study assets. Data-dependent integration tests can be added later, but they should be clearly separated from the lightweight default suite.

## Local Data Workspace

The repo-level `.gitignore` now allows `data/` to be tracked while still ignoring local log files under that tree.

For the original study dataset, the expected local layout is:

```text
data/original_study/
  gcmsCSVs/
  kegg/
  extractedPeaks/
  folds/
```

Stage the minimal workflow inputs with:

```bash
./scripts/stage_previous_dataset.sh
```

That script prefers the existing local checkout at `/Users/jxavier/dev/metaboliteLearner` and otherwise downloads `gcmsCSVs/` and `kegg/` from the original GitHub repository.

Run the end-to-end workflow against the staged data with:

```bash
metabolitelearner2 run-workflow \
  --gcms-csv-dir data/original_study/gcmsCSVs \
  --extracted-peaks-dir data/original_study/extractedPeaks \
  --folds-dir data/original_study/folds \
  --kegg-mat-path data/original_study/kegg/keggCompoundsWithFiehlibSpectrum.mat \
  --regenerate-peaks
```
