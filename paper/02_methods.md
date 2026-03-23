# Methods

## Study system and assay context

MetaboLiteLearner 2.0 was evaluated on the MDA-MB-231 parental, brain-homing, lung-homing, and media benchmark introduced in the original MetaboLiteLearner study [10]. The design preserved the original triplicate-over-three-days structure and therefore retained the same biological contrast while allowing the analysis pipeline itself to change. This study system remains useful because it is small enough to inspect component by component, but rich enough to expose the consequences of different representation choices.

Cells were grown under standard DMEM conditions, extracted in cold methanol, derivatized by methoximation followed by trimethylsilylation, and analyzed by GC/MS in scan-mode electron ionization [8-10]. The chemistry is unchanged from the earlier study. What changes in 2.0 is how the aligned assay matrices are represented before fold-change estimation and learning.

## Aligned GC/MS matrices

Each sample was represented as an aligned matrix defined on a fixed retention-time grid from 6.00 to 30.00 minutes at 0.01-minute intervals and an m/z grid from 50 to 599. Unlike the earlier peak-window workflow, the 2.0 pipeline does not begin by detecting a bulk total-ion-current peak list. Instead, the sample matrices are retained as the primary object of analysis so that chromatographic structure and fragmentation structure can be learned together.

For factorization, the sample tensor was unfolded into a sample-by-feature matrix in which each feature corresponds to a retention-time and m/z coordinate. This keeps the full assay signal available to the model while allowing nonnegative component learning to operate on a compact matrix form [11].

## Joint component extraction

The central methodological change in MetaboLiteLearner 2.0 is a supervised nonnegative matrix factorization stage. The unfolded GC/MS matrix is decomposed into sample-level weights and shared component maps under nonnegativity constraints. Sample weights are then shrunk toward the known study design, so that the extracted components remain aligned with parental, brain-homing, lung-homing, and media structure while still being learned from the data.

Each learned component map is converted into a chromatographic profile and an EI spectrum by a rank-1 nonnegative factorization of the map itself. In practice, this yields three coupled objects for every component:

1. a retention-time profile,
2. a fragmentation spectrum,
3. a sample-abundance vector.

The extracted components are written back into familiar metabolomics tables. Each row is summarized by a peak-like record containing its apex retention time, start and end boundaries, half-height width, reconstruction fraction, and supervision score. This gives the 2.0 workflow a direct bridge from learned factors to analyzable metabolomics objects without collapsing the signal into heuristic TIC windows at the start.

## Component abundance outputs and statistical filtering

The abundance vector for each learned component is the quantity passed to the downstream statistics. Component abundances are first screened by analysis of variance on log-scale abundances across parental, brain-homing, lung-homing, and media groups. Components passing a nominal threshold of `P < 0.05` are retained, and media samples are then removed from the fold-change stage. No additional multiple-testing correction is applied at this filter step in the current implementation.

This design makes the learned abundance matrix the central intermediate representation of the pipeline. It is the object tested for condition-specific behavior, the source of the fold-change response matrix, and the place where component-level interpretation remains tied to sample-level evidence.

## Mixed-model fold-change estimation

Retained component abundances are modeled on the log scale with mixed-effects regression. A scaling model accounts for component-specific baselines together with sample grouping and component-by-batch structure. Fold changes are then estimated in a second mixed model of the form `area ~ 0 + component + component:cell`, with parental samples as the reference condition. The resulting coefficients and confidence intervals are expressed on a log2 scale for brain-homing and lung-homing cells relative to the parental lineage.

The purpose of this stage is not merely inferential. It converts the output of the joint extractor into an effect-size table that can be read biologically and used as the response matrix for the supervised learner.

## Fragmentation-space learner

After fold-change estimation, component spectra are normalized to unit norm and paired with the two-dimensional fold-change response matrix. MetaboLiteLearner 2.0 then fits a partial least squares model using a SIMPLS-style formulation [5, 6]. This stage serves two purposes:

1. it provides a compact predictive map from fragmentation structure to abundance change,
2. it defines latent components whose loadings can be inspected directly.

Model size is selected by leave-one-out cross-validation across 1 to 30 latent components, with the operating point chosen by the one-standard-error rule relative to the minimum cross-validation error.

## Post hoc reference projection

Reference knowledge enters only after the data-driven representation has been learned. The extracted component spectra are compared post hoc with curated Fiehn and KEGG spectra [7-9]. These matches are used to contextualize components and latent directions, not to define the factorization itself. In that sense, the workflow is hybrid: component learning is GC/MS-data-driven, while library information is used only to interpret the learned objects after fitting.

## Reproducibility note

The executable pipeline described here is implemented in [../metabolite_learner/joint_extract.py](../metabolite_learner/joint_extract.py), [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py), and [../metabolite_learner/pls.py](../metabolite_learner/pls.py). The manuscript’s current result set is anchored to the staged run documented in [../docs/reports/previous_dataset_run.md](../docs/reports/previous_dataset_run.md).
