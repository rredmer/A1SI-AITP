# Exchange Connectors & Data Sources Setup Guide

This guide walks through signing up for cryptocurrency exchange accounts, generating API keys, and connecting them to the A1SI-AITP platform.

---

## Supported Exchanges

| Exchange | ID         | Signup URL                                      | Passphrase Required |
|----------|------------|------------------------------------------------|---------------------|
| Binance  | `binance`  | https://www.binance.com/en/register             | No                  |
| Bybit    | `bybit`    | https://www.bybit.com/register                  | No                  |
| Kraken   | `kraken`   | https://www.kraken.com/sign-up                  | No                  |
| Coinbase | `coinbase` | https://www.coinbase.com/signup                 | No                  |
| KuCoin   | `kucoin`   | https://www.kucoin.com/ucenter/signup           | Yes                 |

---

## Step 1: Create an Exchange Account

### Binance

1. Go to https://www.binance.com/en/register
2. Sign up with email or phone number
3. Complete identity verification (KYC) — required for API access
4. Enable two-factor authentication (2FA) — strongly recommended

### Bybit

1. Go to https://www.bybit.com/register
2. Register with email or phone
3. Complete identity verification
4. Enable 2FA (Google Authenticator or SMS)

### Kraken

1. Go to https://www.kraken.com/sign-up
2. Create account with email and username
3. Complete verification (Starter level minimum for API trading)
4. Enable 2FA

### Coinbase

1. Go to https://www.coinbase.com/signup
2. Register with email
3. Verify identity with government ID
4. Enable 2FA

### KuCoin

1. Go to https://www.kucoin.com/ucenter/signup
2. Register with email or phone
3. Complete KYC verification
4. Enable 2FA
5. Set a trading password — you will need this as the API passphrase

---

## Step 2: Generate API Keys

Each exchange has an API management page where you create keys. You need an **API Key** and **API Secret** (plus a **Passphrase** for KuCoin).

### Binance

