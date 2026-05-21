from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
DATA_DIR = ROOT / "data"


def input_path(file_name: str) -> Path:
    packaged_path = DATA_DIR / file_name
    if packaged_path.exists():
        return packaged_path
    return DOWNLOADS / file_name


TRADES_PATH = input_path("historical_data.csv")
SENTIMENT_PATH = input_path("fear_greed_index.csv")
OUT_DIR = ROOT / "outputs" / "trader_sentiment_analysis"

SENTIMENT_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
CHART_DIR = OUT_DIR / "charts"


def weighted_avg(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & (weights != 0)
    if not mask.any():
        return np.nan
    return float(np.average(values[mask], weights=weights[mask]))


def summarize(group: pd.DataFrame) -> pd.Series:
    realized = group[group["is_realized"]]
    total_volume = group["Size USD"].sum()
    net_pnl = group["net_pnl"].sum()
    unique_accounts = group["Account"].nunique() if "Account" in group.columns else 1
    unique_coins = group["Coin"].nunique() if "Coin" in group.columns else 1
    fear_greed_value = group["fear_greed_value"].mean() if "fear_greed_value" in group.columns else np.nan
    return pd.Series(
        {
            "fear_greed_value": fear_greed_value,
            "trade_count": len(group),
            "realized_trades": len(realized),
            "unique_accounts": unique_accounts,
            "unique_coins": unique_coins,
            "volume_usd": total_volume,
            "gross_closed_pnl": group["Closed PnL"].sum(),
            "fees": group["Fee"].sum(),
            "net_pnl": net_pnl,
            "avg_net_pnl_per_trade": group["net_pnl"].mean(),
            "median_net_pnl_per_trade": group["net_pnl"].median(),
            "win_rate_realized": (realized["Closed PnL"] > 0).mean() if len(realized) else np.nan,
            "avg_realized_pnl": realized["Closed PnL"].mean() if len(realized) else np.nan,
            "pnl_per_1k_volume": (net_pnl / total_volume * 1000) if total_volume else np.nan,
            "avg_trade_size_usd": group["Size USD"].mean(),
            "taker_rate": group["Crossed"].mean(),
        }
    )


def clean_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    trades = pd.read_csv(TRADES_PATH)
    sentiment = pd.read_csv(SENTIMENT_PATH)

    trades["trade_datetime_ist"] = pd.to_datetime(
        trades["Timestamp IST"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    if trades["trade_datetime_ist"].isna().any():
        trades["trade_datetime_ist"] = pd.to_datetime(
            trades["Timestamp IST"], dayfirst=True, errors="coerce"
        )
    trades["trade_date"] = trades["trade_datetime_ist"].dt.date

    sentiment["sentiment_date"] = pd.to_datetime(sentiment["date"], errors="coerce").dt.date
    sentiment = sentiment.rename(
        columns={"value": "fear_greed_value", "classification": "sentiment"}
    )
    sentiment["sentiment"] = pd.Categorical(
        sentiment["sentiment"], categories=SENTIMENT_ORDER, ordered=True
    )

    trades["is_realized"] = trades["Closed PnL"].fillna(0).ne(0)
    trades["net_pnl"] = trades["Closed PnL"].fillna(0) - trades["Fee"].fillna(0)
    trades["pnl_per_1k_volume"] = np.where(
        trades["Size USD"].gt(0), trades["net_pnl"] / trades["Size USD"] * 1000, np.nan
    )

    return trades, sentiment


def build_outputs() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    trades, sentiment = clean_inputs()

    merged = trades.merge(
        sentiment[["sentiment_date", "fear_greed_value", "sentiment"]],
        left_on="trade_date",
        right_on="sentiment_date",
        how="left",
    )
    merged["sentiment"] = pd.Categorical(
        merged["sentiment"], categories=SENTIMENT_ORDER, ordered=True
    )

    by_sentiment = (
        merged.dropna(subset=["sentiment"])
        .groupby("sentiment", observed=False)
        .apply(summarize)
        .reset_index()
    )
    by_sentiment["sentiment"] = by_sentiment["sentiment"].astype(str)

    by_direction = (
        merged.dropna(subset=["sentiment"])
        .groupby(["sentiment", "Direction"], observed=False)
        .apply(summarize)
        .reset_index()
        .sort_values(["sentiment", "net_pnl"], ascending=[True, False])
    )
    by_direction["sentiment"] = by_direction["sentiment"].astype(str)

    daily = (
        merged.dropna(subset=["sentiment"])
        .groupby(["trade_date", "sentiment"], observed=True)
        .apply(summarize)
        .reset_index()
    )
    daily["trade_date"] = daily["trade_date"].astype(str)
    daily["sentiment"] = daily["sentiment"].astype(str)

    coin_summary = (
        merged.dropna(subset=["sentiment"])
        .groupby(["sentiment", "Coin"], observed=False)
        .apply(summarize)
        .reset_index()
    )
    coin_summary["sentiment"] = coin_summary["sentiment"].astype(str)
    coin_summary = coin_summary.sort_values(["sentiment", "net_pnl"], ascending=[True, False])

    account_sentiment = (
        merged.dropna(subset=["sentiment"])
        .groupby(["Account", "sentiment"], observed=False)
        .apply(summarize)
        .reset_index()
    )
    account_sentiment["sentiment"] = account_sentiment["sentiment"].astype(str)
    account_edges = (
        account_sentiment.pivot(index="Account", columns="sentiment", values="pnl_per_1k_volume")
        .reindex(columns=SENTIMENT_ORDER)
        .reset_index()
    )
    account_edges["greed_minus_fear_efficiency"] = account_edges[["Greed", "Extreme Greed"]].mean(
        axis=1, skipna=True
    ) - account_edges[["Fear", "Extreme Fear"]].mean(axis=1, skipna=True)
    account_edges = account_edges.sort_values("greed_minus_fear_efficiency", ascending=False)

    correlation_frame = daily[["fear_greed_value", "net_pnl", "volume_usd", "win_rate_realized", "pnl_per_1k_volume"]].copy()
    correlations = (
        correlation_frame.corr(numeric_only=True)["fear_greed_value"]
        .drop("fear_greed_value")
        .rename("corr_with_fear_greed_value")
        .reset_index()
        .rename(columns={"index": "metric"})
    )

    top_coins = (
        coin_summary.groupby("Coin", as_index=False)
        .agg(net_pnl=("net_pnl", "sum"), volume_usd=("volume_usd", "sum"), realized_trades=("realized_trades", "sum"))
        .assign(pnl_per_1k_volume=lambda x: x["net_pnl"] / x["volume_usd"] * 1000)
        .sort_values("net_pnl", ascending=False)
    )

    statistical_validation = build_statistical_validation(daily)

    files = {
        "joined_sample": OUT_DIR / "joined_trades_sample.csv",
        "by_sentiment": OUT_DIR / "summary_by_sentiment.csv",
        "by_direction": OUT_DIR / "summary_by_sentiment_direction.csv",
        "daily": OUT_DIR / "daily_sentiment_performance.csv",
        "coin_summary": OUT_DIR / "coin_sentiment_summary.csv",
        "account_edges": OUT_DIR / "account_sentiment_edges.csv",
        "correlations": OUT_DIR / "daily_correlations.csv",
        "top_coins": OUT_DIR / "top_coins.csv",
        "statistical_validation": OUT_DIR / "statistical_validation.csv",
    }

    merged.head(5000).to_csv(files["joined_sample"], index=False)
    by_sentiment.to_csv(files["by_sentiment"], index=False)
    by_direction.to_csv(files["by_direction"], index=False)
    daily.to_csv(files["daily"], index=False)
    coin_summary.to_csv(files["coin_summary"], index=False)
    account_edges.to_csv(files["account_edges"], index=False)
    correlations.to_csv(files["correlations"], index=False)
    top_coins.to_csv(files["top_coins"], index=False)
    statistical_validation.to_csv(files["statistical_validation"], index=False)

    write_chart_svgs(by_sentiment, top_coins)

    coverage = {
        "trade_rows": int(len(trades)),
        "sentiment_rows": int(len(sentiment)),
        "joined_rows": int(merged["sentiment"].notna().sum()),
        "unmatched_rows": int(merged["sentiment"].isna().sum()),
        "accounts": int(trades["Account"].nunique()),
        "coins": int(trades["Coin"].nunique()),
        "date_min": str(trades["trade_date"].min()),
        "date_max": str(trades["trade_date"].max()),
    }

    write_report(
        coverage,
        by_sentiment,
        by_direction,
        account_edges,
        correlations,
        top_coins,
        statistical_validation,
    )

    return {"coverage": coverage, "files": files, "out_dir": OUT_DIR}


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:.1%}"


def markdown_table(frame: pd.DataFrame, floatfmt: str = ".3f") -> str:
    display = frame.copy()
    for col in display.columns:
        if pd.api.types.is_numeric_dtype(display[col]):
            display[col] = display[col].map(lambda x: "" if pd.isna(x) else format(x, floatfmt))
        else:
            display[col] = display[col].fillna("").astype(str)
    headers = [str(col) for col in display.columns]
    rows = display.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def bootstrap_mean_ci(values: pd.Series, seed: int, draws: int = 2000) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if len(clean) == 0:
        return np.nan, np.nan
    if len(clean) == 1:
        return float(clean[0]), float(clean[0])
    rng = np.random.default_rng(seed)
    sample_idx = rng.integers(0, len(clean), size=(draws, len(clean)))
    boot_means = clean[sample_idx].mean(axis=1)
    return tuple(np.percentile(boot_means, [2.5, 97.5]).astype(float))


def build_statistical_validation(daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, sentiment in enumerate(SENTIMENT_ORDER):
        subset = daily[daily["sentiment"].eq(sentiment)]
        if subset.empty:
            continue
        eff_low, eff_high = bootstrap_mean_ci(subset["pnl_per_1k_volume"], seed=1100 + idx)
        pnl_low, pnl_high = bootstrap_mean_ci(subset["net_pnl"], seed=2100 + idx)
        mean_eff = subset["pnl_per_1k_volume"].mean()
        mean_pnl = subset["net_pnl"].mean()
        rows.append(
            {
                "sentiment": sentiment,
                "days_observed": len(subset),
                "mean_daily_net_pnl": mean_pnl,
                "mean_daily_net_pnl_ci_low": pnl_low,
                "mean_daily_net_pnl_ci_high": pnl_high,
                "mean_daily_pnl_per_1k_volume": mean_eff,
                "mean_daily_pnl_per_1k_ci_low": eff_low,
                "mean_daily_pnl_per_1k_ci_high": eff_high,
                "mean_daily_win_rate": subset["win_rate_realized"].mean(),
                "interpretation": interpret_ci(eff_low, eff_high),
            }
        )
    return pd.DataFrame(rows)


def interpret_ci(low: float, high: float) -> str:
    if pd.isna(low) or pd.isna(high):
        return "insufficient data"
    if low > 0:
        return "daily efficiency stayed positive in bootstrap interval"
    if high < 0:
        return "daily efficiency stayed negative in bootstrap interval"
    return "bootstrap interval crossed zero; treat edge as less stable"


def svg_escape(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_bar_chart(
    labels: list[str],
    values: list[float],
    title: str,
    subtitle: str,
    output_path: Path,
    value_prefix: str = "$",
    value_suffix: str = "",
    max_label_chars: int = 16,
) -> None:
    width, height = 1100, 560
    left, right, top, bottom = 90, 50, 96, 94
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_val = max(values) if values else 1
    scale_max = max_val * 1.18 if max_val > 0 else 1
    bar_gap = 20
    bar_w = max(20, (chart_w - bar_gap * (len(values) - 1)) / max(len(values), 1))
    colors = ["#315A7D", "#00A676", "#9B5DE5", "#F26D3D", "#19324A", "#5B7C99", "#2A9D8F"]

    def value_label(v: float) -> str:
        if abs(v) >= 1_000_000:
            return f"{value_prefix}{v / 1_000_000:.2f}M{value_suffix}"
        if abs(v) >= 1_000:
            return f"{value_prefix}{v / 1_000:.1f}K{value_suffix}"
        return f"{value_prefix}{v:.2f}{value_suffix}"

    grid = []
    for i in range(5):
        y = top + chart_h - (chart_h * i / 4)
        tick = scale_max * i / 4
        grid.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#E2E8F0" stroke-width="1"/>'
        )
        grid.append(
            f'<text x="{left - 14}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="#52606D">{svg_escape(value_label(tick))}</text>'
        )

    bars = []
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + i * (bar_w + bar_gap)
        bar_h = chart_h * (value / scale_max) if scale_max else 0
        y = top + chart_h - bar_h
        short_label = label if len(label) <= max_label_chars else label[: max_label_chars - 1] + "."
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="8" fill="{colors[i % len(colors)]}"/>'
        )
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="#0B1320">{svg_escape(value_label(value))}</text>'
        )
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 42}" text-anchor="middle" font-size="13" fill="#334155">{svg_escape(short_label)}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#F8FAFC"/>
  <rect x="24" y="22" width="{width - 48}" height="{height - 44}" rx="18" fill="#FFFFFF" stroke="#D9E2EC"/>
  <text x="{left}" y="54" font-size="28" font-weight="800" fill="#0B1320">{svg_escape(title)}</text>
  <text x="{left}" y="78" font-size="14" fill="#52606D">{svg_escape(subtitle)}</text>
  {''.join(grid)}
  <line x1="{left}" y1="{top + chart_h}" x2="{width - right}" y2="{top + chart_h}" stroke="#CBD5E1" stroke-width="1.5"/>
  {''.join(bars)}
