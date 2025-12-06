# DealerFlow Architecture

DealerFlow is a batch-oriented, cross-asset macro research engine designed to be cloud-native and modular. It separates data ingestion, feature engineering, scoring, and reporting into distinct phases.

## 1. High-Level Data Flow

`mermaid
graph TD
    A[External APIs] -->|Databento/CFTC| B(Ingestion Layer)
    B --> C[(Postgres DB)]
    C --> D[Feature Engineering]
    D -->|Net Gamma, Carry, Term Structure| E[Scoring Engine]
    E -->|Instability Scores| F[Report Generator]
    F -->|Context| G[LLM Narrative Engine]
    G --> H[Final Markdown Report]
`

## 2. Core Components

### 2.1 Data Layer (Postgres)
The database schema is normalized into three layers:
1. **Raw Tables** (aw_futures, aw_options, aw_fx): Direct dumps from APIs.
2. **Feature Tables** (eatures_equity, eatures_commodity): Computed signals (e.g., Net Gamma, 20d Volatility).
3. **Scores Table** (sset_scores): Final 0-100 instability scores and regime labels.

### 2.2 Compute Layer (Python)
* **Ingestion**: Standalone scripts (ingest_*.py) that fetch data and handle upserts (idempotent).
* **Math Engine**: Uses py_vollib_vectorized for efficient Black-Scholes calculations on option chains.
* **Scoring**: A deterministic rules engine that maps features to regimes (STABLE, FRAGILE, EXPLOSIVE).

## 3. Azure GPU Orchestration (Hybrid Architecture)

To handle heavy ML workloads (e.g., regime clustering, embeddings) without blocking the core API, the system uses a hybrid AKS architecture.

### 3.1 Cluster Topology
* **Nodepool 1 (System/CPU)**: Runs the Core API and Ingestion jobs.
* **Nodepool 2 (GPU)**: Standard_NC4as_T4_v3 (Nvidia T4). Tainted (sku=gpu:NoSchedule) to ensure only ML jobs land here.

### 3.2 Event-Driven Autoscaling (KEDA)
We minimize costs by keeping the GPU pool at 0 nodes when idle.

1. **Trigger**: Core system pushes a job to Azure Storage Queue dealerflow-gpu-jobs.
2. **Scale Up**: **KEDA** detects queue depth > 0 and scales the dealerflow-gpu-worker deployment.
3. **Infra Scale**: AKS Cluster Autoscaler provisions the VM.
4. **Execute**: Worker pulls features from Postgres, runs PyTorch models, and persists results.

`mermaid
graph LR
    A[Core System] -->|Enqueue| B[Azure Queue]
    B -->|Trigger| C[KEDA]
    C -->|Scale| D[GPU Worker]
    D <-->|Read/Write| E[(Postgres)]
`

## 4. Technology Stack
* **Language**: Python 3.10
* **Container**: Docker, Azure Container Registry (ACR)
* **Orchestration**: Kubernetes (AKS), KEDA
* **Database**: PostgreSQL (Azure Database for PostgreSQL)
* **Data**: Databento (Institutional Futures/Options), Alpha Vantage (FX/Gold Backup)
