from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.io import loadmat
from scipy.stats import pearsonr
from statsmodels.stats.anova import anova_lm

from .extract import extract_spectra_and_integrate
from .joint_extract import extract_joint_components
from .pls import MetaboLiteLearner


@dataclass(slots=True)
class WorkflowResult:
    fold_changes: pd.DataFrame
    spectra: pd.DataFrame
    learner: MetaboLiteLearner


MATLAB_EXCLUDED_KEGG_CLASSES = [
    "Antibiotics",
    "Bufanolide derivatives [Fig]",
    "Vitamins and cofactors",
]


def _infer_cell_type(sample_name: str) -> str:
    return sample_name[0]


def _ols_anova_p_value(values: np.ndarray, cell_types: list[str]) -> float:
    frame = pd.DataFrame({"value": np.log(values), "cell": pd.Categorical(cell_types)})
    model = smf.ols("value ~ C(cell)", data=frame).fit()
    return float(anova_lm(model).iloc[0]["PR(>F)"])


def _prepare_scaled_table(peaks_integrated: pd.DataFrame) -> pd.DataFrame:
    melted = peaks_integrated.melt(id_vars="peakId", var_name="sample", value_name="area")
    melted["sample"] = melted["sample"].astype(str)
    melted["batch"] = pd.Categorical(
        np.select(
            [melted["sample"].str.contains("plate1"), melted["sample"].str.contains("plate2")],
            ["1", "2"],
            default="3",
        )
    )
    melted["cell"] = pd.Categorical(melted["sample"].map(_infer_cell_type), categories=["P", "B", "L"])
    melted["peakId"] = melted["peakId"].astype(str)
    melted["peak_batch"] = melted["peakId"] + ":" + melted["batch"].astype(str)
    melted["area"] = np.log(melted["area"].astype(float))
    return melted


def _fit_scaling_model(frame: pd.DataFrame):
    return smf.mixedlm(
        "area ~ 0 + C(peakId)",
        frame,
        groups=frame["sample"],
        vc_formula={"peak_batch": "0 + C(peak_batch)"},
    ).fit(reml=False, method="lbfgs", disp=False)


def _fit_fold_change_model(frame: pd.DataFrame):
    return smf.mixedlm(
        "area ~ 0 + C(peakId) + C(peakId):C(cell)",
        frame,
        groups=frame["sample"],
        vc_formula={"peak_batch": "0 + C(peak_batch)"},
    ).fit(reml=False, method="lbfgs", disp=False)


def _coefficient_frame(model) -> pd.DataFrame:
    conf = model.conf_int()
    params = model.params
    pvalues = model.pvalues
    records = []
    for name, estimate in params.items():
        if not name.startswith("C(peakId)") or ":C(cell)" not in name:
            continue
        peak_part, cell_part = name.split(":")
        peak_id = peak_part.split("[")[-1].rstrip("]")
        cell = cell_part.split("[")[-1].rstrip("]").replace("T.", "")
        records.append(
            {
                "peakID": peak_id,
                "cell": cell,
                "Estimate": float(estimate),
                "pValue": float(pvalues[name]),
                "Lower": float(conf.loc[name, 0]),
                "Upper": float(conf.loc[name, 1]),
            }
        )
    return pd.DataFrame.from_records(records)


def _save_figure(figure: plt.Figure, *paths: Path) -> Path:
    saved_path = paths[0]
    for path in paths:
        figure.savefig(path, dpi=200)
    plt.close(figure)
    return saved_path


def _plot_series_scatter(
    ax: plt.Axes,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    ylabel: str,
    title: str,
    *,
    n_components: int,
) -> None:
    labels = [
        ("Brain-homing cells", "tab:blue", 0),
        ("Lung-homing cells", "tab:orange", 1),
    ]
    for label, color, index in labels:
        if index >= y_true.shape[1]:
            continue
        ax.scatter(y_true[:, index], y_pred[:, index], s=18, edgecolors="black", linewidths=0.4, alpha=0.8, label=label, color=color)
    flattened_true = y_true.reshape(-1)
    flattened_pred = y_pred.reshape(-1)
    r_value, p_value = pearsonr(flattened_true, flattened_pred)
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title(f"{title}\n(Learner with {n_components} components: r={r_value:.2f}, p={p_value:.0e})")
    ax.set_xlabel("log_2(FC) from actual data")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend(loc="upper left")
    limits = np.array([flattened_true.min(), flattened_true.max(), flattened_pred.min(), flattened_pred.max()], dtype=float)
    span = float(np.max(np.abs(limits))) if limits.size else 1.0
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.set_aspect("equal", adjustable="box")