</svg>'''
    output_path.write_text(svg, encoding="utf-8")


def write_chart_svgs(by_sentiment: pd.DataFrame, top_coins: pd.DataFrame) -> None:
    sentiment_labels = by_sentiment["sentiment"].tolist()
    svg_bar_chart(
        sentiment_labels,
        by_sentiment["pnl_per_1k_volume"].astype(float).tolist(),
        "PnL Efficiency by Sentiment",
        "Net PnL per $1,000 traded volume, grouped by Fear & Greed regime",
        CHART_DIR / "efficiency_by_sentiment.svg",
        value_prefix="$",
    )
    svg_bar_chart(
        sentiment_labels,
        by_sentiment["net_pnl"].astype(float).tolist(),
        "Net PnL by Sentiment",
        "Absolute net PnL by market sentiment classification",
        CHART_DIR / "net_pnl_by_sentiment.svg",
        value_prefix="$",
    )
    top = top_coins.head(8)
    svg_bar_chart(
        top["Coin"].astype(str).tolist(),
        top["net_pnl"].astype(float).tolist(),
        "Top Coins by Net PnL",
        "Highest contributing traded coins across all sentiment regimes",
        CHART_DIR / "top_coins_net_pnl.svg",
        value_prefix="$",
        max_label_chars=12,
    )


def write_report(
    coverage: dict[str, object],
    by_sentiment: pd.DataFrame,
    by_direction: pd.DataFrame,
    account_edges: pd.DataFrame,
    correlations: pd.DataFrame,
    top_coins: pd.DataFrame,
    statistical_validation: pd.DataFrame,
) -> None:
    best_eff = by_sentiment.sort_values("pnl_per_1k_volume", ascending=False).iloc[0]
    worst_eff = by_sentiment.sort_values("pnl_per_1k_volume").iloc[0]
    best_total = by_sentiment.sort_values("net_pnl", ascending=False).iloc[0]
    corr_pnl = correlations.loc[correlations["metric"].eq("net_pnl"), "corr_with_fear_greed_value"].iloc[0]
    corr_eff = correlations.loc[
        correlations["metric"].eq("pnl_per_1k_volume"), "corr_with_fear_greed_value"
    ].iloc[0]

    high_signal_directions = by_direction[
        (by_direction["realized_trades"] >= 100) & by_direction["volume_usd"].gt(0)
    ].sort_values("pnl_per_1k_volume", ascending=False)

    report = [
        "# Trader Performance vs Bitcoin Market Sentiment",
        "",
        "## Dataset Coverage",
        f"- Trades analyzed: {coverage['trade_rows']:,}",
        f"- Joined to sentiment: {coverage['joined_rows']:,} rows; unmatched: {coverage['unmatched_rows']:,}",
        f"- Date range: {coverage['date_min']} to {coverage['date_max']}",
        f"- Accounts: {coverage['accounts']}; coins: {coverage['coins']}",
        "",
        "## Executive Insights",
        f"1. Best risk-adjusted sentiment bucket by net PnL per $1k volume was **{best_eff['sentiment']}** "
        f"at {money(best_eff['pnl_per_1k_volume'])} per $1k traded, with a realized win rate of {pct(best_eff['win_rate_realized'])}.",
        f"2. Worst efficiency appeared in **{worst_eff['sentiment']}** at {money(worst_eff['pnl_per_1k_volume'])} "
        f"per $1k traded. This is the regime where size discipline matters most.",
        f"3. Highest absolute net PnL came during **{best_total['sentiment']}**: {money(best_total['net_pnl'])}, "
        f"partly because activity/volume was also high in that bucket.",
        f"4. Daily fear-greed value correlation with net PnL was **{corr_pnl:.3f}**; correlation with PnL efficiency "
        f"was **{corr_eff:.3f}**. Treat sentiment as a regime filter, not a standalone signal.",
        "",
        "## Sentiment Summary",
        markdown_table(by_sentiment[
            [
                "sentiment",
                "trade_count",
                "realized_trades",
                "volume_usd",
                "net_pnl",
                "win_rate_realized",
                "pnl_per_1k_volume",
                "taker_rate",
            ]
        ]),
        "",
        "## Strongest Direction/Regime Combinations",
        markdown_table(high_signal_directions[
            [
                "sentiment",
                "Direction",
                "realized_trades",
                "volume_usd",
                "net_pnl",
                "win_rate_realized",
                "pnl_per_1k_volume",
            ]
        ].head(12)),
        "",
        "## Account-Level Pattern",
        "The `account_sentiment_edges.csv` output ranks accounts by whether they performed more efficiently in Greed/Extreme Greed than in Fear/Extreme Fear. This is useful for separating traders who thrive in momentum regimes from traders who perform better during panic/liquidation regimes.",
        "",
        "## Statistical Validation",
        "Daily regime metrics were bootstrapped to create 95% confidence intervals for average daily PnL efficiency. This does not prove causality, but it checks whether the observed regime edge is stable across days instead of coming from one isolated trade cluster.",
        "",
        markdown_table(statistical_validation[
            [
                "sentiment",
                "days_observed",
                "mean_daily_pnl_per_1k_volume",
                "mean_daily_pnl_per_1k_ci_low",
                "mean_daily_pnl_per_1k_ci_high",
                "mean_daily_win_rate",
                "interpretation",
            ]
        ]),
        "",
        "## Top Coins by Net PnL",
        markdown_table(top_coins.head(12)[["Coin", "realized_trades", "volume_usd", "net_pnl", "pnl_per_1k_volume"]]),
        "",
        "## Strategy Recommendations",
        "- **Regime-aware sizing:** Use larger size only where both absolute PnL and PnL efficiency are strong. Extreme Greed had the best efficiency; Fear had the highest total PnL but should still be monitored for volume-driven noise.",
        "- **Playbook selection:** Avoid using the same long/short playbook in every sentiment regime. Direction-level results show that certain close/sell patterns performed much better in specific regimes.",
        "- **Trader selection:** Rank accounts by `greed_minus_fear_efficiency` before copying trades. Positive values suggest a trader is more suitable for momentum/greed environments; negative values suggest better fit for defensive or fear-driven environments.",
        "- **Risk controls:** When the bootstrap interval crosses zero, cap exposure or require confirmation from additional signals such as BTC trend, realized volatility, funding rates, and liquidation intensity.",
        "- **Production improvement:** Add BTC returns, funding rates, open interest, volatility, and liquidation data so sentiment is tested alongside market structure rather than in isolation.",
    ]

    (OUT_DIR / "trader_sentiment_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    result = build_outputs()
    print(result["coverage"])
    print(result["out_dir"])
