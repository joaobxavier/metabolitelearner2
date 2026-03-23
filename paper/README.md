# Companion Paper Workspace

This directory contains the Markdown-first draft of the MetaboLiteLearner 2.0 paper. The manuscript now treats the current 2.0 workflow and its staged outputs as the primary result set, with the 2024 paper retained only as prior work and comparison material.

## Current Structure

- `00_abstract.md`: paper abstract for the 2.0 manuscript
- `01_introduction.md`: motivation, problem framing, and why fragmentation structure can be predictive before full identification
- `02_methods.md`: the current workflow description, including joint extraction, fold-change estimation, and the learner
- `03_results.md`: the current results narrative centered on 12 joint components, 12 fold-change peaks, and 4 latent components
- `04_discussion.md`: interpretation, limitations, and how the 2.0 workflow should be used in practice
- `05_references.md`: bibliography for the draft
- `outline.md`: the section map for the replacement paper
- `source_papers/`: archived source PDFs, including the published 2024 Methods paper
- `figures/`: paper-facing figure assets for the current draft
- `notes/`: working notes and draft support material

## Writing Principle

The paper now follows a simple rule:

1. the 2.0 workflow and its staged outputs are the source of record for the manuscript
2. the 2024 paper is used only for concise historical comparison
3. all claims in `03_results.md` should track the current code and current figure set, not the older narrative by default

That keeps the draft anchored in the current paper result set while still acknowledging where the idea came from.

## Main Linked Assets

- current paper figures: [`figures/figure_1_predictive_performance.png`](figures/figure_1_predictive_performance.png), [`figures/figure_2_variance_explained.png`](figures/figure_2_variance_explained.png), [`figures/figure_3_interpretability.png`](figures/figure_3_interpretability.png)
- current workflow: [`../metabolite_learner/workflow.py`](../metabolite_learner/workflow.py)
- joint extractor: [`../metabolite_learner/joint_extract.py`](../metabolite_learner/joint_extract.py)
- learner implementation: [`../metabolite_learner/pls.py`](../metabolite_learner/pls.py)
- staged baseline data and outputs: [`../data/original_study`](../data/original_study)
- baseline run report: [`../docs/reports/previous_dataset_run.md`](../docs/reports/previous_dataset_run.md)

## Drafting Notes

- keep the result section centered on the current 12/12/4 baseline
- keep the prior 2024 paper as a short comparison point only
- keep the paper body manuscript-like and confine most implementation pointers to methods/reproducibility notes
- avoid reintroducing placeholder language from the bootstrap draft
