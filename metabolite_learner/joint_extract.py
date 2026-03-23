from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .extract import MZ_GRID, TIME_GRID, _load_matrix_csv


EPSILON = 1e-8


@dataclass(slots=True)
class JointComponentResult:
    peaks_integrated: pd.DataFrame
    spectra: pd.DataFrame
    chromatograms: pd.DataFrame
    components: pd.DataFrame
    component_effects: pd.DataFrame
    component_matches: pd.DataFrame


def _infer_cell_type(sample_name: str) -> str:
    return sample_name[0]


def _infer_batch(sample_name: str) -> str:
    if "plate1" in sample_name:
        return "1"
    if "plate2" in sample_name:
        return "2"
    return "3"


def _build_sample_metadata(sample_names: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample": sample_names,
            "cell": [_infer_cell_type(sample_name) for sample_name in sample_names],
            "batch": [_infer_batch(sample_name) for sample_name in sample_names],
        }
    )


def _build_design_matrix(metadata: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    columns = ["intercept", "batch2", "batch3", "cellB", "cellL", "cellM"]
    design = np.column_stack(
        [
            np.ones(len(metadata), dtype=float),
            (metadata["batch"] == "2").to_numpy(dtype=float),
            (metadata["batch"] == "3").to_numpy(dtype=float),
            (metadata["cell"] == "B").to_numpy(dtype=float),
            (metadata["cell"] == "L").to_numpy(dtype=float),
            (metadata["cell"] == "M").to_numpy(dtype=float),
        ]
    )
    return design, columns


def _fit_effects(abundance: np.ndarray, design_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    log_abundance = np.log(np.maximum(np.asarray(abundance, dtype=float), EPSILON))
    coefficients, *_ = np.linalg.lstsq(design_matrix, log_abundance, rcond=None)
    fitted = design_matrix @ coefficients
    residual = log_abundance - fitted
    denominator = float(np.sum((log_abundance - log_abundance.mean()) ** 2))
    if denominator <= EPSILON:
        r_squared = 1.0
    else:
        r_squared = 1.0 - float(np.sum(residual**2) / denominator)
    return coefficients, fitted, r_squared


def _supervised_shrink(abundance: np.ndarray, design_matrix: np.ndarray, strength: float) -> tuple[np.ndarray, np.ndarray, float]:
    coefficients, fitted, r_squared = _fit_effects(abundance, design_matrix)
    target = np.exp(fitted)
    shrunk = (1.0 - strength) * np.asarray(abundance, dtype=float) + strength * target
    return np.maximum(shrunk, EPSILON), coefficients, r_squared


def _normalize_nmf_factors(weights: np.ndarray, component_maps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    scale = np.maximum(component_maps.sum(axis=1, keepdims=True), EPSILON)
    normalized_maps = component_maps / scale
    normalized_weights = weights * scale.reshape(1, -1)
    return normalized_weights, normalized_maps


def _fit_supervised_nmf(
    matrix: np.ndarray,
    design_matrix: np.ndarray,
    *,
    n_components: int,
    supervision_strength: float,
    max_iter: int,
    random_state: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(random_state)
    n_samples, _ = matrix.shape

    weights = rng.random((n_samples, n_components), dtype=np.float32) + 0.05
    row_indices = rng.choice(n_samples, size=n_components, replace=True)
    component_maps = np.maximum(matrix[row_indices, :].copy(), EPSILON)
    weights, component_maps = _normalize_nmf_factors(weights, component_maps)

    for _ in range(max_iter):
        component_gram = component_maps @ component_maps.T
        weights *= (matrix @ component_maps.T) / (weights @ component_gram + EPSILON)
        weights = np.maximum(weights, EPSILON)

        for component_index in range(n_components):
            shrunk, _, _ = _supervised_shrink(weights[:, component_index], design_matrix, supervision_strength)
            weights[:, component_index] = shrunk.astype(np.float32)

        sample_gram = weights.T @ weights
        component_maps *= (weights.T @ matrix) / (sample_gram @ component_maps + EPSILON)
        component_maps = np.maximum(component_maps, EPSILON)

        weights, component_maps = _normalize_nmf_factors(weights, component_maps)

    return weights.astype(float), component_maps.astype(float)


def _smooth_profile(values: np.ndarray) -> np.ndarray:
    kernel = np.array([1.0, 2.0, 3.0, 2.0, 1.0], dtype=float)
    smoothed = np.convolve(np.asarray(values, dtype=float), kernel / kernel.sum(), mode="same")
    return np.maximum(smoothed, EPSILON)


def _factor_component_map(component_map: np.ndarray, *, max_iter: int = 20) -> tuple[np.ndarray, np.ndarray]:
    chromatogram = _smooth_profile(component_map.sum(axis=1))
    spectrum = np.maximum(component_map.sum(axis=0), EPSILON)
    chromatogram /= chromatogram.sum()
    spectrum /= spectrum.sum()

    for _ in range(max_iter):
        chromatogram = _smooth_profile(component_map @ spectrum)
        chromatogram /= np.maximum(chromatogram.sum(), EPSILON)
        spectrum = np.maximum(component_map.T @ chromatogram, EPSILON)
        spectrum /= np.maximum(spectrum.sum(), EPSILON)

    return chromatogram, spectrum


def _component_bounds(profile: np.ndarray, time_grid: np.ndarray) -> tuple[float, float, float, float]:
    peak_index = int(np.argmax(profile))
    peak_height = float(profile[peak_index])
    threshold = peak_height * 0.5
    above_threshold = np.flatnonzero(profile >= threshold)
    if above_threshold.size == 0:
        left_index = peak_index
        right_index = peak_index
    else:
        left_index = int(above_threshold[0])
        right_index = int(above_threshold[-1])
    rt_peak = float(time_grid[peak_index])
    rt_start = float(time_grid[left_index])
    rt_end = float(time_grid[right_index])
    return rt_peak, rt_start, rt_end, float(rt_end - rt_start)


def _safe_extract_library_table(mat_path: str | Path | None) -> pd.DataFrame | None:
    if mat_path is None:
        return None

    mat_path = Path(mat_path)
    csv_fallback = mat_path.with_suffix(".csv")

    def _load_csv_fallback() -> pd.DataFrame | None:
        if not csv_fallback.exists():
            return None
        frame = pd.read_csv(csv_fallback)
        mz_columns = [column for column in frame.columns if column.startswith("mz")]
        class_column = "metClassLevel1" if "metClassLevel1" in frame.columns else "classCol" if "classCol" in frame.columns else None
        if class_column is None or not mz_columns:
            return None
        rows = []
        for _, row in frame.iterrows():
            spectrum = row[mz_columns].to_numpy(dtype=float)
            norm = float(np.linalg.norm(spectrum))
            if norm <= EPSILON:
                continue
            rows.append({"metClassLevel1": str(row[class_column]), "abundance": spectrum / norm})
        return pd.DataFrame.from_records(rows)

    if not mat_path.exists():
        return _load_csv_fallback()

    payload = loadmat(mat_path, squeeze_me=True, struct_as_record=False)
    table = payload.get("tblKegg3")
    if table is None:
        return _load_csv_fallback()
    try:
        rows = []
        iterable = table if np.ndim(table) else [table]
        for entry in iterable:
            met_class = getattr(entry, "metClassLevel1", None)
            abundance = getattr(entry, "abundance", None)
            if met_class is None or abundance is None:
                continue
            spectrum = np.asarray(abundance, dtype=float).reshape(-1)
            norm = float(np.linalg.norm(spectrum))
            if norm <= EPSILON:
                continue
            rows.append({"metClassLevel1": str(met_class), "abundance": spectrum / norm})
        return pd.DataFrame.from_records(rows)
    except Exception:
        return _load_csv_fallback()


def _top_library_match(spectrum: np.ndarray, library_table: pd.DataFrame | None) -> tuple[str, float, np.ndarray | None]:
    if library_table is None or library_table.empty:
        return "", float("nan"), None
    normalized_spectrum = np.asarray(spectrum, dtype=float)
    normalized_spectrum /= np.maximum(np.linalg.norm(normalized_spectrum), EPSILON)
    library_matrix = np.vstack(library_table["abundance"].to_numpy())
    similarities = library_matrix @ normalized_spectrum
    best_index = int(np.argmax(similarities))
    return (
        str(library_table.iloc[best_index]["metClassLevel1"]),
        float(similarities[best_index]),
        np.asarray(library_table.iloc[best_index]["abundance"], dtype=float),
    )


def fit_joint_components_from_tensor(
    tensor: np.ndarray,
    *,
    time_grid: np.ndarray,
    mz_grid: np.ndarray,
    sample_names: list[str],
    n_components: int | None = None,
    supervision_strength: float = 0.35,
    max_iter: int = 40,
    min_component_fraction: float = 0.005,
    library_prior: str = "off",
    library_mat_path: str | Path | None = None,
) -> JointComponentResult:
    if tensor.ndim != 3:
        raise ValueError(f"Expected a 3D tensor, received shape {tensor.shape}.")
    if tensor.shape[2] != len(sample_names):
        raise ValueError("The sample dimension of the tensor does not match the provided sample names.")
    if library_prior not in {"off", "weak"}:
        raise ValueError("library_prior must be 'off' or 'weak'.")

    n_time, n_mz, n_samples = tensor.shape
    chosen_components = n_components if n_components is not None else min(12, max(4, n_samples // 3))
    chosen_components = max(1, min(int(chosen_components), n_samples))

    metadata = _build_sample_metadata(sample_names)
    design_matrix, effect_labels = _build_design_matrix(metadata)
    matrix = np.moveaxis(np.asarray(tensor, dtype=np.float32), 2, 0).reshape(n_samples, n_time * n_mz)

    weights, component_maps = _fit_supervised_nmf(
        matrix,
        design_matrix,
        n_components=chosen_components,
        supervision_strength=supervision_strength,
        max_iter=max_iter,
    )

    library_table = _safe_extract_library_table(library_mat_path)
    total_signal = float(np.sum(weights))
    component_rows: list[dict[str, float | str]] = []
    abundance_rows: list[dict[str, float | str]] = []
    spectra_rows: list[dict[str, float | str]] = []
    chromatogram_rows: list[dict[str, float | str]] = []
    effect_rows: list[dict[str, float | str]] = []
    match_rows: list[dict[str, float | str]] = []

    for component_index in range(chosen_components):
        component_map = component_maps[component_index, :].reshape(n_time, n_mz)
        chromatogram, spectrum = _factor_component_map(component_map)
        matched_class, similarity, matched_spectrum = _top_library_match(spectrum, library_table)
        if library_prior == "weak" and matched_spectrum is not None and similarity >= 0.75:
            spectrum = 0.85 * spectrum + 0.15 * matched_spectrum
            spectrum /= np.maximum(spectrum.sum(), EPSILON)
            matched_class, similarity, _ = _top_library_match(spectrum, library_table)

        abundance = np.maximum(weights[:, component_index], EPSILON)
        coefficients, _, r_squared = _fit_effects(abundance, design_matrix)
        reconstruction_fraction = float(np.sum(abundance) / max(total_signal, EPSILON))
        if reconstruction_fraction < min_component_fraction:
            continue

        rt_peak, rt_start, rt_end, width = _component_bounds(chromatogram, time_grid)
        peak_id = f"JC{component_index + 1:03d}_{rt_peak:.2f}"
        intensity = float(abundance.sum() * chromatogram.max())

        component_rows.append(
            {
                "peakId": peak_id,
                "componentRank": component_index + 1,
                "rtPeak": rt_peak,
                "intensity": intensity,
                "rtStart": rt_start,
                "rtEnd": rt_end,
                "halfHeightWidth": width,
                "reconstructionFraction": reconstruction_fraction,
                "supervisionR2": r_squared,
                "matchedClass": matched_class,
                "matchSimilarity": similarity,
            }
        )

        abundance_row: dict[str, float | str] = {"peakId": peak_id}
        abundance_row.update({sample_name: float(value) for sample_name, value in zip(sample_names, abundance, strict=True)})
        abundance_rows.append(abundance_row)

        spectra_row: dict[str, float | str] = {"peakId": peak_id}
        spectra_row.update({f"mz{mz}": float(value) for mz, value in zip(mz_grid, spectrum, strict=True)})
        spectra_rows.append(spectra_row)

        chromatogram_row: dict[str, float | str] = {"peakId": peak_id}
        chromatogram_row.update({f"rt{rt:.2f}": float(value) for rt, value in zip(time_grid, chromatogram, strict=True)})
        chromatogram_rows.append(chromatogram_row)

        effect_row: dict[str, float | str] = {"peakId": peak_id, "supervisionR2": r_squared}
        for label, coefficient in zip(effect_labels, coefficients, strict=True):
            effect_row[label] = float(coefficient)
        effect_rows.append(effect_row)

        match_rows.append(
            {
                "peakId": peak_id,
                "matchedClass": matched_class,
                "cosineSimilarity": similarity,
                "libraryPrior": library_prior,
            }
        )

    if not abundance_rows or not spectra_rows:
        raise RuntimeError("Joint component extraction did not identify any usable components.")

    component_table = pd.DataFrame(component_rows).sort_values(["rtPeak", "componentRank"]).reset_index(drop=True)
    abundance_table = pd.DataFrame(abundance_rows)
    abundance_table = abundance_table.set_index("peakId").loc[component_table["peakId"]].reset_index()
    spectra_table = pd.DataFrame(spectra_rows)
    spectra_table = spectra_table.set_index("peakId").loc[component_table["peakId"]].reset_index()
    chromatograms_table = pd.DataFrame(chromatogram_rows)
    chromatograms_table = chromatograms_table.set_index("peakId").loc[component_table["peakId"]].reset_index()
    effects_table = pd.DataFrame(effect_rows)
    effects_table = effects_table.set_index("peakId").loc[component_table["peakId"]].reset_index()
    matches_table = pd.DataFrame(match_rows)
    matches_table = matches_table.set_index("peakId").loc[component_table["peakId"]].reset_index()

    return JointComponentResult(
        peaks_integrated=abundance_table,
        spectra=spectra_table,
        chromatograms=chromatograms_table,
        components=component_table,
        component_effects=effects_table,
        component_matches=matches_table,
    )


def extract_joint_components(
    csv_data_dir: str | Path,
    output_spectra_dir: str | Path,
    *,
    n_components: int | None = None,
    supervision_strength: float = 0.35,
    max_iter: int = 40,
    min_component_fraction: float = 0.005,
    library_prior: str = "off",
    library_mat_path: str | Path | None = None,
) -> JointComponentResult:
    csv_root = Path(csv_data_dir)
    output_root = Path(output_spectra_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(csv_root.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files were found in {csv_root}.")

    sample_names = [path.stem for path in csv_files]
    tensor = np.stack([_load_matrix_csv(path) for path in csv_files], axis=2)
    result = fit_joint_components_from_tensor(
        tensor,
        time_grid=TIME_GRID,
        mz_grid=MZ_GRID,
        sample_names=sample_names,
        n_components=n_components,
        supervision_strength=supervision_strength,
        max_iter=max_iter,
        min_component_fraction=min_component_fraction,
        library_prior=library_prior,
        library_mat_path=library_mat_path,
    )

    result.components.to_csv(output_root / "tblComponents.csv", index=False)
    result.components.to_csv(output_root / "tblTicPeaks.csv", index=False)
    result.peaks_integrated.to_csv(output_root / "tblPeaksIntegrated.csv", index=False)
    result.peaks_integrated.to_csv(output_root / "tblComponentAbundance.csv", index=False)
    result.spectra.to_csv(output_root / "tblSpectra.csv", index=False)
    result.spectra.to_csv(output_root / "tblComponentSpectra.csv", index=False)
    result.chromatograms.to_csv(output_root / "tblComponentChromatograms.csv", index=False)
    result.component_effects.to_csv(output_root / "tblComponentEffects.csv", index=False)
    result.component_matches.to_csv(output_root / "tblComponentLibraryMatches.csv", index=False)

    return result
