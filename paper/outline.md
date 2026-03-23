# MetaboLiteLearner 2.0 Paper Outline

## Working Title

MetaboLiteLearner 2.0: joint component extraction and fragmentation-space learning for metabolic rewiring

## Current Draft Logic

This is a full replacement paper. The manuscript should report the present 2.0 workflow and its outputs as the primary result set, while using the 2024 study only as prior work and concise comparison. The draft should read like a methods/results paper, not like a repository transition note.

## Section Map

1. Abstract
   The problem, the joint-component representation, the current 12/12/4 baseline, and the main balanced claim for 2.0.
2. Introduction
   Why metabolite identification remains a bottleneck, why the representation stage matters, and why learning the intermediate GC/MS objects is worth reporting.
3. Methods
   Study system, aligned GC/MS matrices, supervised nonnegative component extraction, fold-change estimation, PLS learning, and post hoc reference projection.
4. Results
   The current baseline: 12 joint components, 12 fold-change peaks, 4 latent components, predictive diagnostics, variance explained, interpretability, and concise comparison with the earlier workflow.
5. Discussion
   What the model learns statistically and biologically, where the current baseline is useful, what still requires validation, and why oversplitting is the next algorithmic target.
6. References
   Current bibliography for the replacement paper.

## Results Emphasis

- lead with the current joint-extractor output rather than with historical context
- describe the 12-peak fold-change table as the supervised response set
- use the 4-component learner fit as the compact predictive model
- keep the 2024 paper to one concise comparison paragraph
- tie each result subsection to the current paper figures in `paper/figures/`

## Near-Term Writing Tasks

- keep the prose manuscript-like and reduce visible repo scaffolding in the main text
- align figure captions with the current 2.0 outputs
- keep citations matched to the actual method description
- make sure the Methods/Results boundary stays clean
- keep historical comparison brief and explicitly secondary

## Future 2.0 Expansion Points

- benchmark the current baseline against additional datasets
- test how stable the joint extractor is when the sample tensor changes
- evaluate whether the 4-component fit remains the right compact summary outside this staged run
- extend the discussion once new experimental results exist
