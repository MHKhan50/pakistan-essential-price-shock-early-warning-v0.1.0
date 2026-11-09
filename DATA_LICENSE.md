# Data licensing and attribution

This repository's **source code** is MIT-licensed. That licence does not apply to third-party PBS observations.

The data downloader retrieves a specific CSV curated by OpenDoc Pakistan from Pakistan Bureau of Statistics (PBS) weekly SPI Excel annexures. The Hugging Face dataset card displays `cc-by-4.0`; however, its provenance section states that PBS's original public website data have no explicit open redistribution licence identified and warns not to label the underlying PBS data CC-BY or public domain unless PBS publishes such terms.

Accordingly:

- No PBS-derived observations are included in this ZIP.
- Use the downloaded file for analysis with clear attribution to **Pakistan Bureau of Statistics, Price Statistics / Weekly Sensitive Price Indicator**, and acknowledge the OpenDoc Pakistan curation where applicable.
- Do not redistribute, mirror, or publish the raw or transformed PBS data until the applicable source terms have been checked and permission/licensing questions resolved.
- The synthetic data generator is original software-generated test data and is explicitly marked synthetic.

Source references:

- PBS Price Statistics: https://www.pbs.gov.pk/price-statistics/
- OpenDoc Pakistan dataset card: https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices
- Curated CSV revision: https://huggingface.co/datasets/opendoc-pakistan/pakistan_inflation_and_prices/resolve/54c5231/data/processed/weekly_spi_city_item_prices.csv
