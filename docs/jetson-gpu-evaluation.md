# Jetson Orin Nano GPU Evaluation

Evaluation of whether distributing components to Jetson Orin Nano GPU(s) would justify the networking and deployment complexity for the A1SI-AITP platform. The current deployment is a single HP Intel Core i7 desktop running Docker.

---

## 1. Current Architecture

- **Host**: Single HP Intel Core i7 desktop, all services in Docker Compose
- **Backend**: Django 5.x / Daphne (ASGI), Django REST Framework, Django Channels
- **Frontend**: nginx serving React 19 + Vite 6 production build
- **Database**: SQLite with WAL mode
- **Trading Frameworks**: VectorBT (screening), Freqtrade (crypto trading), NautilusTrader (multi-asset), hftbacktest (HFT research)
- **ML**: LightGBM classifier for signal prediction (~200 estimators)
- **Data**: Parquet files for OHLCV, CCXT (crypto) + yfinance (equity/forex) adapters
- **Indicators**: 16 technical indicator functions (pandas/numpy vectorized)

---

## 2. Jetson Orin Nano Specs

| Spec | Value |
|------|-------|
| GPU | 1024 CUDA cores, 32 Tensor cores (Ampere) |
| RAM | 8GB LPDDR5 (shared CPU + GPU) |
| AI Performance | 40 TOPS (INT8) |
| Power Envelope | 7-15W |
| Networking | GbE (some models 10GbE) |
| Storage | M.2 NVMe slot |
| CPU | 6-core Arm Cortex-A78AE |
| OS | JetPack (Ubuntu-based, CUDA toolkit included) |

Key constraint: the 8GB RAM is **shared** between CPU and GPU. Any GPU workload reduces memory available to the OS, Python runtime, and application code.

---

## 3. Candidate Workloads

### a) ML Model Training (LightGBM)

LightGBM uses gradient-based decision tree ensembles (GBDT). It is fundamentally CPU-optimized:

- The `gpu_hist` tree method exists in LightGBM but is designed for large-scale regression/ranking tasks, not the small classification models we run (~200 estimators, modest feature sets).
- Our current training completes in **seconds** on the desktop i7 (4+ cores, high single-thread performance).
- The Jetson's Arm CPU cores have significantly lower single-thread performance than the i7, meaning LightGBM would actually run **slower** on the Jetson even without GPU involvement.

**Verdict: No benefit.** LightGBM is CPU-optimized, already trains fast on the desktop, and the Jetson's Arm cores would be a downgrade.

### b) ML Model Training (Future PyTorch / Neural Networks)

If we add neural network models (LSTM, Transformer architectures for time-series prediction):

- The Jetson's 1024 CUDA cores and 32 Tensor cores could accelerate training compared to CPU-only execution.
- Estimated speedup: 2-5x over CPU-only for small models that fit in shared memory.
- **However**: 8GB shared RAM severely limits model size and batch sizes. A Transformer model with attention over long sequences could easily exhaust available GPU memory after accounting for OS and application overhead (~4-5GB usable for GPU).
- A desktop discrete GPU (e.g., RTX 3060 with 12GB dedicated VRAM, RTX 4060 with 8GB dedicated VRAM) provides far more capability: dedicated VRAM, higher clock speeds, more CUDA cores, PCIe bandwidth, and no network overhead.
- Adding a desktop GPU is a single hardware change with zero architectural impact. Adding a Jetson requires distributed system design.

**Verdict: Marginal benefit. A desktop discrete GPU is strongly preferred if GPU training becomes necessary.**

### c) Technical Indicator Computation

Our 16 technical indicator functions (`common/indicators/technical.py`) use pandas and numpy vectorized operations:

- SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ADX, OBV, Stochastic, Williams %R, CCI, MFI, VWAP, Ichimoku, Supertrend, Squeeze Momentum.
- These operate on 1D/2D arrays with pandas Series operations. Execution time is **single-digit milliseconds** on the desktop for typical dataset sizes (1000-10000 bars).
- cuDF (RAPIDS GPU DataFrames) exists as a GPU-accelerated alternative to pandas, but:
  - Data must be transferred to GPU memory (serialization + copy overhead).
  - For our dataset sizes, the transfer latency alone (~0.5-2ms) would approach or exceed the total CPU computation time.
  - cuDF does not support all pandas operations we use (e.g., some rolling window functions).
- Network transfer to a remote Jetson would add 1-10ms of additional latency, making this strictly worse.

**Verdict: No benefit.** CPU computation is already sub-millisecond; GPU transfer overhead would exceed computation time.

### d) Backtest Engines (VectorBT / NautilusTrader)

- **VectorBT**: numpy-based vectorized backtesting. All operations are array-level CPU computations. No CUDA acceleration path exists.
- **NautilusTrader**: Rust/Cython event-driven engine. Performance comes from compiled code and efficient memory layout, not GPU parallelism. No CUDA acceleration path exists.
- **Freqtrade**: Python-based event loop with TA-Lib indicators. CPU-bound, no GPU path.
- **hftbacktest**: Rust-based event-driven simulation. CPU-optimized, no GPU path.

None of these frameworks have GPU-accelerated execution modes. Their performance bottlenecks are single-thread CPU speed (event processing) and memory bandwidth (vectorized operations), both of which favor the desktop i7 over the Jetson's Arm cores.

**Verdict: No benefit.** No backtesting framework in our stack supports GPU acceleration.

### e) Data Pipeline

The data pipeline (`common/data_pipeline/pipeline.py`) performs:

- Network API calls to CCXT exchanges and yfinance (I/O-bound, waiting on remote servers).
- Parquet file read/write (disk I/O bound, sequential).
- Data validation and transformation (lightweight CPU operations).

GPU acceleration provides zero value to network I/O or disk I/O workloads. The bottleneck is external API response times (100ms-2s per request), not local computation.

**Verdict: No benefit.** Pipeline is I/O-bound; GPU cannot accelerate network or disk operations.

### f) Real-time Inference

If we add PyTorch models for live signal generation during trading:

- NVIDIA TensorRT on the Jetson can optimize inference graphs for low-latency execution (sub-millisecond for small models).
- The Jetson's always-on, low-power profile is well-suited for continuous inference at the edge.
- **However**: Our trading frequency ranges from minutes (Freqtrade crypto) to hours (VectorBT screening triggers). We do not need sub-millisecond inference latency.
- CPU inference for small models (which is all that fits in 8GB shared RAM) takes 1-10ms on the desktop, which is well within our latency budget.
- The complexity of routing inference requests over the network to the Jetson and back would add more latency than it saves.

**Verdict: Minimal benefit for our use case.** Trading frequency is far too low to justify dedicated inference hardware.

---

## 4. Complexity Cost

Adding a Jetson Orin Nano to the deployment introduces significant operational complexity:

### Network Latency
- Every cross-host request adds 1-10ms of network latency (GbE, local network).
- For workloads that currently complete in milliseconds, this overhead is proportionally enormous.
- Jitter and packet loss on local networks can cause occasional 50-100ms spikes.

### Docker Networking
- Requires overlay network or host-level routing between two Docker hosts.
- Service discovery must work across hosts (Docker Swarm or manual configuration).
- Port mapping and firewall rules on two machines instead of one.

### Data Serialization
- Any data passed between desktop and Jetson must be serialized (JSON, protobuf, or similar).
- Parquet files would need to be synced or served over the network.
- SQLite database cannot be shared over the network (single-writer, file-based).

### Monitoring and Operations
- Two hosts to monitor: CPU, memory, disk, GPU utilization, thermals.
- Two sets of Docker logs to aggregate and search.
- Health checks must cover cross-host connectivity.
- Alerting must account for network partition scenarios.

### Failure Modes
- Network partition splits the trading system: half on desktop, half on Jetson.
- If the Jetson hosts a critical component (e.g., inference), network failure stops trading.
- Recovery procedures become more complex (which host to restart, in what order).
- Power management: the Jetson could lose power independently of the desktop.

### Deployment Complexity
- Two Docker hosts require version-synchronized deployments.
- Container images must be built for both x86_64 (desktop) and aarch64 (Jetson).
- Multi-architecture Docker builds add CI/CD complexity.
- Testing must cover both architectures and the network path between them.

### RAM Constraint
- 8GB shared RAM on the Jetson is less than what the desktop provides.
- Any workload moved to the Jetson gets less RAM, not more.
- GPU memory allocation reduces available CPU memory on the Jetson.

---

## 5. Decision Matrix

| Workload | GPU Benefit | Implementation Effort | Operational Risk | Recommendation |
|----------|------------|----------------------|-----------------|----------------|
| LightGBM training | None | Low | Low | **Skip** |
| PyTorch training (future) | Low-Medium | High | Medium | **Desktop GPU preferred** |
| Technical indicators | None | Medium | Low | **Skip** |
| Backtesting (VectorBT/Nautilus) | None | Medium | Low | **Skip** |
| Data pipeline | None | Low | Low | **Skip** |
| Real-time inference (future) | Low | High | Medium | **Skip** (trading frequency too low) |

---

## 6. Recommendation

### Decision: Do not add Jetson Orin Nano to the deployment.

**Reasoning:**

1. **No current workload benefits from CUDA cores.** LightGBM is CPU-optimized, backtesting engines have no GPU path, technical indicators run in milliseconds on CPU, and the data pipeline is I/O-bound.

2. **LightGBM has no meaningful GPU acceleration** for our classification task. The `gpu_hist` mode targets large-scale regression workloads, not 200-estimator classifiers on modest datasets.

3. **8GB shared RAM is a constraint, not an advantage.** The desktop has more available RAM for any workload. Moving computation to the Jetson means working with less memory, not more.

4. **Network latency and deployment complexity outweigh any marginal gains.** Even if a workload gained 2x speedup on the Jetson GPU, adding 1-10ms of network latency per request and managing a distributed deployment negates that benefit for our use case.

5. **Desktop discrete GPU is the superior upgrade path.** If GPU acceleration becomes necessary (e.g., PyTorch model training), installing a PCIe GPU in the desktop provides dedicated VRAM, higher performance, zero network overhead, and no architectural changes.

### Re-evaluate if:

- **We add PyTorch/TensorFlow models requiring GPU training** -- but consider a desktop discrete GPU first (RTX 3060/4060, single PCIe slot, no network overhead).
- **We need always-on, low-power inference at the edge** -- the Jetson's 7-15W power envelope is genuinely advantageous for 24/7 inference appliances, but only if inference latency requirements exceed what CPU can deliver.
- **Multiple trading strategies need parallel GPU inference** -- unlikely at our current scale (3-7 strategies, minute-to-hour frequency), but would be a legitimate use case at institutional scale.
- **We deploy to a remote location** where the Jetson operates independently -- e.g., a dedicated trading node with its own exchange connectivity, not as a peripheral to the desktop.
