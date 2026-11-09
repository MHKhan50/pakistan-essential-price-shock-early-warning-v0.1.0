"""Chronological splitting and metrics."""
from __future__ import annotations

import math
from collections import namedtuple
from datetime import date
from typing import Dict, List, Sequence, Tuple

from .data import ForecastExample

TemporalSplit = namedtuple("TemporalSplit", "train calibration test")


def chronological_split(examples: Sequence[ForecastExample], train_fraction: float = 0.60,
                        calibration_fraction: float = 0.20) -> TemporalSplit:
    dates = sorted({example.origin_date for example in examples})
    if len(dates) < 10:
        raise ValueError("at least 10 distinct forecast-origin weeks are required")
    if not 0 < train_fraction < 1 or not 0 < calibration_fraction < 1:
        raise ValueError("split fractions must be between 0 and 1")
    if train_fraction + calibration_fraction >= 1:
        raise ValueError("train + calibration fractions must be below 1")
    train_end = max(1, int(len(dates) * train_fraction))
    calibration_end = max(train_end + 1, int(len(dates) * (train_fraction + calibration_fraction)))
    if calibration_end >= len(dates):
        calibration_end = len(dates) - 1
    train_dates = set(dates[:train_end])
    calibration_dates = set(dates[train_end:calibration_end])
    test_dates = set(dates[calibration_end:])
    train = [x for x in examples if x.origin_date in train_dates]
    calibration = [x for x in examples if x.origin_date in calibration_dates]
    test = [x for x in examples if x.origin_date in test_dates]
    if not train or not calibration or not test:
        raise ValueError("temporal split produced an empty partition")
    assert max(x.origin_date for x in train) < min(x.origin_date for x in calibration)
    assert max(x.origin_date for x in calibration) < min(x.origin_date for x in test)
    return TemporalSplit(train, calibration, test)


def _binary_metrics(actual: Sequence[bool], predicted: Sequence[bool]) -> Dict[str, float]:
    tp = sum(1 for a, p in zip(actual, predicted) if a and p)
    fp = sum(1 for a, p in zip(actual, predicted) if not a and p)
    fn = sum(1 for a, p in zip(actual, predicted) if a and not p)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "true_positive": float(tp), "false_positive": float(fp), "false_negative": float(fn)}


def calculate_metrics(actual: Sequence[float], predicted: Sequence[float], lower: Sequence[float],
                      upper: Sequence[float], shock_threshold_log: float) -> Dict[str, float]:
    if not actual or not (len(actual) == len(predicted) == len(lower) == len(upper)):
        raise ValueError("metric arrays must be non-empty and aligned")
    errors = [p - a for a, p in zip(actual, predicted)]
    mae = sum(abs(value) for value in errors) / len(errors)
    rmse = math.sqrt(sum(value * value for value in errors) / len(errors))
    shocks = [value >= shock_threshold_log for value in actual]
    watch = [hi >= shock_threshold_log for hi in upper]
    alert = [lo >= shock_threshold_log for lo in lower]
    watch_metrics = _binary_metrics(shocks, watch)
    alert_metrics = _binary_metrics(shocks, alert)
    coverage = sum(1 for a, lo, hi in zip(actual, lower, upper) if lo <= a <= hi) / len(actual)
    width = sum(hi - lo for lo, hi in zip(lower, upper)) / len(actual)
    result = {
        "n_test": float(len(actual)),
        "n_shocks": float(sum(shocks)),
        "mae_log_return": mae,
        "rmse_log_return": rmse,
        "interval_coverage": coverage,
        "mean_interval_width": width,
        "watch_precision": watch_metrics["precision"],
        "watch_recall": watch_metrics["recall"],
        "watch_f1": watch_metrics["f1"],
        "watch_false_positives": watch_metrics["false_positive"],
        "watch_false_per_100": 100.0 * watch_metrics["false_positive"] / len(actual),
        "alert_precision": alert_metrics["precision"],
        "alert_recall": alert_metrics["recall"],
        "alert_f1": alert_metrics["f1"],
        "alert_false_positives": alert_metrics["false_positive"],
    }
    return result
