# Peer Review Critique

## Overall Assessment

This draft is technically informed, but it is not yet readable as an external paper. The current text still behaves like a repository companion note: it repeatedly points readers to code paths, baseline artifacts, and the published manuscript as the "source of record" instead of standing on its own as a scientific article.

The core idea is promising. The manuscript argues that EI fragmentation structure can carry biologically useful signal about metabolic rewiring, and the draft correctly preserves the interpretability-first framing. The main problem is not the scientific premise; it is that the draft has not yet separated three different things:

1. the 2024 published result set,
2. the current Python reimplementation and baseline outputs,
3. the future 2.0 scientific contribution.

Those are currently mixed together in the abstract, introduction, methods, results, and captions. As a reviewer, I would ask for a much sharper thesis before considering the paper ready.

## Top 5 Findings

1. The manuscript does not yet have a single, clear contribution. It reads like a repo-backed restatement of prior work rather than a paper with a defined scientific claim.
2. The draft conflates historical results with current baseline outputs, and the numbers do not line up cleanly across sections and figures.
3. The writing is too repo-internal for a paper: file paths, "current baseline" language, staged artifacts, and "source of record" disclaimers appear where manuscript prose should be self-contained.
4. The methods are still underspecified for an external reader, especially around preprocessing, peak filtering, fold-change estimation, cross-validation, and the shuffle test.
5. The figures are not yet publication-quality, with overloaded layouts, tiny labels, empty or repeated panels, and captions that depend on internal repo context.

## Detailed Critique

### 1) The paper's identity and contribution are still unclear

The draft currently oscillates between being a reproduction of the 2024 paper, a description of the Python codebase, and a placeholder for future 2.0 experiments. That is not a stable manuscript identity.

Specific examples:

- `paper/README.md` and `paper/outline.md` explicitly say the current pass is a "write up the previous version first" exercise.
- `paper/00_abstract.md` and `paper/01_introduction.md` repeatedly frame the goal as preserving the prior claim set rather than advancing a new one.
- `paper/03_results.md` says the published manuscript remains the source of record for claims, which is a repository-maintenance stance, not a paper stance.

For a real paper, the introduction should answer one of two questions clearly:

- What new scientific result is being claimed?
- Or, if this is a reproducibility/reimplementation paper, what new evidence, benchmark, or validation does the reimplementation add?

Right now the draft does neither cleanly. A stronger paper would have a single sentence in the abstract that states the contribution unambiguously and then keeps every section aligned to that claim.

### 2) Historical results and current baseline outputs are mixed together

The most serious communication problem is that the manuscript switches between the original 2024 numbers and the current repo baseline without establishing a clean boundary.

Examples:

- `paper/00_abstract.md`, `paper/01_introduction.md`, and `paper/03_results.md` emphasize the published 153-spectrum dataset and five-component model.
- The same `paper/03_results.md` also points to the current baseline run summary that reports a 125-peak, 3-component snapshot.
- `paper/03_results.md` embeds figures whose titles and contents reflect the current Python baseline, while the surrounding text still says the published result remains the source of record.

This creates a reader problem: which result set is the paper actually about?

If the intent is to reproduce the published result, then the manuscript should stay on the published numbers and move the current baseline artifacts to supplement or appendix material.

If the intent is to present the new Python baseline as the paper's actual computational result, then the manuscript must explain the numerical differences explicitly and consistently, not only in a side note. A paper cannot simultaneously cite the old result as authoritative and showcase new figures whose values and component counts differ.

### 3) The manuscript is still too internal to the repository

The draft repeatedly refers to code files, committed outputs, and repo-local directories. That is appropriate in developer notes, but it is too visible in the main paper text.

Examples of repo-internal phrasing that should be reduced or moved out of the main manuscript:

- direct links to `../metabolite_learner/workflow.py`, `../metabolite_learner/pls.py`, and similar implementation files
- "current repository baseline"
- "staged baseline dataset"
- "committed figure"
- "source of record"
- "workspace"
- explanations of what is "visible in code"

These phrases make the paper feel like documentation for maintainers instead of a scientific narrative for readers.

The manuscript should instead use paper language:

- "analysis pipeline"
- "reference dataset"
- "reproducible implementation"
- "supplementary materials"
- "implementation details"

If file links are kept at all, they should be relegated to a reproducibility appendix or supplement, not the main body.

### 4) The methods are not yet specific enough for external evaluation

The Methods section is more concrete than the abstract or results, but it still leaves too much implicit for a first-time reader.

The missing or under-specified items are:

- the exact sample inclusion/exclusion logic
- the statistical threshold used for peak filtering
- the ANOVA-style test details
- the mixed-effects model formula used for fold-change estimation
- how normalization is performed before the learner fits
- the exact cross-validation protocol, including folds, randomization, and how the one-standard-error rule is applied
- the shuffle test procedure, including what is randomized, how many repeats are run, and what null summary is reported
- whether any multiple-testing correction is applied anywhere

