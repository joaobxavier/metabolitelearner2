# Research Positioning

## Core Thesis

MetaboLiteLearner 2.0 is built around the claim that **fragmentation structure alone can recover biologically useful signal about metabolic rewiring**.

That claim is narrower than “spectra are enough to identify metabolites” and stronger than “spectra contain some statistical information.” The working position is:

- electron-impact fragmentation patterns encode structural regularities,
- structural regularities correlate with how metabolites participate in adaptive metabolic programs,
- and a supervised model can exploit those regularities even when metabolite identification is incomplete.

## What 2.0 Should Improve

Relative to the original implementation, 2.0 should aim to improve:

- reproducibility,
- benchmark design,
- model interpretability,
- experiment hygiene,
- and paper-level articulation of what the method can and cannot claim biologically.

## Scientific Boundaries

The project should avoid overclaiming:

- peak-level predictions are not automatically metabolite-level mechanistic conclusions,
- good predictive signal does not imply direct biochemical causality,
- and identification-free learning should be presented as complementary to annotation, not a replacement for it.

## Desired Paper Contribution

The companion paper should not merely present another software port. It should argue, with evidence, that fragmentation-space learning is a principled and useful representation for studying metabolic adaptation.
