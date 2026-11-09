"""Data validation and leakage-safe city/item panel construction."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple

RAW_REQUIRED = {
    "week_end_date", "item_number", "item_description", "unit", "city_code",
    "city", "price_type", "price_pkr", "availability_status", "source_url",
}
CANONICAL_FIELDS = [
    "week_end_date", "item_number", "item_description", "unit", "city_code",
    "city", "price_pkr", "source_url",
]


@dataclass(frozen=True)
class PriceObservation:
    week_end_date: date
    item_number: str
    item_description: str
    unit: str
    city_code: str
    city: str
    price_pkr: float
    source_url: str = ""

    @property
    def group_key(self) -> Tuple[str, str]:
        return (self.city_code, self.item_number)


@dataclass(frozen=True)
class ForecastExample:
    city_code: str
    city: str
    item_number: str
    item_description: str
    unit: str
    origin_date: date
    target_date: date
    features: Tuple[float, ...]
    target_log_return: float
    is_shock: bool


def _parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("Unsupported week_end_date: {!r}".format(value))


def normalize_raw_csv(input_path: Path, output_path: Path) -> int:
    """Filter a PBS-derived raw CSV and write a canonical positive-price panel."""
    with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(RAW_REQUIRED - fields)
        if missing:
            raise ValueError("Raw CSV is missing required columns: {}".format(", ".join(missing)))
        selected: Dict[Tuple[str, str, str], PriceObservation] = {}
        for line_number, row in enumerate(reader, start=2):
            if (row.get("price_type") or "").strip().lower() != "avg":
                continue
            if (row.get("availability_status") or "").strip().lower() != "reported":
                continue
            raw_price = (row.get("price_pkr") or "").strip()
            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(price) or price <= 0:
                continue
            week = _parse_date(row["week_end_date"]).isoformat()
            item_number = str(row["item_number"]).strip()
            city_code = str(row["city_code"]).strip()
            if not item_number or not city_code:
                continue
            key = (week, city_code, item_number)
            if key in selected:
                raise ValueError("Duplicate average-price key at input line {}: {}".format(line_number, key))
            selected[key] = PriceObservation(
                week_end_date=date.fromisoformat(week),
                item_number=item_number,
                item_description=(row.get("item_description") or "").strip(),
                unit=(row.get("unit") or "").strip(),
                city_code=city_code,
                city=(row.get("city") or "").strip(),
                price_pkr=price,
                source_url=(row.get("source_url") or "").strip(),
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(selected.values(), key=lambda x: (x.week_end_date, x.city_code, x.item_number))
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        for obs in ordered:
            writer.writerow({
                "week_end_date": obs.week_end_date.isoformat(),
                "item_number": obs.item_number,
                "item_description": obs.item_description,
                "unit": obs.unit,
                "city_code": obs.city_code,
                "city": obs.city,
                "price_pkr": "{:.8f}".format(obs.price_pkr),
                "source_url": obs.source_url,
            })
    return len(ordered)


def load_canonical_csv(path: Path) -> List[PriceObservation]:
    observations: List[PriceObservation] = []
    seen = set()
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(set(CANONICAL_FIELDS) - fields)
        if missing:
            raise ValueError("Canonical CSV is missing columns: {}".format(", ".join(missing)))
        for line_number, row in enumerate(reader, start=2):
            price = float(row["price_pkr"])
            if not math.isfinite(price) or price <= 0:
                raise ValueError("Canonical prices must be finite and positive (line {})".format(line_number))
            week = _parse_date(row["week_end_date"])
            item_number = row["item_number"].strip()
            city_code = row["city_code"].strip()
            key = (week, city_code, item_number)
            if key in seen:
                raise ValueError("Duplicate canonical city/item/week key: {}".format(key))
            seen.add(key)
            observations.append(PriceObservation(
                week_end_date=week,
                item_number=item_number,
                item_description=row["item_description"].strip(),
                unit=row["unit"].strip(),
                city_code=city_code,
                city=row["city"].strip(),
                price_pkr=price,
                source_url=row.get("source_url", "").strip(),
            ))
    return observations


MIN_GAP_DAYS = 6
MAX_GAP_DAYS = 8


def build_examples(
    observations: Sequence[PriceObservation], shock_threshold: float = 0.05
) -> List[ForecastExample]:
    """Create one-week-ahead examples using four strictly historical weekly returns."""
    if shock_threshold <= 0:
        raise ValueError("shock_threshold must be positive")
    grouped = defaultdict(list)
    for obs in observations:
        grouped[obs.group_key].append(obs)

    examples: List[ForecastExample] = []
    threshold_log = math.log1p(shock_threshold)
    for group in sorted(grouped):
        series = sorted(grouped[group], key=lambda x: x.week_end_date)
        for index in range(4, len(series) - 1):
            window = series[index - 4:index + 2]
            # PBS releases are weekly but some move by a day around holidays (6- or 8-day gaps);
            # a gap outside MIN_GAP_DAYS..MAX_GAP_DAYS means a missing release, so the window is skipped.
            if any(not MIN_GAP_DAYS <= (window[j + 1].week_end_date - window[j].week_end_date).days <= MAX_GAP_DAYS
                   for j in range(5)):
                continue
            current = series[index]
            following = series[index + 1]
            returns = [
                math.log(series[k].price_pkr / series[k - 1].price_pkr)
                for k in range(index, index - 4, -1)
            ]
            recent_mean = mean(returns)
            recent_std = math.sqrt(sum((value - recent_mean) ** 2 for value in returns) / len(returns))
            momentum = mean(returns[:2]) - mean(returns[2:])
            features = tuple(returns + [recent_mean, recent_std, momentum])
            target = math.log(following.price_pkr / current.price_pkr)
            examples.append(ForecastExample(
                city_code=current.city_code,
                city=current.city,
                item_number=current.item_number,
                item_description=current.item_description,
                unit=current.unit,
                origin_date=current.week_end_date,
                target_date=following.week_end_date,
                features=features,
                target_log_return=target,
                is_shock=target >= threshold_log,
            ))
    return sorted(examples, key=lambda x: (x.origin_date, x.city_code, x.item_number))
