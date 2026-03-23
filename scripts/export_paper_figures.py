from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FOLDS_DIR = ROOT / "data" / "original_study" / "folds"
PAPER_FIGURES_DIR = ROOT / "paper" / "figures"

EXPORTS = {
    "figure_1.png": "figure_1_predictive_performance.png",
    "figure_2.png": "figure_2_variance_explained.png",
    "figure_3.png": "figure_3_interpretability.png",
}


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


def export_paper_figures() -> list[Path]:
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source_name, target_name in EXPORTS.items():
        image = mpimg.imread(FOLDS_DIR / source_name)
        cropped = _crop_whitespace(image)
        target = PAPER_FIGURES_DIR / target_name
        plt.imsave(target, cropped)
        written.append(target)
    return written


if __name__ == "__main__":
    for path in export_paper_figures():
        print(path)
