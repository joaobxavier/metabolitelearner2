# Results

This section follows the published 2024 MetaboLiteLearner results [10]. Because the manuscript is being developed as a reproducibility-first restatement of that study, the distinction between the published claim set and the current Python reimplementation is stated explicitly before the figures.

| Quantity | Published 2024 study | Reproducible Python reimplementation |
| --- | --- | --- |
| Spectra retained after filtering | 153 | 125 |
| Selected latent components | 5 | 3 |
| Role in this draft | Scientific claims reported in the text | Supporting figure rendering and implementation reference |

The quantitative claims below report the published study. The embedded figures are reproducible renderings of the corresponding analysis stages and are included to give the manuscript stable visual support while the 2.0 experiments are still being developed.

## The MetaboLiteLearner Open Dataset

The central result of the published workflow was the construction of the MetaboLiteLearner Open Dataset from GC/MS scan-mode data without requiring prior metabolite identification or deconvolution. From the MDA-MB-231 parental, brain-homing, lung-homing, and blank-media conditions, the preprocessing pipeline yielded 153 unique spectra paired with log2 fold-change labels for brain-homing and lung-homing cells relative to the parental lineage [10].

That change in unit of analysis is the key result of the workflow. Instead of treating each biological sample as a single supervised example, MetaboLiteLearner treats each metabolite spectrum as a data point. The 36-sample experiment is therefore expanded into a metabolite-centered dataset that retains the measured EI fragmentation structure while making the prediction task tractable.

## Predictive performance and component selection

Cross-validation across 1 to 30 latent components showed the expected bias-variance tradeoff. Training error decreased monotonically as components were added, while test error reached a minimum at 11 components before rising again. Using the one-standard-error rule, the published analysis selected a five-component operating model.

That five-component model achieved a correlation of rho = 0.39 between predicted and observed log2 fold changes, with P <= 0.01. The shuffle control reinforced that this was not a chance-level association: when the fold-change labels were randomized 1,000 times, prediction error was consistently worse than on the original data.

![Model-selection and prediction diagnostics.](figures/figure_1_predictive_performance.png)

*Figure 1. Model-selection and prediction diagnostics. The panel shows training and cross-validation error across latent components together with observed-versus-predicted fold-change plots. The scientific interpretation in the text follows the published five-component analysis, while the rendering shown here is a reproducible implementation of the same evaluation logic.*

## Variance explained and latent structure

The five-component model trained on the full published dataset explained 32% of the predictor variance and 68% of the response variance. That asymmetry is important: the model preserves only a modest fraction of the raw spectral variance, yet it captures most of the variance in the biologically relevant response space.

The latent structure was also interpretable. Components 1 and 3 corresponded to metabolites that decreased in both organ-homing lineages, whereas components 2 and 5 captured metabolites that increased in both. Component 1 accounted for 27% of the response variance, while component 4 accounted for just 4.9%, yet still separated brain-homing from lung-homing behavior rather than summarizing a shared shift. In the manuscript, that component-level decomposition was the main reason the model could be described as both predictive and biologically informative.

![Variance explained by latent components.](figures/figure_2_variance_explained.png)

*Figure 2. Variance explained by latent components in predictor and response space. The figure illustrates the asymmetry between spectral variance retained in X and biologically relevant variance captured in Y. The numerical variance summary discussed in the text follows the published analysis.*

## Fragment-level interpretation

The biplot of fragment coefficients gave the first biochemical clues. The published analysis highlighted m/z 104 as a fragment associated with increases in both cell types and m/z 306 as a fragment associated with decreases. These were interpreted as structural signatures, not direct metabolite identifications.

Reference-spectrum projections extended that interpretation. A curated set of 263 KEGG and Fiehn reference spectra projected into the latent space suggested that many metabolites changed in the same direction across both metastatic lineages, while carbohydrates and nucleic-acid-related compounds were more strongly associated with lung-specific increases. Within the latent decomposition, amino acids largely followed the shared-decrease trend captured by component 1, whereas carbohydrates and deoxyribonucleosides contributed more strongly to the lineage-separating component 4.

![Fragment-level and reference-projection interpretation figure.](figures/figure_3_interpretability.png)

*Figure 3. Fragment-level and reference-projection interpretation. The left panels summarize fragment coefficients and latent-component orientation in fold-change space, while the right panels show class-level distributions for projected KEGG/Fiehn reference spectra. The layout shown here is restricted to the latent components retained in the reproducible Python implementation so that the interpretability panels remain readable and non-empty.*

## Chance control and interpretation boundary

The shuffle test is the right boundary for interpretation. It shows that MetaboLiteLearner recovered more than an arbitrary correlation structure, because randomized fold-change labels consistently produced worse prediction error. At the same time, the model does not prove mechanism on its own. The learned latent components summarize covariance between fragmentation patterns and rewiring labels, which makes them useful for prioritization and hypothesis generation, but not sufficient for pathway assignment without follow-up chemistry.

Taken together, the published results show that EI fragmentation spectra can carry enough structure to predict metabolite-level rewiring in a small, unidentified metabolomics dataset, and that the resulting latent space contains both shared and lineage-specific signals relevant to metastatic adaptation [10].

## Reproducibility note

The executable workflow that generated the renderings used here is implemented in [../metabolite_learner/workflow.py](../metabolite_learner/workflow.py) and [../metabolite_learner/pls.py](../metabolite_learner/pls.py). The manuscript figure assets are [figures/figure_1_predictive_performance.png](figures/figure_1_predictive_performance.png), [figures/figure_2_variance_explained.png](figures/figure_2_variance_explained.png), and [figures/figure_3_interpretability.png](figures/figure_3_interpretability.png).
