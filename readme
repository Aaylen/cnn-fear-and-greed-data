CNN Fear & Greed Index Backtester
This program can be used for:

Backtesting investment strategies

Scraping CNN’s Fear and Greed index data

Scraping the Fear & Greed Index:
This website has all of CNN's historical Fear & Greed data.

Data is not continuous, but typically includes 4–5 data points per month going back to 2011.

To use the scraper:

python
Copy
Edit
from scrapeCNNData import fetch_fear_greed_data

Backtesting Strategy:
The backtester assumes a fixed weekly investment budget.

You decide how much of the budget to invest each week, based on the Fear & Greed index:

Spend more when there is fear

Spend less when there is greed

Unspent budget rolls over to future weeks, allowing flexible investing.

Both DCA (Dollar Cost Averaging) and active strategy have access to the same total capital over time.

Spoiler:
I tried optimizing the allocation strategy — see results.txt for details — but it's not worth trying to outperform DCA (at least on SPY).