def _plot_variance_explained(learner: MetaboLiteLearner, output_dir: Path) -> Path:
    figure, axes = plt.subplots(2, 1, figsize=(3.475, 3.505), constrained_layout=True)
    axes[0].bar(range(1, learner.nopt + 1), learner.pctvar[0] * 100)
    axes[0].set_xlabel("Latent component")
    axes[0].set_ylabel("Explained variance\nin X (%)")
    axes[0].grid(True)
    axes[1].bar(range(1, learner.nopt + 1), learner.pctvar[1] * 100)
    axes[1].set_xlabel("Latent component")
    axes[1].set_ylabel("Explained variance\nin Y (%)")
    axes[1].grid(True)
    path = output_dir / "variance_explained.png"
    return _save_figure(figure, path, output_dir / "figure_2.png")


def _safe_extract_kegg_table(mat_path: Path) -> pd.DataFrame | None:
    csv_fallback = mat_path.with_suffix(".csv")

    def _load_csv_fallback() -> pd.DataFrame | None:
        if not csv_fallback.exists():
            return None
        frame = pd.read_csv(csv_fallback)
        mz_columns = [column for column in frame.columns if column.startswith("mz")]
        class_column = "metClassLevel1" if "metClassLevel1" in frame.columns else "classCol" if "classCol" in frame.columns else None
        if class_column is None or not mz_columns:
            return None
        records = []
        for _, row in frame.iterrows():
            records.append(
                {
                    "metClassLevel1": str(row[class_column]),
                    "abundance": row[mz_columns].to_numpy(dtype=float),
                }
            )
        return pd.DataFrame.from_records(records)

    if not mat_path.exists():
        return _load_csv_fallback()
    payload = loadmat(mat_path, squeeze_me=True, struct_as_record=False)
    table = payload.get("tblKegg3")
    if table is None:
        return _load_csv_fallback()
    try:
        records = []
        iterable = table if np.ndim(table) else [table]
        for row in iterable:
            met_class = getattr(row, "metClassLevel1", None)
            abundance = getattr(row, "abundance", None)
            if met_class is None or abundance is None:
                continue
            records.append({"metClassLevel1": str(met_class), "abundance": np.asarray(abundance, dtype=float).reshape(-1)})
        return pd.DataFrame.from_records(records)
    except Exception:
        return _load_csv_fallback()


def _prepare_kegg_projection(learner: MetaboLiteLearner, kegg_mat: Path) -> pd.DataFrame | None:
    kegg_table = _safe_extract_kegg_table(kegg_mat)
    if kegg_table is not None and not kegg_table.empty:
        kegg_table = kegg_table.loc[~kegg_table["metClassLevel1"].isin(MATLAB_EXCLUDED_KEGG_CLASSES)].copy()
        spectra = np.vstack(kegg_table["abundance"].to_numpy())
        spectra = spectra / np.linalg.norm(spectra, axis=1, keepdims=True)
        latent_scores, predicted = learner.map_to_latent_space(spectra)
        for component_index in range(min(5, latent_scores.shape[1])):
            kegg_table[f"latent{component_index + 1}"] = latent_scores[:, component_index]
        kegg_table["predictedY1"] = predicted[:, 0]
        kegg_table["predictedY2"] = predicted[:, 1] if predicted.shape[1] > 1 else predicted[:, 0]
        return kegg_table
    return None


