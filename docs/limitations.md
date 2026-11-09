# Limitations and responsible interpretation

1. **Snapshot age:** the pinned curated weekly city/item file ends on 2 July 2026 according to its dataset card. It is not a live feed and does not include PBS releases published after that date. Update only after inspecting newer source files and preserving their provenance.
2. **Short time span:** fewer than one year of weekly city/item observations is not enough to establish long-run seasonality, robust crisis behaviour or structural stability.
3. **Source licensing:** PBS's reviewed source page does not state an explicit open redistribution licence for the underlying files. The curated Hugging Face dataset card displays CC-BY-4.0, but its own README distinguishes that repository label from the PBS source-data terms. This repository does not redistribute the observations; obtain legal/licensing review before republishing them.
4. **Coverage and missingness:** only reported average prices are retained. Missing, unavailable and reported-zero cells are excluded. This may create selection bias if missingness is systematic by city, item or week.
5. **Price comparability:** item units and specifications must be consistent over time. The pipeline keeps item identifiers and units, but cannot detect every definitional or quality change in PBS source workbooks.
6. **No household outcomes:** market prices alone do not measure household income, food consumption, dietary quality, access, stocks or coping strategies. The model must not predict IPC phases or label a city/district food insecure.
7. **No causal inference:** lagged price patterns do not establish why a price changed. The system has no verified weather, transport, supply, policy or market-intervention causal variables.
8. **Model scope:** pooled ridge is a small baseline, not a deep neural model. It omits city/item embeddings and exogenous covariates by design. Any apparent advantage may be sensitive to the chosen split, threshold or calibration block.
9. **Conformal assumptions:** panel observations are dependent and temporal distributions may drift. Empirical interval coverage on one holdout does not guarantee future or group-conditional coverage.
10. **Operational risk:** a `WATCH` or `ALERT` is a model output for research evaluation only. It must not automatically trigger procurement, subsidy, enforcement or public messaging without human review and validation.
11. **Synthetic data:** injected shocks in the generator are artificial software fixtures. Their metrics are not empirical results and must never be mixed with official-source experiment results.
