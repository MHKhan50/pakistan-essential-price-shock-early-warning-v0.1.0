# Research protocol — PakPriceSentinel v0.1.0

## Problem framing

Weekly essential-item price monitoring is an observable component of food affordability risk. The project does not estimate household consumption, income, dietary diversity, food security phase or causal drivers. It asks whether recent price trajectories in PBS city/item panels provide a useful one-week-ahead warning signal.

## Prior-work check and gap hypothesis

This topic is not being presented as an untouched research area. Prior Pakistan studies have examined monthly food-price volatility across multiple cities with GARCH-style methods (Zehra & Fatima, 2019), and agricultural commodity forecasting has compared ARIMA, Random Forest and LSTM for spinach prices in Vehari (Rana et al., 2024). An SSRN working paper posted on 29 July 2026 also reports machine-learning analysis of WFP Pakistan food-price observations from 2010–2023. These works make a generic claim of “AI for Pakistan food prices” untenable.

The narrower gap hypothesis tested here is different: **weekly PBS SPI city–item panels, one-week-ahead positive price-shock detection, strict time-ordered train/calibration/test separation, and calibrated prediction intervals converted into auditable watch/alert states**. The gap is a hypothesis, not a proven novelty claim; a formal systematic review and direct baseline replication are required before a paper can claim novelty. See `docs/source_register.md` for source links and scope.

## Research questions

- **RQ1:** Does a pooled ridge model reduce out-of-time next-week log-return MAE/RMSE relative to zero-change and city/item historical-median baselines?
- **RQ2:** Do split-conformal residual intervals achieve useful empirical coverage on the final chronological holdout, and how wide are they?
- **RQ3:** What precision/recall and false-watch burden result when a `WATCH` is issued if the interval upper bound crosses the shock threshold, and an `ALERT` if the lower bound crosses it?
- **RQ4:** How stable are these findings across cities, commodities and 3%, 5% and 10% event thresholds?

## Dataset

Primary table: OpenDoc Pakistan's `weekly_spi_city_item_prices.csv`, curated from PBS weekly SPI Excel annexures. It contains weekly city/item price summaries and metadata. The dataset card reports a coverage window of 23 October 2025–2 July 2026 for this table. Confirm the downloaded CSV's actual min/max dates and row counts before each analysis; do not assume the card remains current.

Use only `price_type=avg`, `availability_status=reported`, and finite `price_pkr > 0`. `reported_zero`, blank, unavailable and non-average rows are excluded. Duplicate `(week_end_date, city_code, item_number)` average-price keys cause a hard failure.

## Forecast target and features

For city `c`, item `i`, and week `t`, target:

`y(c,i,t+1) = ln(price(c,i,t+1) / price(c,i,t))`.

Features are computed only from prices available at week `t`:

1. returns at lags 1–4 weeks;
2. mean and population standard deviation of those four returns;
3. difference between mean of the two most recent returns and mean of the preceding two returns.

A training example is created only when the six observations needed to calculate four historical returns and the next-week target are separated by exact seven-day intervals. Missing weeks are not interpolated or forward-filled.

## Event definition

Default positive event: `y >= ln(1.05)`, equivalent to at least a 5% one-week price increase. This is a research threshold selected for the benchmark, not a PBS threshold, regulatory trigger or IPC criterion. Repeat the full evaluation at 3% and 10% and publish class prevalence for each.

## Models

- `zero_change`: forecast 0 log return.
- `group_median`: median training target for the same `(city_code, item_number)`; training-global median for an unseen group.
- `pooled_ridge`: standardised ridge regression across all training city/item examples, with intercept unpenalised and `alpha=5.0` by default.

The pooled model is intentionally small and dependency-free. It does not use city/item identifiers as predictive features; it tests whether common short-run dynamics transfer across panels.

## Temporal protocol

Sort distinct forecast-origin dates. Allocate earliest 60% to model fitting, next 20% to residual calibration, final 20% to test. The ridge coefficients and group medians use training data only. For each model, absolute residuals from the calibration block determine a split-conformal radius at `alpha=0.10`. The test block is never used for fitting or calibration.

This single holdout is a first reproducibility baseline. It is not a substitute for repeated rolling-origin evaluation. Panel observations share common dates and may be dependent; the nominal conformal level should not be interpreted as a guaranteed conditional coverage level under temporal drift.

## Decision states

Let `[L,U]` be the calibrated log-return interval and `tau=ln(1+threshold)`:

- `NORMAL`: `U < tau`;
- `WATCH`: `L < tau <= U`;
- `ALERT`: `L >= tau`.

The reported watch metrics treat both `WATCH` and `ALERT` as positive warnings. Alert metrics treat only `ALERT` as positive. This makes the sensitivity-oriented and high-confidence policies separately auditable.

## Metrics

Forecast: MAE and RMSE of log return.  
Detection: precision, recall, F1, false positives, and false positives per 100 test examples.  
Uncertainty: empirical test interval coverage and mean interval width.  
Always report test count, event count, event prevalence, threshold, calibration sample size and exact date boundaries.

## Reproducibility checklist

- Preserve the raw source file and its checksum outside the processed table.
- Record collection date, file revision, source URLs and exact min/max observation dates.
- Do not merge different PBS base years or definitions without an explicit harmonisation step.
- Report excluded status counts and duplicate checks.
- Run the same chronological split for all baselines.
- Compare at 3%, 5%, 10% shock thresholds.
- Disaggregate by city and item; suppress or flag groups with too few events.
- Re-run on newer PBS releases before claiming current operational relevance.
