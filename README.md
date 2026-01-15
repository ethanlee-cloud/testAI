# Insight Radar

Scans chosen websites for latest news/insights, summarizes with citations, maps themes to ETFs,
pulls market data from Yahoo Finance, and estimates what looks priced-in vs not.

## Setup
1. `pip install -r requirements.txt`
2. Fill DeepSeek key/model/base_url in `config.yaml`
3. Run: `python main.py`

## Customize
- Websites: `config.yaml -> websites`
- RSS feeds: `config.yaml -> rss_feeds`
- ETF map: `etf_map.json`
- Prompts: `prompts/*.txt`

## Output
- `output/report.md`
- Cached extracted articles in `.cache/`
- Or in batch: cat output/report.md
## Disclaimer
Not financial advice.
