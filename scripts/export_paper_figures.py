from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "original_study"
EXTRACTED_PEAKS_DIR = DATA_DIR / "extractedPeaks"
FOLDS_DIR = DATA_DIR / "folds"
GCMS_DIR = DATA_DIR / "gcmsCSVs"
KEGG_CSV_PATH = DATA_DIR / "kegg" / "keggCompoundsWithFiehlibSpectrum.csv"
PAPER_FIGURES_DIR = ROOT / "paper" / "figures"

RASTER_EXPORTS = {
    "figure_1.png": "figure_1_predictive_performance.png",
    "figure_2.png": "figure_2_variance_explained.png",
    "figure_3.png": "figure_3_interpretability.png",
}

CELL_COLORS = {
    "P": "#4c78a8",
    "B": "#f58518",
    "L": "#54a24b",
    "M": "#e45756",
}

CELL_LABELS = {
    "P": "Parental",
    "B": "Brain-homing",
    "L": "Lung-homing",
    "M": "Media",
}

EPSILON = 1e-8


def _content_mask(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image < 0.995

    rgb = image[..., :3]
    if image.shape[-1] == 4:
        alpha = image[..., 3] > 0.0
    else:
        alpha = np.ones(rgb.shape[:2], dtype=bool)
    return np.any(rgb < 0.995, axis=-1) & alpha


def _crop_whitespace(image: np.ndarray, *, pad: int = 8) -> np.ndarray:
    mask = _content_mask(image)
    if not np.any(mask):
        return image

    rows, cols = np.where(mask)
    row_min = max(int(rows.min()) - pad, 0)
    row_max = min(int(rows.max()) + pad + 1, image.shape[0])
    col_min = max(int(cols.min()) - pad, 0)
    col_max = min(int(cols.max()) + pad + 1, image.shape[1])
    return image[row_min:row_max, col_min:col_max]


def _save_and_crop(figure: plt.Figure, path: Path, *, dpi: int = 200) -> Path:
    figure.savefig(path, dpi=dpi, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    image = mpimg.imread(path)
    plt.imsave(path, _crop_whitespace(image))
    return path


def _copy_existing_fold_figures() -> list[Path]:
    written: list[Path] = []
    for source_name, target_name in RASTER_EXPORTS.items():
        image = mpimg.imread(FOLDS_DIR / source_name)
        cropped = _crop_whitespace(image)
        target = PAPER_FIGURES_DIR / target_name
        plt.imsave(target, cropped)
        written.append(target)
    return written


def _infer_cell_type(sample_name: str) -> str:
    return sample_name[0]


def _load_component_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    components = pd.read_csv(EXTRACTED_PEAKS_DIR / "tblComponents.csv").sort_values("rtPeak").reset_index(drop=True)
    ordered_ids = components["peakId"].to_list()
    chromatograms = pd.read_csv(EXTRACTED_PEAKS_DIR / "tblComponentChromatograms.csv")
    spectra = pd.read_csv(EXTRACTED_PEAKS_DIR / "tblComponentSpectra.csv")
    chromatograms = pd.concat(
        [
            pd.DataFrame({"peakId": ordered_ids}),
            chromatograms.set_index("peakId").loc[ordered_ids].reset_index(drop=True),
        ],
        axis=1,
    )
    spectra = pd.concat(
        [
            pd.DataFrame({"peakId": ordered_ids}),
            spectra.set_index("peakId").loc[ordered_ids].reset_index(drop=True),
        ],
        axis=1,
    )
    return components, chromatograms, spectra


def _load_mean_tics() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    tic_rows: dict[str, list[np.ndarray]] = {cell: [] for cell in CELL_COLORS}
    for csv_path in sorted(GCMS_DIR.glob("*.csv")):
        cell_type = _infer_cell_type(csv_path.stem)
        matrix = np.loadtxt(csv_path, delimiter=",", dtype=float)
        tic_rows[cell_type].append(matrix.sum(axis=1))

    if not tic_rows["P"]:
        raise FileNotFoundError(f"No GC/MS CSV matrices were found in {GCMS_DIR}.")

    n_time = tic_rows["P"][0].shape[0]
    time_grid = np.linspace(6.0, 30.0, n_time)
    mean_tics = {
        cell_type: np.mean(traces, axis=0)
        for cell_type, traces in tic_rows.items()
        if traces
    }
    return time_grid, mean_tics


def _component_time_grid(chromatograms: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    time_columns = [column for column in chromatograms.columns if column.startswith("rt")]
    time_grid = np.array([float(column[2:]) for column in time_columns], dtype=float)
    return time_columns, time_grid


def _component_window(chromatogram: np.ndarray, time_grid: np.ndarray, rt_peak: float) -> tuple[float, float]:
    peak_height = float(np.max(chromatogram))
    support = chromatogram >= (peak_height * 0.05)
    if np.any(support):
        support_times = time_grid[support]
        radius = max((float(support_times[-1]) - float(support_times[0])) * 0.5, 0.25)
    else:
        radius = 0.35
    radius = float(np.clip(radius + 0.1, 0.35, 1.2))
    return rt_peak - radius, rt_peak + radius


def _plot_component_chromatogram_overview() -> Path:
    components, chromatograms, _ = _load_component_tables()
    time_grid, mean_tics = _load_mean_tics()
    _, component_time_grid = _component_time_grid(chromatograms)

    figure = plt.figure(figsize=(16, 15), constrained_layout=True)
    grid = figure.add_gridspec(5, 3, height_ratios=[1.4, 1.0, 1.0, 1.0, 1.0])
    tic_axis = figure.add_subplot(grid[0, :])
    panel_axes = [figure.add_subplot(grid[row, column]) for row in range(1, 5) for column in range(3)]

    global_tic_scale = max(float(np.max(trace)) for trace in mean_tics.values())
    for cell_type, trace in mean_tics.items():
        tic_axis.plot(
            time_grid,
            trace / max(global_tic_scale, EPSILON),
            color=CELL_COLORS[cell_type],
            linewidth=1.8,
            label=CELL_LABELS[cell_type],
        )

    for component_index, component in components.iterrows():
        rt_peak = float(component["rtPeak"])
        tic_axis.axvline(rt_peak, color="0.65", linewidth=0.8, alpha=0.7)
        tic_axis.text(
            rt_peak,
            1.02 + 0.04 * (component_index % 2),
            f"C{component_index + 1}",
            rotation=90,
            va="bottom",
            ha="center",
            fontsize=7,
            color="0.35",
        )

    tic_axis.set_xlim(time_grid[0], time_grid[-1])
    tic_axis.set_ylim(0.0, 1.15)
    tic_axis.set_ylabel("Mean TIC\n(normalized)")
    tic_axis.set_title("Average total ion chromatograms with learned component locations", fontsize=13)
    tic_axis.legend(ncol=4, frameon=False, loc="upper right")
    tic_axis.spines["top"].set_visible(False)
    tic_axis.spines["right"].set_visible(False)

    time_columns, _ = _component_time_grid(chromatograms)
    for axis, (_, component) in zip(panel_axes, components.iterrows(), strict=True):
        chromatogram = chromatograms.loc[chromatograms["peakId"] == component["peakId"], time_columns].iloc[0].to_numpy(dtype=float)
        rt_peak = float(component["rtPeak"])
        left_rt, right_rt = _component_window(chromatogram, component_time_grid, rt_peak)
        panel_mask = (time_grid >= left_rt) & (time_grid <= right_rt)
        local_scale = max(float(np.max(mean_tics[cell_type][panel_mask])) for cell_type in mean_tics)

        for cell_type, trace in mean_tics.items():
            axis.plot(
                time_grid[panel_mask],
                trace[panel_mask] / max(local_scale, EPSILON),
                color=CELL_COLORS[cell_type],
                linewidth=1.3,
                alpha=0.95,
            )

        component_mask = (component_time_grid >= left_rt) & (component_time_grid <= right_rt)
        axis.plot(
            component_time_grid[component_mask],
            chromatogram[component_mask] / max(float(np.max(chromatogram[component_mask])), EPSILON),
            color="black",
            linewidth=2.0,
            label="Learned component",
        )
        axis.axvline(rt_peak, color="0.7", linestyle="--", linewidth=0.8)
        axis.set_xlim(left_rt, right_rt)
        axis.set_ylim(0.0, 1.05)
        axis.set_title(f"{component['peakId']} | {component['matchedClass']}", fontsize=9)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="both", labelsize=8)

    for axis in panel_axes[9:]:
        axis.set_xlabel("Retention time (min)", fontsize=9)
    for axis in (panel_axes[0], panel_axes[3], panel_axes[6], panel_axes[9]):
        axis.set_ylabel("Local\nscale", fontsize=9)

    return _save_and_crop(figure, PAPER_FIGURES_DIR / "component_chromatogram_overview.png")


def _load_reference_library() -> pd.DataFrame:
    library = pd.read_csv(KEGG_CSV_PATH)
    mz_columns = [column for column in library.columns if column.startswith("mz")]
    class_column = "metClassLevel1" if "metClassLevel1" in library.columns else "classCol"
    matrix = library[mz_columns].to_numpy(dtype=float)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = matrix / np.maximum(norms, EPSILON)
    result = pd.DataFrame({"matchLabel": library[class_column].astype(str)})
    result["spectrum"] = list(normalized)
    return result


def _best_reference_match(spectrum: np.ndarray, library: pd.DataFrame) -> tuple[str, float, np.ndarray]:
    normalized_spectrum = np.array(spectrum, dtype=float, copy=True)
    normalized_spectrum /= max(float(np.linalg.norm(normalized_spectrum)), EPSILON)
    library_matrix = np.vstack(library["spectrum"].to_numpy())
    similarities = library_matrix @ normalized_spectrum
    best_index = int(np.argmax(similarities))
    return (
        str(library.iloc[best_index]["matchLabel"]),
        float(similarities[best_index]),
        np.asarray(library.iloc[best_index]["spectrum"], dtype=float),
    )


def _plot_component_reference_matches() -> Path:
    components, _, spectra = _load_component_tables()
    mz_columns = [column for column in spectra.columns if column.startswith("mz")]
    mz_grid = np.array([int(column[2:]) for column in mz_columns], dtype=int)
    library = _load_reference_library()

    figure, axes = plt.subplots(4, 3, figsize=(16, 14), constrained_layout=True)
    axes_flat = list(axes.ravel())

    for axis, (_, component) in zip(axes_flat, components.iterrows(), strict=True):
        spectrum = spectra.loc[spectra["peakId"] == component["peakId"], mz_columns].iloc[0].to_numpy(dtype=float)
        match_label, similarity, reference = _best_reference_match(spectrum, library)

        spectrum = spectrum / max(float(np.max(spectrum)), EPSILON)
        reference = reference / max(float(np.max(reference)), EPSILON)
        keep_mask = (spectrum >= 0.08) | (reference >= 0.08)
        if keep_mask.sum() < 8:
            strongest = np.argsort(-(spectrum + reference))[:8]
            keep_mask = np.zeros_like(keep_mask, dtype=bool)
            keep_mask[strongest] = True

        keep_mz = mz_grid[keep_mask]
        keep_spectrum = spectrum[keep_mask]
        keep_reference = reference[keep_mask]

        axis.vlines(keep_mz - 0.15, 0.0, keep_spectrum, color="#4c78a8", linewidth=2.2, label="Learned component")
        axis.vlines(keep_mz + 0.15, 0.0, keep_reference, color="#f58518", linewidth=1.6, alpha=0.9, label="Best reference")
        axis.scatter(keep_mz + 0.15, keep_reference, color="#f58518", s=10, alpha=0.9)
        axis.set_ylim(0.0, 1.05)
        axis.set_xlim(keep_mz.min() - 3, keep_mz.max() + 3)
        axis.set_title(f"{component['peakId']} | RT {component['rtPeak']:.2f}", fontsize=9)
        axis.text(
            0.02,
            0.97,
            f"Best Fiehn/KEGG class match\n{match_label}\ncosine = {similarity:.2f}",
            transform=axis.transAxes,
            va="top",
            ha="left",
            fontsize=8,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "0.85"},
        )
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="both", labelsize=8)

    for axis in axes[-1, :]:
        axis.set_xlabel("m/z", fontsize=9)
    for axis in axes[:, 0]:
        axis.set_ylabel("Normalized intensity", fontsize=9)

    handles = [
        Line2D([0], [0], color="#4c78a8", linewidth=2.2, label="Learned component"),
        Line2D([0], [0], color="#f58518", linewidth=1.6, label="Best available reference spectrum"),
    ]
    figure.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.01))

    return _save_and_crop(figure, PAPER_FIGURES_DIR / "component_reference_matches.png")


def export_paper_figures() -> list[Path]:
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    written = _copy_existing_fold_figures()
    written.append(_plot_component_chromatogram_overview())
    written.append(_plot_component_reference_matches())
    return written


if __name__ == "__main__":
    for path in export_paper_figures():
        print(path)
