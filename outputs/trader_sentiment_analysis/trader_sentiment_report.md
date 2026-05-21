# Trader Performance vs Bitcoin Market Sentiment

## Dataset Coverage
- Trades analyzed: 211,224
- Joined to sentiment: 211,218 rows; unmatched: 6
- Date range: 2023-05-01 to 2025-05-01
- Accounts: 32; coins: 246

## Executive Insights
1. Best risk-adjusted sentiment bucket by net PnL per $1k volume was **Extreme Greed** at $22 per $1k traded, with a realized win rate of 89.2%.
2. Worst efficiency appeared in **Extreme Fear** at $6 per $1k traded. This is the regime where size discipline matters most.
3. Highest absolute net PnL came during **Fear**: $3,264,698, partly because activity/volume was also high in that bucket.
4. Daily fear-greed value correlation with net PnL was **-0.079**; correlation with PnL efficiency was **0.081**. Treat sentiment as a regime filter, not a standalone signal.

## Sentiment Summary
| sentiment | trade_count | realized_trades | volume_usd | net_pnl | win_rate_realized | pnl_per_1k_volume | taker_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extreme Fear | 21400.000 | 10406.000 | 114484261.440 | 715221.615 | 0.762 | 6.247 | 0.567 |
| Fear | 61837.000 | 29808.000 | 483324789.790 | 3264698.493 | 0.873 | 6.755 | 0.601 |
| Neutral | 37686.000 | 18159.000 | 180242063.080 | 1253546.407 | 0.824 | 6.955 | 0.619 |
| Greed | 50303.000 | 25176.000 | 288582494.720 | 2087030.581 | 0.769 | 7.232 | 0.614 |
| Extreme Greed | 39992.000 | 20853.000 | 124465164.570 | 2688140.645 | 0.892 | 21.598 | 0.622 |

## Strongest Direction/Regime Combinations
| sentiment | Direction | realized_trades | volume_usd | net_pnl | win_rate_realized | pnl_per_1k_volume |
| --- | --- | --- | --- | --- | --- | --- |
| Extreme Greed | Sell | 7161.000 | 10131467.810 | 2079897.431 | 0.925 | 205.291 |
| Greed | Sell | 5846.000 | 10153613.580 | 764600.856 | 0.790 | 75.303 |
| Neutral | Sell | 2298.000 | 3817114.710 | 208930.325 | 0.779 | 54.735 |
| Extreme Fear | Close Short | 3117.000 | 12393421.550 | 382149.356 | 0.706 | 30.835 |
| Neutral | Close Short | 5849.000 | 20815400.250 | 549161.876 | 0.777 | 26.382 |
| Fear | Close Short | 9212.000 | 75309305.270 | 1899341.625 | 0.862 | 25.221 |
| Extreme Greed | Close Long | 7185.000 | 28240750.790 | 437225.479 | 0.888 | 15.482 |
| Greed | Close Short | 11319.000 | 51702249.450 | 613003.708 | 0.689 | 11.856 |
| Extreme Fear | Close Long | 6241.000 | 42635958.850 | 497410.910 | 0.846 | 11.666 |
| Extreme Greed | Close Short | 6489.000 | 19491848.220 | 183427.664 | 0.860 | 9.410 |
| Greed | Close Long | 7963.000 | 76086336.030 | 695099.963 | 0.867 | 9.136 |
| Fear | Close Long | 17260.000 | 159250581.290 | 1402575.181 | 0.899 | 8.807 |

## Account-Level Pattern
The `account_sentiment_edges.csv` output ranks accounts by whether they performed more efficiently in Greed/Extreme Greed than in Fear/Extreme Fear. This is useful for separating traders who thrive in momentum regimes from traders who perform better during panic/liquidation regimes.

## Statistical Validation
Daily regime metrics were bootstrapped to create 95% confidence intervals for average daily PnL efficiency. This does not prove causality, but it checks whether the observed regime edge is stable across days instead of coming from one isolated trade cluster.

| sentiment | days_observed | mean_daily_pnl_per_1k_volume | mean_daily_pnl_per_1k_ci_low | mean_daily_pnl_per_1k_ci_high | mean_daily_win_rate | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Extreme Fear | 14.000 | 7.595 | -3.129 | 19.645 | 0.654 | bootstrap interval crossed zero; treat edge as less stable |
| Fear | 91.000 | 8.801 | 1.643 | 16.427 | 0.881 | daily efficiency stayed positive in bootstrap interval |
| Neutral | 67.000 | 7.346 | -1.271 | 16.716 | 0.794 | bootstrap interval crossed zero; treat edge as less stable |
| Greed | 193.000 | 9.533 | 5.377 | 14.533 | 0.813 | daily efficiency stayed positive in bootstrap interval |
| Extreme Greed | 114.000 | 20.812 | 12.298 | 32.030 | 0.887 | daily efficiency stayed positive in bootstrap interval |

## Top Coins by Net PnL
| Coin | realized_trades | volume_usd | net_pnl | pnl_per_1k_volume |
| --- | --- | --- | --- | --- |
| @107 | 17166.000 | 55760858.630 | 2777959.694 | 49.819 |
| HYPE | 32011.000 | 141990206.050 | 1923122.669 | 13.544 |
| SOL | 5030.000 | 125074752.060 | 1611599.623 | 12.885 |
| ETH | 5228.000 | 118280994.070 | 1296887.535 | 10.964 |
| BTC | 11009.000 | 644232116.630 | 728820.506 | 1.131 |
| MELANIA | 2211.000 | 7040710.450 | 389340.681 | 55.298 |
| ENA | 332.000 | 1625400.500 | 217053.076 | 133.538 |
| SUI | 893.000 | 7781167.590 | 197265.629 | 25.352 |
| ZRO | 794.000 | 1213825.420 | 183543.715 | 151.211 |
| DOGE | 459.000 | 2452103.460 | 147020.932 | 59.957 |
| PURR/USDC | 1187.000 | 1642418.690 | 73416.502 | 44.700 |
| AIXBT | 494.000 | 1273650.180 | 73358.613 | 57.597 |

## Strategy Recommendations
- **Regime-aware sizing:** Use larger size only where both absolute PnL and PnL efficiency are strong. Extreme Greed had the best efficiency; Fear had the highest total PnL but should still be monitored for volume-driven noise.
- **Playbook selection:** Avoid using the same long/short playbook in every sentiment regime. Direction-level results show that certain close/sell patterns performed much better in specific regimes.
- **Trader selection:** Rank accounts by `greed_minus_fear_efficiency` before copying trades. Positive values suggest a trader is more suitable for momentum/greed environments; negative values suggest better fit for defensive or fear-driven environments.
- **Risk controls:** When the bootstrap interval crosses zero, cap exposure or require confirmation from additional signals such as BTC trend, realized volatility, funding rates, and liquidation intensity.
- **Production improvement:** Add BTC returns, funding rates, open interest, volatility, and liquidation data so sentiment is tested alongside market structure rather than in isolation.