# MetaboLiteLearner 2.0

MetaboLiteLearner 2.0 is a Python-first successor workspace for the original MetaboLiteLearner project. This repository is the starting point for:

- refining the fragmentation-to-rewiring learning pipeline,
- hardening the Python implementation as the primary codebase,
- and developing a companion paper that expands the claim that useful biological signal about metabolic rewiring can be recovered from fragmentation structure alone.

This repo intentionally starts lean. It excludes the full legacy MATLAB workflow and most generated result artifacts. It now includes a committed snapshot of the original study's processed Python inputs and outputs under `data/original_study/`. The repo otherwise keeps:

- the Python package baseline,
- lightweight tests,
- manuscript scaffolding in Markdown,
- and agent-facing planning/governance documents.

## Layout

- `metabolite_learner/`: Python package baseline
- `tests/`: lightweight default test suite
- `paper/`: companion-paper manuscript workspace in Markdown
- `docs/`: project docs and reproducibility notes
- `plans/`: milestone and experiment planning notes
- `references/`: imported summaries and comparison notes
- `scripts/`: helper scripts and future automation
- `examples/`: small example assets only

## Current Status

This is a scaffold-first bootstrap. The current code is a direct Python starting point from the original project, but this repo is not intended to be a mirror of the historical MATLAB implementation. It is the home for MetaboLiteLearner 2.0 development.

## Quick Start

```bash
python3 -m venv ~/dev/venvs/metabolitelearner2
source ~/dev/venvs/metabolitelearner2/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests
```

## Reproducibility and Data

The repository now includes the staged original-study dataset workspace under `data/original_study/`. See:

- [docs/reproducibility.md](docs/reproducibility.md)
- [docs/research_positioning.md](docs/research_positioning.md)
- [paper/README.md](paper/README.md)

## Provenance

This repo is bootstrapped from the Python implementation in the original MetaboLiteLearner repository and is meant to become the research and engineering home for the 2.0 line of work.