def _plot_loadings(learner: MetaboLiteLearner, output_dir: Path, kegg_mat: Path) -> Path:
    kegg_table = _prepare_kegg_projection(learner, kegg_mat)
    displayed_components = min(
        5,
        learner.nopt,
        sum(column.startswith("latent") for column in kegg_table.columns) if kegg_table is not None else learner.nopt,
    )
    displayed_components = max(displayed_components, 1)

    figure_height = 4.8 + 0.9 * displayed_components
    figure = plt.figure(figsize=(8.2, figure_height), constrained_layout=True)
    outer = figure.add_gridspec(2, 2, width_ratios=[1.15, 1.75], height_ratios=[1.0, 1.0])
    ax_beta = figure.add_subplot(outer[0, 0])
    ax_yload = figure.add_subplot(outer[1, 0])
    right_grid = outer[:, 1].subgridspec(displayed_components, 1, hspace=0.05)
    right_axes = [figure.add_subplot(right_grid[idx, 0]) for idx in range(displayed_components)]

    beta_x = learner.beta[1:, 0]
    beta_y = learner.beta[1:, 1] if learner.beta.shape[1] > 1 else learner.beta[1:, 0]
    ax_beta.plot(np.vstack([np.zeros_like(beta_x), beta_x]), np.vstack([np.zeros_like(beta_y), beta_y]), "k-", linewidth=0.8)
    ax_beta.plot(beta_x, beta_y, "k.", markersize=3)
    mz_array = np.arange(50, 50 + beta_x.shape[0])
    top_beta = np.argsort(beta_x**2 + beta_y**2)[-2:][::-1]
    for index in top_beta:
        ax_beta.text(beta_x[index], beta_y[index], str(mz_array[index]), fontsize=8)
    ax_beta.axhline(0, color="black", linestyle="--", linewidth=1)
    ax_beta.axvline(0, color="black", linestyle="--", linewidth=1)
    ax_beta.set_xlabel("log_2(FC) in brain-homing cells")
    ax_beta.set_ylabel("log_2(FC) in lung-homing cells")
    ax_beta.set_title("Fragment and reference projection", fontsize=10, loc="left")
    ax_beta.set_xlim(-2, 2)
    ax_beta.set_ylim(-3, 3)
    ax_beta.set_aspect("equal", adjustable="box")
    ax_beta.grid(True)

    if kegg_table is not None and not kegg_table.empty:
        categories = list(pd.Categorical(kegg_table["metClassLevel1"]).categories)
        cmap = plt.get_cmap("tab10")
        color_map = {category: cmap(index % 10) for index, category in enumerate(categories)}
        for category in categories:
            subset = kegg_table.loc[kegg_table["metClassLevel1"] == category]
            ax_beta.scatter(
                subset["predictedY1"],
                subset["predictedY2"],
                s=12,
                alpha=0.35,
                label=category,
                color=color_map[category],
                edgecolors="none",
            )
        ax_beta.legend(loc="lower left", fontsize=7, title=None, frameon=True)

        jitter_rng = np.random.default_rng(0)
        display_labels = {
            "Carbohydrates": "Carbo-\nhydrates",
            "Hormones and transmitters": "Hormones and\ntransmitters",
            "Nucleic acids": "Nucleic\nacids",
            "Organic acids": "Organic\nacids",
        }
        for component_index, axis in enumerate(right_axes, start=1):
            axis.axhline(0, color="black", linewidth=1)
            axis.grid(True, axis="y")
            field = f"latent{component_index}"
            means = []
            for category_index, category in enumerate(categories):
                subset = kegg_table.loc[kegg_table["metClassLevel1"] == category, field].to_numpy(dtype=float)
                x_values = category_index + jitter_rng.uniform(-0.1, 0.1, size=subset.size)
                axis.scatter(x_values, subset, s=10, alpha=0.25, color="tab:blue", edgecolors="none")
                means.append(float(np.mean(subset)))
            axis.scatter(range(len(categories)), means, marker="_", s=400, linewidths=2.5, color="tab:blue")
            axis.set_title(f"Latent component {component_index}", fontsize=9, loc="left")
            axis.set_ylabel("Input")
            axis.set_ylim(-0.4, 0.6)
            axis.set_xlim(-0.5, len(categories) - 0.5 if kegg_table is not None else 6.5)
            if component_index < len(right_axes):
                axis.set_xticks(range(len(categories)))
                axis.set_xticklabels([])
            else:
                axis.set_xticks(range(len(categories)))
                axis.set_xticklabels(
                    [display_labels.get(category, category) for category in categories],
                    rotation=18,
                    ha="right",
                    fontsize=7,
                )

    y_loading_x = learner.y_loadings[0, : learner.nopt]
    y_loading_y = learner.y_loadings[1, : learner.nopt] if learner.y_loadings.shape[0] > 1 else np.zeros(learner.nopt, dtype=float)
    colors = plt.get_cmap("tab10")(np.arange(learner.nopt) % 10)
    for idx in range(learner.nopt):
        ax_yload.plot([0, y_loading_x[idx]], [0, y_loading_y[idx]], color=colors[idx], linewidth=2)
        ax_yload.scatter(y_loading_x[idx], y_loading_y[idx], s=36, color=colors[idx], label=str(idx + 1))
    ax_yload.axhline(0, color="black", linestyle="--", linewidth=1)
    ax_yload.axvline(0, color="black", linestyle="--", linewidth=1)
    ax_yload.set_xlabel("log_2(FC) in brain-homing cells")
    ax_yload.set_ylabel("log_2(FC) in lung-homing cells")
    ax_yload.set_title("Latent components in response space", fontsize=10, loc="left")
    ax_yload.set_xlim(-2, 2)
    ax_yload.set_ylim(-3, 3)
    ax_yload.set_aspect("equal", adjustable="box")
    ax_yload.grid(True)
    ax_yload.legend(loc="lower right", title="Latent component", fontsize=7)

    path = output_dir / "loadings.png"
    return _save_figure(figure, path, output_dir / "figure_3.png")


