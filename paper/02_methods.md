# Methods

## Study design and data provenance

This companion implementation follows the published MetaboLiteLearner workflow for predicting metabolite abundance changes from electron ionization (EI) fragmentation spectra in gas chromatography/mass spectrometry (GC/MS) scan-mode data. The original manuscript used an MDA-MB-231 lineage model with parental, lung-homing, brain-homing, and blank-media conditions, and the staged baseline dataset in this repository mirrors that experimental structure under [../data/original_study](../data/original_study). That directory contains processed matrix CSVs, extracted peak tables, fold-change outputs, and the KEGG/Fiehn reference material used for downstream interpretation.

In the published paper, MetaboLiteLearner was framed as a lightweight supervised-learning pipeline that uses the fragmentation spectrum itself as the predictor representation, rather than requiring prior compound identification or metabolic-network annotation. The current repository expresses that same workflow in Python, with the command-line entry points in [../metabolite_learner/cli.py](../metabolite_learner/cli.py) dispatching the main steps implemented in [../metabolite_learner/agilent.py](../metabolite_learner/agilent.py), [../metabolite_learner/extract.py](../metabolite_learner/extract.py), [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py), and [../metabolite_learner/pls.py](../metabolite_learner/pls.py).

## Raw data ingestion and matrix construction

The published workflow begins with Agilent GC/MS data in vendor `.D` directories, which are converted into CSV matrices before any learning is performed. In the Python port, this step is implemented in [../metabolite_learner/agilent.py](../metabolite_learner/agilent.py). The loader reconstructs each scan into a fixed two-dimensional matrix spanning retention time and m/z bins, using a time grid from 6.00 to 30.00 minutes at 0.01-minute resolution and an m/z grid from 50 to 599 at unit resolution. This produces the same fixed-shape representation expected by the downstream extractor.

When raw Agilent directories are not available, the implementation also accepts precomputed matrix CSVs or TIC-front exports, which is how the staged baseline dataset is packaged in [../data/original_study/gcmsCSVs](../data/original_study/gcmsCSVs). The conversion step is exposed as `convert-agilent` in [../metabolite_learner/cli.py](../metabolite_learner/cli.py), and it writes one matrix CSV per sample. This matches the manuscript's emphasis on a reproducible preprocessing boundary between vendor data and analysis-ready arrays.

## Peak detection and spectrum extraction

The manuscript describes a "virtual bulk sample" built from the full GC/MS matrix, with peak detection performed directly on that aggregate signal and without a deconvolution stage. The Python implementation in [../metabolite_learner/extract.py](../metabolite_learner/extract.py) follows the same design. It first sums each matrix across m/z to form a total-ion-chromatogram-like trace for every sample, then adds those traces to produce a bulk TIC over which peaks are detected with `scipy.signal.find_peaks`.

Detected peaks are expanded to half-height boundaries with `peak_widths`, and each peak window is then integrated across every sample matrix. The extractor writes three manuscript-facing tables to the output directory: `tblTicPeaks.csv`, `tblPeaksIntegrated.csv`, and `tblSpectra.csv`. These correspond to the peak boundary table, the integrated peak area table, and the summed spectral representation used for learning. The repository's staged baseline outputs under [../data/original_study/extractedPeaks](../data/original_study/extractedPeaks) reflect this exact intermediate structure.

This step is the Python expression of the manuscript's "no deconvolution" choice. Rather than splitting coeluting signals into putative compounds, the workflow retains the integrated peak windows and their summed EI spectra, which keeps the representation close to the measured data and avoids dependence on library matching at this stage.

## Peak filtering and fold-change estimation

After extraction, the published paper filters peaks that do not differ meaningfully from blank-media controls and then estimates log2 fold changes for the remaining peaks in brain-homing and lung-homing cells relative to the parental lineage. The repository implements this part of the pipeline in [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py), where the extracted peak areas are first screened by an ANOVA-style test and then passed into mixed-effects models for fold-change estimation.

Concretely, the Python workflow reshapes the integrated peak table into long format, logs peak areas, and assigns each sample to a cell-type label derived from the sample name. It then fits a scaling model and a fold-change model with `statsmodels` mixed linear models. The resulting coefficients are converted into a peak-level table of estimated brain-homing and lung-homing log2 fold changes, with confidence intervals and p-values, and written to [../data/original_study/folds/peakFoldChanges.csv](../data/original_study/folds/peakFoldChanges.csv) in the staged baseline dataset.

