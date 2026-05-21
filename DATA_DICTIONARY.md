# Data Dictionary

This file explains the raw fields, derived metrics, and output tables used in the trader sentiment analysis.

## Raw Input Files

| File | Description |
|---|---|
| `data/historical_data.csv` | Hyperliquid historical trade-level data. |
| `data/fear_greed_index.csv` | Daily Bitcoin Fear & Greed Index values and classifications. |

## Historical Trader Data Columns

| Column | Meaning | Used for |
|---|---|---|
| `Account` | Trader/account wallet identifier. | Account-level performance and regime edge analysis. |
| `Coin` | Asset traded on Hyperliquid. | Coin-level PnL and volume summaries. |
| `Execution Price` | Trade execution price. | Trade context and possible future price-quality analysis. |
| `Size Tokens` | Trade size in base asset units. | Trade sizing context. |
| `Size USD` | Notional trade value in USD. | Volume, PnL efficiency, and position sizing analysis. |
| `Side` | Buy or sell side. | Trade behavior analysis. |
| `Timestamp IST` | Human-readable trade timestamp in India Standard Time. | Converted into `trade_date` for sentiment joining. |
| `Start Position` | Position size before the trade. | Direction/position context. |
| `Direction` | Trade intent such as Open Long, Close Long, Open Short, Close Short, Sell, or Buy. | Direction/regime performance comparison. |
| `Closed PnL` | Realized profit/loss on closing or realized rows. | Core performance metric. |
| `Transaction Hash` | Blockchain transaction hash. | Audit/reference field. |
| `Order ID` | Exchange order identifier. | Audit/reference field. |
| `Crossed` | Whether the trade crossed the spread/took liquidity. | Taker-rate analysis. |
| `Fee` | Trading fee paid. | Net PnL calculation. |
| `Trade ID` | Trade identifier. | Audit/reference field. |
| `Timestamp` | Numeric timestamp. | Secondary time reference. |

Note: the assignment overview mentioned leverage, but the downloaded historical dataset did not include a leverage column.

## Fear & Greed Index Columns

| Column | Meaning | Used for |
|---|---|---|
| `timestamp` | Unix timestamp for the index date. | Source timestamp reference. |
| `value` | Numeric Fear & Greed score. | Daily sentiment correlation analysis. |
| `classification` | Sentiment bucket such as Fear or Greed. | Main regime grouping variable. |
| `date` | Calendar date. | Join key with trade date. |

## Derived Analysis Fields

| Field | Formula / Logic | Why it matters |
|---|---|---|
| `trade_datetime_ist` | Parsed from `Timestamp IST`. | Enables date-level matching. |
| `trade_date` | Date portion of `trade_datetime_ist`. | Join key to sentiment data. |
| `sentiment` | Fear & Greed classification joined by date. | Main market regime variable. |
| `fear_greed_value` | Numeric index value joined by date. | Correlation and trend checks. |
| `is_realized` | `Closed PnL != 0`. | Identifies rows used for realized win-rate calculations. |
| `net_pnl` | `Closed PnL - Fee`. | Fee-adjusted performance. |
| `pnl_per_1k_volume` | `net_pnl / Size USD * 1000`. | Volume-adjusted performance efficiency. |
| `win_rate_realized` | Share of realized rows with `Closed PnL > 0`. | Measures realized trade success rate by regime. |
| `taker_rate` | Mean of `Crossed`. | Measures how often trades crossed/took liquidity. |
| `greed_minus_fear_efficiency` | Average Greed/Extreme Greed efficiency minus average Fear/Extreme Fear efficiency. | Identifies accounts better suited to momentum regimes versus fear regimes. |

## Output Files

| Output | Purpose |
|---|---|
| `outputs/trader_sentiment_analysis/trader_sentiment_analysis.xlsx` | Main judge-facing workbook with executive dashboard and detail tabs. |
| `outputs/trader_sentiment_analysis/trader_sentiment_report.md` | Written analysis report with findings and recommendations. |
| `outputs/trader_sentiment_analysis/summary_by_sentiment.csv` | Core sentiment-regime summary table. |
| `outputs/trader_sentiment_analysis/summary_by_sentiment_direction.csv` | Performance by sentiment and trade direction. |
| `outputs/trader_sentiment_analysis/daily_sentiment_performance.csv` | Daily performance metrics after sentiment join. |
| `outputs/trader_sentiment_analysis/statistical_validation.csv` | Bootstrap confidence intervals for daily regime efficiency. |
| `outputs/trader_sentiment_analysis/account_sentiment_edges.csv` | Account-level regime specialization scores. |
| `outputs/trader_sentiment_analysis/top_coins.csv` | Coin-level ranking by net PnL and PnL efficiency. |
| `outputs/trader_sentiment_analysis/charts/*.svg` | README-ready visual charts for quick judge review. |
