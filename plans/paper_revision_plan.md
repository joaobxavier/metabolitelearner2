# Paper Revision Plan

## Purpose

Address the first-pass reviewer critique of the companion paper draft and move the manuscript from "repo-backed notes" toward a readable paper starter.

## Priority Findings

1. The paper's contribution is not stated sharply enough.
2. Published 2024 results and current baseline outputs are mixed too loosely.
3. Too much repo-internal language appears in the manuscript body.
4. The methods section needs stronger experimental detail.
5. The figures need paper-facing exports and cleaner presentation.
6. The draft needs at least a minimal references section.

## Revision Actions

### A. Clarify manuscript identity

- Treat the current draft as a paper-style restatement of the published 2024 manuscript.
- Keep current Python baseline outputs as supporting implementation artifacts, not as replacement scientific claims.

### B. De-internalize the prose

- Remove project-management language from the abstract, introduction, results, and discussion.
- Keep file links only where they materially support reproducibility.

### C. Restore missing method detail

- State the experimental system, sample counts, derivatization workflow, GC/MS instrument setup, dataset construction logic, cross-validation scheme, and shuffle control clearly in the methods section.

### D. Create paper-facing figure assets

- Export manuscript figures into `paper/figures/`.
- Regenerate the interpretability figure so it does not include empty latent-component panels when the current baseline uses fewer than five components.
- Point the manuscript to paper-facing figure assets rather than directly to development outputs where practical.

### E. Add minimal bibliography support

- Add a references section with the key metabolomics, PLSR, KEGG/Fiehn, and prior-study citations needed by the current draft.
- Add a light layer of inline citations in the manuscript where unsupported claims were previously too broad.

## Acceptance Criteria

- The abstract reads like a scientific abstract.
- The introduction, methods, results, and discussion read as paper sections rather than repo notes.
- The methods section contains enough detail for an external reader to follow the published workflow.
- The results section distinguishes clearly between published claims and current implementation renderings.
- Figure files used in the paper live under `paper/figures/`.
- The paper includes a references section and corresponding inline citations.
- A second-pass review finds fewer unresolved issues than the first-pass critique.

## Status After Revision

- Addressed: manuscript voice in the abstract, introduction, methods, results, and discussion is now substantially less repo-internal.
- Addressed: methods now state the sample structure, derivatization workflow, instrument setup, filtering threshold, mixed-effects fold-change estimation, normalization, and shuffle-control design more explicitly.
- Addressed: figures are exported into `paper/figures/`, and the interpretability figure layout was rebuilt so the displayed latent-component panels match the executable baseline.
- Addressed: the paper now includes a minimal references section and inline citations across the main text.
- Partially addressed: the distinction between published 2024 claims and the current Python baseline is now explicit in the Results section, but the manuscript still needs a future supplement or appendix once genuine 2.0 experiments replace the historical result narrative.

## Remaining Follow-Up

- Rebuild a fully publication-ready figure set once the 2.0 experiments exist.
- Decide whether the eventual paper is a reproduction paper, a methods-extension paper, or a new-benchmark paper.
- Add a dedicated supplementary reproducibility appendix if the paper continues to reference implementation details.
