import csv
import math
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from pakprice.data import PriceObservation, build_examples, load_canonical_csv, normalize_raw_csv
from pakprice.evaluation import chronological_split
from pakprice.experiment import run_experiment
from pakprice.model import RidgeRegressor, conformal_radius
from scripts.generate_synthetic import generate


class DataPipelineTests(unittest.TestCase):
    def test_normalizer_keeps_only_reported_average_positive_prices(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.csv"
            clean = Path(temp) / "clean.csv"
            fields = ["week_end_date", "item_number", "item_description", "unit", "city_code", "city",
                      "price_type", "price_pkr", "availability_status", "source_url"]
            rows = [
                ["2026-01-01", "1", "Rice", "kg", "C1", "City", "avg", "100", "reported", "pbs"],
                ["2026-01-01", "1", "Rice", "kg", "C1", "City", "min", "95", "reported", "pbs"],
                ["2026-01-08", "1", "Rice", "kg", "C1", "City", "avg", "0", "reported_zero", "pbs"],
                ["2026-01-15", "1", "Rice", "kg", "C1", "City", "avg", "", "blank", "pbs"],
            ]
            with raw.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            self.assertEqual(normalize_raw_csv(raw, clean), 1)
            observations = load_canonical_csv(clean)
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0].price_pkr, 100.0)

    def test_duplicate_average_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.csv"
            fields = ["week_end_date", "item_number", "item_description", "unit", "city_code", "city",
                      "price_type", "price_pkr", "availability_status", "source_url"]
            row = ["2026-01-01", "1", "Rice", "kg", "C1", "City", "avg", "100", "reported", "pbs"]
            with raw.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerow(row)
                writer.writerow(row)
            with self.assertRaises(ValueError):
                normalize_raw_csv(raw, Path(temp) / "clean.csv")

    def test_gap_prevents_forecast_example(self):
        observations = []
        start = date(2026, 1, 1)
        for index in range(9):
            day = start + timedelta(days=7 * index)
            if index == 5:
                continue
            observations.append(PriceObservation(day, "1", "Rice", "kg", "C1", "City", 100.0 + index))
        examples = build_examples(observations)
        self.assertEqual(examples, [])

    def test_future_target_change_does_not_change_its_own_features(self):
        start = date(2026, 1, 1)
        original = [PriceObservation(start + timedelta(days=7 * i), "1", "Rice", "kg", "C1", "City", 100 + i)
                    for i in range(8)]
        changed = list(original)
        changed[-1] = PriceObservation(changed[-1].week_end_date, "1", "Rice", "kg", "C1", "City", 500.0)
        first = build_examples(original)
        second = build_examples(changed)
        self.assertEqual(first[-1].features, second[-1].features)
        self.assertNotEqual(first[-1].target_log_return, second[-1].target_log_return)


class ModelTests(unittest.TestCase):
    def test_ridge_learns_linear_relationship(self):
        x = [[float(i), float(i % 3)] for i in range(1, 30)]
        y = [2.0 + 0.5 * row[0] - 0.25 * row[1] for row in x]
        model = RidgeRegressor(alpha=1e-5).fit(x, y)
        prediction = model.predict(x)
        mae = sum(abs(a - b) for a, b in zip(y, prediction)) / len(y)
        self.assertLess(mae, 0.02)

    def test_conformal_quantile(self):
        self.assertAlmostEqual(conformal_radius([1, -2, 3, -4], alpha=0.25), 4.0)

    def test_chronological_split_has_no_date_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.csv"
            clean = Path(temp) / "clean.csv"
            generate(raw, weeks=40, cities=2, items=2, seed=17)
            normalize_raw_csv(raw, clean)
            examples = build_examples(load_canonical_csv(clean))
            split = chronological_split(examples)
            self.assertLess(max(x.origin_date for x in split.train), min(x.origin_date for x in split.calibration))
            self.assertLess(max(x.origin_date for x in split.calibration), min(x.origin_date for x in split.test))

    def test_end_to_end_experiment_writes_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "synthetic_raw.csv"
            clean = Path(temp) / "synthetic_clean.csv"
            out = Path(temp) / "results"
            generate(raw, weeks=52, cities=3, items=4, seed=29)
            normalize_raw_csv(raw, clean)
            summary = run_experiment(clean, out)
            self.assertGreater(summary["test_examples"], 0)
            self.assertTrue((out / "metrics.csv").is_file())
            self.assertTrue((out / "predictions.csv").is_file())
            self.assertTrue((out / "summary.json").is_file())
            with (out / "metrics.csv").open("r", encoding="utf-8") as handle:
                models = {row["model"] for row in csv.DictReader(handle)}
            self.assertEqual(models, {"zero_change", "group_median", "pooled_ridge"})


if __name__ == "__main__":
    unittest.main()
