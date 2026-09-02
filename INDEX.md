# Use cases

Land, copy a snippet, take a key, build. Every example uses the live roster on one prepaid balance: embed, rerank, then a chat model. No product-specific SDK to remove later.

These are working shapes, not benchmarks. Throughput on embed and rerank is best-effort by contract (retry a `429`). Generation numbers live on the [model pages](/model), each with its curl.

| Use case | What you build | Models |
|---|---|---|
| [Agent memory](./agent-memory.md) | Remember facts across turns: embed once, retrieve, rerank, answer | `qwen/qwen3-embedding-8b` · `qwen/qwen3-reranker-8b` · `zai/glm-5.3-flash` |
| [Company knowledge base](./company-knowledge-base.md) | Ingest papers and notes, let the model file them, then ask with citations | `qwen/qwen3-embedding-8b` · `qwen/qwen3-reranker-8b` · `qwen/qwen3.8-27b` |

Get an [API key](/login). Base URL `https://api.tiyuvta.ai/v1`. Export `TIYUVTA_KEY`.