def _plot_learner_diagnostics(learner: MetaboLiteLearner, output_dir: Path, *, shuffle_test: bool) -> Path:
    figure = plt.figure(figsize=(9.42, 9.93), constrained_layout=True)
    grid = figure.add_gridspec(2, 2)
    ax_mse = figure.add_subplot(grid[:, 0] if shuffle_test else grid[0, 0])
    ax_fit = figure.add_subplot(grid[0, 1])
    ax_cv = figure.add_subplot(grid[1, 1])
    ax_shuffle = figure.add_subplot(grid[1, 0]) if shuffle_test else None

    components = np.arange(1, learner.maxn + 1)
    mean_train = learner.train_sse.mean(axis=0)
    mean_test = learner.test_sse.mean(axis=0)
    ax_mse.plot(components, mean_train, "o-", linewidth=2, label="Training MSE")
    ax_mse.errorbar(components, mean_test, learner.test_stderr, color="black", linewidth=1, marker=None)
    ax_mse.plot(components, mean_test, "o-", linewidth=2, label="Cross-validation MSE")
    ax_mse.axvline(learner.nmin, color="black", linestyle=":", label=f"Minimum (N={learner.nmin})")
    ax_mse.axvline(learner.nopt, color="black", linestyle="--", label=f"Optimal (N={learner.nopt})")
    ax_mse.set_xlabel("Number of latent components")
    ax_mse.set_ylabel("MSE")
    ax_mse.grid(True)
    ax_mse.legend(loc="upper right", fontsize=8)

    cv_prediction = learner.cv_predictions[:, :, learner.nopt - 1]
    _plot_series_scatter(
        ax_fit,
        learner.y_full_data,
        learner.y_pred,
        ylabel="log_2(FC) fit by model",
        title="True metabolite abundances vs. model prediction",
        n_components=learner.nopt,
    )
    _plot_series_scatter(
        ax_cv,
        learner.y_full_data,
        cv_prediction,
        ylabel="log_2(FC) predicted by model\nin leave-one-out cross-validation",
        title="True metabolite abundances vs. model prediction",
        n_components=learner.nopt,
    )

    if ax_shuffle is not None:
        shuffle_result = learner.shuffling_test()
        ax_shuffle.hist(shuffle_result.randomized_mse, bins=100, color="0.75")
        ax_shuffle.axvline(
            shuffle_result.real_mse,
            color="black",
            linestyle="--",
            label=f"MSE of model (N={learner.nopt}) trained in real data",
        )
        ax_shuffle.set_xlabel(f"MSE of models (N={learner.nopt}) trained in shuffled data")
        ax_shuffle.set_ylabel("Distribution density")
        ax_shuffle.grid(True)
        ax_shuffle.legend(loc="upper right", fontsize=8)

    path = output_dir / "learner_diagnostics.png"
    extra_paths = [path, output_dir / "figure_1.png"]
    if shuffle_test and ax_shuffle is not None:
        extra_paths.append(output_dir / "shuffle_test.png")
    return _save_figure(figure, *extra_paths)


