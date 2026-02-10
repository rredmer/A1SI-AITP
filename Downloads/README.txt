CRYPTO-INVESTOR PLATFORM — Downloaded Software
================================================

This folder contains all installed software frameworks and their dependencies.

PACKAGES (archived from /usr/local/lib/python3.12/dist-packages/):
  packages/freqtrade.tar.gz       — Freqtrade 2026.1 (crypto trading engine)
  packages/nautilus_trader.tar.gz  — NautilusTrader 1.222.0 (institutional execution)
  packages/vectorbt.tar.gz        — VectorBT 0.28.4 (vectorized backtesting)
  packages/hftbacktest.tar.gz     — hftbacktest 2.4.4 (HFT backtesting)
  packages/ccxt.tar.gz            — CCXT 4.5.37 (100+ exchange APIs)
  packages/talib.tar.gz           — TA-Lib 0.6.8 (158 technical indicators)

MANIFESTS:
  installed_packages_manifest.json — Detailed metadata for 25 core packages
  package_locations.txt            — Install paths and sizes
  pip_freeze_trading_packages.txt  — Core trading package versions (28 packages)
  pip_freeze_full.txt              — Complete environment (243 packages)

TO REINSTALL:
  pip install freqtrade nautilus_trader vectorbt hftbacktest ccxt ta-lib

  Or from the full requirements:
  pip install -r ../Documents/configs/requirements.txt
