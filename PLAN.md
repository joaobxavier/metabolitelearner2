# MetaboLiteLearner 2.0 Plan

## Near-Term Milestones

1. Bootstrap the Python-only repo, docs, and manuscript scaffold.
2. Stabilize the Python workflow as the canonical implementation baseline.
3. Define the first MetaboLiteLearner 2.0 research hypotheses and evaluation criteria.
4. Build a reproducible experiment layer that can regenerate figures and tables from external datasets.
5. Draft the companion paper sections around motivation, method, benchmarks, and biological interpretation.

## Open Technical Questions

- Which parts of the current workflow should remain linear and interpretable versus become more expressive in 2.0?
- How should peak-level uncertainty propagate into the learner?
- What is the right benchmark suite beyond the original breast-cancer lineage dataset?
- How should fragmentation-only learning be compared against identification-dependent baselines?

## Open Scientific Questions

- When does fragmentation structure alone stop being sufficient?
- Which biological claims can be made at the peak level versus the metabolite level?
- How should unidentified peaks be discussed in a paper without overselling mechanistic certainty?

## Current Default

This repo starts from the current Python implementation as a research baseline, not as a finished product.