1. Log in and go to **Account > API Management** (https://www.binance.com/en/my/settings/api-management)
2. Click **Create API** and choose **System Generated**
3. Name your key (e.g., "a1si-aitp")
4. Complete 2FA verification
5. Copy the **API Key** and **Secret Key** immediately — the secret is only shown once
6. Configure restrictions:
   - Enable **Read Info** (required)
   - Enable **Enable Spot & Margin Trading** (for live trading)
   - Restrict to your IP address if possible
   - Do **not** enable withdrawals unless you specifically need them

### Bybit

1. Log in and go to **Account & Security > API** (https://www.bybit.com/app/user/api-management)
2. Click **Create New Key**
3. Select **System-generated API Keys**
4. Set permissions:
   - **Read** (required)
   - **Trade** (for live trading)
5. Set IP restriction if possible
6. Copy the API Key and Secret — shown only once

### Kraken

1. Log in and go to **Security > API** (https://www.kraken.com/u/security/api)
2. Click **Add key**
3. Set a description (e.g., "a1si-aitp")
4. Configure permissions:
   - **Query Funds** (required)
   - **Query Open Orders & Trades** (required)
   - **Create & Modify Orders** (for live trading)
5. Copy the API Key and Private Key

### Coinbase

1. Log in and go to **Settings > API** or use Coinbase Developer Platform
2. Click **New API Key**
3. Select the accounts you want to grant access to
4. Set permissions:
   - **wallet:accounts:read** (required)
   - **wallet:trades:create** (for live trading)
5. Complete 2FA verification
6. Copy the API Key and API Secret

### KuCoin

1. Log in and go to **Account Security > API Management**
2. Click **Create API**
3. Enter your trading password
4. Set a name and passphrase — **save this passphrase, you will need it**
5. Set permissions:
   - **General** (required)
   - **Trade** (for live trading)
6. Set IP restriction if possible
7. Copy the API Key, Secret, and Passphrase

### Security Best Practices for API Keys

- **Never enable withdrawal permissions** unless absolutely necessary
- **Restrict API keys to your IP address** when the exchange supports it
- **Use separate API keys** for this platform — don't reuse keys from other apps
- **Never share API keys** or commit them to version control
- **Rotate keys regularly** (every 90 days recommended)
- **Start with read-only permissions** until you're ready for live trading

---

## Step 3: Configure the Platform

There are two ways to add exchange credentials: the **web UI** (recommended) or **environment variables**.

### Option A: Web UI (Recommended)

The web dashboard provides a Settings page for managing exchange connections with encrypted storage.

1. Start the platform:
   ```bash
   make dev
   ```

2. Open http://localhost:5173 and log in (default: `admin` / `admin`)

3. Navigate to **Settings**

4. Under **Exchange Connections**, click **Add Exchange**

5. Fill in the form:
   - **Name**: A friendly label (e.g., "Binance Main", "Kraken Trading")
   - **Exchange**: Select from dropdown
   - **API Key**: Paste your API key
   - **API Secret**: Paste your secret key
   - **Passphrase**: (KuCoin only) Paste your API passphrase
   - **Sandbox mode**: Check this to use the exchange's testnet (recommended for initial setup)
   - **Set as default**: Check to make this the default exchange for market data

6. Click **Add Exchange**

7. Click **Test** next to the new connection to verify connectivity
   - Green dot = connected successfully
   - Red dot = connection failed (hover to see error)

All credentials are encrypted at rest using Fernet symmetric encryption before being stored in the database. The API never returns raw credentials — only masked versions (e.g., `abcd****mnop`).

### Option B: Environment Variables

For CLI-based workflows (data pipeline, Freqtrade), set credentials in the `.env` file:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Generate an encryption key (required for credential storage):
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Edit `.env` and fill in your credentials:
   ```bash
   # Encryption key (paste the generated key)
   DJANGO_ENCRYPTION_KEY=your-generated-fernet-key

   # Default exchange for CLI operations
   EXCHANGE_ID=binance

   # Binance API credentials
   BINANCE_API_KEY=your-api-key-here
   BINANCE_SECRET=your-api-secret-here

   # Bybit API credentials (if using Bybit)
   BYBIT_API_KEY=your-api-key-here
   BYBIT_SECRET=your-api-secret-here

   # Kraken API credentials (if using Kraken)
   KRAKEN_API_KEY=your-api-key-here
   KRAKEN_SECRET=your-api-secret-here
   ```

4. Secure the file permissions:
   ```bash
   make harden
   ```
   This sets `.env` to mode 600 (owner read/write only).

### Freqtrade Exchange Configuration

If using Freqtrade for automated trading, also update `freqtrade/config.json`:

```json
{
  "exchange": {
    "name": "binanceus",
    "key": "your-api-key",
    "secret": "your-api-secret",
    "pair_whitelist": [
      "BTC/USDT",
      "ETH/USDT",
      "SOL/USDT"
    ]
  },
  "dry_run": true
}
```

Alternatively, Freqtrade reads environment variables using the double-underscore convention:
```bash
# In .env — overrides freqtrade/config.json values
FREQTRADE__EXCHANGE__KEY=your-api-key
FREQTRADE__EXCHANGE__SECRET=your-api-secret
```

---

## Step 4: Sandbox / Testnet Mode

All exchanges offer testnet environments for paper trading. **Always start in sandbox mode** before using real funds.

| Exchange | Testnet URL                          | Notes                                    |
|----------|--------------------------------------|------------------------------------------|
| Binance  | https://testnet.binance.vision       | Separate signup, free test funds         |
| Bybit    | https://testnet.bybit.com            | Separate signup, free test funds         |
| Kraken   | https://demo-futures.kraken.com      | Futures testnet only                     |
| KuCoin   | https://sandbox.kucoin.com           | Separate signup                          |

To use sandbox mode:
- **Web UI**: Check the "Sandbox mode" checkbox when adding an exchange
- **Platform config**: Set `sandbox: true` in `configs/platform_config.yaml`
- **Freqtrade**: Set `"dry_run": true` in `freqtrade/config.json`

When you're ready for live trading, uncheck sandbox mode in the Settings page or set `sandbox: false` in the config. The platform config also enforces a minimum of 14 days paper trading before live (`min_paper_trade_days: 14`).

---

## Step 5: Configure Data Sources

Data sources define which trading pairs and timeframes to fetch from each exchange. You need at least one exchange connection before adding a data source.

### Via Web UI

1. In **Settings**, scroll to **Data Sources**
2. Click **Add Data Source**
3. Fill in:
   - **Exchange**: Select a configured exchange connection
   - **Symbols**: Comma-separated trading pairs (e.g., `BTC/USDT, ETH/USDT, SOL/USDT`)
   - **Timeframes**: Click to toggle: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`
   - **Fetch interval**: How often to refresh data (in minutes, default: 60)
4. Click **Add Data Source**

### Via Platform Config

The watchlist in `configs/platform_config.yaml` defines default symbols for CLI operations:

```yaml
data:
  watchlist:
    - "BTC/USDT"
    - "ETH/USDT"
    - "SOL/USDT"
    - "BNB/USDT"
    - "XRP/USDT"
    - "ADA/USDT"
    - "AVAX/USDT"
    - "DOGE/USDT"
    - "DOT/USDT"
    - "LINK/USDT"

  timeframes:
    - "1m"
    - "5m"
    - "15m"
    - "1h"
    - "4h"
    - "1d"

  history_days: 365
```

---

## Step 6: Download Market Data

### Via Web UI

1. Navigate to **Data Management**
2. Configure the download:
   - **Symbols**: Comma-separated pairs (default: BTC/USDT, ETH/USDT, SOL/USDT)
   - **Timeframes**: Click to select (e.g., 1h, 4h)
   - **Exchange**: Select from dropdown (Binance, Bybit, Kraken)
   - **History (days)**: How far back to fetch (default: 90)
3. Click **Download**
4. A progress bar shows download status
5. Downloaded data appears in the **Available Data** table below

To test without API keys, click **Generate Sample Data** — this creates synthetic OHLCV data for BTC, ETH, and SOL (1h + 4h, 90 days) with no exchange connection required.

### Via CLI

```bash
# Download default watchlist from Binance
python run.py data download

# Download specific symbols
python run.py data download --symbols BTC/USDT,ETH/USDT --timeframes 1h,4h --exchange binance --days 365

# Generate synthetic test data (no API keys needed)
python run.py data generate-sample

# List available data files
python run.py data list

# Check data info for a specific symbol
python run.py data info BTC/USDT --timeframe 1h --exchange binance
```

### Data Storage

- Format: Apache Parquet (snappy compression)
- Location: `data/processed/`
- Naming: `{exchange}_{SYMBOL}_{timeframe}.parquet` (e.g., `binance_BTC_USDT_1h.parquet`)
- New downloads merge with existing data (no duplicates)
- Data is shared across all trading framework tiers (VectorBT, Freqtrade, NautilusTrader)

### Data Quality Validation

The pipeline includes built-in data quality checks:
- Gap detection (missing candles)
- Staleness monitoring
- NaN value auditing
- Price spike detection (configurable threshold)
- OHLC constraint verification (high >= max(open, close), etc.)

Run validation via the data pipeline:
```python
from common.data_pipeline.pipeline import validate_data
report = validate_data("BTC/USDT", "1h", "binance", "data/processed")
print(report.issues_summary)
```

---

## Troubleshooting

### Connection Test Fails

| Error                        | Cause                                   | Fix                                                  |
|-----------------------------|-----------------------------------------|------------------------------------------------------|
| `AuthenticationError`        | Invalid API key or secret               | Re-check credentials, regenerate if needed           |
| `ExchangeNotAvailable`       | Exchange is down or blocked             | Try again later, check exchange status page          |
| `NetworkError`               | No internet or firewall blocking        | Check network, ensure exchange API is reachable      |
| `InvalidNonce`               | Clock sync issue                        | Sync system clock (`timedatectl set-ntp true`)       |
| `PermissionDenied`           | Insufficient API permissions            | Enable required permissions in exchange API settings |
| `Sandbox not supported`      | Exchange has no testnet for that mode   | Uncheck sandbox mode or use a different exchange     |

### Common Issues

- **KuCoin "Passphrase required"**: KuCoin API keys require a passphrase set during key creation. Enter it in the Passphrase field.
- **Binance US vs Binance Global**: If you're in the US, you may need to use `binanceus` instead of `binance`. Update the exchange ID accordingly in Freqtrade config.
- **Rate limiting**: The platform handles rate limits automatically with backoff. If you see persistent rate limit errors, reduce the number of symbols or increase the fetch interval.
- **IP restrictions**: If you set IP restrictions on your API key, ensure the IP of the machine running A1SI-AITP is whitelisted.

### Verify Platform Status

```bash
# Check overall platform status including exchange configs
python run.py status

# Validate that CCXT and exchange libraries are installed correctly
python run.py validate
```

---

## Security Summary

| Layer               | Protection                                                     |
|--------------------|----------------------------------------------------------------|
| Transport           | HTTPS (TLS certs via `make certs`)                            |
| Authentication      | Django session-based auth, CSRF protection                    |
| API credentials     | Fernet encryption at rest (AES-128-CBC)                       |
| API responses       | Credentials masked, never returned in plaintext               |
| File permissions    | `.env` set to 600 via `make harden`                           |
| Database backups    | GPG-encrypted via `BACKUP_ENCRYPTION_KEY`                     |
| Password hashing    | Argon2id (Django default)                                     |
| Sandbox enforcement | 14-day paper trading minimum before live (`platform_config`)  |
