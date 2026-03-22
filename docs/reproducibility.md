# Reproducibility

## Repo Policy

This repository does **not** commit the full study datasets or generated study artifacts by default.

Excluded by design:

- raw Agilent `.D` directories
- full matrix CSV collections
- extracted peak tables from the original study
- generated workflow figures and parity outputs

## Why

The 2.0 repo is meant to stay lightweight and automation-friendly. Large historical assets belong in external storage or release artifacts, with explicit instructions for retrieval.

## Expected Reproducibility Pattern

1. install the package in editable mode
2. obtain the required dataset from its documented source
3. place or symlink the dataset into a local non-tracked workspace
4. run the workflow or experiment scripts
5. save outputs under a non-tracked local directory

## Data Documentation Standard

Any future dataset integration should document:

- source URL or DOI
- expected directory structure
- checksum or version identifier when available
- exact command to regenerate intermediate and final outputs

## Default Testing Policy

The default test suite must remain self-contained and runnable without full external study assets. Data-dependent integration tests can be added later, but they should be clearly separated from the lightweight default suite.
