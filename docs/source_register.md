# Source register and evidence trail

Checked for this project on **9 November 2026**. Links are included so the research team can verify later revisions.

## Pakistan problem evidence

1. **Pakistan Bureau of Statistics (PBS), Price Statistics.** PBS states that the weekly Sensitive Price Indicator covers 51 essential items collected from 50 markets in 17 cities. The page listed the week ended **5 November 2026** with an SPI of **374.61**, up **0.29%** from the previous week. The index is a short-term price movement indicator; it is not itself a household food-security measure.  
   https://www.pbs.gov.pk/price-statistics/

2. **Integrated Food Security Phase Classification (IPC), Pakistan analysis, released 17 April 2026.** The report states that approximately **7.5 million people (21% of the analysed population)** were classified in IPC Phase 3 or above for December 2025–March 2026. Its projected April–September 2026 coverage and population denominator differ; comparisons must account for geographic coverage.  
   https://www.ipcinfo.org/ipc-country-analysis/details-map/en/c/1161020/

3. **FEWS NET, Pakistan Food Security Outlook, June 2026.** The analysis describes poor households' high dependence on market purchases, exposure to staple-price volatility and constrained purchasing power; it estimates food at roughly 45–50% of total expenditure for poor households in the cited context. This is contextual evidence, not a model label.  
   https://fews.net/asia/pakistan/food-security-outlook/june-2026

4. **World Food Programme (WFP), Pakistan country page.** WFP describes persistent food insecurity and nutrition challenges and links food-security programming with affordable nutritious diets and resilience. Use the latest linked IPC assessment for time-specific counts rather than treating the country-page headline as a fixed time series.  
   https://www.wfp.org/countries/pakistan

## Dataset and provenance

5. **OpenDoc Pakistan, Pakistan Inflation and SPI Prices dataset card.** The curator documents the PBS source files, parsing pipeline, source inventory, data dictionary and limitations. The card describes 106,593 parsed observations across its combined tables; the weekly city/item file specifically covers **23 October 2025–2 July 2026**. The weekly city/item CSV is a curated secondary artifact, not a native PBS API endpoint.  
   https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices

6. **Exact pinned weekly city/item CSV file.** The downloader pins file revision `54c5231` and checks the SHA-256 shown on the file page.  
   https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices/resolve/54c5231/data/processed/weekly_spi_city_item_prices.csv

7. **PBS weekly SPI release for the week ended 5 November 2026.** This newer release demonstrates that PBS continued publishing after the pinned curated dataset snapshot. It is not automatically merged into this v0.1.0 experiment.  
   https://www.pbs.gov.pk/weekly-sensitive-price-indicator-spi-for-the-week-ended-on-05-11-2026/

## Related research and differentiation

8. **Zehra, N. & Fatima, A. (2019), “Food Price Volatility: A Comparative Analysis among Major Cities of Pakistan,” Pakistan Journal of Applied Economics.** The abstract describes 16 food commodities, 14 cities, monthly PBS price data from July 2002 to June 2016, and GARCH/IGARCH/standard-deviation analyses.  
   https://www.prdb.pk/article/food-price-volatility-a-comparative-analysis-among-major-ci-4412

9. **Rana et al. (2024), “Prediction of Agricultural Commodity Prices using Big Data Framework,” Engineering, Technology & Applied Science Research.** The study compares ARIMA, Random Forest and LSTM for spinach price trends in Vehari using a 2007–2022 historical dataset.  
   https://etasr.com/index.php/ETASR/article/view/6468

10. **“Analytics of Food Prices in Pakistan: Machine Learning, Regional Disparities & Policy Recommendations for Food Security” (SSRN working paper, posted 29 July 2026).** The abstract describes WFP price observations from 2010–2023 and compares linear regression, decision tree, random forest and SVM. This is a working-paper source and should not be represented as peer-reviewed without checking its publication status.  
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7113179

**Differentiation statement:** PakPriceSentinel does not claim that price forecasting in Pakistan is new. Its proposed experimental distinction is the use of the weekly PBS SPI city/item panel for one-week-ahead event detection, explicit missingness filtering, leakage-safe temporal calibration, conformal intervals and two-level warning states. The available weekly snapshot is short, so the project must be treated as a pilot until newer weekly files and repeated rolling-origin tests are added.
