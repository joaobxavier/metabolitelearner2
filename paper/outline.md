# MetaboLiteLearner 2.0 Paper Outline

## Working Title

MetaboLiteLearner 2.0: learning biologically useful metabolic rewiring signal from fragmentation structure alone

## Current Draft Logic

The manuscript currently functions as a "write up the previous version first" pass. That means the immediate goal is not to claim a new 2.0 result set, but to restate the published 2024 paper in a cleaner Markdown structure while attaching it to the current Python codebase and baseline assets in this repository.

## Section Map

1. Abstract
   The problem, the fragmentation-first representation, the original validation result, and the 2.0 framing boundary.
2. Introduction
   Why metabolite identification is a bottleneck, why fragmentation structure can be predictive before identification, and why interpretability matters.
3. Methods
   The published workflow restated through the current Python implementation:
   data ingestion, peak extraction, fold-change estimation, PLSR/SIMPLS learning, validation, and interpretability outputs.
4. Results
   The published result narrative:
   the 153-spectrum MLOD, component selection, predictive fit, variance explained, fragment-level interpretation, KEGG/Fiehn projections, and the shuffle-test control.
5. Discussion
   What the model learns, what it does not learn, where identification still matters, and what a 2.0 expansion should test next.
6. References
   Minimal bibliography supporting the current draft while fuller citation management is still being built.

## Near-Term Writing Tasks

- tighten the prose so it reads as a manuscript rather than as a repository narrative
- add citations into `bibliography/`
- export paper-facing figures into `paper/figures/`
- mark exactly where the future 2.0 experiments will replace or extend the published-paper narrative

## Future 2.0 Expansion Points

- benchmark updated Python results against the published MATLAB-era claims
- add clearer failure analysis and uncertainty reporting
- test whether fragmentation-space learning transfers across datasets, sample-prep regimes, or instrument classes
- separate "published prior result" text from "new 2.0 contribution" text once the new experiments exist
