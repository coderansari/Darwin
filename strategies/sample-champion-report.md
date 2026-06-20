# Darwin — Champion Strategy Report

**Golden Cross 20/50 x RSI Reversion 14 x Golden Cross 20/50 x RSI Reversion 14 #8550**  `[82497015bdd5]`

> ride medium-term trends via EMA crossover

- Universe: `BTC, ETH, BNB, SOL`  ·  Timeframe: `1d`
- Data: synthetic  ·  Bars: 500
- Evolution: 7 generations · 123 unique specs evaluated
- Claude operators: off

## Performance

| Metric | Value |
| --- | --- |
| Total return | +31.8% |
| CAGR | +22.4% |
| Sharpe | 1.80 |
| Sortino | 2.32 |
| Max drawdown | -7.0% |
| Calmar | 3.22 |
| Win rate | 64% |
| Trades | 14 |
| Exposure | 38% |
| Rule adherence | 100% |
| Fitness | 1.335 |

Equity curve:
```
▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▂▂▃▃▃▃▃▅▅▅▆▆▆▆▆▆▆▆▆▆▆▆▇█
$10,000  →  $13,184
```

## Fitness progression (best per generation)
`+0.04 → +0.76 → +0.76 → +0.79 → +1.03 → +1.04 → +1.34`

## Hall of fame
1. Golden Cross 20/50 x RSI Reversion 14 x Golden Cross 20/50 x RSI Reversion 14 #8550 [82497015bdd5] ret=+31.8% cagr=+22.4% sharpe=1.80 maxDD=-7.0% trades=14 adher=100% fit=1.335
2. Golden Cross 20/50 x Trend Pullback #9134 [a5ec35485b1f] ret=+19.2% cagr=+13.7% sharpe=1.55 maxDD=-4.7% trades=15 adher=100% fit=1.074
3. Golden Cross 20/50 x RSI Reversion 14 x Golden Cross 20/50 x RSI Reversion 14 #7307 [7e489d7ebfc0] ret=+24.3% cagr=+17.2% sharpe=1.47 maxDD=-7.6% trades=15 adher=100% fit=1.044
4. Golden Cross 20/50 x Trend Pullback #6660 [22925a7b12ef] ret=+18.3% cagr=+13.1% sharpe=1.49 maxDD=-4.8% trades=15 adher=100% fit=1.030
5. Golden Cross 20/50 x Trend Pullback #4435 [075abde4a22a] ret=+18.3% cagr=+13.1% sharpe=1.49 maxDD=-4.8% trades=15 adher=100% fit=1.030

## Champion spec (backtestable, executable)
```json
{
  "name": "Golden Cross 20/50 x RSI Reversion 14 x Golden Cross 20/50 x RSI Reversion 14 #8550",
  "universe": [
    "BTC",
    "ETH",
    "BNB",
    "SOL"
  ],
  "timeframe": "1d",
  "indicators": [
    {
      "id": "ma_fast",
      "type": "EMA",
      "period": 31,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    {
      "id": "ma_slow",
      "type": "EMA",
      "period": 52,
      "source": "close",
      "fast": 12,
      "slow": 26,
      "signal": 9
    }
  ],
  "entry": {
    "any": [
      {
        "left": "ma_fast",
        "op": "cross_above",
        "right": "ma_slow"
      }
    ]
  },
  "exit": {
    "any": [
      {
        "left": "ma_fast",
        "op": "cross_above",
        "right": "ma_slow"
      }
    ]
  },
  "risk": {
    "max_position_pct": 0.317,
    "max_open_positions": 2,
    "stop_loss_pct": 0.086,
    "take_profit_pct": 0.15,
    "max_drawdown_pct": 0.3,
    "trailing_stop_pct": 0.0
  },
  "sizing": {
    "type": "equal_weight",
    "fraction": 0.2
  },
  "rationale": "ride medium-term trends via EMA crossover"
}
```