def run_workflow(
    gcms_csv_dir: str | Path = "gcmsCSVs",
    extracted_peaks_dir: str | Path = "extractedPeaks",
    folds_dir: str | Path = "folds",
    kegg_mat_path: str | Path = "kegg/keggCompoundsWithFiehlibSpectrum.mat",
    *,
    regenerate_peaks: bool = False,
    kfold_learn: int = 0,
    max_components: int = 30,
    nrandomized: int = 1000,
    shuffle_test: bool = False,
    extractor: str = "joint-components",
    extractor_n_components: int | None = None,
    supervision_strength: float = 0.35,
    library_prior: str = "off",
) -> WorkflowResult:
    gcms_csv_dir = Path(gcms_csv_dir)
    extracted_peaks_dir = Path(extracted_peaks_dir)
    folds_dir = Path(folds_dir)
    folds_dir.mkdir(parents=True, exist_ok=True)

    peaks_path = extracted_peaks_dir / "tblPeaksIntegrated.csv"
    spectra_path = extracted_peaks_dir / "tblSpectra.csv"
    if regenerate_peaks or not peaks_path.exists() or not spectra_path.exists():
        if extractor == "joint-components":
            extraction_result = extract_joint_components(
                gcms_csv_dir,
                extracted_peaks_dir,
                n_components=extractor_n_components,
                supervision_strength=supervision_strength,
                library_prior=library_prior,
                library_mat_path=kegg_mat_path,
            )
            peaks_integrated = extraction_result.peaks_integrated
            spectra = extraction_result.spectra
        elif extractor == "legacy-peaks":
            peaks_integrated, spectra = extract_spectra_and_integrate(gcms_csv_dir, extracted_peaks_dir)
        else:
            raise ValueError("extractor must be 'joint-components' or 'legacy-peaks'.")
    else:
        peaks_integrated = pd.read_csv(peaks_path)
        spectra = pd.read_csv(spectra_path)

    sample_columns = list(peaks_integrated.columns[1:])
    cell_types = [_infer_cell_type(name) for name in sample_columns]
    p_values = [
        _ols_anova_p_value(peaks_integrated.loc[row_index, sample_columns].to_numpy(dtype=float), cell_types)
        for row_index in range(len(peaks_integrated))
    ]
    filtered = peaks_integrated.loc[np.array(p_values) < 0.05, ["peakId", *[name for name in sample_columns if not name.startswith("M")]]].copy()

    scaled = _prepare_scaled_table(filtered)
    scaling_model = _fit_scaling_model(scaled)
    scaled["areaModel"] = scaling_model.resid

    fold_change_model = _fit_fold_change_model(scaled)
    coefficients = _coefficient_frame(fold_change_model)
    if coefficients.empty:
        raise RuntimeError("The mixed-effects fold-change model did not produce any B/L coefficients.")

    fold_changes = coefficients.pivot(index="peakID", columns="cell", values="Estimate").reset_index().rename_axis(columns=None)
    pvals = coefficients.pivot(index="peakID", columns="cell", values="pValue").reset_index().rename_axis(columns=None)
    lower = coefficients.pivot(index="peakID", columns="cell", values="Lower").reset_index().rename_axis(columns=None)
    upper = coefficients.pivot(index="peakID", columns="cell", values="Upper").reset_index().rename_axis(columns=None)

    fold_changes = fold_changes.merge(pvals, on="peakID", suffixes=("", "_p"))
    fold_changes = fold_changes.merge(lower, on="peakID", suffixes=("", "_lower"))
    fold_changes = fold_changes.merge(upper, on="peakID", suffixes=("", "_upper"))

    log2_factor = np.log(2.0)
    for column in ["B", "L", "B_lower", "L_lower", "B_upper", "L_upper"]:
        if column in fold_changes:
            fold_changes[column] = fold_changes[column] / log2_factor

    fold_changes = fold_changes.rename(
        columns={
            "B_p": "pValB",
            "L_p": "pValL",
            "B_lower": "lowerB",
            "L_lower": "lowerL",
            "B_upper": "upperB",
            "L_upper": "upperL",
        }
    )
    fold_changes = fold_changes[["peakID", "B", "L", "pValB", "pValL", "lowerB", "lowerL", "upperB", "upperL"]]
    fold_changes = fold_changes.sort_values("peakID").reset_index(drop=True)
    fold_changes.to_csv(folds_dir / "peakFoldChanges.csv", index=False)

    spectra = spectra.copy()
    spectra["peakId"] = spectra["peakId"].astype(str)
    fold_changes["peakID"] = fold_changes["peakID"].astype(str)
    spectra = spectra.loc[spectra["peakId"].isin(fold_changes["peakID"]), :].sort_values("peakId").reset_index(drop=True)
    fold_changes = fold_changes.sort_values("peakID").reset_index(drop=True)

    matrix_spectra = spectra.iloc[:, 1:].to_numpy(dtype=float)
    x = matrix_spectra / np.linalg.norm(matrix_spectra, axis=1, keepdims=True)
    y = fold_changes[["B", "L"]].to_numpy(dtype=float)
    learner = MetaboLiteLearner(x, y, kfold=kfold_learn, max_components=max_components, nrandomized=nrandomized)

    _plot_learner_diagnostics(learner, folds_dir, shuffle_test=shuffle_test)
    _plot_variance_explained(learner, folds_dir)
    _plot_loadings(learner, folds_dir, Path(kegg_mat_path))

    return WorkflowResult(fold_changes=fold_changes, spectra=spectra, learner=learner)
