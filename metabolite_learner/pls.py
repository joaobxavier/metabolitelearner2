from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class ShufflingTestResult:
    randomized_mse: np.ndarray
    real_mse: float


@dataclass(slots=True)
class SimplsModel:
    x_mean: np.ndarray
    y_mean: np.ndarray
    x_weights: np.ndarray
    x_loadings: np.ndarray
    y_loadings: np.ndarray
    x_scores: np.ndarray
    y_scores: np.ndarray
    beta: np.ndarray

    def predict(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return self.y_mean + (x - self.x_mean) @ self.beta

    def transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return (x - self.x_mean) @ self.x_weights


class MetaboLiteLearner:
    """Partial least-squares learner aligned with MATLAB plsregress output."""

    def __init__(
        self,
        x: np.ndarray,
        y: np.ndarray,
        kfold: int = 0,
        max_components: int = 30,
        nrandomized: int = 1000,
        random_state: int = 0,
    ) -> None:
        self.x_full_data = np.asarray(x, dtype=float)
        self.y_full_data = np.asarray(y, dtype=float)
        self.maxn = min(max_components, self.x_full_data.shape[0] - 1, self.x_full_data.shape[1], self.y_full_data.shape[1] + self.x_full_data.shape[1])
        self.nrandomized = nrandomized
        self.random_state = random_state
        self.cv_indices = self._build_cv_indices(kfold, self.x_full_data.shape[0], random_state)
        self.kfold = int(self.cv_indices.max())

        (
            self.nopt,
            self.test_sse,
            self.train_sse,
            self.cv_predictions,
            self.nmin,
            self.test_stderr,
        ) = self.optimize_components_and_learn()

        (
            self.model,
            self.beta,
            self.y_pred,
            self.loss,
            self.sse,
            self.x_loadings,
            self.y_loadings,
            self.x_scores,
            self.y_scores,
            self.pctvar,
        ) = self.learn(self.x_full_data, self.y_full_data, self.nopt)

    @staticmethod
    def _build_cv_indices(kfold: int, n_samples: int, random_state: int) -> np.ndarray:
        if kfold == 0:
            return np.arange(1, n_samples + 1, dtype=int)

        rng = np.random.default_rng(random_state)
        assignments = np.tile(np.arange(1, kfold + 1, dtype=int), int(np.ceil(n_samples / kfold)))[:n_samples]
        rng.shuffle(assignments)
        return assignments

    def map_to_latent_space(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        latent_scores = self.model.transform(x)
        predicted_y = self.model.predict(x)
        return latent_scores, predicted_y

    def shuffling_test(self) -> ShufflingTestResult:
        rng = np.random.default_rng(self.random_state)
        randomized = np.zeros(self.nrandomized, dtype=float)
        for idx in range(self.nrandomized):
            y_rand = self.y_full_data[rng.permutation(self.y_full_data.shape[0]), :]
            _, _, kfold_sse, _ = self.cross_validation_evaluation(self.x_full_data, y_rand, self.nopt)
            randomized[idx] = np.mean(kfold_sse)
        return ShufflingTestResult(randomized_mse=randomized, real_mse=float(np.mean(self.test_sse[:, self.nopt - 1])))

    def learn(
        self,
        x: np.ndarray,
        y: np.ndarray,
        n_components: int,
    ) -> tuple[SimplsModel, np.ndarray, np.ndarray, np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        model = self._fit_simpls(x, y, n_components)
        y_pred = model.predict(x)
        loss = (y_pred - y) ** 2
        sse = float(loss.sum())
        beta = np.vstack([model.y_mean.reshape(1, -1) - model.x_mean.reshape(1, -1) @ model.beta, model.beta])
        pctvar = self._calculate_pctvar(x, y, model)
        return (
            model,
            beta,
            y_pred,
            loss,
            sse,
            model.x_loadings,
            model.y_loadings,
            model.x_scores,
            model.y_scores,
            pctvar,
        )

    def cross_validation_evaluation(
        self,
        x: np.ndarray,
        y: np.ndarray,
        n_components: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        y_pred = np.zeros_like(y, dtype=float)
        train_sse = np.zeros(self.kfold, dtype=float)
        kfold_sse = np.zeros(self.kfold, dtype=float)
        beta_distribution = np.zeros((x.shape[1] + 1, y.shape[1], x.shape[0]), dtype=float)

        for fold_index in range(1, self.kfold + 1):
            train_idx = self.cv_indices != fold_index
            test_idx = self.cv_indices == fold_index

            model, beta, _, _, sse, *_ = self.learn(x[train_idx], y[train_idx], n_components)
            predicted = model.predict(x[test_idx])
            y_pred[test_idx] = predicted
            train_sse[fold_index - 1] = sse / np.count_nonzero(train_idx)
            kfold_sse[fold_index - 1] = np.sum((predicted - y[test_idx]) ** 2) / np.count_nonzero(test_idx)

            row_indices = np.flatnonzero(test_idx)
            for row_idx in row_indices:
                beta_distribution[:, :, row_idx] = beta

        return y_pred, train_sse, kfold_sse, beta_distribution

    def optimize_components_and_learn(self) -> tuple[int, np.ndarray, np.ndarray, np.ndarray, int, np.ndarray]:
        train_sse = np.zeros((self.kfold, self.maxn), dtype=float)
        test_sse = np.zeros((self.kfold, self.maxn), dtype=float)
        cv_predictions = np.zeros((self.y_full_data.shape[0], self.y_full_data.shape[1], self.maxn), dtype=float)

        for component_index in range(1, self.maxn + 1):
            y_pred, train_sse_component, test_sse_component, _ = self.cross_validation_evaluation(
                self.x_full_data,
                self.y_full_data,
                component_index,
            )
            cv_predictions[:, :, component_index - 1] = y_pred
            train_sse[:, component_index - 1] = train_sse_component
            test_sse[:, component_index - 1] = test_sse_component

        mean_test_sse = test_sse.mean(axis=0)
        n_min = int(np.argmin(mean_test_sse)) + 1
        std_error = test_sse.std(axis=0, ddof=1) / np.sqrt(test_sse.shape[0])
        min_error = mean_test_sse[n_min - 1] + std_error[n_min - 1]
        candidate_idx = np.where((mean_test_sse > min_error) & (np.arange(1, self.maxn + 1) < n_min))[0]
        n_opt = int(candidate_idx.max() + 1) if candidate_idx.size else n_min
        return n_opt, test_sse, train_sse, cv_predictions, n_min, std_error

    @staticmethod
    def _fit_simpls(x: np.ndarray, y: np.ndarray, n_components: int) -> SimplsModel:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        x_mean = x.mean(axis=0)
        y_mean = y.mean(axis=0)
        x_centered = x - x_mean
        y_centered = y - y_mean

        n_samples, n_features = x_centered.shape
        n_targets = y_centered.shape[1]
        n_components = min(n_components, n_features, n_samples - 1)

        x_scores = np.zeros((n_samples, n_components), dtype=float)
        y_scores = np.zeros((n_samples, n_components), dtype=float)
        x_loadings = np.zeros((n_features, n_components), dtype=float)
        y_loadings = np.zeros((n_targets, n_components), dtype=float)
        x_weights = np.zeros((n_features, n_components), dtype=float)
        v_basis = np.zeros((n_features, n_components), dtype=float)

        covariance = x_centered.T @ y_centered
        projector = np.eye(n_features, dtype=float)

        for component_index in range(n_components):
            _, _, vh = np.linalg.svd(covariance, full_matrices=False)
            response_weight = vh.T[:, 0]
            x_weight = covariance @ response_weight
            x_weight_norm = np.linalg.norm(x_weight)
            if not np.isfinite(x_weight_norm) or x_weight_norm == 0.0:
                break
            x_weight = x_weight / x_weight_norm

            score = x_centered @ x_weight
            score_ss = float(score.T @ score)
            if not np.isfinite(score_ss) or score_ss == 0.0:
                break

            x_loading = (x_centered.T @ score) / score_ss
            y_loading = (y_centered.T @ score) / score_ss
            y_score = y_centered @ y_loading

            x_scores[:, component_index] = score
            y_scores[:, component_index] = y_score
            x_loadings[:, component_index] = x_loading
            y_loadings[:, component_index] = y_loading
            x_weights[:, component_index] = x_weight

            v = projector @ x_loading
            v_norm = np.linalg.norm(v)
            if np.isfinite(v_norm) and v_norm != 0.0:
                v = v / v_norm
                v_basis[:, component_index] = v
                projector = projector - np.outer(v, v)
                covariance = projector @ covariance

        used_components = np.count_nonzero(np.linalg.norm(x_weights, axis=0))
        if used_components == 0:
            raise RuntimeError("SIMPLS failed to identify any latent component.")

        x_scores = x_scores[:, :used_components]
        y_scores = y_scores[:, :used_components]
        x_loadings = x_loadings[:, :used_components]
        y_loadings = y_loadings[:, :used_components]
        x_weights = x_weights[:, :used_components]

        rotation = x_weights @ np.linalg.pinv(x_loadings.T @ x_weights)
        beta = rotation @ y_loadings.T

        return SimplsModel(
            x_mean=x_mean,
            y_mean=y_mean,
            x_weights=rotation,
            x_loadings=x_loadings,
            y_loadings=y_loadings,
            x_scores=x_scores,
            y_scores=y_scores,
            beta=beta,
        )

    @staticmethod
    def _calculate_pctvar(x: np.ndarray, y: np.ndarray, model: SimplsModel) -> np.ndarray:
        x_centered = np.asarray(x, dtype=float) - model.x_mean
        y_centered = np.asarray(y, dtype=float) - model.y_mean
        total_x = np.sum(x_centered**2)
        total_y = np.sum(y_centered**2)

        x_residual = x_centered.copy()
        y_residual = y_centered.copy()
        explained_x: list[float] = []
        explained_y: list[float] = []

        for component_index in range(model.x_scores.shape[1]):
            score = model.x_scores[:, component_index]
            x_loading = model.x_loadings[:, component_index]
            y_loading = model.y_loadings[:, component_index]
            x_hat = np.outer(score, x_loading)
            y_hat = np.outer(score, y_loading)
            explained_x.append(np.sum(x_hat**2) / total_x if total_x else 0.0)
            explained_y.append(np.sum(y_hat**2) / total_y if total_y else 0.0)
            x_residual = x_residual - x_hat
            y_residual = y_residual - y_hat

        return np.vstack([explained_x, explained_y])
