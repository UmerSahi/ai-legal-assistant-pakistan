# Khan & Associates — System Administration & Security Guide
### IT Administrator & Compliance Officer Manual

This manual governs the configuration, deployment, security auditing, and maintenance of the **Khan & Associates AI Legal Assistant** cluster.

---

## 1. System Architecture & Topology

The platform operates as an isolated, containerized stack composed of 4 services:

```
                      [Client Browsers / REST Clients]
                                     │ (Port 8000)
                                     ▼
                      ┌─────────────────────────────┐
                      │    khan_legal_api (FastAPI) │
                      │  • Reverse Proxy & Web UI   │
                      │  • Security Engine & Auth   │
                      └──────┬───────────────┬──────┘
                             │               │
            ┌────────────────┴─────┐   ┌─────┴────────────────┐
            ▼                      ▼   ▼                      ▼
    ┌───────────────┐      ┌───────────────┐          ┌───────────────┐
    │ khan_chromadb │      │  khan_neo4j   │          │  khan_worker  │
    │  Vector DB    │      │ Knowledge     │          │  Background   │
    │  (Port 8001)  │      │ Graph (7474)  │          │  Ingestion    │
    └───────────────┘      └───────────────┘          └───────────────┘
```

---

## 2. Production Deployment via Docker Compose

### Prerequisites
- Docker Engine 24.0+ and Docker Compose v2.20+
- Host Machine: 8 vCPUs, 16 GB RAM, 50 GB NVMe Storage
- OS: Ubuntu 22.04 LTS or Windows Server 2022

### Launching the Cluster
```bash
# Clone the repository
git clone https://github.com/khan-associates/ai-legal-assistant.git
cd ai-legal-assistant

# Launch multi-service cluster
docker compose up -d --build

# Verify container statuses
docker compose ps
```

### Checking Cluster Health
```bash
curl -f http://localhost:8000/api/health
```

---

## 3. Security Engine & Access Control Configuration

### Role-Based Access Control (RBAC) & Matter Directory
User credentials and matter assignments are managed in `src/security.py` via `LEGAL_STAFF_DIRECTORY`:

| User ID | Staff Name | Role | Assigned Matter IDs |
|---|---|---|---|
| `usr_mp_01` | Tariq Khan | ManagingPartner | `*` (Firm-wide clearance) |
| `usr_sp_02` | Ayesha Malik | SeniorPartner | `MAT-2024-KHI-001`, `MAT-2024-KHI-002`, `MAT-2024-ISB-015` |
| `usr_asc_03` | Bilal Ahmed | Associate | `MAT-2024-KHI-001` |
| `usr_asc_04` | Fatima Noor | Associate | `MAT-2024-LHR-042` |
| `usr_para_05` | Usman Raza | Paralegal | `MAT-2024-KHI-001` |
| `usr_aud_06` | Zainab Shah | Auditor | Audit logs only |

### Enforcing Multi-Tenant Isolation
When querying ChromaDB or executing hybrid searches, `MatterAccessController.build_secure_filter` enforces strict tenant boundary parameters:
```python
# ChromaDB metadata filter injected automatically:
where_filter = {"matter_id": user_authorized_matter_id}
```
Any attempt by `usr_asc_03` to query `MAT-2024-LHR-042` is immediately blocked with HTTP `403 Forbidden` and logged as a security alert.

---

## 4. Cryptographic Audit Trail (HMAC-SHA256)

Audit logs are persisted in two synchronized destinations:
1. `outputs/security_audit.log`: Human-readable text stream.
2. `outputs/security_audit.jsonl`: Cryptographically chained JSON records.

### Verification of Audit Log Integrity
Run the built-in cryptographic integrity audit:
```bash
python -c "from src.security import SecurityAuditLogger; logger = SecurityAuditLogger(); valid, count, err = logger.verify_chain_integrity(); print('Chain Valid:', valid, '| Records Checked:', count)"
```
Each entry includes the `prev_hash` of the preceding record and signs the current payload with `HMAC-SHA256`. Any retroactive modification or deletion breaks the chain.

---

## 5. Automated CI/CD Testing & Compliance Verification

GitHub Actions executes the full test suite and security scan on every code change:
```bash
# Run all unit and integration tests locally
pytest tests/ -v

# Run 20-vector red-team attack evaluation
python src/security.py

# Re-generate system evaluation dashboard
python src/evaluation_suite.py
```

### Statutory Compliance Checkpoints
- **PECA 2016 (Prevention of Electronic Crimes Act, Pakistan):** Full data confidentiality; zero PII leakage in application logs.
- **Legal Practitioners & Bar Councils Act 1973:** Client attorney privilege strictly preserved via tenant isolation.
- **ISO/IEC 27001 & SOC-2 Type II Alignment:** Tamper-evident logging and human-in-the-loop review controls.
