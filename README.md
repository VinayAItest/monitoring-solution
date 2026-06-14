# 🔭 Azure Monitoring Solution

Complete end-to-end monitoring stack: **Docker → AKS → Prometheus → Grafana → ServiceNow**

---

## 🏗 Architecture

```
GitHub (source)
    │
    └─► GitHub Actions CI/CD
            │
            ├─► Docker Build → Azure Container Registry (ACR)
            │
            ├─► Terraform → Azure Resource Group + AKS Cluster
            │
            └─► kubectl deploy to AKS
                    │
                    ├── monitoring-app (Flask + /metrics)
                    │
                    ├── Prometheus  (scrapes /metrics, fires alerts)
                    │       │
                    │       └── Alertmanager ──► ServiceNow Bridge ──► ServiceNow Incidents
                    │
                    └── Grafana  (dashboards from Prometheus data)
```

---

## 📁 Project Structure

```
monitoring-solution/
├── app/
│   ├── app.py                    # Flask app with Prometheus metrics
│   └── requirements.txt
├── docker/
│   └── Dockerfile                # Multi-stage production image
├── terraform/
│   ├── main.tf                   # AKS + ACR + Azure resources
│   ├── variables.tf
│   └── outputs.tf
├── k8s/
│   └── deployment.yaml           # App deployment + HPA
├── prometheus/
│   ├── prometheus.yaml           # Prometheus + alert rules
│   └── alertmanager.yaml         # Alertmanager → ServiceNow webhook
├── servicenow/
│   ├── servicenow_bridge.py      # Webhook → ServiceNow incidents
│   └── servicenow-bridge.yaml    # K8s deployment
├── grafana/
│   ├── grafana.yaml              # Grafana deployment + datasource
│   └── monitoring-dashboard.json # Pre-built dashboard
└── .github/workflows/
    └── deploy.yml                # Full CI/CD pipeline
```

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install tools
az cli, kubectl, terraform, docker, helm
```

### 2. Set GitHub Secrets
```
AZURE_CREDENTIALS   → az ad sp create-for-rbac --sdk-auth output
```

### 3. Update configuration
- `terraform/variables.tf`  → set your ACR name, location, email
- `servicenow/servicenow-bridge.yaml` → set your ServiceNow instance/credentials
- `grafana/grafana.yaml` → set admin password

### 4. Push to main
```bash
git add .
git commit -m "Initial monitoring stack"
git push origin main
```
GitHub Actions will: build image → provision infra → deploy everything.

---

## 🔗 Accessing Services

```bash
# Grafana dashboard
kubectl get svc grafana -n monitoring
# → Open EXTERNAL-IP in browser, login admin / <your password>

# Prometheus UI
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# → http://localhost:9090

# Application
kubectl get svc monitoring-app-svc -n monitoring-app
```

---

## 🚨 Alert Flow

```
Prometheus detects issue
    → Alertmanager groups alert
        → POST to ServiceNow Bridge (:8080/alert)
            → Bridge calls ServiceNow API
                → Incident created (P1/P2/P3)
                    → When resolved → Incident auto-closed
```

---

## 📊 Grafana Dashboard Panels

| Panel | Metric |
|-------|--------|
| App Status | `up{job="monitoring-app"}` |
| Requests/sec | `rate(app_requests_total[5m])` |
| Error Rate | `rate(app_requests_total{status="500"}[5m])` |
| P95 Latency | `histogram_quantile(0.95, ...)` |
| CPU / Memory | Container resource metrics |
| Active Alerts | `ALERTS{alertstate="firing"}` |
