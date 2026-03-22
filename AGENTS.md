# AGENTS.md

## Mission

This repository exists to develop **MetaboLiteLearner 2.0** and its companion paper.

The software goal is to improve the Python implementation into a stable, extensible research codebase.
The scientific goal is to sharpen and test the thesis that **fragmentation structure alone can carry biologically useful signal about metabolic rewiring**.

## Working Rules

1. Python is the primary implementation language.
2. Do not reintroduce MATLAB as a runtime dependency.
3. Keep repo-tracked data small. Prefer reproducible download/build instructions over committing large study assets.
4. When adding experiments, make the hypothesis explicit in Markdown before implementing the analysis.
5. Preserve interpretability as a first-class constraint. Prefer methods whose outputs can still be discussed in biological terms.

## Source-of-Truth Files

- `README.md`: repo purpose and quick-start
- `PLAN.md`: top-level roadmap
- `docs/research_positioning.md`: scientific framing
- `docs/reproducibility.md`: data and regeneration policy
- `paper/outline.md`: manuscript structure

## Expectations for Agents

- Write design intent before writing complex code.
- Put experiment plans in `plans/` before adding large analysis branches.
- Put manuscript prose only under `paper/`.
- Keep default tests lightweight and self-contained.
- If a change depends on external data, state the required asset clearly and avoid assuming it is present locally.
