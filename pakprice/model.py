"""Small standard-library forecasting and calibration models."""
from __future__ import annotations

import math
from statistics import median
from typing import Dict, List, Sequence, Tuple

from .data import ForecastExample


def _solve_linear_system(matrix: List[List[float]], vector: List[float]) -> List[float]:
    n = len(vector)
    augmented = [matrix[i][:] + [vector[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            raise ValueError("Ridge system is singular; increase alpha")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [value / scale for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            if factor:
                augmented[row] = [
                    augmented[row][j] - factor * augmented[col][j] for j in range(n + 1)
                ]
    return [augmented[i][-1] for i in range(n)]


class RidgeRegressor:
    """Standardised ridge regression with an unpenalised intercept."""
    def __init__(self, alpha: float = 5.0) -> None:
        if alpha <= 0:
            raise ValueError("alpha must be positive")
        self.alpha = alpha
        self.means: List[float] = []
        self.scales: List[float] = []
        self.coefficients: List[float] = []

    def fit(self, features: Sequence[Sequence[float]], targets: Sequence[float]) -> "RidgeRegressor":
        if not features or len(features) != len(targets):
            raise ValueError("features and targets must be non-empty and aligned")
        dimension = len(features[0])
        if any(len(row) != dimension for row in features):
            raise ValueError("inconsistent feature dimensions")
        self.means = [sum(row[j] for row in features) / len(features) for j in range(dimension)]
        self.scales = []
        for j in range(dimension):
            variance = sum((row[j] - self.means[j]) ** 2 for row in features) / len(features)
            scale = math.sqrt(variance)
            self.scales.append(scale if scale > 1e-12 else 1.0)
        design = [[1.0] + [(row[j] - self.means[j]) / self.scales[j] for j in range(dimension)] for row in features]
        width = dimension + 1
        gram = [[0.0] * width for _ in range(width)]
        rhs = [0.0] * width
        for row, target in zip(design, targets):
            for i in range(width):
                rhs[i] += row[i] * target
                for j in range(width):
                    gram[i][j] += row[i] * row[j]
        for i in range(1, width):
            gram[i][i] += self.alpha
        self.coefficients = _solve_linear_system(gram, rhs)
        return self

    def predict_one(self, row: Sequence[float]) -> float:
        if not self.coefficients:
            raise RuntimeError("model has not been fitted")
        if len(row) != len(self.means):
            raise ValueError("feature dimension mismatch")
        standardised = [(row[j] - self.means[j]) / self.scales[j] for j in range(len(row))]
        return self.coefficients[0] + sum(self.coefficients[j + 1] * standardised[j] for j in range(len(row)))

    def predict(self, features: Sequence[Sequence[float]]) -> List[float]:
        return [self.predict_one(row) for row in features]


def group_medians(examples: Sequence[ForecastExample]) -> Tuple[Dict[Tuple[str, str], float], float]:
    by_group: Dict[Tuple[str, str], List[float]] = {}
    all_targets = []
    for example in examples:
        key = (example.city_code, example.item_number)
        by_group.setdefault(key, []).append(example.target_log_return)
        all_targets.append(example.target_log_return)
    if not all_targets:
        raise ValueError("cannot fit group medians without training examples")
    return {key: median(values) for key, values in by_group.items()}, median(all_targets)


def conformal_radius(residuals: Sequence[float], alpha: float = 0.10) -> float:
    """Finite-sample split-conformal absolute-residual quantile."""
    if not residuals:
        raise ValueError("at least one calibration residual is required")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    ordered = sorted(abs(value) for value in residuals)
    rank = int(math.ceil((len(ordered) + 1) * (1.0 - alpha)))
    rank = min(max(rank, 1), len(ordered))
    return ordered[rank - 1]
