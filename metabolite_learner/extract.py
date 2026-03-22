from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths

TIME_GRID = np.round(np.arange(6.0, 30.0 + 0.01, 0.01), 2)
MZ_GRID = np.arange(50, 600, 1)
EXPECTED_SHAPE = (TIME_GRID.size, MZ_GRID.size)


def _load_matrix_csv(path: Path) -> np.ndarray:
    matrix = pd.read_csv(path, header=None).to_numpy(dtype=float)
    if matrix.shape != EXPECTED_SHAPE:
        raise ValueError(f"{path} has shape {matrix.shape}, expected {EXPECTED_SHAPE}.")
    return matrix


def extract_spectra_and_integrate(
    csv_data_dir: str | Path,
    output_spectra_dir: str | Path,
    *,
    prominence: float | None = None,
    distance: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract bulk TIC peaks and integrated spectra from matrix CSVs."""

    csv_root = Path(csv_data_dir)
    output_root = Path(output_spectra_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(csv_root.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files were found in {csv_root}.")

    sample_names = [path.stem for path in csv_files]
    sample_matrices = {path.stem: _load_matrix_csv(path) for path in csv_files}

    sample_tic = pd.DataFrame({"time": TIME_GRID})
    for sample_name, matrix in sample_matrices.items():
        sample_tic[sample_name] = matrix.sum(axis=1)

    bulk_tic = sample_tic[sample_names].sum(axis=1).to_numpy(dtype=float)
    effective_prominence = prominence if prominence is not None else np.quantile(bulk_tic, 0.90) * 0.02
    peaks, properties = find_peaks(bulk_tic, prominence=effective_prominence, distance=distance)
    if peaks.size == 0:
        raise RuntimeError("No TIC peaks were detected. Consider reducing the prominence threshold.")

    widths, _, left_ips, right_ips = peak_widths(bulk_tic, peaks, rel_height=0.5)
    left_idx = np.clip(np.floor(left_ips).astype(int), 0, len(TIME_GRID) - 1)
    right_idx = np.clip(np.ceil(right_ips).astype(int), 0, len(TIME_GRID) - 1)

    peak_rows: list[dict[str, float]] = []
    integrated_rows: list[dict[str, float]] = []
    spectra_rows: list[dict[str, float]] = []

    for peak_index, peak_pos in enumerate(peaks):
        peak_id = float(TIME_GRID[peak_pos])
        rt_start = float(TIME_GRID[left_idx[peak_index]])
        rt_end = float(TIME_GRID[right_idx[peak_index]])
        peak_rows.append(
            {
                "peakId": peak_id,
                "rtPeak": peak_id,
                "intensity": float(bulk_tic[peak_pos]),
                "rtStart": rt_start,
                "rtEnd": rt_end,
                "halfHeightWidth": float(widths[peak_index] * 0.01),
            }
        )

        integrated_row: dict[str, float] = {"peakId": peak_id}
        combined_spectrum = np.zeros(MZ_GRID.size, dtype=float)
        window = slice(left_idx[peak_index], right_idx[peak_index] + 1)
        for sample_name, matrix in sample_matrices.items():
            peak_area = matrix[window, :].sum()
            integrated_row[sample_name] = float(peak_area)
            combined_spectrum += matrix[window, :].sum(axis=0)
        integrated_rows.append(integrated_row)

        spectra_row = {"peakId": peak_id}
        spectra_row.update({f"mz{mz}": float(value) for mz, value in zip(MZ_GRID, combined_spectrum, strict=True)})
        spectra_rows.append(spectra_row)

    peak_table = pd.DataFrame(peak_rows).sort_values("peakId").reset_index(drop=True)
    peaks_integrated = pd.DataFrame(integrated_rows).sort_values("peakId").reset_index(drop=True)
    spectra = pd.DataFrame(spectra_rows).sort_values("peakId").reset_index(drop=True)

    peak_table.to_csv(output_root / "tblTicPeaks.csv", index=False)
    peaks_integrated.to_csv(output_root / "tblPeaksIntegrated.csv", index=False)
    spectra.to_csv(output_root / "tblSpectra.csv", index=False)

    return peaks_integrated, spectra
