# Vector DB Benchmark for Music Semantic Search

This repository benchmarks **6-7 vector databases** for music semantic search, using a shared dataset and query set. It provides both a CLI benchmarking tool and a web UI for side-by-side DB comparison.

**🏆 Key Finding**: Comprehensive benchmarking across 15-20 iterations reveals **Qdrant as the production winner**, delivering equivalent performance to competitors while maintaining single-service operational simplicity.

## Features

- **Comprehensive benchmarking**: ingest time, query latency, recall, hit rate, and throughput (QPS)
- **6-7 Vector Databases**: Qdrant, Milvus, Weaviate, ChromaDB, Pinecone, SQLite, and TopK (with quota)
- **Production-grade testing**: Up to 20 iterations for statistical reliability
- **Flexible embedding**: Use `sentence-transformers` (default) or OpenAI embeddings
- **Heuristic relevance**: Weak label matching using tags/genres for recall/hit metrics
- **Rich CLI**: Many flags for DB selection, concurrency, top-k sweep, teardown, etc.
- **Modern UI**: FastAPI backend + static frontend for live DB comparison
- **Automated result plots**: Generates summary charts and per-k metrics tables
- **Comprehensive reporting**: Detailed analysis with production recommendations

---

## Supported Databases

| Database        | Deployment  | Performance Tier | Best For                                            |
| --------------- | ----------- | ---------------- | --------------------------------------------------- |
| **🥇 Qdrant**   | Local/Cloud | Champion         | Production systems (optimal speed + ops simplicity) |
| **🥈 Milvus**   | Local       | High-Performance | Maximum speed with complex infrastructure           |
| **🥉 Weaviate** | Local/Cloud | Good             | Feature-rich applications                           |
| **ChromaDB**    | Local       | Solid            | Development & moderate workloads                    |
| **Pinecone**    | Cloud       | Managed          | Fully managed cloud deployments                     |
| **SQLite**      | Embedded    | Specialized      | Embedded/edge applications                          |
| **TopK**        | Cloud       | Unknown\*        | Testing (requires quota upgrade from support)       |

_\*TopK requires quota increases for benchmarking - contact support for higher limits_

## Dataset

