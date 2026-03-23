# Abstract

Metabolic rewiring enables cells to adapt to changes in nutrients, tissue context, and stress, yet metabolomics is still often organized around identification rather than prediction. Here we ask whether electron ionization fragmentation patterns already contain enough structure to predict how metabolites change across rewired cell states, even before complete annotation is available.

MetaboLiteLearner represents gas chromatography-mass spectrometry scan-mode spectra as a 550-dimensional feature vector and uses partial least squares regression to predict log2 fold changes in brain-homing and lung-homing derivatives of the MDA-MB-231 breast cancer line. In the published study, the model was trained on 153 unique spectra from the MetaboLiteLearner Open Dataset and evaluated without requiring prior metabolite identification or a curated metabolic network.

The model recovered both shared and lineage-specific signals associated with metastatic rewiring, including a component that distinguished brain-homing from lung-homing patterns. Shuffle controls indicated that the learned associations exceeded chance structure. These results show that fragmentation spectra can carry predictive information about metabolite behavior and can support downstream biological interpretation before full chemical identification is complete.
