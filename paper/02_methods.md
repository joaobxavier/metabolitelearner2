# Methods

## Study design and data provenance

The study used the MDA-MB-231 breast cancer lineage system, including parental, lung-homing, brain-homing, and blank-media conditions, to ask whether electron ionization (EI) fragmentation spectra alone can predict metabolite-level rewiring [10]. Cells were cultured in triplicate groups over three days, yielding 36 samples in total.

MetaboLiteLearner was designed to learn from fragmentation structure rather than from prior compound identification or curated pathway annotation. In that framing, each detected metabolite becomes a supervised-learning example, and the response is a pair of log2 fold changes describing abundance shifts in brain-homing and lung-homing cells relative to the parental lineage.

## Cell culture, extraction, and GC/MS acquisition

The published experiments used standard DMEM-based culture conditions at 37 C in 5% CO2. Metabolites were extracted with ice-cold 80% methanol, dried, reconstituted in methoxyamine hydrochloride in pyridine, and derivatized with N-methyl-N-(trimethylsilyl) trifluoroacetamide, with ethyl acetate as the final solvent. This methoximation and trimethylsilylation workflow was used to improve volatility and produce reproducible EI fragmentation patterns [9, 10].

GC/MS analysis was performed on an Agilent 7890A gas chromatograph coupled to an Agilent 5977C mass selective detector. Samples were injected in splitless mode, 1 microliter per run, onto an HP-5ms column with helium flow at 1 ml/min. The oven temperature ramped from 60 C to 290 C over 25 minutes, following the Agilent Fiehn method protocol [8, 10]. Data were acquired in scan mode so that the full fragmentation pattern, rather than selected ions alone, could be used downstream.

## Peak detection and dataset construction

Raw scan-mode matrices were aligned to a common retention-time grid from 6.00 to 30.00 minutes at 0.01-minute increments and an m/z grid from 50 to 600 at unit intervals. Peak detection was performed directly on a virtual bulk sample built from the combined GC/MS signal, using the MATLAB `mspeaks` routine and no deconvolution step. The spectra of detected peaks were then extracted and their peak areas calculated for each sample.

Peak areas were summarized in a peak table and filtered by analysis of variance on log peak areas across parental, brain-homing, lung-homing, and media groups. Peaks passing a nominal threshold of P < 0.05 were retained, and media samples were then removed from downstream modeling. This yielded the MetaboLiteLearner Open Dataset, or MLOD: 153 unique spectra paired with log2 fold-change labels for brain-homing and lung-homing cells. Each spectrum was encoded as a 550-dimensional EI feature vector spanning m/z 50 to 600. No additional multiple-testing correction was reported at this filtering stage [10].

## Spectral representation for learning

Each retained spectrum was normalized to unit norm before modeling so that the learner focused on spectral shape rather than absolute ionization intensity. The predictor matrix therefore consisted of normalized EI fragmentation vectors, while the response matrix contained the corresponding two-dimensional fold-change labels. This representation preserves the structural information carried by the fragmentation pattern and keeps the learning problem tied directly to measured chemistry.

Within the parental, brain-homing, and lung-homing samples, log peak areas were rescaled with a linear mixed-effects model containing peak-specific fixed effects, a sample-level grouping term, and a peak-by-batch variance component. Fold changes were then estimated from peak-by-cell interaction terms in a second mixed-effects model of the form `area ~ 0 + peak + peak:cell`, again accounting for sample-level and peak-by-batch structure. Coefficients and confidence intervals were expressed on a log2 scale.

## Partial least squares regression

The published model used partial least squares regression (PLSR), implemented through MATLAB `plsregress`, to map the 550-dimensional spectral input onto the two-dimensional fold-change response [5, 6]. PLSR was chosen because it reduces dimensionality while retaining the covariance structure between spectra and abundance shifts. In the manuscript, the latent components are interpreted as compact directions in which fragmentation structure and rewiring behavior co-vary.

## Component selection and validation

Model complexity was chosen by leave-one-out cross-validation across 1 to 30 latent components. Training error decreased monotonically with additional components, while test error reached its minimum at 11 components before increasing again. Applying the one-standard-error rule, the published analysis selected a five-component model as the preferred operating point.

The study also included a permutation control with 1,000 randomized label assignments. This shuffle test preserved internal response correlations but broke the link between spectra and fold-change labels, providing a direct chance-level comparison for the learned relationship. Prediction error under shuffled labels was consistently worse than error on the original data.

## Interpretability outputs

Interpretability was central to the method, not an afterthought. Fragment loadings were examined to identify ions associated with shared increases or decreases across the metastatic lineages, and KEGG/Fiehn reference spectra were projected into the learned latent space to relate model structure to known compound classes [7, 8]. Those projections were used to interpret the latent components biologically, rather than to assign definitive metabolite identities.

## Reproducibility note

A reproducible Python implementation of the analysis pipeline is available in [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) and [../metabolite_learner/pls.py](../metabolite_learner/pls.py). The methods narrative above follows the published study, while the linked implementation provides the executable starting point for the 2.0 development program.
