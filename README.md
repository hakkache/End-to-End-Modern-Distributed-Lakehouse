# 🏗️ End-to-End Modern Distributed Lakehouse

> A production-grade data lakehouse built with Apache Iceberg, Trino, dbt, and Airflow implementing the Medallion Architecture pattern.

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![Airflow](https://img.shields.io/badge/Airflow-3.0.6-017CEE?logo=apache-airflow)](https://airflow.apache.org/)
[![Trino](https://img.shields.io/badge/Trino-476-DD00A1)](https://trino.io/)
[![dbt](https://img.shields.io/badge/dbt-1.10.10-FF694B?logo=dbt)](https://www.getdbt.com/)
[![Iceberg](https://img.shields.io/badge/Iceberg-1.7.1-1E90FF)](https://iceberg.apache.org/)

---

## 📊 System Architecture

![Lakehouse Architecture]([architecture-diagram.png](https://github.com/hakkache/End-to-End-Modern-Distributed-Lakehouse/blob/main/asset/ModernAr.png))

### Architecture Details

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                          🎯 ORCHESTRATION LAYER                            │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║              Apache Airflow 3.0.6 (LocalExecutor)             ║     │
│    ║                                                                ║     │
│    ║   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    ║     │
│    ║   │  API Server  │   │  Scheduler   │   │DAG Processor │    ║     │
│    ║   │  Port: 8080  │◄─►│  (Executor)  │◄─►│              │    ║     │
│    ║   └──────────────┘   └──────┬───────┘   └──────────────┘    ║     │
│    ║                             │                                 ║     │
│    ║                             ▼                                 ║     │
│    ║                      ┌──────────────┐                         ║     │
│    ║                      │  Triggerer   │                         ║     │
│    ║                      └──────────────┘                         ║     │
│    ║                                                                ║     │
│    ║   ┌────────────────────────────────────────────────────┐     ║     │
│    ║   │  Redis 7.2  (Message Broker - Currently Unused)    │     ║     │
│    ║   │  Note: Ready for CeleryExecutor migration          │     ║     │
│    ║   └────────────────────────────────────────────────────┘     ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Executes dbt commands
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                        🔄 TRANSFORMATION LAYER                             │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║                  dbt Core 1.10.10 (dbt-trino)                 ║     │
│    ║                                                                ║     │
│    ║     ┌───────────┐      ┌───────────┐      ┌───────────┐      ║     │
│    ║     │  Bronze   │ ───► │  Silver   │ ───► │   Gold    │      ║     │
│    ║     │   Layer   │      │   Layer   │      │   Layer   │      ║     │
│    ║     └───────────┘      └───────────┘      └───────────┘      ║     │
│    ║                                                                ║     │
│    ║  📦 Raw Data        📊 Business Logic    📈 Analytics         ║     │
│    ║  + Metadata         + Transformations    + Aggregations       ║     │
│    ║  + Type casting     + Enrichment         + KPIs               ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ SQL Queries
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                         ⚡ QUERY ENGINE LAYER                              │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║                    Trino 476 Cluster                          ║     │
│    ║                                                                ║     │
│    ║              ┌───────────────────────────┐                    ║     │
│    ║              │    Coordinator Node       │                    ║     │
│    ║              │  • Query Parsing          │                    ║     │
│    ║              │  • Planning & Optimization│                    ║     │
│    ║              │  • Metadata Management    │                    ║     │
│    ║              │  Port: 9080               │                    ║     │
│    ║              └───────────┬───────────────┘                    ║     │
│    ║                          │                                     ║     │
│    ║          ┌───────────────┼───────────────┐                    ║     │
│    ║          │               │               │                    ║     │
│    ║          ▼               ▼               ▼                    ║     │
│    ║   ┌──────────┐    ┌──────────┐    ┌──────────┐              ║     │
│    ║   │ Worker 1 │    │ Worker 2 │    │ Worker 3 │              ║     │
│    ║   │(Executor)│    │(Executor)│    │(Executor)│              ║     │
│    ║   └──────────┘    └──────────┘    └──────────┘              ║     │
│    ║                                                                ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ ACID Operations
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                       📚 TABLE FORMAT LAYER                                │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║                  Apache Iceberg 1.7.1                         ║     │
│    ║                                                                ║     │
│    ║    ✓ ACID Transactions        ✓ Time Travel Queries          ║     │
│    ║    ✓ Schema Evolution         ✓ Hidden Partitioning          ║     │
│    ║    ✓ Partition Evolution      ✓ Snapshot Isolation           ║     │
│    ║    ✓ Incremental Reads        ✓ Metadata Optimization        ║     │
│    ║                                                                ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Version Control
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                         🗂️ CATALOG LAYER                                  │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║              Project Nessie 0.76.6                            ║     │
│    ║           Git-like Version Control for Data                   ║     │
│    ║                                                                ║     │
│    ║    📌 Multi-table Transactions                                ║     │
│    ║    🌳 Branch & Tag Support                                    ║     │
│    ║    ⏱️  Time-based Snapshots                                   ║     │
│    ║    🔗 Catalog Versioning                                      ║     │
│    ║                                                                ║     │
│    ║    REST API: http://nessie-catalog:19120/api/v1              ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Reads/Writes
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                         💾 STORAGE LAYER                                   │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║              MinIO (S3-Compatible Object Storage)             ║     │
│    ║                                                                ║     │
│    ║    Bucket: lakehouse                                          ║     │
│    ║    ├─ 📁 bronze/                                              ║     │
│    ║    │   ├─ customer_events/        (2M rows, Parquet)         ║     │
│    ║    │   ├─ payment_transactions/   (1M rows, Parquet)         ║     │
│    ║    │   ├─ inventory_snapshots/    (600K rows, Parquet)       ║     │
│    ║    │   └─ support_tickets/        (200K rows, Parquet)       ║     │
│    ║    │                                                           ║     │
│    ║    ├─ 📁 silver/                                              ║     │
│    ║    │   ├─ customer_sessions/                                 ║     │
│    ║    │   ├─ payment_analysis/                                  ║     │
│    ║    │   ├─ inventory_health/                                  ║     │
│    ║    │   └─ support_metrics/                                   ║     │
│    ║    │                                                           ║     │
│    ║    └─ 📁 gold/                                                ║     │
│    ║        ├─ customer_summary/                                   ║     │
│    ║        ├─ daily_metrics/                                      ║     │
│    ║        └─ product_summary/                                    ║     │
│    ║                                                                ║     │
│    ║    API: 9000  │  Console: 9001                               ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Metadata Storage
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                       🗄️ METADATA DATABASE                                │
│                                                                            │
│    ╔════════════════════════════════════════════════════════════════╗     │
│    ║                    PostgreSQL 16                              ║     │
│    ║                                                                ║     │
│    ║    • Airflow Metadata (DAGs, Tasks, Runs)                     ║     │
│    ║    • User Authentication & Roles                              ║     │
│    ║    • Connection Configurations                                ║     │
│    ║    • XCom (Task Communication)                                ║     │
│    ║                                                                ║     │
│    ╚════════════════════════════════════════════════════════════════╝     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: Medallion Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                         📥 DATA INGESTION                                │
│                                                                          │
│   CSV Files (seeds/)                    Total: 3.8M rows                │
│   ├─ customer_events.csv           →   2,000,000 rows                   │
│   ├─ payment_transactions.csv     →   1,000,000 rows                   │
│   ├─ inventory_snapshots.csv      →     600,000 rows                   │
│   └─ support_tickets.csv           →     200,000 rows                   │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    🥉 BRONZE LAYER (Raw + Metadata)                      │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  seed_bronze Task (Polars + Batched INSERT)                    │   │
│   │  • Read CSV with Polars (fast)                                 │   │
│   │  • Batch INSERT (1000 rows/batch)                              │   │
│   │  • Runtime: 2-3 hours                                          │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   📊 Tables Created:                                                    │
│   ├─ bronze_customer_events        + ingested_at, source_system        │
│   ├─ bronze_payment_transactions   + ingested_at, source_system        │
│   ├─ bronze_inventory_snapshots    + ingested_at, source_system        │
│   └─ bronze_support_tickets         + ingested_at, source_system        │
│                                                                          │
│   ✓ Data Quality Checks:                                               │
│     • NULL validation                                                   │
│     • Duplicate detection                                               │
│     • Schema validation                                                 │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                 🥈 SILVER LAYER (Business Logic)                         │
│                                                                          │
│   📊 Transformations (dbt models):                                      │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ silver_customer_sessions                                       │   │
│   │ ├─ Aggregate events by customer_id + session_id               │   │
│   │ ├─ Calculate session_duration_seconds                         │   │
│   │ ├─ Count events by type (view, click, purchase)               │   │
│   │ └─ Flag: is_converted, is_abandoned, is_bounce                │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ silver_payment_analysis                                        │   │
│   │ ├─ Extract transaction hour, day_of_week                       │   │
│   │ ├─ Flag: is_high_value (>$500)                                │   │
│   │ ├─ Flag: is_off_hours (11pm-6am)                              │   │
│   │ └─ Flag: is_weekend                                            │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ silver_inventory_health                                        │   │
│   │ ├─ Calculate days_of_stock (stock_quantity / avg_daily_sales) │   │
│   │ ├─ Flag: is_low_stock (<7 days)                               │   │
│   │ └─ Flag: needs_reorder                                         │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ silver_support_metrics                                         │   │
│   │ ├─ Calculate response_time_hours                               │   │
│   │ ├─ Calculate resolution_time_hours                             │   │
│   │ ├─ Flag: meets_response_sla (by priority)                     │   │
│   │ └─ Flag: meets_resolution_sla (by priority)                   │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ✓ Business Validation:                                                │
│     • Referential integrity                                             │
│     • Aggregation accuracy                                              │
│     • Data freshness                                                    │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                   🥇 GOLD LAYER (Analytics Ready)                        │
│                                                                          │
│   📊 Aggregations (dbt models):                                         │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ gold_customer_summary                                          │   │
│   │ ├─ total_sessions                                              │   │
│   │ ├─ total_orders                                                │   │
│   │ ├─ total_ltv (lifetime value)                                  │   │
│   │ ├─ avg_order_value                                             │   │
│   │ ├─ conversion_rate                                             │   │
│   │ ├─ customer_segment (VIP, Regular, At-Risk)                   │   │
│   │ └─ support_tickets_count                                       │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ gold_daily_metrics                                             │   │
│   │ ├─ total_revenue (by date)                                     │   │
│   │ ├─ total_orders                                                │   │
│   │ ├─ avg_order_value                                             │   │
│   │ ├─ total_customers                                             │   │
│   │ └─ fraud_flag_count                                            │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ gold_product_summary                                           │   │
│   │ ├─ product_views                                               │   │
│   │ ├─ product_purchases                                           │   │
│   │ ├─ conversion_rate                                             │   │
│   │ ├─ revenue_generated                                           │   │
│   │ └─ current_stock_level                                         │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ✓ KPI Validation:                                                     │
│     • Metric calculations                                               │
│     • Completeness checks                                               │
│     • Business rule compliance                                          │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
                  📄 Documentation
                  (dbt docs generate)
```

---

## 🚀 Quick Start

### Prerequisites

```bash
✓ Docker Desktop (running)
✓ 8GB+ RAM allocated to Docker
✓ 10GB+ free disk space
```

### Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd "End To End Modern Distributed Lakehouse"

# 2. Start all services
docker-compose up -d

# 3. Wait for initialization (~2-3 minutes)
docker-compose ps  # Check all services are healthy

# 4. Access Airflow UI
# URL: http://localhost:8080
# Login: admin / admin
```

### First Pipeline Run

```bash
1. Open Airflow UI → http://localhost:8080
2. Find "ecommerce_dag_pipeline" DAG
3. Click Play button (▶️) → Trigger DAG
4. Monitor execution in Graph view
5. Expected runtime: ~2-4 hours
```

---

## 🎲 Test Data Generation

The project includes a Python script to generate realistic e-commerce test data for pipeline validation.

### Generate Test Data

```bash
# Navigate to data generator directory
cd source_data_generator

# Run the generator
python data_generator.py
```

### Generated Files

The script creates 4 CSV files with realistic data:

| File | Records | Description |
|------|---------|-------------|
| **customer_events.csv** | 2,000,000 | Customer interactions (page views, clicks, purchases) |
| **inventory_snapshots.csv** | 500,000 | Product inventory levels over time |
| **payment_transactions.csv** | 1,000,000 | Payment processing records |
| **support_tickets.csv** | 300,000 | Customer support ticket data |

**Total: 3,800,000 records**

### Data Generator Configuration

You can customize the number of records by editing `data_generator.py`:

```python
# Configuration (top of file)
NUM_CUSTOMER_EVENTS = 2_000_000      # Customer events
NUM_INVENTORY_SNAPSHOTS = 500_000    # Inventory snapshots
NUM_PAYMENT_TRANSACTIONS = 1_000_000 # Payment transactions
NUM_SUPPORT_TICKETS = 300_000        # Support tickets
```

### Move Generated Files to Pipeline

After generation, copy the CSV files to the dbt seeds folder:

```bash
# Copy generated files
cp *.csv ../dags/ecommerce_dbt/seeds/
```

Or use the files already in `dags/ecommerce_dbt/seeds/` (pre-generated).

---

## 🌐 Access Points

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Airflow** | http://localhost:8080 | admin / admin | Pipeline orchestration |
| **Trino** | http://localhost:9080 | admin / - | Query interface |
| **MinIO** | http://localhost:9001 | minioadmin / miniopassword | Storage console |
| **Nessie** | http://localhost:19120 | - | Catalog API |

---

## 📦 Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Orchestration** | Apache Airflow | 3.0.6 | Workflow management |
| **Executor** | LocalExecutor | - | Task execution (single-node) |
| **Message Broker** | Redis | 7.2 | Ready for Celery (unused) |
| **Transformation** | dbt Core | 1.10.10 | SQL transformations |
| **Query Engine** | Trino | 476 | Distributed SQL |
| **Table Format** | Apache Iceberg | 1.7.1 | ACID tables |
| **Catalog** | Project Nessie | 0.76.6 | Version control |
| **Storage** | MinIO | Latest | Object storage |
| **Database** | PostgreSQL | 16 | Metadata |
| **Processing** | Polars | 0.20+ | Fast CSV reading |

---

## 📁 Project Structure

```
End To End Modern Distributed Lakehouse/
│
├── 🐳 docker-compose.yaml       # All services orchestration
├── 🐳 dockerfile                # Custom Airflow image
├── 📦 requirements.txt          # Python dependencies
│
├── ⚙️  config/
│   └── airflow.cfg             # Airflow configuration
│
├── 📊 dags/
│   ├── dag_pipeline.py         # Main ETL DAG
│   ├── operators/
│   │   └── dbt_operator.py     # Custom dbt operator
│   └── ecommerce_dbt/          # dbt project
│       ├── dbt_project.yml
│       ├── profiles.yml
│       ├── models/
│       │   ├── bronze/         # 4 raw models
│       │   ├── silver/         # 4 business models
│       │   └── gold/           # 3 analytics models
│       ├── seeds/              # 4 CSV files (3.8M rows)
│       ├── macros/
│       └── tests/
│
├── 🔍 trino/
│   ├── catalog/
│   │   └── iceberg.properties  # Iceberg config
│   ├── coordinator/            # Coordinator config
│   └── worker/                 # 3 worker configs
│
├── 🎲 source_data_generator/   # Test data generator
│   └── data_generator.py       # Python script to generate CSV files
│
├── 📝 logs/                    # Airflow logs
└── 🔌 plugins/                 # Custom plugins
```

---

## 🎮 Usage Examples

### Query with Trino CLI

```sql
-- Enter Trino container
docker exec -it trino-coordinator trino --catalog iceberg

-- List schemas
SHOW SCHEMAS IN iceberg;

-- Query bronze layer
SELECT * FROM iceberg.bronze.bronze_customer_events LIMIT 10;

-- Query silver layer
SELECT 
    customer_id,
    session_duration_seconds,
    is_converted
FROM iceberg.silver.silver_customer_sessions
WHERE is_converted = true;

-- Query gold layer (analytics)
SELECT 
    customer_segment,
    COUNT(*) as customer_count,
    AVG(total_ltv) as avg_ltv
FROM iceberg.gold.gold_customer_summary
GROUP BY customer_segment;

-- Time travel (Iceberg feature)
SELECT * FROM iceberg.gold.gold_daily_metrics
FOR SYSTEM_TIME AS OF TIMESTAMP '2025-12-30 10:00:00';
```

### Run dbt Commands

```bash
# Enter Airflow container
docker exec -it <airflow-container> bash

cd /opt/airflow/dags/ecommerce_dbt

# Run specific layer
dbt run --select tag:bronze
dbt run --select tag:silver
dbt run --select tag:gold

# Run tests
dbt test

# Generate documentation
dbt docs generate
```

---

## 🧹 Maintenance

### Clean All Data

```bash
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

### Clean MinIO Only

```bash
docker exec minio mc rm --recursive --force local/lakehouse
docker exec minio mc mb local/lakehouse
```

### View Logs

```bash
docker-compose logs -f airflow-scheduler
docker-compose logs -f trino-coordinator
```

---

## ⚙️ Configuration

### Change Pipeline Schedule

Edit `dags/dag_pipeline.py`:

```python
schedule=timedelta(hours=6)  # Every 6 hours
# OR
schedule='0 2 * * *'  # Daily at 2 AM
```

### Adjust Memory Limits

Edit `docker-compose.yaml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| CSRF token error | ✅ Already fixed in `docker-compose.yaml` |
| seed_bronze slow | ✅ Optimized with Polars (hardware-limited) |
| Trino can't connect | Check `iceberg.properties` Nessie URI |
| dbt TABLE_NOT_FOUND | Verify bronze tables created first |
| MinIO storage bloat | Run Iceberg table compaction |

---

## 📈 Performance

| Configuration | Runtime | Notes |
|--------------|---------|-------|
| **Full Pipeline** | 2-4 hours | 3.8M rows on laptop |
| **seed_bronze** | 2-3 hours | CSV ingestion (hardware-limited) |
| **Bronze layer** | 2-3 min | dbt transformations |
| **Silver layer** | 3-5 min | Business logic |
| **Gold layer** | 1-2 min | Aggregations |

---

## 🌐 Cloud Deployment

| Provider | Best For | Free Tier |
|----------|----------|-----------|
| **GCP** | Full architecture | $300 credits |
| **AWS** | Production workloads | 12 months |
| **Oracle Cloud** | Permanent free hosting | Forever free |

---

## 📚 Documentation

- [Apache Airflow](https://airflow.apache.org/docs/)
- [Apache Iceberg](https://iceberg.apache.org/)
- [Trino](https://trino.io/docs/)
- [dbt](https://docs.getdbt.com/)
- [Project Nessie](https://projectnessie.org/)

---

## 📝 License

MIT License

---

## ⭐ Features

✅ Production-ready medallion architecture  
✅ Full ACID compliance  
✅ Git-like version control for data  
✅ Automated data quality validation  
✅ SQL-based transformations  
✅ Time travel queries  
✅ Schema evolution  
✅ Docker-based deployment  

---

**Built with ❤️ using modern data engineering best practices**

**⭐ Star this repo if you found it helpful!**