Use the [Muse Musical Sentiment dataset](https://www.kaggle.com/datasets/cakiki/muse-the-musical-sentiment-dataset) from Kaggle. Place the CSV as `data/muse.csv`.

You can test with `data/sample_data.csv` for a dry run.

---

## Quick Start

1. **Install dependencies**

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment**

- Copy `.env.example` to `.env` and fill in DB URLs/API keys as needed

3. **Start local DBs (optional)**

```sh
docker compose -f scripts/docker-compose.yml up -d
```

4. **Generate embeddings**

```sh
python embeddings/embed.py --csv data/muse.csv --out data/embeddings.parquet
# For OpenAI: add --use_openai [--model text-embedding-3-large]
```

5. **Run the benchmark**

```sh
python benchmark.py --csv data/muse.csv --embeddings data/embeddings.parquet --dbs qdrant milvus weaviate chroma pinecone sqlite --topk 10 --repetitions 15
# For TopK (with quota): add 'topk' to --dbs list
# See all CLI flags with: python benchmark.py --help
```

6. **View results**

- Summary and per-k plots: `results/`
- Metrics: `results/metrics.json`

---

## CLI Usage

```sh
python benchmark.py --csv data/muse.csv --embeddings data/embeddings.parquet --dbs qdrant milvus weaviate chroma pinecone sqlite --topk 10 --repetitions 15 [--teardown_after_benchmark]
# For TopK: add 'topk' to --dbs (requires quota increase from support)
```

**Key flags:**

- `--dbs`: List of DBs to benchmark (qdrant, milvus, weaviate, chroma, pinecone, sqlite, topk)
- `--topk`: Top-k for search (default: 10)
- `--topk_sweep`: List of k values to sweep (e.g. 5 10 50)
- `--repetitions`: Number of repetitions per query
- `--concurrency`: Number of concurrent query workers
- `--teardown_after_benchmark`: Delete DB/index after run
- `--query_model`: Embedding model for queries
- `--queries`: Path to YAML file with queries/expected labels

### Advanced Usage: Running a Top-K Sweep

To run the benchmark across multiple `topk` values in a single command, use the `--topk_sweep` argument. The script will loop through each value sequentially for each database. This is more efficient than running the script multiple times.

```sh
python benchmark.py --csv data/muse.csv --embeddings data/embeddings.parquet --dbs qdrant milvus weaviate chroma pinecone sqlite --repetitions 15 --topk_sweep 5 10 15 20 25 50
# For TopK (with higher quota): add 'topk' to the --dbs list
```

**Results:**

- Plots and tables in `results/` (per-k and summary)
- All metrics in `results/metrics.json`

---

## Embedding Generation

By default, uses `sentence-transformers/all-MiniLM-L6-v2`. To use OpenAI embeddings:

```sh
python embeddings/embed.py --csv data/muse.csv --out data/embeddings.parquet --use_openai --model text-embedding-3-large
```

---

## UI: Music Semantic Search – Multi-DB Compare

The `ui/` folder provides a FastAPI backend and static frontend for live, side-by-side DB search and latency comparison.

![Semantic Search UI Demo](semantic_search_ui_demo.png)
*Live comparison of vector databases with real-time latency measurements for music semantic search*

### UI Features

- Compare Qdrant, Milvus, Weaviate, ChromaDB, Pinecone, SQLite, and TopK in parallel
- Per-DB query latency in ms
- Simple, modern UI (HTML/JS/CSS)

### UI Quick Start

1. **Install dependencies**

```sh
pip install -r requirements.txt
```

2. **Configure**

- Create `.env` in repo root with DB endpoints and API keys

3. **Run the server**

```sh
uvicorn ui.backend.server:app --reload --port 8000
```

4. **Open the app**

- Go to [http://localhost:8000](http://localhost:8000)

---

## Project Structure

- `benchmark.py` – Main benchmarking script (CLI)
- `embeddings/embed.py` – Embedding generation (sentence-transformers or OpenAI)
- `databases/` – DB client wrappers (6-7 vector databases including TopK)
- `plot_benchmarks.py` – Plots and summary tables
- `results/` – Output metrics and plots (per-k breakdown + summaries)
- `ui/` – Web UI (FastAPI backend + static frontend)
- `BENCHMARK_REPORT.md` – Comprehensive analysis and recommendations
- `requirements.txt` – Python dependencies

---

## Troubleshooting

- If Docker ports conflict, edit `scripts/docker-compose.yml`
- If you see dimension mismatch errors, check embedding model and DB index size
- For OpenAI, set `OPENAI_API_KEY` in your environment
- For Pinecone, set API key in `.env`
- For TopK, set API key in `.env` and request quota increase from support
- Ensure sufficient disk space for Docker volumes (Milvus requires significant storage)

---

## 🎯 Benchmark Findings

This project conducted extensive benchmarking across **6 vector databases** (7 with TopK quota) with up to **20 iterations** for production-grade statistical reliability. Here are the key findings:

### Performance Rankings

**🥇 Production Winner: Qdrant**

- **Speed**: 4.3-6.8ms (often fastest)
- **Recall**: 0.97-1.0 (excellent accuracy)
- **Deployment**: Single service (operational simplicity)
- **Best for**: 99% of production systems

**🥈 Speed Contender: Milvus**

- **Speed**: 4.2-6.0ms (consistently fast)
- **Recall**: 0.94-0.98 (very good)
- **Deployment**: Complex (3 services: milvus + etcd + minio)
- **Best for**: Teams with dedicated DevOps requiring maximum speed

**🥉 Other Notable Performers:**

- **Weaviate**: Good performance but variable P99 latencies
- **ChromaDB**: Solid for development, lower recall at scale
- **Pinecone**: Perfect recall but network latency (~105ms)
- **SQLite**: Perfect for embedded use cases (~28ms)
- **TopK**: Untested due to quota limitations (requires support approval)

### Key Insights

1. **Performance Parity**: Extended testing reveals Qdrant often matches or exceeds Milvus performance
2. **Operational Complexity**: Milvus requires 3x more operational overhead with minimal speed advantage
3. **Statistical Reliability**: Longer iteration testing (15-20 runs) provides more accurate production predictions
4. **Recall Consistency**: Qdrant and SQLite consistently deliver perfect/near-perfect recall

### Recommendation

**Choose Qdrant for production deployments** - it delivers equivalent performance with zero operational complexity penalty. See `BENCHMARK_REPORT.md` for detailed analysis.

---

## Acknowledgements

- [Muse Musical Sentiment dataset](https://www.kaggle.com/datasets/cakiki/muse-the-musical-sentiment-dataset)
- [sentence-transformers](https://www.sbert.net/)
- [Qdrant](https://qdrant.tech/), [Milvus](https://milvus.io/), [Weaviate](https://weaviate.io/), [ChromaDB](https://www.trychroma.com/), [Pinecone](https://www.pinecone.io/), [TopK](https://www.topk.io/), [sqlite-vec](https://github.com/asg017/sqlite-vec)
