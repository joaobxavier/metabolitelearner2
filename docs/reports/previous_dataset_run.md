# Previous Dataset Run Report

## Scope

This report records a full local integration run of `metabolitelearner2` against the original study dataset, using the new default `joint-components` extractor and the staged `data/original_study/` workspace.

Relevant tracked files:

- [`scripts/stage_previous_dataset.sh`](../../scripts/stage_previous_dataset.sh)
- [`docs/reproducibility.md`](../reproducibility.md)
- [`metabolite_learner/workflow.py`](../../metabolite_learner/workflow.py)
- [`metabolite_learner/joint_extract.py`](../../metabolite_learner/joint_extract.py)
- [`metabolite_learner/pls.py`](../../metabolite_learner/pls.py)

## Environment

- Date: `2026-03-23`
- Repo: `metabolitelearner2`
- Python: `3.14.3`
- Environment path: `~/dev/venvs/metabolitelearner2`
- Install mode: editable install from the local repo

## Data Staging

Dataset staging used:

```bash
./scripts/stage_previous_dataset.sh
```

Observed local result:

- staged root: `data/original_study`
- matrix CSV inputs: `36`
- KEGG reference files: `2`
- source used during staging: existing local checkout at `/Users/jxavier/dev/metaboliteLearner`

The script is written so that it can also download `gcmsCSVs/` and `kegg/` from the original GitHub repo when that local source checkout is not available.

## Workflow Command

```bash
source ~/dev/venvs/metabolitelearner2/bin/activate
metabolitelearner2 run-workflow \
  --gcms-csv-dir data/original_study/gcmsCSVs \
  --extracted-peaks-dir data/original_study/extractedPeaks \
  --folds-dir data/original_study/folds \
  --kegg-mat-path data/original_study/kegg/keggCompoundsWithFiehlibSpectrum.mat \
  --regenerate-peaks
```

## Outcome

The run completed successfully.

- extracted component rows: `12`
- extracted component spectra rows: `12`
- fold-change peaks: `12`
- selected latent components: `4`

Primary local outputs:

- [`data/original_study/extractedPeaks/tblTicPeaks.csv`](../../data/original_study/extractedPeaks/tblTicPeaks.csv)
- [`data/original_study/extractedPeaks/tblComponents.csv`](../../data/original_study/extractedPeaks/tblComponents.csv)
- [`data/original_study/extractedPeaks/tblPeaksIntegrated.csv`](../../data/original_study/extractedPeaks/tblPeaksIntegrated.csv)
- [`data/original_study/extractedPeaks/tblComponentAbundance.csv`](../../data/original_study/extractedPeaks/tblComponentAbundance.csv)
- [`data/original_study/extractedPeaks/tblSpectra.csv`](../../data/original_study/extractedPeaks/tblSpectra.csv)
- [`data/original_study/extractedPeaks/tblComponentSpectra.csv`](../../data/original_study/extractedPeaks/tblComponentSpectra.csv)
- [`data/original_study/extractedPeaks/tblComponentEffects.csv`](../../data/original_study/extractedPeaks/tblComponentEffects.csv)
- [`data/original_study/extractedPeaks/tblComponentLibraryMatches.csv`](../../data/original_study/extractedPeaks/tblComponentLibraryMatches.csv)
- [`data/original_study/folds/peakFoldChanges.csv`](../../data/original_study/folds/peakFoldChanges.csv)
- [`data/original_study/folds/figure_1.png`](../../data/original_study/folds/figure_1.png)
- [`data/original_study/folds/figure_2.png`](../../data/original_study/folds/figure_2.png)
- [`data/original_study/folds/figure_3.png`](../../data/original_study/folds/figure_3.png)
- [`data/original_study/folds/learner_diagnostics.png`](../../data/original_study/folds/learner_diagnostics.png)
- [`data/original_study/folds/variance_explained.png`](../../data/original_study/folds/variance_explained.png)
- [`data/original_study/folds/loadings.png`](../../data/original_study/folds/loadings.png)
- local run log: `data/original_study/run_workflow.log`

Selected summary statistics from `peakFoldChanges.csv`:

- mean `B`: `0.08705576216982457`
- mean `L`: `0.10861749082731065`
- peaks with `|B| > 1`: `6`
- peaks with `|L| > 1`: `5`

Selected summary statistics from `tblComponents.csv`:

- component rows: `12`
- median `supervisionR2`: approximately `0.99`
- strongest library matches are predominantly `Carbohydrates` and `Organic acids`

## Warnings Observed

The run emitted warnings but still finished and wrote all expected outputs:

- `statsmodels` `ConvergenceWarning`: Hessian not positive definite

This warning remains in the downstream mixed-model stage and does not indicate a hard failure in this run.

## Validation of the 2.0 Extractor Path

This run validates the new algorithmic path rather than exact equivalence to the historical Python extractor.

Result:

- the new joint extractor completed end to end on the staged dataset
- compatibility outputs were written in the expected legacy locations
- new 2.0 component-level outputs were also written alongside them
- the downstream mixed-model and PLS stages remained operational without code changes to their core logic

## Conclusion

The integration run succeeded.

`metabolitelearner2` can now:

- stage the original study inputs into the repo-local ignored `data/` workspace,
- run the full workflow end to end with a joint component extractor,
- preserve compatibility with the downstream fold-change and learner stages,
- and emit richer component-level outputs for 2.0 development.

The main remaining caveat is methodological rather than operational: the joint extractor currently tends to split some dominant chromatographic regions into multiple closely related components, so component-merging or diversity regularization is a likely next improvement.