The current prose often says that the code "makes things visible" or that the published paper described something "at a high level." That is not enough for a manuscript. If the paper is meant to stand alone, then the methods section needs enough detail that a reader could reimplement the analysis without opening the repository.

A stronger paper would add either:

- a concise algorithm box or workflow schematic, or
- a compact table of modeling assumptions, thresholds, and outputs.

### 5) The results section is organized around workflow plumbing, not scientific findings

The results narrative is understandable, but it is still too close to a run log. It spends a lot of time telling the reader where files live and how the code mirrors the original pipeline.

What is missing is a more explicit results story:

- What is the main empirical finding?
- How large is the effect?
- How stable is it across resampling?
- What does the model get wrong?
- Which parts of the signal survive scrutiny, and which do not?

At present, the section mostly says that the learner can be run, that the figures exist, and that the current baseline resembles the historical result. That is not enough for a research paper.

The results would be stronger if they were reorganized into a tighter sequence:

- dataset construction
- predictive performance
- latent structure
- interpretability
- negative controls or failure analysis

The current text mentions shuffle testing and interpretability, but it does not yet use them to answer a stronger scientific question about robustness or generalization.

### 6) The figures need serious revision before this can read as a paper

The current figures are useful as internal diagnostics, but they are not publication-ready.

Figure-level issues:

- `paper/03_results.md` Figure 1 is crowded and looks like a development diagnostic. Its title embeds a specific correlation and p-value that are tied to the current baseline, while the surrounding text still frames the published five-component result as the source of record.
- `paper/03_results.md` Figure 3 is especially problematic. It is visually overloaded, the labels are cramped, and the lower panels appear empty or redundant in the current baseline image. That makes the figure look like a template that was not rebuilt for the present result set.
- `paper/03_results.md` Figure 2 is too schematic and does not anchor the variance-explained story strongly enough on its own. It needs clearer annotation and probably a more careful layout if it is meant to carry a central result.
- Captions currently explain repository status more than scientific meaning. A manuscript caption should stand on its own without saying that the figure is a "repository analogue" or a "committed rendering."

Specific figure concerns that should be addressed:

- reduce label density and enlarge typography for print
- remove empty panels or replace them with content that matches the selected model complexity
- ensure the component count shown in the figure matches the count discussed in text
- avoid putting unpublished baseline numbers in a figure that is described as the published result
- consider separating predictive performance, variance explained, and interpretability into distinct figures or a cleaner multi-panel layout

### 7) Citations and bibliographic support are not ready

The draft cites the published paper via a PDF link, but it does not yet function like a manuscript with a bibliography.

Missing pieces include:

- formal citations for metabolomics context and prior work
- citations for PLSR/SIMPLS or the implementation choices being described
- citations for GC/MS fragmentation interpretation
- citations for any claims about derivatization constraints, synchronized measurements, or orthogonal validation

Without a bibliography, the prose reads as unsupported narrative. This is especially important because the draft makes several interpretive claims about what the model learns, what it does not learn, and how it should be used in future workflows.

### 8) The discussion is directionally good but still too generic

The discussion correctly emphasizes that fragmentation-space learning is not a replacement for chemical identification. That is the right framing. But it still reads as a broad positioning statement rather than a paper discussion.

What it needs:

- a clearer statement of the boundary of inference
- a direct accounting of failure modes
- a stronger explanation of when the method should not be trusted
- a more specific comparison to identification-first metabolomics workflows
- a tighter bridge from the current result set to the proposed 2.0 agenda

At the moment, the discussion mostly says that the model is useful as an intermediate layer. That is plausible, but it is not yet argued with enough evidence.

## What Would Make This a Stronger Paper

- Decide whether the paper is a historical reproduction, a reproducibility note, or a new 2.0 scientific result, and write every section to that one purpose.
- Remove repo-internal scaffolding from the main text and move implementation pointers to supplemental material.
- Add a real bibliography and cite the relevant metabolomics, PLSR, and EI fragmentation literature.
- Present one consistent result set with one consistent set of numbers, or explicitly compare the published result against the current implementation with a table of differences.
- Rebuild the figures for print clarity and make sure every panel supports one claim.
- Add robustness and failure analysis so the manuscript can say not just that the signal exists, but when it is stable, when it breaks, and what that means biologically.

## Bottom Line

The technical idea is solid, and the draft has enough structure to become a paper. But in its current form it is still too close to internal notes and too split between "old result," "current baseline," and "future 2.0" to be a coherent manuscript. The next revision should focus on narrowing the paper's claim, cleaning the figure set, and making the methods/results readable to someone who has never seen the repository.
