# Scripts

Use this directory for helper scripts that do one of the following:

- download or verify external assets,
- run reproducible experiment bundles,
- export paper figures,
- or convert intermediate results into manuscript-ready tables.

Avoid placing ad hoc exploratory notebooks or one-off shell fragments here without a short Markdown note explaining their purpose.

Current helper scripts:

- `stage_previous_dataset.sh`: stages the original study's `gcmsCSVs/` and `kegg/` assets into this repo's ignored `data/` workspace. It uses the existing local `metaboliteLearner` checkout when available and otherwise downloads those directories from the original GitHub repo.