This is the one place where the current repository is more explicit than the prose in the published paper: the manuscript describes the statistical filtering and fold-change estimation at a higher level, whereas the Python implementation makes the intermediate normalization and mixed-effects structure visible. The scientific intent is the same, but the code documents the computation more transparently.

## Spectral representation for learning

MetaboLiteLearner treats each metabolite or peak as a predictor vector derived from its EI spectrum. In the manuscript, the spectrum is binned into 550 features corresponding to fragments from m/z 50 to 600, and the learner is asked to predict the pair of fold-change responses for the two metastatic lineages. The repository follows this representation directly: [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) selects the matched spectra for peaks that survived filtering, converts the spectral rows into NumPy arrays, and normalizes each spectrum to unit norm before fitting the learner.

The normalization step is important because it keeps the model focused on spectral shape rather than absolute abundance alone. That is consistent with the manuscript's description of using the EI fragmentation pattern as the input feature set. The staged baseline spectra in [../data/original_study/extractedPeaks/tblSpectra.csv](../data/original_study/extractedPeaks/tblSpectra.csv) provide the repository's reference input for this stage.

## Learner architecture

The published paper uses partial least squares regression (PLSR) to relate the 550-dimensional spectral input to the two-dimensional output of brain-homing and lung-homing fold changes. The Python implementation of that learner is in [../metabolite_learner/pls.py](../metabolite_learner/pls.py), where `MetaboLiteLearner` provides a SIMPLS-style PLS model with centering, latent scores, loadings, and a regression matrix that matches the MATLAB `plsregress` workflow described in the manuscript.

The learner stores both the fitted model and the derived coefficients, and it exposes a `map_to_latent_space` method for projecting new spectra into the latent space. This is used later in the workflow to visualize how KEGG and Fiehn reference spectra align with the learned latent components. In the manuscript, these latent factors are presented as a compact representation of the association between fragmentation structure and metabolic rewiring; in the Python repo, the same interpretation is retained, but the implementation details are visible in code.

## Latent-component selection and validation

The manuscript selected the number of latent components by cross-validation, optimizing prediction error while avoiding overfitting in a small-sample, high-dimensional setting. The repository makes this explicit in [../metabolite_learner/pls.py](../metabolite_learner/pls.py): `MetaboLiteLearner` performs component-wise cross-validation, records training and test mean-squared error, and chooses an operating component count from the error curve. When `kfold` is left at its default of zero, the implementation uses leave-one-out behavior; other fold counts can be set through the workflow entry point in [../metabolite_learner/cli.py](../metabolite_learner/cli.py).

The published study also included a permutation or shuffling test with 1,000 randomized label assignments to ensure the learned relationship was not a chance artifact. The Python implementation preserves that check through the `nrandomized` parameter and the `shuffling_test()` method in [../metabolite_learner/pls.py](../metabolite_learner/pls.py). In the full workflow, this diagnostic is surfaced through [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) and can be enabled from the CLI.

## Interpretability outputs

The paper emphasizes that the model should remain interpretable, not just predictive. The repository implements that requirement in two ways. First, [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) exports fold-change tables and generates diagnostic plots for the learned model, including mean-squared-error curves, observed-versus-predicted scatter plots, and variance-explained summaries. These outputs are written under [../data/original_study/folds](../data/original_study/folds) in the baseline dataset.

Second, the workflow projects reference compound spectra from the KEGG/Fiehn resources into the latent space to help interpret what the model has learned. The implementation reads the reference material from [../data/original_study/kegg/keggCompoundsWithFiehlibSpectrum.mat](../data/original_study/kegg/keggCompoundsWithFiehlibSpectrum.mat), excludes broad classes that were not useful in the original MATLAB analysis, and plots how those reference spectra distribute across latent components. This mirrors the manuscript's use of loadings and reference spectra as a bridge from prediction back to biology.

## Reproducibility and workflow entry points

The current repository expresses the full analysis as a reproducible Python workflow. The top-level command-line interface in [../metabolite_learner/cli.py](../metabolite_learner/cli.py) exposes three steps: Agilent conversion, peak extraction, and the end-to-end workflow run. The full pipeline in [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) can regenerate extracted peaks, fit fold-change models, train the PLS learner, and write the manuscript figures and tables in a single pass.

For this companion paper, the staged baseline data under [../data/original_study](../data/original_study) should be treated as the repository's baseline execution of the workflow, not as a claim that every currently committed output is numerically identical to the figures in the 2024 publication. The goal is to keep the computational steps auditable in Python while preserving the published method sequence and its interpretation.
