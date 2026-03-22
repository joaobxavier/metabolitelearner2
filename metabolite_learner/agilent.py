from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd

TIME_GRID = np.round(np.arange(6.0, 30.0 + 0.01, 0.01), 2)
MZ_GRID = np.arange(50, 600, 1)
EXPECTED_SHAPE = (TIME_GRID.size, MZ_GRID.size)
DEFAULT_PRECISION = 3

Loader = Callable[[Path], np.ndarray]


def _read_prefixed_string(handle, offset: int) -> str:
    handle.seek(offset)
    length = int(np.fromfile(handle, dtype=np.dtype("u1"), count=1)[0])
    payload = np.fromfile(handle, dtype=np.dtype("u1"), count=length).tobytes()
    return payload.decode("latin1", errors="ignore").strip("\x00 ").strip()


def _read_big_endian_array(handle, offset: int, dtype: str, count: int, *, stride: int = 0) -> np.ndarray:
    handle.seek(offset)
    values_dtype = np.dtype(dtype)
    if stride == 0:
        return np.fromfile(handle, dtype=values_dtype, count=count)

    values = np.empty(count, dtype=values_dtype)
    for index in range(count):
        values[index] = np.fromfile(handle, dtype=values_dtype, count=1)[0]
        if stride:
            handle.seek(stride, 1)
    return values


def _load_agilent_ms_file(ms_path: Path, precision: int = DEFAULT_PRECISION) -> np.ndarray:
    with ms_path.open("rb") as handle:
        version = _read_prefixed_string(handle, 0)
        if version not in {"2", "20"}:
            raise ValueError(f"Unsupported Agilent MS version {version!r} in {ms_path}.")

        scans = int(_read_big_endian_array(handle, 278, ">u4", 1)[0])
        tic_offset = int(_read_big_endian_array(handle, 260, ">i4", 1)[0]) * 2 - 2
        xic_offsets = _read_big_endian_array(handle, tic_offset, ">i4", scans, stride=8).astype(np.int64) * 2 - 2

        time = _read_big_endian_array(handle, tic_offset + 4, ">i4", scans, stride=8).astype(float) / 60000.0

        mz_values: list[np.ndarray] = []
        intensity_values: list[np.ndarray] = []
        counts: list[int] = []

        for offset in xic_offsets:
            scan_size = int((_read_big_endian_array(handle, int(offset), ">i2", 1)[0] - 18) / 2 + 2)
            counts.append(scan_size)
            mz_values.append(_read_big_endian_array(handle, int(offset) + 18, ">u2", scan_size, stride=2))
            intensity_values.append(_read_big_endian_array(handle, int(offset) + 20, ">u2", scan_size, stride=2))

    mz = np.concatenate(mz_values).astype(np.float64) / 20.0
    raw_intensity = np.concatenate(intensity_values).astype(np.uint16)
    intensity = np.bitwise_and(raw_intensity, np.uint16(16383)).astype(np.float64) * (
        8.0 ** np.abs(np.right_shift(raw_intensity, 14).astype(np.int16))
    )

    mz = np.round(mz * 10**precision) / 10**precision
    unique_mz = np.unique(mz)

    index_end = np.cumsum(counts)
    index_start = np.concatenate(([0], index_end[:-1]))
    xic = np.zeros((time.size, unique_mz.size), dtype=float)
    columns = np.searchsorted(unique_mz, mz)
    for scan_index, (start, end) in enumerate(zip(index_start, index_end)):
        xic[scan_index, columns[start:end]] = intensity[start:end]

    rebinned = np.zeros((time.size, MZ_GRID.size), dtype=float)
    for mz_index in range(MZ_GRID.size - 1):
        mask = (unique_mz >= MZ_GRID[mz_index]) & (unique_mz < MZ_GRID[mz_index + 1])
        if np.any(mask):
            rebinned[:, mz_index] = xic[:, mask].sum(axis=1)

    last_mask = unique_mz >= MZ_GRID[-1]
    if np.any(last_mask):
        rebinned[:, -1] = xic[:, last_mask].sum(axis=1)

    matrix = np.empty(EXPECTED_SHAPE, dtype=float)
    for mz_index in range(rebinned.shape[1]):
        matrix[:, mz_index] = np.interp(TIME_GRID, time, rebinned[:, mz_index], left=np.nan, right=np.nan)
    return matrix


