# Trader Performance vs Bitcoin Market Sentiment

This repository contains my completed analysis for the trader sentiment assignment. It explores how Hyperliquid trader performance changes across Bitcoin Fear & Greed market sentiment regimes.

## Objective

Analyze the relationship between trader behavior/performance and market sentiment, uncover patterns, and derive insights that can support smarter trading strategy decisions.

## Repository Structure

```text
.
├── analysis/
│   └── trader_sentiment_analysis.py
├── data/
│   ├── fear_greed_index.csv
│   └── historical_data.csv
├── outputs/
│   └── trader_sentiment_analysis/
│       ├── trader_sentiment_analysis.xlsx
│       ├── trader_sentiment_report.md
│       └── summary CSV files
└── requirements.txt
```

## Methodology

1. Parsed Hyperliquid `Timestamp IST` into a trade date.
2. Joined each trade to the Bitcoin Fear & Greed Index using the trade date.
3. Treated rows with nonzero `Closed PnL` as realized trades for win-rate analysis.
4. Calculated `net_pnl = Closed PnL - Fee`.
5. Compared performance across sentiment regimes using:
   - Trade count
   - Realized trades
   - Trading volume
   - Net PnL
   - Realized win rate
   - Net PnL per `$1,000` traded volume
6. Built account-level, coin-level, direction-level, and daily trend summaries.

## Key Findings

- **Extreme Greed** showed the strongest efficiency at about `$21.60` net PnL per `$1,000` traded.
- **Fear** produced the highest absolute net PnL at about `$3.26M`, supported by high trading volume.
- Daily Fear & Greed score had weak correlation with daily PnL, so sentiment is more useful as a regime filter than as a standalone trading signal.
- Some direction/regime combinations performed materially better than others, suggesting that strategy selection should change with sentiment conditions.
- Account-level regime edges can help identify traders who perform better in momentum conditions versus panic/fear conditions.

## Final Deliverables

- Final workbook: `outputs/trader_sentiment_analysis/trader_sentiment_analysis.xlsx`
- Written report: `outputs/trader_sentiment_analysis/trader_sentiment_report.md`
- Reproducible script: `analysis/trader_sentiment_analysis.py`

## Reproduce the Analysis

```bash
pip install -r requirements.txt
python analysis/trader_sentiment_analysis.py
```

The script reads from `data/` and writes refreshed outputs under `outputs/trader_sentiment_analysis/`.
