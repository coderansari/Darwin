# Darwin — Champion Strategy Report

**Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filter x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #9951**  `[10966ca20775]`

> Adds a 100-period EMA macro-regime filter and MACD confirmation to eliminate counter-trend entries during sustained bear phases, reducing drawdown and improving trade quality at the cost of fewer but higher-conviction signals.

- Universe: `BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK`  ·  Timeframe: `1d`
- Data: CMC OHLCV (live)  ·  Bars: 700
- Evolution: 7 generations · 129 unique specs evaluated
- Claude operators: on

## Performance

| Metric | Value |
| --- | --- |
| Total return | +13.1% |
| CAGR | +6.6% |
| Sharpe | 1.58 |
| Sortino | 1.02 |
| Max drawdown | -1.1% |
| Calmar | 6.07 |
| Win rate | 67% |
| Trades | 21 |
| Exposure | 2% |
| Rule adherence | 100% |
| Fitness | 0.851 |

Equity curve:
```
▁▁▁▁▁▁▁▁▁▁▁▅▅▅▅▅▅▆▆▆▆▆▆▆▆▆▆▇▇▇▇▇▇▇▇▇▇▇▇▇█████████▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇
$10,000  →  $11,307
```

## Fitness progression (best per generation)
`+0.11 → +0.18 → +0.20 → +0.76 → +0.77 → +0.77 → +0.85`

## Hall of fame
1. Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filter x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #9951 [10966ca20775] ret=+13.1% cagr=+6.6% sharpe=1.58 maxDD=-1.1% trades=21 adher=100% fit=0.851
2. Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #2355 [94d3e4eb1b1f] ret=+15.1% cagr=+7.6% sharpe=1.64 maxDD=-1.9% trades=33 adher=100% fit=0.773
3. Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse x Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #9009 [65f27de25b9f] ret=+15.1% cagr=+7.6% sharpe=1.64 maxDD=-1.9% trades=33 adher=100% fit=0.773
4. Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #6709 [804e6b99443e] ret=+13.1% cagr=+6.7% sharpe=1.56 maxDD=-1.9% trades=30 adher=100% fit=0.762
5. Dual-MA Trend Follower v3 - Momentum Breakout x Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #5717 [05673a319008] ret=+10.4% cagr=+5.3% sharpe=1.31 maxDD=-1.6% trades=26 adher=100% fit=0.677

## Champion spec (backtestable, executable)
```json
{
  "name": "Dual-MA Trend Follower v2 - Regime Filtered x Dual-MA Trend Follower v2 - Regime Filter x Dual-MA Trend Follower v2 - Regime Filtered x ROC Momentum Pulse x ROC Momentum Pulse #9951",
  "universe": [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "ADA",
    "DOGE",
    "LINK"
  ],
  "timeframe": "1d",
  "indicators": [
    {
      "id": "ema_fast",
      "type": "EMA",
      "period": 12,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "ema_slow",
      "type": "EMA",
      "period": 40,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "ema_regime",
      "type": "EMA",
      "period": 100,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "rsi14",
      "type": "RSI",
      "period": 14,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "macd",
      "type": "MACD",
      "period": 14,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "macd_sig",
      "type": "MACD_SIGNAL",
      "period": 14,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    }
  ],
  "entry": {
    "all": [
      {
        "left": "ema_fast",
        "op": "cross_above",
        "right": "ema_slow"
      },
      {
        "left": "close",
        "op": ">",
        "right": "ema_regime"
      },
      {
        "left": "rsi14",
        "op": ">",
        "right": 45
      },
      {
        "left": "rsi14",
        "op": ">",
        "right": 58.309
      },
      {
        "left": "macd",
        "op": ">",
        "right": "macd_sig"
      }
    ]
  },
  "exit": {
    "any": [
      {
        "left": "ema_fast",
        "op": "cross_below",
        "right": "ema_slow"
      },
      {
        "left": "close",
        "op": "<",
        "right": "ema_regime"
      },
      {
        "left": "rsi14",
        "op": ">",
        "right": 80
      },
      {
        "left": "macd",
        "op": "cross_above",
        "right": "macd_sig"
      }
    ]
  },
  "risk": {
    "max_position_pct": 0.15,
    "max_open_positions": 4,
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.28,
    "max_drawdown_pct": 0.25,
    "trailing_stop_pct": 0.007
  },
  "sizing": {
    "type": "equal_weight",
    "fraction": 0.2
  },
  "rationale": "Adds a 100-period EMA macro-regime filter and MACD confirmation to eliminate counter-trend entries during sustained bear phases, reducing drawdown and improving trade quality at the cost of fewer but higher-conviction signals."
}
```
