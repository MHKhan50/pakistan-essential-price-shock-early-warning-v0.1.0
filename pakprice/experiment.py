"""End-to-end, chronological price-shock forecasting experiment."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import median
from typing import Dict, List, Sequence, Tuple

from .data import ForecastExample, build_examples, load_canonical_csv
from .evaluation import calculate_metrics, chronological_split
from .model import RidgeRegressor, conformal_radius, group_medians

FEATURE_NAMES = ["return_lag_1", "return_lag_2", "return_lag_3", "return_lag_4",
                 "mean_return_4w", "std_return_4w", "momentum_2v2"]


def _predict_group_median(examples: Sequence[ForecastExample], medians, fallback: float) -> List[float]:
    return [medians.get((x.city_code, x.item_number), fallback) for x in examples]


def _write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(input_path: Path, output_dir: Path, shock_threshold: float = 0.05,
                   alpha: float = 0.10, ridge_alpha: float = 5.0) -> Dict[str, object]:
    observations = load_canonical_csv(input_path)
    examples = build_examples(observations, shock_threshold=shock_threshold)
    if len(examples) < 30:
        raise ValueError("Only {} forecast examples were built; at least 30 are required for this prototype".format(len(examples)))
    split = chronological_split(examples)
    train_x = [list(x.features) for x in split.train]
    train_y = [x.target_log_return for x in split.train]
    calibration_x = [list(x.features) for x in split.calibration]
    calibration_y = [x.target_log_return for x in split.calibration]
    test_x = [list(x.features) for x in split.test]
    test_y = [x.target_log_return for x in split.test]

    ridge = RidgeRegressor(alpha=ridge_alpha).fit(train_x, train_y)
    medians, global_median = group_medians(split.train)
    model_predictions = {
        "zero_change": ([0.0] * len(split.calibration), [0.0] * len(split.test)),
        "group_median": (
            _predict_group_median(split.calibration, medians, global_median),
            _predict_group_median(split.test, medians, global_median),
        ),
        "pooled_ridge": (ridge.predict(calibration_x), ridge.predict(test_x)),
    }
    threshold_log = math.log1p(shock_threshold)
    metrics_rows: List[Dict[str, object]] = []
    prediction_rows: List[Dict[str, object]] = []
    model_radii = {}

    for model_name, (cal_predictions, test_predictions) in model_predictions.items():
        residuals = [actual - predicted for actual, predicted in zip(calibration_y, cal_predictions)]
        radius = conformal_radius(residuals, alpha=alpha)
        model_radii[model_name] = radius
        lower = [prediction - radius for prediction in test_predictions]
        upper = [prediction + radius for prediction in test_predictions]
        metric = calculate_metrics(test_y, test_predictions, lower, upper, threshold_log)
        metrics_rows.append({"model": model_name, "conformal_radius_log_return": radius,
                             "nominal_interval_coverage": 1.0 - alpha, **metric})
        for example, prediction, lo, hi in zip(split.test, test_predictions, lower, upper):
            state = "ALERT" if lo >= threshold_log else ("WATCH" if hi >= threshold_log else "NORMAL")
            prediction_rows.append({
                "model": model_name,
                "city_code": example.city_code,
                "city": example.city,
                "item_number": example.item_number,
                "item_description": example.item_description,
                "unit": example.unit,
                "origin_date": example.origin_date.isoformat(),
                "target_date": example.target_date.isoformat(),
                "actual_log_return": "{:.8f}".format(example.target_log_return),
                "actual_pct_change": "{:.6f}".format(100.0 * math.expm1(example.target_log_return)),
                "is_shock": int(example.is_shock),
                "predicted_log_return": "{:.8f}".format(prediction),
                "lower_log_return": "{:.8f}".format(lo),
                "upper_log_return": "{:.8f}".format(hi),
                "alert_state": state,
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "metrics.csv", list(metrics_rows[0].keys()), metrics_rows)
    _write_csv(output_dir / "predictions.csv", list(prediction_rows[0].keys()), prediction_rows)
    summary = {
        "project": "PakPriceSentinel",
        "version": "0.1.0",
        "input_file": str(input_path),
        "observations_after_cleaning": len(observations),
        "forecast_examples": len(examples),
        "distinct_origin_weeks": len({x.origin_date for x in examples}),
        "train_examples": len(split.train),
        "calibration_examples": len(split.calibration),
        "test_examples": len(split.test),
        "train_origin_end": max(x.origin_date for x in split.train).isoformat(),
        "calibration_origin_start": min(x.origin_date for x in split.calibration).isoformat(),
        "calibration_origin_end": max(x.origin_date for x in split.calibration).isoformat(),
        "test_origin_start": min(x.origin_date for x in split.test).isoformat(),
        "test_origin_end": max(x.origin_date for x in split.test).isoformat(),
        "shock_threshold_pct": 100.0 * shock_threshold,
        "conformal_alpha": alpha,
        "ridge_alpha": ridge_alpha,
        "feature_names": FEATURE_NAMES,
        "conformal_radii_log_return": model_radii,
        "data_integrity_note": "Only positive average prices marked reported are retained; reported_zero and missing cells are excluded.",
        "synthetic_data_warning": "If the input was generated by scripts/generate_synthetic, results are software checks only, not evidence about real Pakistani prices.",
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary
