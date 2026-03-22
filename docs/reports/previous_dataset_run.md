# Previous Dataset Run Report

## Scope

This report records a full local integration run of `metabolitelearner2` against the original study dataset, with the required inputs staged under the repo's gitignored `data/` workspace.

Relevant tracked files:

- [`scripts/stage_previous_dataset.sh`](../../scripts/stage_previous_dataset.sh)
- [`docs/reproducibility.md`](../reproducibility.md)
- [`metabolite_learner/workflow.py`](../../metabolite_learner/workflow.py)
- [`metabolite_learner/extract.py`](../../metabolite_learner/extract.py)
- [`metabolite_learner/pls.py`](../../metabolite_learner/pls.py)

## Environment

- Date: `2026-03-22`
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

- runtime: `38.42 s`
- extracted TIC peaks: `195`
- extracted peak-integrated rows: `195`
- extracted spectra rows: `195`
- fold-change peaks: `125`
- selected latent components: `3`

Primary local outputs:

- [`data/original_study/extractedPeaks/tblTicPeaks.csv`](../../data/original_study/extractedPeaks/tblTicPeaks.csv)
- [`data/original_study/extractedPeaks/tblPeaksIntegrated.csv`](../../data/original_study/extractedPeaks/tblPeaksIntegrated.csv)
- [`data/original_study/extractedPeaks/tblSpectra.csv`](../../data/original_study/extractedPeaks/tblSpectra.csv)
- [`data/original_study/folds/peakFoldChanges.csv`](../../data/original_study/folds/peakFoldChanges.csv)
- [`data/original_study/folds/figure_1.png`](../../data/original_study/folds/figure_1.png)
- [`data/original_study/folds/figure_2.png`](../../data/original_study/folds/figure_2.png)
- [`data/original_study/folds/figure_3.png`](../../data/original_study/folds/figure_3.png)
- [`data/original_study/folds/learner_diagnostics.png`](../../data/original_study/folds/learner_diagnostics.png)
- [`data/original_study/folds/variance_explained.png`](../../data/original_study/folds/variance_explained.png)
- [`data/original_study/folds/loadings.png`](../../data/original_study/folds/loadings.png)
- local run log: `data/original_study/run_workflow.log`

Selected summary statistics from `peakFoldChanges.csv`:

- mean `B`: `-0.210939157475332`
- mean `L`: `-0.10726799565656908`
- peaks with `|B| > 1`: `4`
- peaks with `|L| > 1`: `6`

## Warnings Observed

The run emitted warnings but still finished and wrote all expected outputs:

- `numpy.linalg.slogdet` runtime warnings: divide-by-zero, overflow, and invalid-value cases during mixed-model fitting
- `statsmodels` `ConvergenceWarning`: Hessian not positive definite

These warnings are already familiar from the original Python workflow line and do not indicate a hard failure in this run.

## Validation Against the Original Repo's Current Python Code

To verify that `metabolitelearner2` was not introducing a behavioral regression, the same workflow was rerun from the original repo's current Python code into `/tmp/old_current_run`.

Result:

- `metabolitelearner2` output matched the original repo's current Python output exactly
- `peakFoldChanges.csv` equality: exact
- generated figure hashes: exact
- extracted-peak table hashes: exact

SHA-256 matches for representative outputs:

- `tblTicPeaks.csv`: `75be48bf43a7175afcca9c4982d884d376bbc4366eac57ec998621008f0c17f3`
- `tblPeaksIntegrated.csv`: `cfac51a8b85abb5f229e7844eebe14ec43f34bc705125ffc26691e9f936e284b`
- `tblSpectra.csv`: `4cbdb97cf8841d2f0154f25a1a19de34701844bcaf384251ea43baaf7db80a7c`
- `peakFoldChanges.csv`: `81bee732ce940c70220eccf293f0422d34faa36fc7ea52f0d489425e9db9e297`
- `figure_1.png`: `a00006a0f411cbac10fa32a7b250281696748724054ecf6c2a4b660b17fcd624`
- `figure_2.png`: `3b43cce8420d44ca56139e6aa8c2e64fc4bd8709c2045079273de06d3d08eca6`
- `figure_3.png`: `37afca0117027476b1de5b063df76442856f1a076dea2244b032d94a30177704`

## Legacy Artifact Drift in the Original Repo

The checked-in historical outputs in `/Users/jxavier/dev/metaboliteLearner` do not match the current Python code when rerun from scratch.

Observed drift:

- checked-in `extractedPeaks/tblPeaksIntegrated.csv`: `236` rows
- current rerun output: `195` rows
- checked-in `folds/peakFoldChanges.csv`: `153` rows
- current rerun output: `125` rows

Interpretation:

- `metabolitelearner2` is reproducing the original repo's current Python implementation correctly
- the old repo's committed workflow artifacts appear stale relative to the present Python code path
- those legacy checked-in files should not be used as the current regression baseline without being refreshed

## Conclusion

The integration run succeeded.

`metabolitelearner2` can now:

- stage the original study inputs into the repo-local ignored `data/` workspace,
- run the full Python workflow end to end on that dataset,
- and reproduce the original repo's current Python outputs exactly.

The only material caveat from this run is not in `metabolitelearner2` itself: the historical committed outputs in the original repo are out of sync with the current Python implementation and should be treated as stale artifacts.
