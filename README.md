# PakPriceSentinel

**Leakage-safe, cross-city early warning of essential-item price shocks in Pakistan**  
Version: `0.1.0` · Research prototype · 9 November 2026

## Research objective

Test whether a lightweight model trained across Pakistan Bureau of Statistics (PBS) city–item price series can forecast next-week increases in essential-item prices, and whether calibrated prediction intervals can support a useful two-level watch/alert system. The primary research question is:

> Can pooled learning across PBS city–item panels improve one-week-ahead price-change forecasts and price-shock detection over simple historical baselines, while preserving chronological evaluation and uncertainty reporting?

The default event definition is a **5% or greater week-on-week price increase** for the same item in the same city. This is an experimental threshold, not an official PBS or food-security classification. Sensitivity runs at 3% and 10% are recommended before any policy interpretation.

## Why this matters in Pakistan

PBS reports the weekly Sensitive Price Indicator (SPI) using 51 essential items observed in 50 markets across 17 cities. Its weekly city/item annexures create a practical basis for monitoring short-term price movements. Food affordability is a real policy concern: the IPC analysis released on 17 April 2026 classified about 7.5 million people (21% of the analysed population) in Phase 3 or above for December 2025–March 2026. FEWS NET's June 2026 outlook also describes poor households' exposure to food-price volatility and constrained purchasing power. This project studies **market price signals only**; it does not infer household food insecurity or IPC phases from prices.

## Research contribution (prototype claim, not a novelty guarantee)

1. A reproducible city–item panel preparation pipeline that excludes non-average, missing, unavailable and reported-zero price cells rather than treating zero as a real price.
2. A pooled ridge forecaster using only lagged within-series returns, evaluated against zero-change and group-median baselines.
3. A chronological train/calibration/test protocol with split-conformal residual intervals and two-level `NORMAL` / `WATCH` / `ALERT` outputs.
4. City/item-level prediction exports and metrics for forecast error, event detection, empirical interval coverage and false watches.

This is a research prototype, not a deployed early-warning service. A formal literature review is still required before claiming a novel contribution.

## Data provenance and scope

The reproducible downloader fetches the `weekly_spi_city_item_prices.csv` file curated by OpenDoc Pakistan from PBS weekly SPI Excel annexures. The dataset card documents a weekly city/item series from **23 October 2025 through 2 July 2026** and describes its source files and parsing process. The source file is pinned to a specific Hugging Face file revision and SHA-256 checksum in `scripts/fetch_data.py`.

- Official PBS Price Statistics page: <https://www.pbs.gov.pk/price-statistics/>
- Curated dataset card and provenance: <https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices>
- Exact source CSV: <https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices/resolve/54c5231/data/processed/weekly_spi_city_item_prices.csv>

**Important data caveats:** the pinned city/item file is a historical snapshot ending 2 July 2026, not a live feed. PBS has since published newer weekly SPI releases; the project does not silently merge them. The curated dataset's card displays `cc-by-4.0`, but its own provenance section says PBS does not state an explicit open redistribution licence for the underlying official source data. See `DATA_LICENSE.md`; do not assume PBS data are CC-BY or public domain.

No external price observations are bundled in this repository. The included synthetic generator is for tests and software smoke runs only; its output is explicitly labelled synthetic and must never be described as observed Pakistani market prices.

## Requirements

- Python 3.9 or newer
- Standard library only; no NumPy, pandas, scikit-learn, GPU or cloud account required
- Designed for small local runs, including a MacBook Air M4 with 16 GB memory

## Quick start

From the repository root:

```bash
python3 --version
python3 -m unittest discover -s tests -v
python3 -m scripts.generate_synthetic --out data/synthetic/demo_prices.csv --weeks 52 --cities 4 --items 6 --seed 20261109
python3 -m scripts.prepare_data --input data/synthetic/demo_prices.csv --out data/processed/demo_prices_clean.csv
python3 -m scripts.run_experiment --input data/processed/demo_prices_clean.csv --out results/synthetic_smoke
```

The synthetic run validates the pipeline mechanics only. Do not use its scores as evidence about Pakistan's real price dynamics.

## Official-source data workflow

```bash
python3 -m scripts.fetch_data --out data/raw/weekly_spi_city_item_prices.csv
python3 -m scripts.prepare_data --input data/raw/weekly_spi_city_item_prices.csv --out data/processed/weekly_prices_clean.csv
python3 -m scripts.run_experiment --input data/processed/weekly_prices_clean.csv --out results/official_spi
```

The fetch step verifies the pinned file checksum and fails closed if the downloaded bytes differ. If the upstream curator replaces the file, review its provenance and update the pinned revision/checksum deliberately rather than bypassing verification.

## Outputs

`results/<run-name>/` contains:

- `metrics.csv` — model-level forecast and shock-detection metrics;
- `predictions.csv` — per city/item/date forecasts, conformal bounds and alert state;
- `summary.json` — run configuration, temporal split boundaries and observation counts.

Models:

- `zero_change`: predicts zero next-week log return;
- `group_median`: predicts the training-only median return for the same city/item, falling back to the training global median for unseen groups;
- `pooled_ridge`: a single ridge model trained across all city/item panels using seven lag-derived features.

The `WATCH` state is raised when the upper prediction bound reaches the configured shock threshold. `ALERT` is raised when the lower bound reaches it. These are research labels, not operational advice.

## Reproducibility and evaluation

The data pipeline keeps only rows with `price_type=avg`, `availability_status=reported`, and a finite positive `price_pkr`. It rejects duplicate city–item–week keys. Forecast examples require six consecutive weekly observations: four lagged weekly returns, the current price and the next week's price. Missing weeks are not interpolated.

The default experiment sorts unique forecast-origin weeks and uses the earliest 60% for fitting, the next 20% for residual calibration, and the final 20% for the untouched test. All features are historical at forecast time. The ridge model is fitted on the training block only; conformal residual quantiles are estimated on the subsequent calibration block only. No random row split is used.

See `docs/research_protocol.md`, `docs/data_dictionary.md`, `docs/source_register.md` and `docs/limitations.md` before interpreting results. Report all three baselines, the exact data period, missingness, shock prevalence, threshold sensitivity and city/item disaggregation. A single temporal holdout is an initial benchmark, not sufficient evidence of robust generalisation; later work should use multiple rolling-origin folds and additional PBS releases.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests use temporary synthetic fixtures. They do not download data or require network access.

## Licence and citation

- Source code: MIT (`LICENSE`).
- Underlying PBS observations: see `DATA_LICENSE.md`; this repository does not redistribute the PBS-derived CSV.
- Citation metadata: `CITATION.cff`.

## Research integrity

Do not claim that synthetic observations are real, that model outputs establish causal drivers, or that a market-price alert measures household hunger. Do not claim operational accuracy until the official-source pipeline has been run, results have been independently checked, and out-of-time evaluation has been repeated on newer releases.
