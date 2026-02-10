# Crypto-Investor Platform v0.1.0

Multi-layered algorithmic trading platform integrating VectorBT, Freqtrade, NautilusTrader, and hftbacktest.

## Installed & Validated

| Framework | Version | Status |
|-----------|---------|--------|
| Freqtrade + FreqAI | 2026.1 | ✅ |
| NautilusTrader | 1.222.0 | ✅ |
| VectorBT | 0.28.4 | ✅ |
| hftbacktest | 2.4.4 | ✅ |
| CCXT | 4.5.37 | ✅ |
| TA-Lib | 0.6.8 (158 funcs) | ✅ |

## Quick Start

```bash
python run.py status                # Platform status
python run.py validate              # Validate all installs
python run.py data generate-sample  # Generate test data
python run.py research screen       # VectorBT strategy screening
python run.py freqtrade backtest    # Freqtrade backtest
python run.py nautilus test         # NautilusTrader engine test
```

## Workflow: Research → Backtest → Paper Trade → Deploy

See `docs/Platform_Analysis_Report.docx` for full analysis.
