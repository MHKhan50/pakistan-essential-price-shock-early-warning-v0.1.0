"""Generate clearly labelled synthetic price panels for tests and smoke runs."""
import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

FIELDS = ["week_end_date", "item_number", "item_description", "unit", "city_code", "city",
          "price_type", "price_pkr", "availability_status", "source_url"]


def generate(path: Path, weeks: int = 52, cities: int = 4, items: int = 6, seed: int = 20261109) -> int:
    if weeks < 20 or cities < 1 or items < 1:
        raise ValueError("Use at least 20 weeks, one city and one item")
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    start = date(2025, 10, 23)
    rows = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for city_index in range(cities):
            city = "SyntheticCity{:02d}".format(city_index + 1)
            city_code = "S{:02d}".format(city_index + 1)
            for item_index in range(items):
                item_number = str(item_index + 1)
                description = "Synthetic staple {:02d}".format(item_index + 1)
                unit = "kg"
                level = 45.0 + 13.0 * item_index + 4.0 * city_index
                for week in range(weeks):
                    drift = 0.0015 + 0.003 * math.sin(2.0 * math.pi * week / 13.0)
                    level *= math.exp(drift + rng.gauss(0.0, 0.009))
                    # Deliberately injected artificial shocks; these are not observed market events.
                    if week in (22 + (city_index + item_index) % 4, 38 + (city_index * 2 + item_index) % 5):
                        level *= 1.12
                    day = (start + timedelta(days=7 * week)).isoformat()
                    for price_type, factor in (("min", 0.96), ("avg", 1.0), ("max", 1.04)):
                        writer.writerow({
                            "week_end_date": day,
                            "item_number": item_number,
                            "item_description": description,
                            "unit": unit,
                            "city_code": city_code,
                            "city": city,
                            "price_type": price_type,
                            "price_pkr": "{:.6f}".format(level * factor),
                            "availability_status": "reported",
                            "source_url": "SYNTHETIC_ONLY_NOT_PBS",
                        })
                        rows += 1
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/synthetic/demo_prices.csv"))
    parser.add_argument("--weeks", type=int, default=52)
    parser.add_argument("--cities", type=int, default=4)
    parser.add_argument("--items", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20261109)
    args = parser.parse_args()
    count = generate(args.out, args.weeks, args.cities, args.items, args.seed)
    print("Generated {} SYNTHETIC rows at {} (not real Pakistani market observations).".format(count, args.out))


if __name__ == "__main__":
    main()