def _load_tic_front_file(tic_path: Path) -> np.ndarray:
    separator = "\t" if tic_path.suffix.lower() == ".tsv" else ","
    tic = pd.read_csv(tic_path, sep=separator, skiprows=2, header=None, usecols=[0, 1]).to_numpy(dtype=float)
    if tic.ndim != 2 or tic.shape[1] != 2:
        raise ValueError(f"Expected retention-time/intensity pairs in {tic_path}.")

    order = np.argsort(tic[:, 0], kind="stable")
    retention_time = tic[order, 0]
    intensity = tic[order, 1]
    resampled = np.interp(TIME_GRID, retention_time, intensity, left=0.0, right=0.0)

    matrix = np.zeros(EXPECTED_SHAPE, dtype=float)
    matrix[:, 0] = resampled
    return matrix


def _identity_matrix_loader(sample_path: Path) -> np.ndarray:
    ms_candidates = sorted(path for path in sample_path.iterdir() if path.suffix.lower() == ".ms")
    if ms_candidates:
        return _load_agilent_ms_file(ms_candidates[0])

    candidates = [
        sample_path / "matrix.csv",
        sample_path / "xic.csv",
        sample_path / f"{sample_path.stem}.csv",
        sample_path / "tic_front.csv",
        sample_path / "tic_front.tsv",
    ]
    for candidate in candidates:
        if candidate.exists():
            if candidate.name.startswith("tic_front."):
                return _load_tic_front_file(candidate)
            return pd.read_csv(candidate, header=None).to_numpy(dtype=float)

    raise FileNotFoundError(
        "No supported Agilent raw-data, matrix, or TIC file was found inside the sample directory. "
        "The default loader looks for *.ms, matrix.csv, xic.csv, <sample>.csv, tic_front.csv, or tic_front.tsv."
    )


def convert_agilent_to_csv(
    data_dir: str | Path,
    output_dir: str | Path,
    loader: Loader | None = None,
    sample_dirs: Iterable[Path] | None = None,
) -> list[Path]:
    """Convert Agilent sample directories into the repo's CSV matrix format.

    The original MATLAB implementation relied on `ImportAgilent` from the external
    chromatography-master toolbox. The Python port exposes the same workflow step but
    makes the raw-data decoder injectable because Agilent `.D` directories are a
    proprietary vendor format.

    Parameters
    ----------
    data_dir:
        Directory that contains Agilent `.D` sample directories.
    output_dir:
        Destination for the generated CSV matrix files.
    loader:
        Callable that receives a sample directory and returns a 2401x550 matrix.
        When omitted, the function looks for raw `*.ms` files first and then falls
        back to matrix/TIC exports inside each sample directory.
    sample_dirs:
        Optional explicit iterable of sample directories to process.
    """

    input_root = Path(data_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    if sample_dirs is None:
        sample_dirs = sorted(path for path in input_root.iterdir() if path.suffix == ".D")
    else:
        sample_dirs = sorted(sample_dirs)

    if not sample_dirs:
        raise FileNotFoundError(f"No Agilent sample directories (*.D) found in {input_root}.")

    matrix_loader = loader or _identity_matrix_loader
    written_files: list[Path] = []

    for sample_dir in sample_dirs:
        matrix = np.asarray(matrix_loader(sample_dir), dtype=float)
        if matrix.shape != EXPECTED_SHAPE:
            raise ValueError(
                f"Expected matrix shape {EXPECTED_SHAPE} for {sample_dir.name}, "
                f"but received {matrix.shape}."
            )
        sample_name = sample_dir.stem
        destination = output_root / f"{sample_name}.csv"
        pd.DataFrame(matrix).to_csv(destination, header=False, index=False)
        written_files.append(destination)

    return written_files
