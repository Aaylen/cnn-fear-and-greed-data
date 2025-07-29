# CNN Fear & Greed Index Backtester

This program can be used for:

- **Backtesting investment strategies**
- **Scraping CNN’s Fear & Greed index data**

---

## Scraping the Fear & Greed Index

- This website contains CNN’s historical data:
  - [https://www.finhacker.cz/fear-and-greed-index-historical-data-and-chart/](https://www.finhacker.cz/fear-and-greed-index-historical-data-and-chart/)
- The data is not continuous, but typically includes 4–5 data points per month, going back to 2011.
- To use the scraper in your code:

```python
from scrapeCNNData import fetch_fear_greed_data
```

## Backtesting Strategy
- The way I have it set up:
    - You get an investing budget per week.
    - You can choose how much of that budget to spend each week, based on the Fear & Greed index.
    - If you spend less in a week, the remaining budget rolls over, allowing you to spend more in future weeks.
    - This way, both DCA (Dollar Cost Averaging) and active management have access to the same total capital over time.