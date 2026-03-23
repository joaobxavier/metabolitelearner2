# Companion Paper Workspace

This directory now contains the first full Markdown draft for the MetaboLiteLearner 2.0 companion paper. The current text is intentionally written as a disciplined restatement of the published 2024 manuscript so the repo starts from a concrete prior version rather than from outline bullets alone.

## Current Structure

- `00_abstract.md`: startup abstract based on the published paper, with links to the source PDF and current baseline assets
- `01_introduction.md`: motivation, problem framing, and the representation-first argument
- `02_methods.md`: published workflow restated against the current Python implementation
- `03_results.md`: published results narrative, with the current repo baseline used as supporting infrastructure rather than as the source of scientific claims
- `04_discussion.md`: interpretation, limitations, and forward-looking positioning for 2.0
- `outline.md`: updated paper map showing how the current section files fit together
- `source_papers/`: archived source PDFs, including the published Methods paper
- `notes/`: supporting notes and future drafting material
- `figures/`: manuscript-specific figure assets to be added as the 2.0 paper evolves
- `bibliography/`: citation assets and future reference files

## Writing Principle

The current manuscript pass keeps two things separate:

1. the **published paper's claims**, which remain the source of record for the initial scientific narrative
2. the **current repository baseline**, which provides code paths, figures, and reproducible outputs that make that narrative auditable in Python

That separation is deliberate. The next drafting rounds can extend the claims only after the 2.0 experiments exist.

## Main Linked Assets

- published paper: [`source_papers/MetaboLiteLearner_published_paper.pdf`](source_papers/MetaboLiteLearner_published_paper.pdf)
- current Python workflow: [`../metabolite_learner/workflow.py`](../metabolite_learner/workflow.py)
- current learner implementation: [`../metabolite_learner/pls.py`](../metabolite_learner/pls.py)
- staged baseline data and outputs: [`../data/original_study`](../data/original_study)
- previous baseline run report: [`../docs/reports/previous_dataset_run.md`](../docs/reports/previous_dataset_run.md)
