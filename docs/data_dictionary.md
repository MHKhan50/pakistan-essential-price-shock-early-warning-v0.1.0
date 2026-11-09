# Data dictionary

## Raw source CSV fields used

| Field | Type | Meaning | Treatment |
|---|---|---|---|
| `week_end_date` | date | PBS SPI week-ending date | Parsed to ISO date; exact 7-day spacing required for examples |
| `item_number` | string/integer | PBS essential-item identifier | Part of panel key |
| `item_description` | string | Published item label | Retained for output |
| `unit` | string | Published unit (for example kg/dozen/litre) | Retained; prices are never compared across units |
| `city_code` | string | PBS city identifier | Part of panel key |
| `city` | string | City label | Retained for output |
| `price_type` | category | `min`, `avg` or `max` | Only `avg` retained |
| `price_pkr` | number | Published price in Pakistani rupees | Only finite positive values retained |
| `availability_status` | category | `reported`, `blank`, `not_available`, `reported_zero` | Only `reported` retained |
| `source_url` | URL | PBS source workbook URL recorded by curator | Retained for provenance |

## Canonical prepared table

| Field | Type | Meaning |
|---|---|---|
| `week_end_date` | ISO date | Observation week ending |
| `item_number` | string | PBS item identifier |
| `item_description` | string | Published item description |
| `unit` | string | Published measurement unit |
| `city_code` | string | PBS city identifier |
| `city` | string | City name |
| `price_pkr` | float | Positive average price in PKR |
| `source_url` | URL/string | PBS workbook provenance |

Primary key: `(week_end_date, city_code, item_number)`.

## Derived experiment fields

| Field | Type | Meaning |
|---|---|---|
| `origin_date` | date | Latest date available when forecast is issued |
| `target_date` | date | Next week's date being forecast |
| `return_lag_1..4` | float | Historical log price returns, most recent first |
| `mean_return_4w` | float | Mean of four historical weekly returns |
| `std_return_4w` | float | Population standard deviation of those returns |
| `momentum_2v2` | float | Mean of two latest returns minus mean of previous two |
| `target_log_return` | float | Next-week log price return |
| `is_shock` | boolean | Target return at or above configured threshold |
| `predicted_log_return` | float | Model forecast |
| `lower_log_return`, `upper_log_return` | float | Split-conformal prediction bounds |
| `alert_state` | category | `NORMAL`, `WATCH` or `ALERT` |

Synthetic test rows use `source_url=SYNTHETIC_ONLY_NOT_PBS` and generated city/item labels. They are not real market observations.
