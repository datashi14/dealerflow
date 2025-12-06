# DealerFlow: Multi-Asset Macro Risk Engine

**DealerFlow** is a quantitative research engine that measures Structural Flow—the mechanical hedging pressure of option dealers—to score market fragility. It features a cloud-native **Hybrid CPU/GPU Architecture** on Azure.

> **Disclaimer**: Personal research project. Not financial advice.

## Azure GPU Orchestration (AKS + KEDA)

DealerFlow demonstrates a sophisticated event-driven architecture for heavy macro simulation:

1. **Core (CPU)**: A system nodepool runs the API and Ingestion pipeline.
2. **Macro Lab (GPU)**: A dedicated `Standard_NC4as_T4_v3` nodepool for ML workloads (Regime Clustering, Embeddings).
3. **Event-Driven Scaling**:
   * Jobs are pushed to an **Azure Storage Queue**.
   * **KEDA** watches the queue and scales the GPU Deployment from 0 to N.
   * **Cluster Autoscaler** provisions GPU nodes only when needed, minimizing cost.

See `k8s/` folder for Kubernetes manifests.

##  Data Reality Check

| Component | Status | Source |
|-----------|--------|--------|
| **Futures Prices** | 🟢 **Real** | Databento (CME Globex) |
| **SPX Options** | 🟡 **Simulated** | Databento / Mock (Requires OPRA) |
| **Narrative** | 🔵 **Template** | LLM Engine (Requires OpenAI Key) |

##  Quick Start

```bash
# 1. Ingest Real Futures
python scripts/ingest_all_databento.py --date 2024-01-05

# 2. Generate Report
python scripts/generate_report.py --date 2024-01-05
```

##  What This Demonstrates

* **Cloud-Native Data Pipeline**: End-to-end ingestion from Databento (institutional) to Postgres to Markdown reports.
* **Domain Knowledge**: Implementation of complex financial metrics like Net Gamma, Charm, and FX Carry.
* **Infrastructure Design**: Event-driven GPU orchestration on Azure using AKS and KEDA.

##  Tech Stack

* **Compute**: Azure Kubernetes Service (AKS), KEDA, Nvidia T4 GPUs.
* **Data**: Postgres, Databento.
* **Code**: Python 3.10, PyTorch (GPU Worker), Pandas (Core).
* **DevOps**: Docker, Kubernetes.
